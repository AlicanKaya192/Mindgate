"""Code map of a Python project: import graph between modules, import cycles, the most called functions.

Why: to answer "who calls this function, which module depends on which" in a large Python repository without reading
file by file. Files are only parsed with `ast`; none is run or imported. No network.

Every call edge carries a label:
  extracted  explicit in the source: a name in the same module, an imported name or module, a self/cls method
  guessed    `variable.method()` and the project has only one method with that name
A call that fits more than one definition becomes no edge; it is only added to the `ambiguous` count.

Usage (from the vault root):
  code_map.py <folder> [--count N]    summary report; JSON in _system/output/code_map/<folder>.json
  code_map.py <folder> --find <name>  where the name is defined and who calls it
  --exclude <path>                    a folder or file, relative to the root, that is not read (repeatable)
"""
import argparse
import ast
import json
import sys
import warnings
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import OUTPUT  # noqa: E402

SKIPPED_FOLDERS = {"__pycache__", "venv", "env", "node_modules", "build", "dist", "site-packages"}
MAX_BYTES = 2_000_000          # a larger .py is most likely generated code; it is not read
OUTPUT_DIR = OUTPUT / "code_map"
EXTRACTED, GUESSED = "extracted", "guessed"
TOO_LARGE = "too large"


@dataclass(frozen=True)
class Definition:
    name: str      # full name: pkg.mod.Class.method
    short: str
    kind: str      # function | class | method
    file: str
    line: int


@dataclass(frozen=True)
class Call:
    source: str    # full name of the calling function; the module name at module level
    target: str
    label: str
    file: str
    line: int


@dataclass
class CodeMap:
    modules: dict[str, str] = field(default_factory=dict)        # module name -> relative file path
    definitions: list[Definition] = field(default_factory=list)
    imports: set[tuple[str, str]] = field(default_factory=set)
    calls: list[Call] = field(default_factory=list)
    ambiguous: int = 0
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (relative path, reason)


# ---------- files and module names ----------
def is_outside(relative: Path, excluded: frozenset[str]) -> bool:
    if any(p in SKIPPED_FOLDERS or p.startswith(".") for p in relative.parts[:-1]):
        return True
    path = relative.as_posix()
    return any(path == e or path.startswith(f"{e}/") for e in excluded)


def module_name(relative: Path) -> str:
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def parse(text: str, file: str) -> ast.Module:
    # The code is not run; the compiler's escape-sequence warnings ("\p") belong to the project under study, not to the report
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(text, filename=file)


def read_trees(root: Path, excluded: frozenset[str], m: CodeMap) -> dict[str, tuple[ast.Module, str]]:
    trees = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if is_outside(relative, excluded):
            continue
        file = relative.as_posix()
        if path.stat().st_size > MAX_BYTES:
            m.skipped.append((file, TOO_LARGE))
            continue
        try:
            tree = parse(path.read_text(encoding="utf-8"), file)
        except (SyntaxError, ValueError, RecursionError, UnicodeDecodeError) as error:
            m.skipped.append((file, type(error).__name__))
            continue
        module = module_name(relative)
        m.modules[module] = file
        trees[module] = (tree, file)
    return trees


# ---------- definitions ----------
def collect_definitions(body: list[ast.stmt], prefix: str, in_class: bool, file: str) -> list[Definition]:
    result = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "method" if in_class else "function"
        elif isinstance(node, ast.ClassDef):
            kind = "class"
        else:
            continue
        full = f"{prefix}.{node.name}"
        result.append(Definition(full, node.name, kind, file, node.lineno))
        result += collect_definitions(node.body, full, kind == "class", file)
    return result


# ---------- imports ----------
def internal_module(dotted: str, modules: dict[str, str]) -> str | None:
    """For `pkg.sub.x`, returns the longest module prefix that exists in the project."""
    parts = dotted.split(".")
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in modules:
            return candidate
    return None


def relative_base(module: str, is_package: bool, level: int, target: str | None) -> str:
    package = module.split(".") if is_package else module.split(".")[:-1]
    base = package[:len(package) - (level - 1)] if level > 1 else package
    return ".".join([*base, *([target] if target else [])])


