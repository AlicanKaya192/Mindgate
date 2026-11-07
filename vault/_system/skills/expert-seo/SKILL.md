---
name: expert-seo
description: Search engine optimization (SEO) expertise pack. Load when auditing the SEO of a website (especially a personal portfolio site), writing a page title and description, adding structured data (schema, JSON-LD), setting up the site and URL structure, or thinking about visibility in AI search. For interface code, load `expert-frontend` alongside.
---

Expertise pack (not an agent). The project's own rules come first. Do not give a score without measuring (#24): an item that cannot be measured is written as "not measured".

## First
- Look at how the site is produced: static, server-side rendered (SSR) or React that runs only in the browser (CSR). **If critical content is not in the raw HTML**, search engines and AI crawlers may not see it. This is the most important item on a portfolio site.
- Entering a live site is a site visit: write the address, the reason and the link verification and get permission (#32, #33). Opening a local build also needs permission.
- External SEO tools (paid crawlers, services that ask for an API key) are not used; if needed, ask the user (#23).

## Technical SEO checklist
- [ ] **robots.txt:** Does not block important pages by mistake; points to the sitemap address.
- [ ] **XML sitemap:** Contains only canonical and indexable addresses.
- [ ] **Crawlability:** Important pages are at most 3 clicks from the home page. No page that receives a link from nowhere (orphan).
- [ ] **noindex:** If present, was it put there deliberately?
- [ ] **Canonical:** On every page; a unique page points to itself. Trailing slash usage is consistent.
- [ ] **JavaScript:** Title, description, canonical, meta robots and JSON-LD are in the first HTML. Pre-rendering (SSG) for static content, SSR for general content, CSR only for pages that need login.
- [ ] **HTTPS:** Mandatory, no mixed content, an HTTP to HTTPS redirect exists. Security headers (CSP, HSTS, X-Content-Type-Options, Referrer-Policy) are good for security but their effect on ranking is small. For detail see `expert-security`.
- [ ] **Redirects:** A chain of at most 1 step; 301 for a permanent move. When an address changes, the old one is redirected.
- [ ] **Mobile:**
  - viewport tag, no horizontal scroll
  - the main content of the desktop is on mobile too
  - no interstitial covering the page
  - touch target at least 24×24 CSS pixels (WCAG 2.2; `expert-design`)
- [ ] **Core Web Vitals:** Measured at the 75th percentile of real user data. INP replaced FID in 2024.
  - LCP ≤ 2.5 s
  - INP ≤ 200 ms
  - CLS ≤ 0.1

  If you cannot measure, do not write numbers.

## On-page
- **Title:** Unique on every page, the main topic first, about 50–60 characters, consistent with the H1. Example: `AI Engineering Projects | Your Name`.
- **Meta description:** Unique, about 150–160 characters. Says what will be found on the page. No clickbait.
- **Headings:** A single H1 on the page. The H1 → H2 → H3 order is not skipped.
- **Internal links:** Link text is descriptive (not "click here"). No broken links. Important pages (projects) receive many links.
- **Images:** A descriptive file name, meaningful alt text on every image (`alt=""` on a decorative image). Compressed, in a modern format (WebP/AVIF), with dimensions given (CLS), off-screen ones lazy loaded.
- **Addresses (URL):** Readable, lowercase, separated by hyphens. No ID numbers or dates: `/projects/project-name`.
- **Trust:** Who the author is, when it was published and updated, links to sources. Do not write an address or phone number (#18); an e-mail or a profile link is enough for contact.

## Structured data (JSON-LD)
- Types for a portfolio site:
  - `Person` (name, `url`, `jobTitle`, `sameAs`: GitHub, LinkedIn)
  - `WebSite`
  - `ProfilePage` (the about page)
  - `BreadcrumbList`
  - `SoftwareSourceCode` (code projects)
  - `BlogPosting` (blog posts: `headline`, `datePublished`, `dateModified`, `author`, `image`)
- Combine several types in one block with `@graph`. `@context` and `@type` are in every block. Addresses are full (absolute), dates are in ISO format, no placeholder text is left.
- The schema says the same thing as the **visible** content of the page. No invisible or invented information (fake reviews and ratings) is added.
- **Verification:** Schema.org Validator and Google Rich Results Test. These sites are also site visits (#32).
- **Types whose rich results were dropped** (per the source, not verified):
  - `HowTo`: September 2023.
  - `FAQPage`: for all sites, May 2026.
  - `WebSite` search box (`SearchAction`): November 2024. `WebSite` is still used for the site name.

  Do not recommend these types for getting rich results.

## Site structure (portfolio)
- Flat structure, at most 2 levels. Example: home page, `/projects`, `/projects/<name>`, `/blog`, `/blog/<post>`, `/about`.
- Navigation of 4–7 items; the logo goes to the home page.
- Breadcrumb mirrors the address structure; all but the last item are clickable.
- Suggestion output: an ASCII tree or an address table (address, page, purpose, internal links).

## Visibility in AI search
- No separate "writing for AI" is needed; good SEO and clear content are the basis. The sources say special markup is not required.
- Concrete methods:
  - A clear answer to the question at the start of the section.
  - Descriptive headings, short paragraphs, comparisons in tables.
  - Author and date visible; a link to the primary source.
  - Critical content is visible without JavaScript.
- **AI crawlers** (robots.txt): Those for search (OAI-SearchBot, Claude-SearchBot, PerplexityBot) are separate from those for training (GPTBot, ClaudeBot, CCBot, Google-Extended). Allowing or not allowing training crawlers is the user's choice; ask. Google-Extended has no effect on ranking (per the source).
- **`llms.txt`:** No effect for Google search (per the source). Optional for other AI systems. Two sources conflict on this; do not recommend it as a ranking tool.
- Percentages and ratios in the sources (e.g. "30–40% more visible with schema") were not verified; they are not used.

## Audit report format
**Summary:** overall state, the 3–5 most important problems, quick wins.

| Priority | Area | Problem | Evidence (address, file:line, command output) | Fix |
|---|---|---|---|---|

Priority levels:
- **Critical:** blocks indexing
- **High**
- **Medium**
- **Low**
- **Info**

An unmeasured area is written as "not measured"; no score is invented.

## Verify before finishing (#24)
- [ ] The raw HTML was looked at (not the view in the browser): are the title, description, canonical and JSON-LD there?
- [ ] The JSON-LD is valid JSON and consistent with the visible content.
- [ ] Every suggested change has evidence. A Google policy that is not verified is marked "per the source".

## Idea sources
- coreyhaines31/marketingskills (MIT, Corey Haines): `seo-audit`, `schema`, `site-architecture`, `ai-seo`.
- agricidaniel/claude-seo (MIT): `seo-audit`, `seo-technical`, `seo-schema`, `seo-geo`.

Both were read from downloaded copies on 13 October 2026; their match with the official repositories was not verified. Paid tool suggestions, steps that ask for an API key, install scripts and unverified statistics were not adopted.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
