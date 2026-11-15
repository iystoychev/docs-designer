# Designing a docs-designer theme

A theme gives every document a different look without touching its content: other
typefaces, another type scale, a different front page, another way of setting
headings, tables, callouts and the running header and footer. Every theme styles
**the same markup**, so any document can switch theme at any time and be re-printed.

A theme is one JSON object:

```json
{ "name": "Swiss Grid", "description": "One sentence: what it looks and feels like.",
  "css": "/* the stylesheet */", "tokens": { "decision": "#D7261E" } }
```

- `css` is layered **after** docs-designer's base stylesheet (`style.css`), so it only
  needs what it changes. Start from the base rules below and override.
- `tokens` are colour overrides applied last; they are what the GalleyDocs colour editor
  changes. Set your palette as tokens in `:root` inside `css` too, so it stays whole.

## The page

- A4, printed by Chrome. Base margins: 22mm top, 25mm sides, 24mm bottom; the first
  page 18mm 20mm 24mm. The text block is 160mm wide: a 34mm **rail** (`--rail`), an 8mm
  gap (`--gap`) and a 118mm measure; `--indent` is rail + gap. One baseline unit is
  `--step` (14.6pt).
- **`@page { background: … }` is a literal colour in the base: set it to your paper
  colour**, or the page margins show the base's off-white.
- The running header and footer are `@page` margin boxes. The base sets their fonts and
  colours literally, so restyle all four in your theme:
  - `@top-left` holds the kind, `@top-right` the title, and `@bottom-left` the byline.
    The renderer fills their text, so never set `content` on these three.
  - `@bottom-right` holds `counter(page) " / " counter(pages)`, and you may change its `content`.

  The first page has no header or footer.

## The markup

Every document is `<body class="kind-{report|memo|guide|proposal|requirements}">`, then a
front (`header.front`), then `<main class="doc">` with the body. `<html lang>` is `en` or `bg`.

### Front pages

```html
<!-- report, proposal: a full cover page (title low, form below) -->
<header class="front cover">
  <div class="masthead"><span class="kind">Report</span><span class="when">15 November 2026</span></div>
  <div class="titling">
    <h1><span class="w">Each</span> <span class="w">word</span> …</h1>
    <p class="subtitle">…</p>                       <!-- optional -->
  </div>
  <div class="form">                                <!-- a ruled grid of cells -->
    <div class="cell wide-2"><span class="field">Author</span><span class="value">…</span></div>
    <div class="cell"><span class="field">Date</span><span class="value"><time>…</time></span></div>
    <div class="cell"><span class="field">Any meta key</span><span class="value">…</span></div>
    <div class="cell full abstract"><span class="field">Summary</span><p class="value">…</p></div>
    <div class="cell full outcome"><span class="field">Recommendation</span><p class="value">…</p></div>
  </div>
</header>
<!-- guide, requirements: header.front.cover.cover-map, title high, then the form,
     then <nav class="contents"><span class="field">Contents</span><ol><li>Section</li>…</ol></nav> -->
<!-- memo: header.front.memo-head, no cover page: masthead, h1, subtitle, form,
     then the body continues on the same page -->
```

