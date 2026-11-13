# Changelog

## Unreleased

- The document card now appears in the chat under the render call, instead of a side pane. **Inspect and edit** opens that card's own document, even an older one.

## 0.1.0 (2026-11-13)

First release.

- Five document kinds (report, memo, guide, proposal, technical requirements) in one design system, chosen with a `kind` field.
- English and Bulgarian labels, dates and fonts (`"lang": "bg"`).
- The author's name and the creation date on every document.
- Components: numbered sections, decision, warning, note and aside callouts, key facts, steps, code with hanging indents, tables with group rows and totals, numbered requirements, quotes, figures.
- Click-to-edit inspector: edit any text in place, or send Claude an instruction that references the exact element.
- A Claude Code plugin that bundles the skill and the inspector pane, with a `/docs-inspect` command.
- `extract_session.py` to document a past Claude Code session.