def resolve_imports(tree: ast.Module, module: str, file: str, m: CodeMap) -> dict[str, str]:
    """Adds edges to `m.imports`; returns the map local name -> full name in the project (module or definition)."""
    aliases, is_package = {}, file.endswith("__init__.py")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                target = internal_module(a.name, m.modules)
                if target:
                    m.imports.add((module, target))
                    # `import a.b` binds `a` locally, `import a.b as m` binds `m` to `a.b`
                    first = a.name.split(".")[0]
                    aliases[a.asname or first] = a.name if a.asname else first
        elif isinstance(node, ast.ImportFrom):
            base = relative_base(module, is_package, node.level, node.module) if node.level else node.module or ""
            for a in node.names:
                full = f"{base}.{a.name}"
                target = full if full in m.modules else internal_module(base, m.modules)
                if target:
                    m.imports.add((module, target))
                    aliases[a.asname or a.name] = full
    m.imports.discard((module, module))
    return aliases


# ---------- calls ----------
def dotted_name(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        parent = dotted_name(expr.value)
        return f"{parent}.{expr.attr}" if parent else None
    return None


class CallCollector(ast.NodeVisitor):
    def __init__(self, module: str, file: str, aliases: dict[str, str], defined: set[str],
                 methods: dict[str, list[str]], m: CodeMap):
        self.module, self.file, self.aliases, self.m = module, file, aliases, m
        self.defined, self.methods = defined, methods
        self.scope: list[tuple[str, str]] = []   # (kind, name): "class" or "function"

    def _enter(self, kind: str, node: ast.AST) -> None:
        self.scope.append((kind, node.name))
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node):
        self._enter("class", node)

    def visit_FunctionDef(self, node):
        self._enter("function", node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _caller(self) -> str:
        limit = max((i for i, (kind, _) in enumerate(self.scope) if kind == "function"), default=-1)
        return ".".join([self.module, *(n for _, n in self.scope[:limit + 1])])

    def _class(self) -> str | None:
        classes = [i for i, (kind, _) in enumerate(self.scope) if kind == "class"]
        return ".".join([self.module, *(n for _, n in self.scope[:classes[-1] + 1])]) if classes else None

    def _resolve(self, expr: ast.expr) -> tuple[str, str] | None:
        dotted = dotted_name(expr)
        if dotted is None:
            return None
        head, _, rest = dotted.partition(".")
        if not rest and f"{self.module}.{head}" in self.defined:
            return f"{self.module}.{head}", EXTRACTED
        owner = self._class()
        if head in ("self", "cls") and owner and f"{owner}.{rest}" in self.defined:
            return f"{owner}.{rest}", EXTRACTED
        if head in self.aliases:
            full = ".".join(filter(None, [self.aliases[head], rest]))
            if full in self.defined:
                return full, EXTRACTED
        # Only `variable.method()`: chains such as `self.button.clicked.connect()` are mostly objects of an outside
        # library (a GUI signal) and would be attached wrongly to the project's only method with that name
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            candidates = self.methods.get(expr.attr, [])
            if len(candidates) == 1:
                return candidates[0], GUESSED
            if len(candidates) > 1:
                self.m.ambiguous += 1
        return None

    def visit_Call(self, node):
        result = self._resolve(node.func)
        if result:
            self.m.calls.append(Call(self._caller(), result[0], result[1], self.file, node.lineno))
        self.generic_visit(node)


# ---------- map ----------
def build_map(root: Path, excluded: frozenset[str] = frozenset()) -> CodeMap:
    """`excluded`: file or folder paths relative to the root (e.g. `content`); module names are still computed from the root."""
    m = CodeMap()
    trees = read_trees(root, frozenset(excluded), m)
    for module, (tree, file) in trees.items():
        m.definitions += collect_definitions(tree.body, module, False, file)
    defined = {d.name for d in m.definitions}
    methods: dict[str, list[str]] = {}
    for d in m.definitions:
        if d.kind == "method":
            methods.setdefault(d.short, []).append(d.name)
    for module, (tree, file) in trees.items():
        aliases = resolve_imports(tree, module, file, m)
        CallCollector(module, file, aliases, defined, methods, m).visit(tree)
    return m


def import_cycles(edges: set[tuple[str, str]]) -> list[list[str]]:
    """Strongly connected components (Tarjan, without recursion): every component with at least two modules is a cycle."""
    adjacent: dict[str, list[str]] = {}
    for a, b in sorted(edges):
        adjacent.setdefault(a, []).append(b)
        adjacent.setdefault(b, [])
    order, low, stack, on_stack, counter, result = {}, {}, [], set(), 0, []
    for root in adjacent:
        if root in order:
            continue
        work = [(root, iter(adjacent[root]))]
        order[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            child = next(children, None)
            if child is None:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == order[node]:
                    component = []
                    while True:
                        top = stack.pop()
                        on_stack.discard(top)
                        component.append(top)
                        if top == node:
                            break
                    if len(component) > 1:
                        result.append(sorted(component))
            elif child not in order:
                order[child] = low[child] = counter
                counter += 1
                stack.append(child)
                on_stack.add(child)
                work.append((child, iter(adjacent[child])))
            elif child in on_stack:
                low[node] = min(low[node], order[child])
    return sorted(result)


def most_called(m: CodeMap, count: int) -> list[tuple[str, int]]:
    """Only extracted edges: guesses must not distort the ranking."""
    return Counter(c.target for c in m.calls if c.label == EXTRACTED).most_common(count)


def find(m: CodeMap, query: str) -> tuple[list[Definition], list[Call]]:
    definitions = [d for d in m.definitions if query in (d.short, d.name) or d.name.endswith(f".{query}")]
    targets = {d.name for d in definitions}
    return definitions, sorted((c for c in m.calls if c.target in targets), key=lambda c: (c.file, c.line))


def save(m: CodeMap, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {"modules": m.modules, "definitions": [asdict(d) for d in m.definitions],
            "imports": sorted(map(list, m.imports)), "calls": [asdict(c) for c in m.calls],
            "ambiguous": m.ambiguous, "skipped": m.skipped}
    target.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- command line ----------
def print_report(root: Path, m: CodeMap, count: int) -> None:
    kinds = Counter(d.kind for d in m.definitions)
    labels = Counter(c.label for c in m.calls)
    print(f"{root.name}: {len(m.modules)} modules, {kinds['class']} classes, "
          f"{kinds['function']} functions, {kinds['method']} methods")
    print(f"Import edges (between internal modules): {len(m.imports)}")
    print(f"Call edges: {labels[EXTRACTED]} extracted, {labels[GUESSED]} guessed; "
          f"ambiguous (fits more than one definition) {m.ambiguous}")
    print("Most imported modules:")
    for module, number in Counter(b for _, b in m.imports).most_common(count):
        print(f"  {module} ({number})")
    cycles = import_cycles(m.imports)
    print(f"Import cycles ({len(cycles)}):" + ("" if cycles else " none"))
    for c in cycles[:count]:
        print(f"  {' ↔ '.join(c)}")
    print("Most called (extracted edges only):")
    for target, number in most_called(m, count):
        print(f"  {target} ({number})")
    if m.skipped:
        print(f"Skipped files ({len(m.skipped)}): " + ", ".join(f"{p} ({r})" for p, r in m.skipped[:count]))


def print_find(m: CodeMap, query: str) -> None:
    definitions, callers = find(m, query)
    if not definitions:
        print(f"No definition named '{query}' was found.")
        return
    for d in definitions:
        print(f"{d.kind} {d.name} — {d.file}:{d.line}")
    print(f"Callers ({len(callers)}):")
    for c in callers:
        print(f"  {c.source} — {c.file}:{c.line} [{c.label}]")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Code map of a Python project (ast; no code is run)")
    p.add_argument("folder", type=Path)
    p.add_argument("--find", metavar="NAME", help="the definition of the name and its callers")
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--exclude", metavar="PATH", action="append", default=[],
                   help="file or folder relative to the root; repeatable (e.g. --exclude content)")
    args = p.parse_args(argv)
    root = args.folder.resolve()
    if not root.is_dir():
        print(f"ERROR: folder not found: {root}", file=sys.stderr)
        return 1
    m = build_map(root, frozenset(e.strip("/\\").replace("\\", "/") for e in args.exclude))
    if args.find:
        print_find(m, args.find)
        return 0
    print_report(root, m, args.count)
    target = OUTPUT_DIR / f"{root.name}.json"
    save(m, target)
    print(f"JSON: {target}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
