# Unreal Engine

The source pack targets UE 5.8 (5.9 in preview); version and behavior information is the owner's declaration of 11 November 2026 and was not independently verified.

## Read the project first
- The engine version is in the `*.uproject` file. Modules are in the `Build.cs` files; ask the user before adding a module.
- `.uasset` is a binary file and cannot be read with grep. Verify a change with the command line and a headless test; if that is not possible, give the user a node-by-node description and ask them for the result.

## Verification
**Scope:** Building, packaging and testing.

- A reproducible build and packaging is done with UAT (Unreal Automation Tool).
- A Shipping build has no log. Reproduce the bug in a Development or Test build.
- Run a Niagara test with `-RenderOffscreen`, not with `-nullrhi`; `-nullrhi` draws nothing at all.
- In 5.8 loose files cooked with Zen Server cannot be distributed; package with `-pak`.

## Pitfalls
- The `.generated.h` include must be the last include in the header file.
- A UObject pointer not marked with `UPROPERTY` is freed by the garbage collector (GC); the pointer becomes invalid.
- If the Enhanced Input context is added in `BeginPlay`, it does not work on the client. Test the place where you add the context in the client role.
- In a behavior tree a decorator set to `Observer Aborts None` does not cut the branch when the Blackboard key changes.
- A misspelled name fails silently: a Blackboard key, a Niagara User variable, an input action.
- A change made during Play-in-Editor can leak into assets.
