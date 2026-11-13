#!/usr/bin/env python3
"""Render a docs-designer document spec to an A4 PDF.

  render.py doc.json [--out file.pdf] [--author "Name"] [--keep-html]

doc.json (plain-text fields; the renderer escapes them):
  {
    "kind":     "report | memo | guide | proposal | requirements  (default: report)",
    "lang":     "en | bg  (default: en) - sets labels, date format and hyphenation language",
    "title":    "Required. Short, specific title",
    "subtitle": "Optional one-line framing",
    "abstract": "Optional. 2-4 sentences shown on the front page",
    "outcome":  "Optional. The single most important point, struck in the accent colour",
    "meta":     {"Optional label": "value", "...": "..."},
    "author":   "Optional. Defaults to git user.name",
    "body":     "Required. Path (relative to doc.json) to the body HTML fragment"
  }

The author and the creation date are always printed: on the front page and in
the running footer of every following page. The date is the moment of
rendering and cannot be set by the spec.
"""
import argparse
import html
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"
STATE_DIR = Path.home() / ".docs-designer"   # last.json: the most recently rendered document
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
]
# The body may only use the shared vocabulary; styling and scripts belong to the template.
FORBIDDEN = [
    (re.compile(r"<\s*(style|script|link|iframe)\b", re.I), "<style>/<script>/<link>/<iframe> elements"),
    (re.compile(r"<[^>]*\sstyle\s*=", re.I), "inline style= attributes"),
    (re.compile(r"<\s*h1\b", re.I), "<h1> (the title lives on the front page; start sections at <h2>)"),
]

# Per-language words the template prints. Body labels (Decision, Step, Table...) live in style.css.
LANG = {
    "en": {
        "months": ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"],
        "date": "{d} {m} {y}",
        "date_label": "Date", "contents": "Contents",
        "kinds": {
            "report":       {"name": "Report", "author": "Author", "abstract": "Summary", "outcome": "Outcome"},
            "memo":         {"name": "Memo", "author": "From", "abstract": "Summary", "outcome": "Decision"},
            "guide":        {"name": "Guide", "author": "Author", "abstract": "About this guide", "outcome": "Goal"},
            "proposal":     {"name": "Proposal", "author": "Prepared by", "abstract": "Summary", "outcome": "Recommendation"},
            "requirements": {"name": "Technical requirements", "author": "Author", "abstract": "Overview", "outcome": "Objective"},
        },
    },
    "bg": {
        "months": ["януари", "февруари", "март", "април", "май", "юни", "юли",
                   "август", "септември", "октомври", "ноември", "декември"],
        "date": "{d} {m} {y} г.",
        "date_label": "Дата", "contents": "Съдържание",
        "kinds": {
            "report":       {"name": "Доклад", "author": "Автор", "abstract": "Резюме", "outcome": "Резултат"},
            "memo":         {"name": "Докладна записка", "author": "От", "abstract": "Резюме", "outcome": "Решение"},
            "guide":        {"name": "Ръководство", "author": "Автор", "abstract": "За ръководството", "outcome": "Цел"},
            "proposal":     {"name": "Предложение", "author": "Изготвил", "abstract": "Резюме", "outcome": "Препоръка"},
            "requirements": {"name": "Техническо задание", "author": "Автор", "abstract": "Обща информация", "outcome": "Цел"},
        },
    },
}
KINDS = tuple(LANG["en"]["kinds"])


class RenderError(Exception):
    pass


def fail(msg: str):
    raise RenderError(msg)


def resolve_author(explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    try:
        name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        name = ""
    if not name:
        name = pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0].strip()
    if not name:
        fail("no author: pass --author, set it in doc.json, or set `git config user.name`")
    return name


def find_chrome() -> str:
    for c in [os.environ.get("CHROME_PATH", "")] + CHROME_CANDIDATES:
        if c and Path(c).is_file():
            return c
        if c and shutil.which(c):
            return shutil.which(c)
    fail("Google Chrome/Chromium not found; install it or set CHROME_PATH")


def esc(s) -> str:
    return html.escape(" ".join(str(s).split()))


def css_string(s: str) -> str:
    """Quote text for a CSS content: value, safe inside a <style> element."""
    s = " ".join(s.split()).replace("\\", "\\\\").replace('"', '\\"').replace("<", "\\3C ")
    return f'"{s}"'


def slugify(s: str) -> str:
    return re.sub(r"[^\w]+", "-", s.lower()).strip("-")[:60] or "document"


