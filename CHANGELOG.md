# Changelog

## Unreleased

- The document card now appears in the chat under the render call, instead of a side pane. **Inspect and edit** opens that card's own document, even an older one.
- GalleyDocs is optional: without it, rendering works exactly as before (no network calls, no extra files, no extra output), and a GalleyDocs problem never fails a render.
- Document identity: a document saved to GalleyDocs gets a stable `doc_id` (in doc.json and in `.galleydocs.json` next to the PDF), so later saves become new versions instead of duplicates. A similar title with no id stops and asks (`--doc-id` / `--new-doc`). `galley.py log` shows how each render was recognised.
- GalleyDocs: after rendering, the skill asks whether to save the document to the user's library and saves through the GalleyDocs connector (`save_doc`, `create_version`) or `galley.py push`; `galley.py remember` records the identity after a connector save. Saving is never automatic unless `galley.py login --auto-save` was chosen. A newer version saved elsewhere is never overwritten: the save reports a conflict and `galley.py pull` fetches it. The card gets an **Open in GalleyDocs** button.
- Themes: `render.py --theme theme.json` recolours the design with a GalleyDocs theme (colour tokens only, validated); after `galley.py login` the chosen theme is applied automatically.
- `render.build_page` takes a fixed date, stylesheet URL and head markup, so a server renderer prints a revision exactly like a local render; `CHROME_EXTRA_FLAGS` and `DOCS_DESIGNER_STATE` are honoured.
- The on-screen A4 sheet styling moved from `inspector.css` to `sheet.css`, shared with GalleyDocs.

## 0.1.0 (2026-11-13)

First release.

- Five document kinds (report, memo, guide, proposal, technical requirements) in one design system, chosen with a `kind` field.
- English and Bulgarian labels, dates and fonts (`"lang": "bg"`).
- The author's name and the creation date on every document.
- Components: numbered sections, decision, warning, note and aside callouts, key facts, steps, code with hanging indents, tables with group rows and totals, numbered requirements, quotes, figures.
- Click-to-edit inspector: edit any text in place, or send Claude an instruction that references the exact element.
- A Claude Code plugin that bundles the skill and the inspector pane, with a `/docs-inspect` command.
- `extract_session.py` to document a past Claude Code session.
