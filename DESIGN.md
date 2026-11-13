---
name: docs-designer
description: One versatile A4 document system; five document kinds share one ruled design language, each with a front page shaped for its job.
colors:
  paper: "#F6F7F5"
  ink: "#121417"
  ink-2: "#4A4F57"
  rule: "#C9CCD1"
  rule-strong: "#121417"
  tint: "#ECEEEC"
  decision: "#2B3FD6"
  decision-wash: "#E9ECFB"
  on-decision: "#FFFFFF"
  warning: "#8A5A00"
  warning-mark: "#E0A100"
  warning-wash: "#FBF2DC"
typography:
  display:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "48pt"
    fontWeight: 720
    lineHeight: 0.98
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 70"
  display-memo:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "30pt"
    fontWeight: 720
    lineHeight: 0.98
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 75"
  kind:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "9pt"
    fontWeight: 750
    letterSpacing: "0.16em"
    fontVariation: "'wdth' 125"
  subtitle:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "15pt"
    fontWeight: 400
    lineHeight: 1.3
  outcome:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "15pt"
    fontWeight: 650
    lineHeight: 1.22
    fontVariation: "'wdth' 88"
  headline:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "15pt"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.005em"
    fontVariation: "'wdth' 85"
  title:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "10.5pt"
    fontWeight: 650
    lineHeight: 1.35
    fontVariation: "'wdth' 95"
  subhead:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "9.5pt"
    fontWeight: 650
    lineHeight: 1.35
    fontVariation: "'wdth' 95"
  value:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "11pt"
    fontWeight: 620
    lineHeight: 1.25
    fontVariation: "'wdth' 92"
  contents:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "10.5pt"
    fontWeight: 560
    lineHeight: 1.3
    fontVariation: "'wdth' 92"
  lede:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "12.5pt"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "10pt"
    fontWeight: 400
    lineHeight: "14.6pt"
    fontFeature: "'locl' 0"
  data:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "8.5pt"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "'tnum'"
  caption:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "7.5pt"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Roboto Flex, Helvetica Neue, Arial, sans-serif"
    fontSize: "6.8pt"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.1em"
    fontVariation: "'wdth' 112"
  code:
    fontFamily: "JetBrains Mono, Menlo, monospace"
    fontSize: "8pt"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  none: "0"
  code: "1pt"
spacing:
  step: "14.6pt"
  rail: "34mm"
  gap: "8mm"
  indent: "42mm"
components:
  masthead:
    textColor: "{colors.ink}"
    typography: "{typography.kind}"
    padding: "3mm 0 0"
  form-cell:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.value}"
    rounded: "{rounded.none}"
    padding: "2.2mm 3mm 3.2mm"
    height: "17mm"
  form-cell-abstract:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "2.2mm 3mm 3.2mm"
  form-cell-outcome:
    backgroundColor: "{colors.decision}"
    textColor: "{colors.on-decision}"
    typography: "{typography.outcome}"
    rounded: "{rounded.none}"
    padding: "2.2mm 3mm 5mm"
  contents-item:
    textColor: "{colors.ink}"
    typography: "{typography.contents}"
    padding: "2mm 0 2.2mm"
  section-heading:
    textColor: "{colors.ink}"
    typography: "{typography.headline}"
    padding: "2.5mm 0 0"
  callout-note:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "2.4mm 0 2.6mm"
  callout-aside:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "2.4mm 0 2.6mm"
  callout-decision:
    backgroundColor: "{colors.decision-wash}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "2.4mm 3.5mm 2.6mm"
  callout-warning:
    backgroundColor: "{colors.warning-wash}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "2.4mm 3.5mm 2.6mm"
  keyfacts-cell:
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "2mm 3mm 2.6mm"
  step:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "2mm 0 2.4mm"
  requirement:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "1.6mm 0 1.8mm"
  code-block:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
    typography: "{typography.code}"
    rounded: "{rounded.none}"
    padding: "3.5mm 4mm 3.5mm 42mm"
  code-inline:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.code}"
    padding: "0.2mm 1mm"
  table:
    textColor: "{colors.ink}"
    typography: "{typography.data}"
    padding: "1.8mm 3mm 1.8mm 0"
---

# Design System: docs-designer

## Overview

**Creative North Star: "One Form, Five Kinds"**

