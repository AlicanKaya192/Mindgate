// Runs inside the page: measures the rendered state, returns findings, measurements and the inventory. It does not change the page and does not go out to the network.
(() => {
  const MAX_EXAMPLES = 8;
  const MAX_ELEMENTS = 6000;
  const MOBILE_LIMIT = 768;
  const CONTROL = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[tabindex]:not([tabindex="-1"])';
  const CODE_TAGS = new Set(["CODE", "PRE", "KBD", "SAMP"]);
  const SKIPPED = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "HEAD", "META", "LINK", "TITLE"]);

  // On a mobile browser an overflowing page enlarges innerWidth; the real screen width is clientWidth.
  const width = document.documentElement.clientWidth;
  const height = document.documentElement.clientHeight;
  const isMobile = width < MOBILE_LIMIT;
  const findings = [];
  const findingCounts = {};

  function add(rule, severity, element, detail) {
    findingCounts[rule] = (findingCounts[rule] || 0) + 1;
    if (findingCounts[rule] > MAX_EXAMPLES) return;
    findings.push({ rule, severity, selector: element ? selector(element) : "page", detail });
  }

  function selector(element) {
    const classes = (element.getAttribute("class") || "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
    return element.tagName.toLowerCase() + (element.id ? `#${element.id}` : "") + classes.map((c) => `.${c}`).join("");
  }

  function plain(text) {
    return (text || "").replace(/\s+/g, " ").trim().slice(0, 120);
  }

  function isVisible(element, style, box) {
    return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0" && box.width > 1 && box.height > 1;
  }

  const elements = [...document.querySelectorAll("body *")]
    .filter((element) => !SKIPPED.has(element.tagName))
    .slice(0, MAX_ELEMENTS)
    .map((element) => ({ element, style: getComputedStyle(element), box: element.getBoundingClientRect() }))
    .filter((e) => isVisible(e.element, e.style, e.box));

  const directText = (element) =>
    [...element.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join("").trim();
  const withText = elements.filter((e) => directText(e.element));
  const inCode = (element) => CODE_TAGS.has(element.tagName) || !!element.closest("code,pre,kbd,samp");

  // The browser may return a color as oklch, color-mix and similar; painting it on a canvas reduces all of them to RGB.
  const canvas = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
  const colorCache = new Map();
  function color(value) {
    if (colorCache.has(value)) return colorCache.get(value);
    canvas.clearRect(0, 0, 1, 1);
    canvas.fillStyle = "#000";
    canvas.fillStyle = value;
    canvas.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = canvas.getImageData(0, 0, 1, 1).data;
    const result = { r, g, b, a: a / 255 };
    colorCache.set(value, result);
    return result;
  }

  function composite(top, bottom) {
    const a = top.a;
    return { r: top.r * a + bottom.r * (1 - a), g: top.g * a + bottom.g * (1 - a), b: top.b * a + bottom.b * (1 - a), a: 1 };
  }

  // An image or gradient background has no single color; null is returned instead of a wrong finding.
  function background(element) {
    const layers = [];
    for (let e = element; e; e = e.parentElement) {
      const style = getComputedStyle(e);
      if (style.backgroundImage !== "none") return null;
      const c = color(style.backgroundColor);
      if (c.a > 0) layers.push(c);
      if (c.a === 1) break;
    }
    return layers.reverse().reduce((under, over) => composite(over, under), { r: 255, g: 255, b: 255, a: 1 });
  }

  function luminance({ r, g, b }) {
    const channel = (d) => { const c = d / 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  }

  function contrast(a, b) {
    const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (light + 0.05) / (dark + 0.05);
  }

  function accumulatedOpacity(element) {
    let total = 1;
    for (let e = element; e; e = e.parentElement) total *= parseFloat(getComputedStyle(e).opacity);
    return total;
  }

  let unmeasurableContrast = 0;
  function checkContrast() {
    for (const { element, style } of withText) {
      const back = background(element);
      if (!back) { unmeasurableContrast++; continue; }
      const text = color(style.color);
      const seen = composite({ ...text, a: text.a * accumulatedOpacity(element) }, back);
      const size = parseFloat(style.fontSize);
      const isLarge = size >= 24 || (size >= 18.66 && parseInt(style.fontWeight, 10) >= 700);
      const limit = isLarge ? 3 : 4.5;
      const ratio = contrast(seen, back);
      if (ratio < limit) add("T03", "error", element, `contrast ${ratio.toFixed(2)}:1, at least ${limit}:1`);
    }
  }

  function hasClippingAncestor(element) {
    for (let e = element.parentElement; e && e !== document.body; e = e.parentElement) {
      const s = getComputedStyle(e);
      if (s.overflowX !== "visible" || s.position === "fixed") return true;
    }
    return false;
  }

  function checkOverflow() {
    const overflow = document.documentElement.scrollWidth - width;
    if (overflow > 1) add("T01", "error", null, `horizontal scroll: ${overflow}px overflow`);
    for (const { element, style, box } of elements) {
      const outside = box.right > width + 1 || box.left < -1;
      if (outside && style.position !== "fixed" && !hasClippingAncestor(element)) add("T02", "error", element, `off screen: ${Math.round(box.left)}–${Math.round(box.right)}px`);
    }
  }

  const isInlineTextLink = (element, style) => element.tagName === "A" && style.display === "inline" && !!directText(element.parentElement);
  const isLabelledChoice = (element) => /^(checkbox|radio)$/.test(element.type || "") && element.labels && element.labels.length > 0;
  const controls = elements.filter((e) => e.element.matches(CONTROL));

  function checkTargets() {
    for (const { element, style, box } of controls) {
      if (isInlineTextLink(element, style) || isLabelledChoice(element)) continue;
      const size = `${Math.round(box.width)}×${Math.round(box.height)}px`;
      if (box.width < 24 || box.height < 24) add("T04", "error", element, `target ${size}, at least 24×24`);
      else if (isMobile && (box.width < 44 || box.height < 44)) add("T04", "warning", element, `touch target ${size}, at least 44 on mobile`);
      if (isMobile && /^(INPUT|SELECT|TEXTAREA)$/.test(element.tagName) && parseFloat(style.fontSize) < 16) add("T05", "warning", element, `input text ${style.fontSize}, below 16px iOS zooms in`);
    }
  }

  function dominantTextSize() {
    const total = new Map();
    for (const { element, style } of withText) {
      if (inCode(element)) continue;
      const size = parseFloat(style.fontSize);
      total.set(size, (total.get(size) || 0) + directText(element).length);
    }
    return [...total.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? 0;
  }

  // Only text nodes are counted, so the boxes of icons and inner elements are not taken for lines.
  function countLines(nodes, element) {
    const range = document.createRange();
    const tops = [];
    for (const node of nodes) {
      if (!node.textContent.trim()) continue;
      range.selectNodeContents(node);
      for (const box of range.getClientRects()) if (box.width > 1) tops.push(box.top);
    }
    tops.sort((a, b) => a - b);
    const threshold = parseFloat(getComputedStyle(element).fontSize) * 0.6;
    return tops.filter((t, i) => i === 0 || t - tops[i - 1] > threshold).length;
  }

  function lineCount(element) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    return countLines(nodes, element);
  }

  const directLineCount = (element) => countLines([...element.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE), element);

  function checkReading(dominant) {
    const limit = isMobile ? 16 : 14;
    if (dominant && dominant < limit) add("T06", "warning", null, `dominant text ${dominant}px, at least ${limit}px`);
    for (const { element, style } of withText) {
      if (inCode(element) || !element.matches("p,li,blockquote,dd,figcaption,div")) continue;
      const lines = lineCount(element);
      if (lines < 2) continue;
      const average = element.textContent.trim().length / lines;
      if (average > 90) add("T07", "warning", element, `~${Math.round(average)} characters per line, at most 90`);
      const size = parseFloat(style.fontSize);
      const lineHeight = parseFloat(style.lineHeight);
      if (size < 24 && lineHeight && lineHeight / size < 1.2) add("T08", "warning", element, `line height ${Math.round((lineHeight / size) * 100)}%, at least 120%`);
    }
  }

  const firstFamily = (style) => style.fontFamily.split(",")[0].replace(/["']/g, "").trim().toLowerCase();

  function countProperty(read) {
    return new Set(elements.map((e) => read(e.style)).filter(Boolean));
  }

  function checkSystem() {
    const families = new Set(withText.filter((e) => !inCode(e.element)).map((e) => firstFamily(e.style)));
    if (families.size > 2) add("T09", "warning", null, `${families.size} font families: ${[...families].join(", ")}`);

    const spacings = elements.flatMap((e) => [e.style.paddingTop, e.style.paddingRight, e.style.paddingBottom, e.style.paddingLeft, e.style.rowGap, e.style.columnGap]).map(parseFloat).filter((d) => d > 0);
    const offScale = spacings.filter((d) => Math.abs(d / 4 - Math.round(d / 4)) > 0.05);
    if (spacings.length >= 20 && offScale.length / spacings.length > 0.25) add("T10", "note", null, `${Math.round((offScale.length / spacings.length) * 100)}% of spacings are outside the 4-step scale`);

    const family = colorFamilies();
    if (family.size > 4) add("T11", "note", null, `${family.size} color families; there may be too much color`);

    const pageBackground = background(document.body);
    const pure = (c) => c && ((c.r === 0 && c.g === 0 && c.b === 0) || (c.r === 255 && c.g === 255 && c.b === 255));
    if (pure(pageBackground) || pure(color(getComputedStyle(document.body).color))) add("T12", "note", null, "pure black or white; near black or near white is easier on the eye");

    const shadows = countProperty((s) => (s.boxShadow === "none" ? "" : s.boxShadow));
    if (shadows.size > 3) add("T13", "note", null, `${shadows.size} different shadows; use one depth technique`);
    if (shadows.size > 0 && pageBackground && luminance(pageBackground) < 0.05) add("T13", "note", null, "shadow in a dark interface; surface lightness works better");
    return { family, families, shadows };
  }

  function hueFamily({ r, g, b, a }) {
    const max = Math.max(r, g, b) / 255;
    const min = Math.min(r, g, b) / 255;
    const range = max - min;
    const light = (max + min) / 2;
    if (a < 0.5 || range === 0 || light < 0.15 || light > 0.9) return null;
    if (range / (1 - Math.abs(2 * light - 1)) < 0.25) return null;
    const [cr, cg, cb] = [r / 255, g / 255, b / 255];
    const hue = max === cr ? ((cg - cb) / range + 6) % 6 : max === cg ? (cb - cr) / range + 2 : (cr - cg) / range + 4;
    return Math.round((hue * 60) / 30) % 12;
  }

  function colorFamilies() {
    const family = new Set();
    for (const { style } of elements) {
      for (const value of [style.backgroundColor, style.color, style.borderTopColor]) {
        const h = hueFamily(color(value));
        if (h !== null) family.add(h);
      }
    }
    return family;
  }

  function checkCorners() {
    for (const { element, style, box } of elements) {
      const parent = element.parentElement;
      if (!parent || parent === document.body) continue;
      const parentBox = parent.getBoundingClientRect();
      // The browser limits the radius to half the box: a 999px pill is really as round as half its height.
      const effective = (radius, b) => Math.min(parseFloat(radius), b.width / 2, b.height / 2);
      const outer = effective(getComputedStyle(parent).borderTopLeftRadius, parentBox);
      const own = effective(style.borderTopLeftRadius, box);
      if (!(outer > 0 && own > 0) || style.borderTopLeftRadius.endsWith("%")) continue;
      const gap = Math.min(box.left - parentBox.left, box.top - parentBox.top);
      if (gap >= 0 && gap < outer && own > outer - gap + 2) add("T14", "warning", element, `inner corner ${own}px, should be ${outer} − ${gap} = ${outer - gap}px`);
    }
  }

  const seconds = (value) => Math.max(...value.split(",").map((d) => (d.trim().endsWith("ms") ? parseFloat(d) / 1000 : parseFloat(d))));

  function checkMotion() {
    let hasMotion = false;
    for (const { element, style } of elements) {
      const duration = seconds(style.transitionDuration);
      if (style.animationName !== "none" || duration > 0) hasMotion = true;
      if (duration > 0 && style.transitionProperty.split(",").some((p) => p.trim() === "all")) add("T15", "warning", element, "transition: all; list the properties one by one");
      if (duration > 0.3 && element.matches(CONTROL)) add("T16", "warning", element, `transition ${duration * 1000}ms, at most 300ms`);
    }
    if (hasMotion && hasReducedMotionRule() === false) add("T27", "warning", null, "there is motion but no prefers-reduced-motion counterpart");
  }

  // A style sheet from another domain cannot be read; when unsure, null is returned so no finding is made.
  function hasReducedMotionRule() {
    const contains = (rules) => [...rules].some((r) => (r.media && r.media.mediaText.includes("prefers-reduced-motion")) || (r.cssRules && contains(r.cssRules)));
    let unreadable = false;
    for (const sheet of document.styleSheets) {
      try { if (contains(sheet.cssRules)) return true; } catch { unreadable = true; }
    }
    return unreadable ? null : false;
  }

  function accessibleName(element) {
    return plain(element.getAttribute("aria-label") || element.getAttribute("title") || element.textContent || element.querySelector("img[alt]")?.alt || "");
  }

  function fieldLabel(element) {
    const label = element.labels && element.labels.length ? element.labels[0].textContent : "";
    return plain(label || element.getAttribute("aria-label") || element.getAttribute("title") || "");
  }

  function checkNames() {
    for (const { element } of elements) {
      if (element.tagName === "IMG" && !element.hasAttribute("alt")) add("T17", "error", element, "image has no alt");
      else if (/^(INPUT|SELECT|TEXTAREA)$/.test(element.tagName) && !/^(submit|button|reset)$/.test(element.type) && !fieldLabel(element) && !element.hasAttribute("aria-labelledby")) add("T17", "error", element, "field has no label");
      else if (element.matches('button,a[href],[role=button]') && !accessibleName(element) && !element.hasAttribute("aria-labelledby")) add("T17", "error", element, "control has no name");
    }
    const text = document.body.innerText;
    const placeholder = text.match(/lorem ipsum|john doe|jane doe|sarah johnson|acme (inc|corp)/i);
    if (placeholder) add("T18", "warning", null, `placeholder content: ${placeholder[0]}`);
  }

  function checkTraces() {
    let smallUppercase = 0;
    let monoLabel = 0;
    for (const { element, style } of elements) {
      const clip = style.webkitBackgroundClip || style.backgroundClip;
      if (clip === "text") add("T19", "note", element, "gradient text");
      const left = parseFloat(style.borderLeftWidth);
      const others = Math.max(parseFloat(style.borderTopWidth), parseFloat(style.borderRightWidth), parseFloat(style.borderBottomWidth));
      if (left >= 3 && others <= 1 && parseFloat(style.borderTopLeftRadius) > 0) add("T20", "note", element, "single side stripe on a rounded card");
    }
    for (const { element, style } of withText) {
      const size = parseFloat(style.fontSize);
      if (style.textTransform === "uppercase" && size <= 13) smallUppercase++;
      if (size <= 13 && !inCode(element) && /mono|courier|consolas/i.test(style.fontFamily)) monoLabel++;
      if (element.matches("button,a,h1,h2,h3,[role=button]")) {
        const text = directText(element);
        if (/\p{Extended_Pictographic}/u.test(text.replace(/[©®™]/g, ""))) add("T23", "note", element, "emoji instead of an icon");
        if (/[→➜]\s*$/.test(text)) add("T24", "note", element, "arrow at the end of the text");
      }
      if (element.tagName === "TD" && /\d/.test(directText(element)) && /^[\d.,%\s₺$€+-]+$/.test(directText(element)) && !style.fontVariantNumeric.includes("tabular-nums")) add("T26", "note", element, "no tabular-nums on the numbers");
    }
    if (smallUppercase >= 3) add("T21", "note", null, `${smallUppercase} small uppercase labels`);
    if (monoLabel >= 3) add("T22", "note", null, `${monoLabel} small monospace labels`);
  }

  function checkLabelBreaks() {
    // A button with several blocks, like a card, is not a finding; it is reported only when a single text itself breaks.
    for (const { element } of elements) {
      if (!element.matches("button,[role=button],nav a")) continue;
      const carriers = [element, ...element.querySelectorAll("*")].filter(directText);
      if (carriers.some((e) => directLineCount(e) > 1)) add("T25", "warning", element, "label breaks across lines");
    }
  }

  function checkFocus() {
    const previousFocus = document.activeElement;
    const trace = (s) => [s.outlineStyle, s.outlineWidth, s.boxShadow, s.borderTopColor, s.backgroundColor].join("|");
    for (const { element, style } of controls.filter((c) => !c.element.disabled).slice(0, 5)) {
      const before = trace(style);
      element.focus({ preventScroll: true });
      if (document.activeElement === element && trace(getComputedStyle(element)) === before) add("T28", "warning", element, "no visible change on focus");
      element.blur();
    }
    if (previousFocus instanceof HTMLElement && previousFocus !== document.body) previousFocus.focus({ preventScroll: true });
  }

  function checkStructure() {
    const h1s = elements.filter((e) => e.element.tagName === "H1");
    if (h1s.length !== 1) add("T30", "warning", null, `${h1s.length} h1 elements, there should be 1`);
    const bottom = Math.max(0, ...withText.map((e) => e.box.bottom), ...controls.map((e) => e.box.bottom));
    const documentHeight = document.documentElement.scrollHeight;
    if (documentHeight <= height + 1 && bottom < height * 0.6) add("T29", "note", null, `content ends at ${Math.round(bottom)}px, the bottom of the screen is empty`);
  }

  function sectionSpacings() {
    const root = document.querySelector("main") || document.body;
    const blocks = [...root.children].map((e) => e.getBoundingClientRect()).filter((b) => b.height > 1);
    // Side-by-side columns give a negative difference; section spacing means something only for stacked blocks.
    return blocks.slice(1).map((b, i) => Math.round(b.top - blocks[i].bottom)).filter((s) => s >= 0);
  }

  function externalResources() {
    const local = new Set([location.host, ""]);
    return [...new Set(performance.getEntriesByType("resource").map((r) => { try { return new URL(r.name).host; } catch { return ""; } }))].filter((h) => !local.has(h));
  }

  function firstScreenWords() {
    return withText.filter((e) => e.box.top < height && e.box.bottom > 0).reduce((t, e) => t + directText(e.element).split(/\s+/).filter(Boolean).length, 0);
  }

  function takeInventory() {
    const all = (s) => [...document.querySelectorAll(s)];
    return {
      links: all("a[href]").map((a) => `${accessibleName(a)} -> ${a.getAttribute("href")}`),
      buttons: all('button,[role=button],input[type=submit],input[type=button]').map((b) => accessibleName(b) || plain(b.value)),
      fields: all('input:not([type=hidden]):not([type=submit]):not([type=button]),select,textarea').map((f) => fieldLabel(f) || f.name || f.placeholder || f.type),
      headings: all("h1,h2,h3,h4,h5,h6").map((h) => `${h.tagName.toLowerCase()}: ${plain(h.textContent)}`),
      images: all("img").map((i) => plain(i.alt) || (i.getAttribute("src") || "").slice(0, 60)),
      tables: all("table").map((t) => plain(t.caption?.textContent || t.rows[0]?.textContent || "table")),
    };
  }

  checkOverflow();
  checkContrast();
  checkTargets();
  const dominant = dominantTextSize();
  checkReading(dominant);
  const system = checkSystem();
  checkCorners();
  checkMotion();
  checkNames();
  checkTraces();
  checkLabelBreaks();
  checkFocus();
  checkStructure();

  const h1 = document.querySelector("h1");
  return {
    findings,
    inventory: takeInventory(),
    measurements: {
      width,
      height,
      document_height: document.documentElement.scrollHeight,
      control_heights: [...new Set(controls.map((c) => Math.round(c.box.height)))].sort((a, b) => a - b),
      section_spacings: sectionSpacings(),
      first_screen_words: firstScreenWords(),
      h1_on_first_screen: !!h1 && h1.getBoundingClientRect().top < height,
      dominant_text: dominant,
      font_families: [...system.families],
      color_family_count: system.family.size,
      shadow_variety: system.shadows.size,
      corner_variety: countProperty((s) => (s.borderTopLeftRadius === "0px" ? "" : s.borderTopLeftRadius)).size,
      unmeasurable_contrast: unmeasurableContrast,
      external_resources: externalResources(),
      finding_counts: findingCounts,
    },
  };
})()