def cell(label: str, value: str, cls: str = "") -> str:
    """One ruled field of the front-page form; value is already-escaped HTML."""
    classes = " ".join(["cell", cls]).strip()
    return f'<div class="{classes}"><span class="field">{esc(label)}</span><span class="value">{value}</span></div>'


def contents(body: str, label: str) -> str:
    heads = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2\b[^>]*>(.*?)</h2>", body, re.S | re.I)]
    if not heads:
        return ""
    items = "".join(f"<li>{esc(html.unescape(h))}</li>" for h in heads)
    return f'<nav class="contents"><span class="field">{esc(label)}</span><ol>{items}</ol></nav>'


PRE_CODE = re.compile(r"(<pre\b[^>]*>\s*<code\b[^>]*>)(.*?)(</code>\s*</pre>)", re.S | re.I)


def hang_code_lines(body: str) -> str:
    """Wrap each listing line in a span so wrapped lines get a hanging indent."""
    def wrap(m):
        lines = m.group(2).strip("\n").split("\n")
        return m.group(1) + "".join(f'<span class="ln">{ln}</span>' for ln in lines) + m.group(3)
    return PRE_CODE.sub(wrap, body)


def fill(template: str, values: dict) -> str:
    # Single pass: inserted values are never re-scanned for placeholders.
    def sub(m):
        key = m.group(1)
        if key not in values:
            fail(f"template placeholder {{{{{key}}}}} has no value")
        return values[key]
    return re.sub(r"\{\{([A-Z_]+)\}\}", sub, template)


def load(spec_path: Path) -> tuple[dict, Path, str]:
    """Read and validate a spec; return it, the body's path and the body."""
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read spec {spec_path}: {e}")
    for key in ("title", "body"):
        if not str(spec.get(key, "")).strip():
            fail(f"spec is missing required field '{key}'")
    if spec.get("kind", "report") not in KINDS:
        fail(f"unknown kind '{spec.get('kind')}'; use one of: {', '.join(KINDS)}")
    if spec.get("lang", "en") not in LANG:
        fail(f"unknown lang '{spec.get('lang')}'; use one of: {', '.join(LANG)}")
    if not isinstance(spec.get("meta") or {}, dict):
        fail("'meta' must be an object of label: value pairs")
    body_path = (spec_path.parent / spec["body"]).resolve()
    try:
        body = body_path.read_text(encoding="utf-8")
    except OSError as e:
        fail(f"cannot read body {body_path}: {e}")
    for pattern, what in FORBIDDEN:
        if pattern.search(body):
            fail(f"body uses {what}; only the shared vocabulary is allowed (see SKILL.md)")
    return spec, body_path, body