Every document is filled in on the same ruled form. Five kinds (report, memo, guide, proposal, technical requirements) share one design language and one set of front-page parts: a 3pt masthead rule with the kind name in extended capitals on the left and the date on the right, a condensed grotesk title, an optional italic serif subtitle, and a ruled grid of form cells holding the author, the date, any extra fields, a summary and the key point struck in solid cobalt. What changes per kind is only the order and placement of those parts, chosen for the document's job: a report sets its title low over the form, a proposal leads its form with the recommendation, a guide or requirements document sets its title high and anchors a contents map at the foot, and a memo drops the cover and starts its body on page one.

Body pages are the same for every kind. A 34mm rail on the left holds section numbers, sub-section numbers and the label of every component; a 118mm measure carries serif prose; wide elements span both. The material is cool paper and near-black ink, structured by rules of graded weight rather than boxes or shadows. Colour is rationed by meaning: cobalt marks decisions and the front-page key point, amber marks warnings, and everything else is ink on paper. Density is that of a well-set working document: 10pt serif on a 14.6pt step, generous space before numbered sections, nothing decorative.

The system is print-native and bilingual. It is defined in physical units (pt, mm), printed to A4 by headless Chrome through `@page` margin boxes, and has no hover, focus, motion or responsive behaviour. Every face covers Latin and Cyrillic, and every printed word of apparatus (kind names, field names, rail labels, dates) switches between English and Bulgarian with the document's language. A document ends with its last body section: there is no closing colophon, no issue number and no series name.

**Key Characteristics:**
- One set of front-page parts (masthead, title, ruled form, cobalt key point, contents map), arranged per kind.
- A left rail (34mm) that carries numbers and component labels; prose never enters it.
- Roboto Flex on its width axis for the title, headings, labels and form; Source Serif 4 for prose; JetBrains Mono only for code.
- Structure by rules of graded weight; no shadows, no rounded containers.
- Colour by role only: cobalt for decisions and the key point, amber for warnings.
- Author and date on the front-page form and in every following page's running footer.
- English and Bulgarian with one set of Cyrillic letterforms across all three faces.

## Colors

A near-monochrome ink-on-paper palette with two rationed signal colours, each owning exactly one meaning.

### Primary
- **Decision Cobalt** (`decision`): the key-point cell on the front page (labelled Outcome, Decision, Goal, Recommendation or Objective by kind), and the rules and rail label of decision callouts. It means "this is the point" or "this was decided". Nothing else is cobalt.
- **Cobalt Wash** (`decision-wash`): the ground of decision callouts.
- **On-Cobalt White** (`on-decision`): text in the cobalt cell; its field label drops to 84% opacity.

### Secondary
- **Warning Amber Ink** (`warning`): the rail label of warning callouts; the only amber that carries text.
- **Warning Amber Mark** (`warning-mark`): the top and bottom rules of warning callouts. Never used for text.
- **Warning Wash** (`warning-wash`): the ground of warning callouts.

### Neutral
- **Cool Paper** (`paper`): the page itself, printed edge to edge (`print-color-adjust: exact`), including the `@page` margins.
- **Ink** (`ink`): prose, headings, form values, section and requirement numbers, the running footer.
- **Graphite** (`ink-2`): secondary text: field names, the running header, the subtitle, captions, table heads, sub-section numbers, list markers, link underlines.
- **Hairline Grey** (`rule`): 0.5pt separators: table rows, step and requirement dividers, contents rows, blockquote and code-block rules, aside callouts, the footer rule.
- **Strong Rule** (`rule-strong`, the ink value): structural rules: masthead, form grid, contents head, section heads, note callouts, key-facts grid, table head and foot.
- **Tint** (`tint`): the ground of code blocks, inline code and table group rows.

### Named Rules
**The Rationed Colour Rule.** Cobalt means the key point or a decision and amber means warning. Neither is used for emphasis, links, headings, diagrams or decoration. A page with no decision and no warning is ink on paper.

**The One Solid Block Rule.** The solid cobalt block appears at most once per document: the key-point cell in the front-page form. Decisions in the body get a wash, not a solid fill.

## Typography

**Display Font:** Roboto Flex (with Helvetica Neue, Arial), vendored variable font, weight 100–1000, width 25–151%
**Body Font:** Source Serif 4 (with Georgia), vendored, roman and italic, optical sizing on
**Label/Mono Font:** JetBrains Mono (with Menlo), code and identifiers only

