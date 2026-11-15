---
name: docs-designer
description: Turn a conversation or a previous Claude Code session into a designed A4 PDF (report, memo, guide, proposal or technical requirements) in one consistent design language, with the author's name and creation date, in English or Bulgarian. Use when the user asks to document, write up, summarize, export or "make a PDF/report/memo/guide/proposal/spec/assignment" from this conversation or a past session, e.g. "turn this into a PDF", "write up what we decided as a memo", "make the requirements doc".
---

# docs-designer

Turn conversation content into an A4 PDF printed through one shared design system. Your job is editorial: choosing what matters and writing it well. The design is fixed in code (`assets/`, `scripts/render.py`) and must never be changed per document.

`SKILL_DIR` below means the directory that contains this file.

## 1. Get the source

- **This conversation (default):** use what is already in your context.
- **Another session:** list the candidates, then extract one:
  ```bash
  python3 SKILL_DIR/scripts/extract_session.py --list --project "$PWD"
  python3 SKILL_DIR/scripts/extract_session.py <session-id>               # or a path to a .jsonl
  python3 SKILL_DIR/scripts/extract_session.py --latest --skip-current --project "$PWD"
  ```
  Redirect long output to a scratch file and read it in parts.
- **A file the user gives you** (PDF, Markdown, notes): read it and use it as the source.

## 2. Pick the kind

| `kind` | Use for | Front page |
|---|---|---|
| `report` | findings, technical summaries, recaps, decision records | full cover: title, summary, key point |
| `memo` | a short decision or announcement (1–2 pages) | no cover; compact head, body starts on page one |
| `guide` | how-tos, onboarding, step-by-step instructions | cover with a contents map |
| `proposal` | a plan or request that someone must approve | cover that leads with the recommendation |
| `requirements` | specs, assignment briefs, acceptance criteria | cover with a contents map; requirements numbered across the document |

If the user names a kind, use it. Otherwise pick the closest one, and ask only when two fit equally well.

## 3. Distill

- Lead with the outcome. Keep final code, commands, names, numbers and dates exactly as they appeared.
- **Never invent anything.** Every claim, number and quote must come from the source. If something is unresolved, say so.
- **The document never mentions Claude, the AI, the chat or the session.** Write as the author's own document about its subject. The only exception is when the user explicitly asks for that.
- Write in the language the user wants. Use `"lang": "bg"` for Bulgarian (labels, dates and headings switch automatically). If the user hasn't said, use the language of the source.
- Keep it short. A memo is 1–2 pages; most reports and guides are 2–6.

## 4. Write two files (in a scratch/temp directory, not the user's repo)

**`doc.json`**: plain text only. The renderer escapes it.
```json
{
  "kind": "report",
  "lang": "en",
  "title": "Short, specific title (≤ 8 words works best)",
  "subtitle": "Optional one-line framing",
  "abstract": "Optional. 2–4 sentences shown on the front page",
  "outcome": "Optional. The single most important point, struck in cobalt on the front page",
  "meta": {"Status": "Draft", "Version": "1.2"},
  "body": "body.html"
}
```
- `meta` adds extra labelled cells to the front-page form, in the order given, for example `To` (memo), `Prepared for` (proposal), `Audience` (guide) or `Revision` (requirements). Use labels in the document's language.
- The front page labels `outcome` per kind: Outcome, Decision, Goal, Recommendation or Objective.
- Leave `author` out unless the user names someone. It defaults to `git config user.name`, and `--author` overrides it. **The date is always the render date**, so never add one.

**`body.html`**: a fragment that uses **only** this vocabulary. Look at `examples/<kind>/body.html` for each kind. Don't use `<style>`, `style=`, `<script>` or `<h1>`; the renderer rejects them.

| Element | Use for |
|---|---|
| `<p class="lede">` | optional opening paragraph, once at the top |
| `<h2>`, `<h3>`, `<h4>` | sections (numbered 1, 1.1 automatically; `h2` feeds the contents map), and unnumbered `h4` sub-heads |
| `<p>`, `<ul>`, `<ol>`, `<strong>`, `<em>`, `<code>`, `<a>` | prose |
| `<ol class="requirements"><li><p>…</p></li></ol>` | numbered requirements; numbering continues across every list in the document |
| `<div class="callout decision">` | a decision and its reason |
| `<div class="callout warning">` | a risk, a gotcha or something not to do |
| `<div class="callout note">` | an aside that matters |
| `<div class="callout aside">` | allowances, exceptions, permitted deviations (set in italic) |
| `data-label="…"` on any callout | renames its rail label, e.g. `data-label="Allowed deviations"` |
| `<dl class="keyfacts"><div><dt>Label</dt><dd>Value</dd></div>…</dl>` | 3, 6 or 9 short facts (dates, versions, counts, owners) |
| `<ol class="steps"><li><p>…</p></li>…</ol>` | a procedure; a `<pre>` may sit inside a step |
| `<pre data-label="Shell"><code>…</code></pre>` | code or commands (escape `<`, `>` and `&`). Keep lines ≤ 68 characters |
| `<table><caption>…</caption><thead>…</thead><tbody>…</tbody></table>` | comparisons. `class="num"` right-aligns numbers, `<tr class="group">` marks a subtotal or group row, `<tfoot>` holds a total, and `<table class="long">` lets a long table break across pages |
| `<blockquote><p>…</p><cite>…</cite></blockquote>` | someone's exact words, only when the wording matters |
| `<figure>…<figcaption>…</figcaption></figure>` | an inline SVG diagram or `<img>` (paths are relative to doc.json); draw in ink, not cobalt |

