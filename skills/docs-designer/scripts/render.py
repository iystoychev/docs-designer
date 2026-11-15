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
# last.json (the most recently rendered document), galley.json, identity.log
STATE_DIR = Path(os.environ.get("DOCS_DESIGNER_STATE") or Path.home() / ".docs-designer")
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


INSPECTOR_HEAD = ('<base href="/doc/"><link rel="stylesheet" href="/assets/sheet.css">'
                  '<link rel="stylesheet" href="/assets/inspector.css">'
                  '<script src="/assets/inspector.js" defer></script>')


# A theme is a stylesheet layered after style.css (fonts, type, front pages, any of the
# document markup; see assets/THEMING.md) plus colour tokens applied last.
THEME_TOKENS = ("paper", "ink", "ink-2", "rule", "rule-strong", "tint", "decision", "decision-wash",
                "warning", "warning-mark", "warning-wash")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
THEME_MAX_BYTES = 64 * 1024
# A theme restyles; it never loads anything: fonts come from fonts.css, images only as data: URLs.
THEME_FORBIDDEN = re.compile(r"<|@import|@font-face|@charset|@namespace|expression\s*\(|javascript:|"
                             r"behavior\s*:|-moz-binding", re.I)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I | re.S)
DATA_IMAGE = re.compile(r"^data:image/(png|svg\+xml)[;,]", re.I)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
CSS_ESCAPE = re.compile(r"\\([0-9A-Fa-f]{1,6})\s?|\\(.)", re.S)


def _unescape_css(css: str) -> str:
    def one(m: re.Match) -> str:
        if m.group(1):
            n = int(m.group(1), 16)
            return chr(n) if 0 < n <= 0x10FFFF else "\ufffd"
        return m.group(2)
    return CSS_ESCAPE.sub(one, css)


def check_theme_css(css: str) -> str:
    """A theme stylesheet as given, or RenderError. Checked with comments removed and
    escapes decoded too, so neither can hide a forbidden construct."""
    if len(css.encode("utf-8")) > THEME_MAX_BYTES:
        raise RenderError(f"the theme stylesheet is larger than {THEME_MAX_BYTES // 1024} KB")
    for text in (css, _unescape_css(CSS_COMMENT.sub("", css))):
        m = THEME_FORBIDDEN.search(text)
        if m:
            raise RenderError(f"the theme stylesheet may not contain {m.group(0)!r}")
        for _, url in CSS_URL.findall(text):
            if not DATA_IMAGE.match(url.strip()):
                raise RenderError("a theme may use only data:image/png or data:image/svg+xml URLs")
    return css


def normalize_theme(theme: dict | None) -> dict:
    """{"css", "tokens"} from a theme, a GalleyDocs theme file, or a bare token map."""
    if not theme:
        return {"css": "", "tokens": {}}
    if "css" in theme or "tokens" in theme:
        return {"css": str(theme.get("css") or ""), "tokens": dict(theme.get("tokens") or {})}
    return {"css": "", "tokens": dict(theme)}


def theme_css(tokens: dict | None) -> str:
    """A :root override for colour tokens. Unknown tokens and non-colour values are ignored."""
    decl = "".join(f"--{k}:{v};" for k, v in sorted((tokens or {}).items())
                   if k in THEME_TOKENS and HEX_COLOR.match(str(v)))
    return f"<style>:root{{{decl}}}</style>" if decl else ""


def theme_head(theme: dict | None, stylesheet: str) -> str:
    """The head markup for a theme: the font library and its stylesheet (when it has
    one), then its colour tokens. Nothing at all without a theme."""
    t = normalize_theme(theme)
    head = ""
    if t["css"].strip():
        fonts = stylesheet.rsplit("/", 1)[0] + "/fonts.css"
        head += f'<link rel="stylesheet" href="{html.escape(fonts, quote=True)}"><style>{check_theme_css(t["css"])}</style>'
    return head + theme_css(t["tokens"])