- Proposals put the outcome cell first.
- The order of cells varies by kind.
- `abstract`, `outcome`, `subtitle` and the meta cells are all optional.
- `.cover` is **exactly one page** in the base (`height: 255mm; break-after: page`). Either keep it exactly one page (change that height if you change the first page's margins), or let the body start on it (`height: auto; break-after: auto`), as a newspaper front page does.

### Body

| Markup | What it is |
|---|---|
| `p.lede` | optional opening paragraph |
| `h2`, `h3` | numbered sections. The base puts the number in the rail (`h2::before`, `h3::before`) from counters `h2` and `h3` |
| `h4` | an unnumbered sub-head |
| `p`, `ul`, `ol`, `strong`, `em`, `code`, `a` | prose |
| `ol.requirements > li` | requirements, numbered across the document (counter `req`), the number in the rail |
| `ol.steps > li` | a procedure; "Step n" sits in the rail (counter `step`) |
| `div.callout.decision` / `.warning` / `.note` / `.aside` | callouts; the label (`::before`) sits in the rail. `[data-label]` renames it |
| `dl.keyfacts > div > dt + dd` | 3, 6 or 9 facts in a ruled grid |
| `pre[data-label] > code > span.ln` | code; one `span.ln` per source line |
| `table` (`caption`, `thead`, `tbody`, `tfoot`, `td.num`, `tr.group`, `table.long`) | tables; "Table n" is `caption::before` |
| `blockquote > p + cite` | a quotation |
| `figure > (svg or img) + figcaption` | a figure; "Figure n" is `figcaption::before` |

`pre`, `table`, `figure` and `.keyfacts` span the rail and the measure.

**Labels are translated in CSS.** "Note", "Decision", "Warning", "Aside", "Step", "Table" and "Figure" come from `content`, with `:lang(bg)` versions. Style them freely. If you change their wording, give the Bulgarian rules too, and keep `.callout[data-label]::before { content: attr(data-label) }` winning.

## Tokens (CSS custom properties)

| Token | Role |
|---|---|
| `--paper` | page ground |
| `--ink`, `--ink-2` | text, secondary text |
| `--rule`, `--rule-strong` | hairlines, structural rules |
| `--tint` | code and group rows |
| `--decision`, `--decision-wash` | decisions and the front-page outcome **only** |
| `--warning`, `--warning-mark`, `--warning-wash` | warnings **only** |

Also: `--sans`, `--serif`, `--mono` (font stacks), and `--rail`, `--gap`, `--indent`, `--step` (geometry). Colour carries meaning: keep decision and warning distinct from each other and from everything else.

## Fonts

A theme may use only these families. Images can be `url(data:image/png…)` or `url(data:image/svg+xml…)`; nothing can be loaded from anywhere else.

| Family | Weights | Italic | Character |
|---|---|---|---|
| Roboto Flex | 100–1000, width 25–151% | – | the base sans; condensed to extended |
| Source Serif 4 | 200–900 | yes | the base serif |
| JetBrains Mono | 400–700 | – | the base mono |
| IBM Plex Sans | 100–700 | yes | neutral, engineered grotesk |
| IBM Plex Serif | 400, 600, 700 | 400 | sturdy, technical serif |
| IBM Plex Mono | 400, 500, 600 | – | drawing-office mono |
| Playfair Display | 400–900 | yes | high-contrast display serif (headlines, not text) |
| EB Garamond | 400–800 | yes | classic book face |
| Literata | 200–900 | yes | warm reading serif for long text |
| Oswald | 200–700 | – | condensed gothic, headlines and labels |
| Unbounded | 200–900 | – | wide geometric display (titles only) |
| Manrope | 200–800 | – | geometric humanist sans |

Every family covers Latin and Cyrillic (Bulgarian). Set fallbacks in the stack, for example `"Literata", Georgia, serif`.

## Rules (a theme is refused otherwise)

- The CSS is at most 64 KB.
- It may not contain `<`, `@import`, `@font-face`, `@charset`, `@namespace`, `expression(`, `javascript:`, `behavior:` or `-moz-binding`.
- `url(…)` is allowed only with `data:image/png` or `data:image/svg+xml`.

## The quality bar

- **It reads as a document first.** Body text is at least 9pt. Labels are at least 6pt and stay readable in print.
- **Contrast:** text against its ground is at least 4.5:1, labels at least 4.5:1, and large display type at least 3:1, including white on `--decision`.
- **The whole range works:**
  - all five kinds, each front page designed rather than left to the base;
  - Bulgarian titles and labels;
  - long titles (four lines) and short ones;
  - a memo that continues on its first page;
  - a long table that breaks across pages.
- **It's a world of its own,** not the base in other colours. Commit to a direction: type pairing, a scale, how sections announce themselves, what the cover does. Then carry it through every element, including the running header and footer.
- **Restraint where it counts.** Ornament lives on the front page and in headings. Paragraphs, tables and code stay calm and legible.
