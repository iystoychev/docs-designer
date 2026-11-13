---
version: 1
slug: "skills-docs-designer-assets-template-html"
primary_target: "skills/docs-designer/assets/template.html"
related_targets: ["skills/docs-designer/assets/style.css"]
---

# Surface brief: docs-designer PDF template

Scope: the A4 print system (front page per kind + shared body pages) that every docs-designer PDF is rendered through. Visitor mode: Read.
Audience: the author plus teammates, stakeholders, students or reviewers who never saw the conversation. Job: understand the document's subject, what is decided or required, and what happens next.
Constraints: author and creation date on the front page and every following page; five kinds (report, memo, guide, proposal, requirements); English and Bulgarian; fixed component vocabulary; offline fonts; headless Chrome print; documents never mention Claude or the session.

## Direction contract

THESIS: One versatile document system. A family of five document kinds shares one design language, and each kind has a front page shaped for its job. It refuses both the one-size "exported doc" and a costume-per-kind template pack. (Revised from the earlier "Technical Report Series" at the user's request: looser, not a report series, no issue numbers.)

OWN-WORLD: Cool paper (#F6F7F5), ink #121417, hairline rules #C9CCD1. Colour is rationed by role: cobalt #2B3FD6 only for decisions and the front-page key point, amber only for warnings. Roboto Flex is used with its width axis for headings, labels and the front-page form; Source Serif 4 for prose; JetBrains Mono only for code. A rail-plus-measure grid holds every label, and the ruled form grid is the front page's grammar.

STORY: The reader sees the kind and date in the masthead, the condensed title, the ruled form with author and date, and the key point in cobalt. Then they read numbered sections, with labels in the rail.

FIRST VIEWPORT: Masthead: a 3pt rule, the kind label (extended caps) on the left and the date on the right. Below it, per kind:
- Report: title low over the form, summary and key point.
- Proposal: recommendation first.
- Guide and requirements: title high, form, and a contents map anchored at the foot.
- Memo: compact head, with the body starting on page one.

FORM: Technical Report Series raised into a multi-kind system; original seed key f5673377.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