def build_page(spec_path: Path, author: str | None = None, inspect: bool = False) -> tuple[str, dict]:
    """Fill the template for a spec. inspect=True tags every editable element with
    data-dd and points assets at the inspector server instead of the file system."""
    spec, body_path, body = load(spec_path)
    kind, lang_code, meta = spec.get("kind", "report"), spec.get("lang", "en"), spec.get("meta") or {}
    L, K = LANG[lang_code], LANG[lang_code]["kinds"][kind]
    author = resolve_author(author or spec.get("author"))
    now = datetime.now().astimezone()
    date_long = L["date"].format(d=now.day, m=L["months"][now.month - 1], y=now.year)

    def dd(ref: str) -> str:
        return f' data-dd="{html.escape(ref, quote=True)}"' if inspect else ""

    def value_cell(label: str, value: str, ref: str, cls: str) -> str:
        return (f'<div class="cell {cls}"><span class="field">{esc(label)}</span>'
                f'<p class="value"{dd(ref)}>{esc(value)}</p></div>')

    subtitle = str(spec.get("subtitle") or "").strip()
    abstract = str(spec.get("abstract") or "").strip()
    outcome = str(spec.get("outcome") or "").strip()
    meta_cells = (
        cell(K["author"], esc(author), "wide-2")
        + cell(L["date_label"], f'<time datetime="{now.date().isoformat()}">{esc(date_long)}</time>')
        + "".join(f'<div class="cell"><span class="field">{esc(k)}</span>'
                  f'<span class="value"{dd("meta:" + str(k))}>{esc(v)}</span></div>' for k, v in meta.items())
    )
    values = {
        "LANG": lang_code,
        "KIND": kind,
        "KIND_LABEL": esc(K["name"]),
        "TITLE": esc(spec["title"]),
        "TITLE_WORDS": " ".join(f'<span class="w">{html.escape(w)}</span>' for w in str(spec["title"]).split()),
        "DD_TITLE": dd("spec:title"),
        "SUBTITLE_BLOCK": f'<p class="subtitle"{dd("spec:subtitle")}>{esc(subtitle)}</p>' if subtitle else "",
        "AUTHOR": esc(author),
        "DATE_ISO": now.date().isoformat(),
        "DATE_LONG": esc(date_long),
        "META_CELLS": meta_cells,
        "ABSTRACT_BLOCK": value_cell(K["abstract"], abstract, "spec:abstract", "full abstract") if abstract else "",
        "OUTCOME_BLOCK": value_cell(K["outcome"], outcome, "spec:outcome", "full outcome") if outcome else "",
        "CONTENTS_BLOCK": contents(body, L["contents"]),
        "BODY": hang_code_lines(blocks.annotate(body) if inspect else body),
        "STYLESHEET": "/assets/style.css" if inspect else (ASSETS / "style.css").as_uri(),
        "HEAD_EXTRA": ('<base href="/doc/"><link rel="stylesheet" href="/assets/inspector.css">'
                       '<script src="/assets/inspector.js" defer></script>') if inspect else "",
        "CSS_KIND": css_string(K["name"]),
        "CSS_TITLE": css_string(str(spec["title"])),
        "CSS_BYLINE": css_string(f"{author}  ·  {date_long}"),
    }
    front = fill((ASSETS / "fronts" / f"{kind}.html").read_text(encoding="utf-8"), values)
    page = fill((ASSETS / "template.html").read_text(encoding="utf-8"), {**values, "FRONT": front})
    info = {"title": str(spec["title"]), "kind": kind, "lang": lang_code, "author": author,
            "date": date_long, "spec": str(spec_path.resolve()), "body": str(body_path)}
    return page, info


def print_pdf(page: str, html_dir: Path, out: Path, keep_html: bool = False) -> None:
    """Print a filled page to PDF with headless Chrome."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)  # never mistake a stale PDF for this render
    # The HTML sits next to the spec so relative image paths in the body resolve.
    html_path = html_dir / f".{out.stem}.render.html"
    html_path.write_text(page, encoding="utf-8")
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as profile:
        cmd = [chrome, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={profile}", "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
               "--allow-file-access-from-files", f"--print-to-pdf={out}", html_path.as_uri()]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            fail("Chrome timed out while printing")
        finally:
            if not keep_html:
                html_path.unlink(missing_ok=True)
    if proc.returncode != 0 or not out.is_file() or out.stat().st_size == 0:
        fail(f"Chrome did not produce a PDF (exit {proc.returncode}):\n{proc.stderr[-2000:]}")


def render(spec_path: Path, out: Path | None = None, author: str | None = None, keep_html: bool = False) -> dict:
    """Render a spec to PDF and record it as the most recent document."""
    page, info = build_page(spec_path, author)
    out = (out or Path.cwd() / "docs" / f"{slugify(info['title'])}-{datetime.now().date().isoformat()}.pdf").resolve()
    print_pdf(page, spec_path.parent.resolve(), out, keep_html)
    info = {**info, "pdf": str(out), "author_override": author, "rendered_at": datetime.now().astimezone().isoformat()}
    try:
        record(info)
    except OSError:
        pass  # the inspector is optional; a render never fails because of it
    return info


def record(info: dict) -> None:
    """Make this document the one the inspector shows (~/.docs-designer/last.json)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_DIR / "last.json.tmp"
    tmp.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_DIR / "last.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path, help="document spec JSON")
    ap.add_argument("--out", type=Path, help="output PDF (default: ./docs/<title-slug>-<date>.pdf)")
    ap.add_argument("--author", help="author name (overrides doc.json and git user.name)")
    ap.add_argument("--keep-html", action="store_true", help="keep the intermediate HTML next to the spec")
    a = ap.parse_args()
    try:
        info = render(a.spec, a.out, a.author, a.keep_html)
    except RenderError as e:
        sys.exit(f"render.py: error: {e}")
    # The docs-designer mod reads these lines to show the document card in the chat.
    print(f"PDF: {info['pdf']}")
    print(f"Title: {info['title']}")
    print(f"Spec: {info['spec']}")
    print(f"Kind: {info['kind']} | Author: {info['author']} | Date: {info['date']}")


if __name__ == "__main__":
    main()