**Character:** A working grotesk whose width axis does the expressive work (condensed for the title and headings, extended for tracked labels and the kind name) against a calm, bookish text serif. The pairing reads as a document someone made, not a brochure and not an export.

Roboto Flex is a deliberate choice, not a default. It is the only free face with both Cyrillic and a width axis, and the width axis carries the system: the condensed titles and headings and the extended labels. It replaced Archivo, which has no Cyrillic. Roboto is commonly flagged as overused; here it is never set at its default width for display. Default width appears only in small running text (table data, captions, the date, the footer).

All three faces are vendored as WOFF2 subsets (Latin, Latin Extended, Cyrillic, Cyrillic Extended) with `font-display: block`, so a document renders offline and never prints in a fallback.

### Hierarchy
- **Display** (720, 48pt, 0.98, width 70%): the cover title for report, proposal, guide and requirements. Balanced wrap; render.py wraps each word so names never split.
- **Display Memo** (720, 30pt, 0.98, width 75%): the memo title in its compact head.
- **Kind** (750, 9pt, 0.16em, width 125%, uppercase): the kind name in the masthead; the date beside it is 500 9pt with tabular figures.
- **Subtitle** (Source Serif 4 italic 400, 15pt, 1.3, Graphite; 13pt on the memo): the optional one-line framing under the title.
- **Outcome** (650, 15pt, 1.22, width 88%): the key point in the cobalt cell.
- **Headline** (650, 15pt, 1.15, width 85%): numbered section heads (h2); the number repeats at 700 in the rail.
- **Title** (650, 10.5pt, 1.35, width 95%): sub-sections (h3); `n.n` at 500 9pt Graphite in the rail.
- **Subhead** (650, 9.5pt, 1.35, width 95%): unnumbered h4 sub-heads.
- **Value** (620, 11pt, 1.25, width 92%): filled-in form values; key-facts values use the same voice at 10.5pt with tabular figures.
- **Contents** (560, 10.5pt, 1.3, width 92%): contents-map entries; the number at 750, tabular.
- **Lede** (Source Serif 4 400, 12.5pt, 1.5): the optional opening paragraph of the body, once.
- **Body** (Source Serif 4 400, 10pt on the 14.6pt step): prose in the 118mm measure; manual hyphenation, orphans and widows 3; bold at 650. The front-page summary uses the serif at 11.5pt/1.5.
- **Data** (400, 8.5pt, 1.4, tabular figures): table cells; group rows at 650, totals at 750.
- **Caption** (400, 7.5pt, 1.4, Graphite): figure descriptions and blockquote attributions; the running footer byline uses the same size at 500 in Ink. Table descriptions are serif italic 8.5pt Graphite.
- **Label** (600–650, 6.3–7pt, 0.08–0.11em, width 112%, uppercase): field names, rail labels (Note, Decision, Warning, Aside, Step n), code-block labels, table heads, the running header's kind name, and the "Table n" and "Figure n" headers.
- **Code** (JetBrains Mono 400, 8pt, 1.55): code blocks; inline code at 0.86em with ligatures off.

### Named Rules
**The Width Axis Rule.** Hierarchy in Roboto Flex is carried by width as much as weight: condensed (70–95%) for anything read as a title or heading, extended (112–125%) for tracked uppercase labels. Display text is never at default width. Never fake width by scaling.

**The Three Voices Rule.** Roboto Flex speaks for the form and its apparatus, Source Serif 4 speaks the prose, JetBrains Mono speaks only code and identifiers. Prose is never set in the grotesk; labels are never set in the serif.

**The One Cyrillic Rule.** `font-feature-settings: "locl" 0` is set on the body and inherited everywhere, so Bulgarian text uses one set of Cyrillic letterforms across all three faces instead of switching to localized forms in some of them.

**The Tabular Rule.** Every number that sits in a column or identifies something (dates, section and requirement numbers, contents numbers, step numbers, the page counter, table data, key facts) uses tabular figures.

## Layout

The page is A4 portrait with margins of 22mm top, 25mm sides and 24mm bottom, giving a 160mm text block. The first page runs on 18mm top, 20mm sides and 24mm bottom, and has no running header or byline; its page counter remains.