Colour carries meaning: cobalt marks decisions and the front-page key point, and amber marks warnings. Don't use them for anything else.

## 5. Render

```bash
python3 SKILL_DIR/scripts/render.py /path/to/doc.json --out "$PWD/docs/<slug>-<YYYY-MM-DD>.pdf"
```
Without `--out`, the file goes to `./docs/<title-slug>-<date>.pdf`. Ask before writing into the user's repo if they didn't give a location. The renderer needs Google Chrome or Chromium (`CHROME_PATH` can point to it).

## 6. Check and report

Read the PDF back. Check that the front page shows the title, author and date, that no section is empty, and that tables and code aren't cut off. Then give the user the path and a one-line summary. If the render fails, fix the body (usually a forbidden element or invalid JSON), never the stylesheet.

## GalleyDocs (optional)

GalleyDocs is the user's library of these documents: every version kept, a chosen PDF theme, share links. It is reached through the **GalleyDocs connector** (tools `get_theme`, `save_doc`, `create_version`, `search`, `list_docs`, `get_doc`) or, in Claude Code, through `scripts/galley.py` after the user ran `galley.py login` once; then the render prints a `Galley:` line.

The skill is complete without it. **When the connector's tools are not available and the render printed no `Galley:` line, skip this section entirely: do not offer to save, do not mention GalleyDocs, do not add `--save`, `--doc-id` or `--new-doc`.** Steps 1–6 above are the whole job.

**Theme (before step 5).** With the connector, call `get_theme`, write its `{"name", "tokens"}` to `theme.json` next to doc.json and add `--theme theme.json` to the render command. With `galley.py login` the theme is applied automatically.

**Save (after step 6): only when the user says yes.** Ask once: “Save it to GalleyDocs?” Then:
- **New document, connector:** `save_doc` with the doc.json object as `spec` and body.html as `body` (images, if any, base64 by path). If it returns `similar` documents, nothing was saved: ask the user whether this is a new version of one of them (`create_version` with its id and `latest_version` as `base_version`) or a new document (`save_doc` again with `new_document: true`). Never guess.
- **Doc.json already has `doc_id`, connector:** `create_version` with that id, `base_version` = its `revision`, the full spec and body, and a one-line note.
- After either, run `python3 SKILL_DIR/scripts/galley.py remember <doc.json> --pdf <pdf> --doc-id <id> --revision <version>` so the next save of this document becomes its next version. Report the GalleyDocs link.
- **Without the connector:** run the `push` command the render printed (`galley.py push <doc.json> --pdf <pdf>`). `Identity: ambiguous` with `Candidate:` lines means: ask the user, then push again with `--doc-id <id>` or `--new-doc`.
- `conflict`: someone saved a newer version (on the web or from another session). Fetch it (`get_doc`, or the printed `galley.py pull` command), re-apply the change, render, then save again. Never overwrite the newer version.

Keep the render's `Identity:` / `Galley:` / `Galley-URL:` lines intact. To keep a document's identity, edit and re-render its existing doc.json rather than writing a fresh one.

**Earlier documents.** When the user refers to a document they made before (“update the renderer decision”, “use the figures from last week's report”), find it with `search` or `list_docs` and read its source with `get_doc` instead of asking them to paste it. To update it, edit that source, render it locally if they want the PDF, and save it with `create_version`.

## Inspector (optional)

Every render records itself in `~/.docs-designer/last.json`. With the docs-inspector mod installed, a card for the document appears in the chat under your render call; from it the user opens the inspector, clicks any text to edit it or sends you an instruction about it. Keep the render script's output lines (PDF, Title, Spec, Kind) intact: the card is built from them. Those instructions arrive as a prompt that names the element, its section, its current text and its file. Apply them to that element in the source and re-render to the same PDF path. Without the mod, `python3 SKILL_DIR/scripts/inspect_server.py` serves the same inspector at http://127.0.0.1:8765.