def load_theme(path: Path) -> dict:
    """Read a theme file ({"name", "css", "tokens"}, e.g. from the connector's get_theme,
    or a bare token map) and check its stylesheet."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read theme {path}: {e}")
    if not isinstance(data, dict):
        fail(f"theme {path} must be a JSON object")
    theme = normalize_theme(data)
    check_theme_css(theme["css"])
    return theme


def build_page(spec_path: Path, author: str | None = None, inspect: bool = False, *,
               date: datetime | None = None, stylesheet: str | None = None,
               head_extra: str | None = None, theme: dict | None = None) -> tuple[str, dict]:
    """Fill the template for a spec. inspect=True tags every editable element with
    data-dd and points assets at the inspector server instead of the file system.
    A server renderer passes the revision's date, its own stylesheet URL and head
    markup; a local render always uses the moment of rendering. theme restyles
    the design (see normalize_theme and assets/THEMING.md)."""
    spec, body_path, body = load(spec_path)
    kind, lang_code, meta = spec.get("kind", "report"), spec.get("lang", "en"), spec.get("meta") or {}
    L, K = LANG[lang_code], LANG[lang_code]["kinds"][kind]
    author = resolve_author(author or spec.get("author"))
    now = (date or datetime.now()).astimezone()
    if stylesheet is None:
        stylesheet = "/assets/style.css" if inspect else (ASSETS / "style.css").as_uri()
    if head_extra is None:
        head_extra = INSPECTOR_HEAD if inspect else ""
    head_extra += theme_head(theme, stylesheet)
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
        "STYLESHEET": html.escape(stylesheet, quote=True),
        "HEAD_EXTRA": head_extra,
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
        # CHROME_EXTRA_FLAGS: e.g. "--no-sandbox" inside a container that is itself the sandbox
        cmd = [chrome, *os.environ.get("CHROME_EXTRA_FLAGS", "").split(), "--headless", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check",
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


def render(spec_path: Path, out: Path | None = None, author: str | None = None, keep_html: bool = False,
           *, doc_id: str | None = None, new_doc: bool = False, theme: dict | None = None,
           save: bool = False) -> dict:
    """Render a spec to PDF and record it as the most recent document. Without a
    theme, the user's GalleyDocs theme is used when GalleyDocs is set up. With
    save (or --doc-id/--new-doc, or auto-save), the render is saved to GalleyDocs."""
    if theme is None:
        theme = optional_galley("default_theme", None)
    page, info = build_page(spec_path, author, theme=theme)
    out = (out or Path.cwd() / "docs" / f"{slugify(info['title'])}-{datetime.now().date().isoformat()}.pdf").resolve()
    print_pdf(page, spec_path.parent.resolve(), out, keep_html)
    info = {**info, "pdf": str(out), "author_override": author, "theme": theme or {},
            "rendered_at": datetime.now().astimezone().isoformat()}
    try:
        record(info)
    except OSError:
        pass  # the inspector is optional; a render never fails because of it
    info["galley"] = optional_galley("sync", {"status": "error", "lines": []}, info, spec_path, out,
                                     doc_id=doc_id, new_doc=new_doc, save=save or bool(doc_id) or new_doc)
    return info


def optional_galley(name: str, fallback, *args, **kwargs):
    """Call galley.<name>. GalleyDocs is optional: without it the skill works as before,
    and nothing it does (a missing module, an unreachable or misbehaving server) may
    fail a render. Errors become a Galley: line when the user asked to save."""
    try:
        import galley  # local module; imported late so the server renderer never loads it
        return getattr(galley, name)(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 - optional integration, never worth failing a render for
        if isinstance(fallback, dict) and kwargs.get("save"):
            return {**fallback, "lines": [f"Galley: error: {e}"]}
        return fallback


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
    who = ap.add_mutually_exclusive_group()
    who.add_argument("--doc-id", help="GalleyDocs: this render is a new revision of that document")
    who.add_argument("--new-doc", action="store_true", help="GalleyDocs: this render starts a new document")
    ap.add_argument("--theme", type=Path,
                    help="theme JSON ({\"css\": ..., \"tokens\": {...}}, e.g. from the connector's get_theme)")
    ap.add_argument("--save", action="store_true", help="GalleyDocs: save this render to the library")
    a = ap.parse_args()
    try:
        theme = load_theme(a.theme) if a.theme else None
        info = render(a.spec, a.out, a.author, a.keep_html, doc_id=a.doc_id, new_doc=a.new_doc, theme=theme, save=a.save)
    except RenderError as e:
        sys.exit(f"render.py: error: {e}")
    # The docs-designer mod reads these lines to show the document card in the chat.
    print(f"PDF: {info['pdf']}")
    print(f"Title: {info['title']}")
    print(f"Spec: {info['spec']}")
    print(f"Kind: {info['kind']} | Author: {info['author']} | Date: {info['date']}")
    for line in info["galley"].get("lines", []):
        print(line)


if __name__ == "__main__":
    main()