**Front page, by kind.** Every kind uses the same parts; the arrangement is the variable.
- **Report:** a full cover page (255mm tall, a column); the title block is pushed to the bottom of the open area, 11mm above the form. Form order: author (half width), date, extra fields, summary, key point last.
- **Proposal:** the same cover; the form leads with the cobalt recommendation, then the summary, then author, date and fields. The title sits 9mm above the form.
- **Guide and requirements:** a cover map. The title is set 30mm below the masthead, the form follows directly, and the contents map (a numbered two-column list built from the body's h2) is anchored at the foot of the page.
- **Memo:** no cover. The title (Display Memo) sits 14mm below the masthead, the form 8mm under the subtitle with the decision before the summary, and the body begins 2.4 steps later on the same page.

The form's cells flow in a wrapping row at a quarter width each and stretch, so every row closes on the right edge; the author cell takes half and the summary and key point take the full width.

**Body grid.** A two-column split of the text block: a **rail** (34mm), a **gap** (8mm) and a **measure** (118mm). The rail plus gap (the **indent**, 42mm) is the system's master offset: body flow is indented by it and rail content is pulled back by it. Section numbers, sub-section numbers, callout labels, step labels, requirement numbers, code-block labels, table headers and figure captions all live in the rail. Wide elements (code blocks, tables, figures, key facts) span rail plus measure, the full 160mm.

**Rhythm.** One **step** (14.6pt, the body line height). Paragraphs are followed by 0.6 step; sections open with 2.2 steps above and 0.7 below; sub-sections 1.4 above and 0.35 below (0.5 directly under a section head); wide components take 0.8 step above and one below; callouts one step each side.

**Running heads.** The header carries the kind name (left, Label style) and the document title (right, 500 6.8pt), both in Graphite, 5mm above the text block. The footer carries "author · date" (left) and "page / total" (right, 650, tabular) under a 0.5pt Hairline Grey rule. Components avoid breaking inside themselves, headings stay with what follows, table heads repeat, and only a table marked long may break.

### Named Rules
**The Rail Rule.** The rail holds numbers and labels, never prose. Every component's identity is named in the rail at the top of the component, aligned to its first rule.

**The Indent Rule.** All horizontal offsets derive from the rail (34mm), the gap (8mm) or their sum (42mm). Do not introduce new indents.

**The Shared Parts Rule.** A new kind is a new arrangement of the existing front-page parts, never new parts or a new style. Kinds differ in order, placement and labels only.

## Elevation & Depth

The system is flat. There are no shadows anywhere; depth and grouping come from rules of graded weight and from flat tonal grounds. A 0.5pt line separates items within a component; a 1pt strong rule opens a section, the contents map, the key-facts grid, and a table's head and foot; a 1.5pt rule tops the front-page form and a table total; a single 3pt rule opens the masthead, the heaviest line in the document. Tonal grounds (tint, cobalt wash, warning wash, the cobalt key-point cell) mark a region without lifting it.

### Named Rules
**The Graded Rule Rule.** Weight of line equals weight of boundary: 0.5pt within, 1pt between sections, 1.5pt over the form, 3pt only for the masthead. Never add a shadow or an outline box to show grouping.

## Shapes

Square, ruled geometry throughout. Containers have no corner radius; the only rounding is a 1pt radius on inline code. Rules are horizontal by default: callouts, blockquotes, code blocks, steps, requirements and contents rows are bounded above and below, open at the sides. Fully boxed grids (all four sides ruled) are reserved for the form grammar: the front-page form and the key-facts grid. Section heads draw a rule over the measure and a separate rule over the rail, so the number and the heading each sit under their own line.

## Components

### Front-Page Form (signature)
The ruled form every kind fills in.
- **Masthead:** 3pt strong rule; kind name (Kind style) left, the long date right. Labels and date follow the document language ("13 November 2026", "13 ноември 2026 г.").
- **Titling:** display title up to 165mm wide; italic serif subtitle up to 135mm in Graphite.
- **Form grid:** a 1.5pt strong top rule, every cell ruled 0.5pt on right and bottom, square corners, at least 17mm tall. Each cell carries a field name (Label, Graphite) over a value (Value style). Field names vary per kind and language: the author field reads Author, From or Prepared by; the summary reads Summary, About this guide or Overview.
- **Key-point cell:** full width, solid cobalt, On-Cobalt White text in the Outcome style, 5mm bottom padding; the only solid colour block in the document.

### Contents Map
Guide and requirements covers only. A Graphite field name ("Contents" / "Съдържание"), then a two-column numbered list under a 1pt strong rule; each entry is a row with its number in an 8mm column, separated by hairlines. Built by the renderer from the body's h2.

### Section Heads
- **Numbered:** a strong 1pt rule over the measure and a matching rule over the rail; the section number (700, tabular) in the rail, the Headline in the measure. Sub-sections carry `n.n` in Graphite in the rail with no rule. h4 is unnumbered.

### Callouts
Bounded by top and bottom rules, label in the rail; `data-label` renames the label.
- **Note:** 0.5pt strong rules, no ground, label in Ink. Flush with the measure.
- **Aside:** hairline rules, italic text, label in Graphite. For allowances, exceptions and permitted deviations.
- **Decision:** cobalt rules, cobalt wash, 3.5mm side padding, label in cobalt. Typically opens with a bold lead phrase.
- **Warning:** amber-mark rules, warning wash, 3.5mm side padding, label in amber ink.

### Key Facts
The front page's form grammar inside the body: a full-width three-column ruled grid (1pt strong top, 0.5pt cell rules) of 3, 6 or 9 cells; a Label over a Value-voice value at 10.5pt with tabular figures.

### Steps
A procedure with "Step n" (650, 7pt, extended tracked uppercase) in the rail; each step bounded by hairlines. A code block inside a step stays within the measure and its label moves above the code.

### Requirements
Numbered across the whole document: the number (700, 11pt, width 88%, tabular) in the rail, the requirement in the measure, each bounded by hairlines. Numbering continues across every requirements list.

### Code
- **Block:** full-width tint band with hairlines top and bottom, square corners; code begins at the measure, an optional uppercase label (a filename or "Shell") in the rail. Wrapped lines hang 4ch so indentation stays truthful.
- **Inline:** tint ground, 1pt radius, 0.86em JetBrains Mono, ligatures off, may break anywhere.

### Tables
Full width, Data style. Caption above: "Table n" in the rail position, italic serif description in Graphite in the measure. Head row in tracked uppercase Graphite between two 1pt strong rules; body rows separated by hairlines; the last row closed by a 1pt strong rule. Numeric columns right-aligned. Group rows take a tint ground and 650 weight; a footer total sits under a 1.5pt rule at 750. No vertical rules, no zebra striping.

### Figures
A full-width two-column grid: the caption in the rail ("Figure n" header, then a Caption-style description), the image or inline SVG in the measure. Diagrams are drawn in ink.

### Blockquote
Someone's exact words: a hairline above, italic serif at 11pt/1.5 in the measure, attribution beneath in Caption style.

### Lists
Unordered items take an en-dash marker in Graphite; ordered items take tabular grotesk numerals in Graphite.

## Do's and Don'ts

### Do:
- **Do** derive every horizontal offset from the rail (34mm), gap (8mm) or indent (42mm), and every vertical gap from the 14.6pt step.
- **Do** build a kind's front page only from the shared parts: masthead, title, subtitle, ruled form, cobalt key point and contents map.
- **Do** set titles and headings in condensed Roboto Flex (70–95%) and labels in extended tracked uppercase (112–125%).
- **Do** keep `font-feature-settings: "locl" 0` so Cyrillic keeps one set of letterforms across all three faces.
- **Do** keep cobalt for decisions and the key point, and amber for warnings; everything else is Ink, Graphite and rules.
- **Do** use tabular figures for any number that identifies or aligns.
- **Do** print the author and date on the front-page form and in every following page's running footer.
- **Do** add every printed apparatus word in both English and Bulgarian (the renderer's language table or a `:lang(bg)` rule).

### Don't:
- **Don't** add per-document CSS, inline styles or new components; the stylesheet is the only design source.
- **Don't** set Roboto Flex at its default width for any title or heading.
- **Don't** use cobalt or amber for links, headings, emphasis or diagram fills, and don't add a second solid cobalt block.
- **Don't** add shadows, rounded containers or side-only accent stripes; the only radius is 1pt on inline code.
- **Don't** set prose in the grotesk or labels in the serif; don't use JetBrains Mono outside code and identifiers.
- **Don't** add a closing colophon, issue number or series name; a document ends with its last section.
- **Don't** print any reference to Claude, an AI or the session in labels, running heads or the form.
- **Don't** add a tracked-caps line above a title or heading; the masthead kind name is the only label above the title.
- **Don't** add company branding, logos or brand colours; the byline is personal.
