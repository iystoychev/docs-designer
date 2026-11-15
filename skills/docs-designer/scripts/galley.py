#!/usr/bin/env python3
"""GalleyDocs client: save renders to the library with a stable document identity.

  galley.py login --url https://galley.example --token gd_... [--auto-save]   once per computer
  galley.py push <doc.json> --pdf <pdf> [--doc-id ID | --new-doc]           save a rendered document
  galley.py remember <doc.json> --pdf <pdf> --doc-id ID --revision N        record a connector save
  galley.py pull <doc_id> --into DIR                                        write the latest source to DIR
  galley.py status | log [-n 20]

Once logged in, renders use the theme chosen in GalleyDocs. Saving happens only when
asked (render.py --save, galley.py push) unless auto-save was chosen at login.
Identity is resolved, when saving, in this order:
  1. --doc-id / --new-doc given on the command line (the user answered the question)
  2. "doc_id" in doc.json
  3. .galleydocs.json next to the PDF: same output file, then the same title
  4. similar titles in GalleyDocs or in that manifest -> "ambiguous": nothing is
     uploaded and Claude asks the user (new revision of X, or a new document?)
  5. otherwise a new document
The resolved id (and, after an upload, the revision number) is written back to
doc.json and to the manifest, so later renders in the same place reuse them.
A sync never fails a render: problems come back as output lines.
"""
import argparse
import base64
import difflib
import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

CONFIG = render.STATE_DIR / "galley.json"      # {"url": "...", "token": "..."}
LOG = render.STATE_DIR / "identity.log"        # one JSON object per identity decision
MANIFEST = ".galleydocs.json"                  # next to the rendered PDFs
SIMILAR = 0.6                                  # title similarity that makes a render ambiguous
MAX_ASSET = 8 * 1024 * 1024
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
IMG_SRC = re.compile(r"<img\b[^>]*\bsrc\s*=\s*([\"'])(.*?)\1", re.I | re.S)


class GalleyError(Exception):
    pass


def uuid7() -> str:
    """A time-ordered UUID (version 7), so document ids sort by creation."""
    value = (int(time.time() * 1000) << 80) | int.from_bytes(os.urandom(10), "big")
    value = (value & ~(0xF << 76)) | (0x7 << 76)
    value = (value & ~(0x3 << 62)) | (0x2 << 62)
    return str(uuid.UUID(int=value))


def config() -> dict | None:
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return cfg if cfg.get("url") and cfg.get("token") else None


def write_json(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def log(entry: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now().astimezone().isoformat(), **entry}, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ---------- HTTP ----------

def call(cfg: dict, method: str, path: str, payload: dict | None = None, timeout: int = 60) -> tuple[int, dict]:
    url = cfg["url"].rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {cfg['token']}", "Content-Type": "application/json",
        "Accept": "application/json", "User-Agent": "docs-designer-galley/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"{}")
        except json.JSONDecodeError:
            body = {}
        return e.code, body
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise GalleyError(f"cannot reach {cfg['url']}: {e}") from e


# ---------- identity ----------

def manifest_path(out: Path) -> Path:
    return out.parent / MANIFEST


def read_manifest(out: Path) -> dict:
    try:
        m = json.loads(manifest_path(out).read_text(encoding="utf-8"))
        return m if isinstance(m.get("documents"), dict) else {"version": 1, "documents": {}}
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "documents": {}}


def similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.casefold().strip(), b.casefold().strip()).ratio()


def candidates(cfg: dict | None, title: str, manifest: dict) -> list[dict]:
    """Existing documents whose title is close to this one."""
    found: dict[str, dict] = {}
    for entry in manifest["documents"].values():
        if entry.get("doc_id") and similar(entry.get("title", ""), title) >= SIMILAR:
            found[entry["doc_id"]] = {"doc_id": entry["doc_id"], "title": entry.get("title", ""), "url": ""}
    if cfg:
        status, res = call(cfg, "GET", "/api/search?" + urllib.parse.urlencode({"q": title, "scope": "title"}), timeout=20)
        if status == 200:
            for hit in res.get("results", []):
                if similar(hit.get("title", ""), title) >= SIMILAR:
                    found[hit["doc_id"]] = {"doc_id": hit["doc_id"], "title": hit["title"], "url": hit.get("url", "")}
    return list(found.values())


def resolve(spec: dict, out: Path, cfg: dict | None, doc_id: str | None, new_doc: bool) -> tuple[str | None, str, list]:
    """Return (doc_id or None when ambiguous, how it was decided, candidates)."""
    if doc_id:
        if not UUID_RE.match(doc_id.lower()):
            raise GalleyError(f"--doc-id {doc_id!r} is not a document id")
        return doc_id.lower(), "asked-existing", []
    if new_doc:
        return uuid7(), "asked-new", []
    if UUID_RE.match(str(spec.get("doc_id", "")).lower()):
        return spec["doc_id"].lower(), "spec", []
    manifest = read_manifest(out)
    entry = manifest["documents"].get(out.name)
    if entry and entry.get("doc_id"):
        return entry["doc_id"], "manifest-path", []
    slug = render.slugify(str(spec.get("title", "")))
    for e in manifest["documents"].values():
        if e.get("doc_id") and render.slugify(e.get("title", "")) == slug:
            return e["doc_id"], "manifest-title", []
    found = candidates(cfg, str(spec.get("title", "")), manifest)
    if found:
        return None, "ambiguous", found
    return uuid7(), "new", []


def remember(spec_path: Path, spec: dict, out: Path, doc_id: str, revision: int | None) -> None:
    """Write the identity (and the revision) back to doc.json and the manifest."""
    spec = {**spec, "doc_id": doc_id}
    if revision is not None:
        spec["revision"] = revision
    else:
        spec.pop("revision", None)
    write_json(spec_path, spec)
    manifest = read_manifest(out)
    manifest["documents"][out.name] = {"doc_id": doc_id, "title": spec.get("title", ""),
                                       **({"revision": revision} if revision is not None else {})}
    write_json(manifest_path(out), manifest)


# ---------- bundle ----------

def theme_ref() -> str:
    """The base theme this render used: docs-designer plus a hash of its design files."""
    h = hashlib.sha256()
    for p in sorted([render.ASSETS / "style.css", render.ASSETS / "template.html",
                     *(render.ASSETS / "fronts").glob("*.html")]):
        h.update(p.name.encode() + b"\0" + p.read_bytes())
    return "docs-designer@" + h.hexdigest()[:12]


@functools.lru_cache(maxsize=1)
def chrome_version() -> str:
    try:
        return subprocess.run([render.find_chrome(), "--version"], capture_output=True, text=True,
                              timeout=15).stdout.strip()
    except (render.RenderError, OSError, subprocess.SubprocessError):
        return ""


def session_id() -> str:
    """The Claude Code session that produced this render: the newest transcript of this project."""
    try:
        import extract_session
        newest = extract_session.sessions(os.getcwd())[:1]
    except Exception:  # noqa: BLE001 - optional metadata, never worth failing for
        return ""
    if newest and time.time() - newest[0].stat().st_mtime < 3600:
        return newest[0].stem
    return ""


def bundle(spec: dict, spec_path: Path, body_path: Path) -> dict:
    """The revision source: doc.json, body.html and the images the body uses."""
    body = body_path.read_text(encoding="utf-8")
    assets = {}
    for _, src in IMG_SRC.findall(body):
        if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I) or src.startswith(("/", "#")):
            continue  # data:, http: and absolute paths are not bundle files
        p = (body_path.parent / src).resolve()
        try:
            p.relative_to(spec_path.parent.resolve())
        except ValueError:
            raise GalleyError(f"image {src} is outside the document folder")
        if not p.is_file():
            raise GalleyError(f"image {src} not found")
        if p.stat().st_size > MAX_ASSET:
            raise GalleyError(f"image {src} is larger than {MAX_ASSET // 1024 // 1024} MB")
        assets[src] = base64.b64encode(p.read_bytes()).decode()
    source_spec = {k: v for k, v in spec.items() if k not in ("revision", "doc_id")}
    source_spec["body"] = "body.html"
    return {"spec": source_spec, "body": body, "assets": assets}


def upload(cfg: dict, doc_id: str, spec: dict, spec_path: Path, info: dict) -> tuple[int, dict]:
    payload = {
        "base_revision": spec.get("revision"),
        "source": bundle(spec, spec_path, Path(info["body"])),
        "pdf": base64.b64encode(Path(info["pdf"]).read_bytes()).decode(),
        "meta": {"author": info["author"], "rendered_at": info.get("rendered_at", ""),
                 "session_id": session_id(), "renderer": chrome_version(), "theme": theme_ref()},
    }
    status, res = call(cfg, "POST", f"/api/docs/{doc_id}/revisions", payload)
    if status == 404:  # first upload of this document
        status, res = call(cfg, "POST", "/api/docs", {"doc_id": doc_id, **payload})
    return status, res


def renderer_drift(local: str, server: str) -> str:
    """A note when the local Chrome is another major version than the server's pinned one:
    page breaks can differ, and GalleyDocs keeps the server's PDF."""
    ver = re.compile(r"(\d+)\.\d+\.\d+\.\d+")
    a, b = ver.search(local), ver.search(server)
    if not a or not b or a.group(1) == b.group(1):
        return ""
    return (f"Galley: note: your Chrome {a.group(1)} differs from the server's pinned Chrome {b.group(1)}; "
            "GalleyDocs keeps the server's PDF, whose page breaks may differ from yours.")


def base_revision(cfg: dict | None, spec: dict, out: Path, doc_id: str, how: str) -> int | None:
    """The revision this render builds on. GalleyDocs refuses an upload whose base is
    not the latest revision, so a web or Claude edit is never silently buried."""
    if how in ("asked-new", "new"):
        return None
    if how == "asked-existing":
        # The user chose this document: the render becomes its next revision.
        if not cfg:
            return None
        status, res = call(cfg, "GET", f"/api/docs/{doc_id}", timeout=20)
        return int(res["document"]["latest_revision"]) if status == 200 else None
    if str(spec.get("doc_id", "")).lower() == doc_id and isinstance(spec.get("revision"), int):
        return spec["revision"]
    known = [e["revision"] for e in read_manifest(out)["documents"].values()
             if e.get("doc_id") == doc_id and isinstance(e.get("revision"), int)]
    return max(known) if known else None


# ---------- entry point used by render.py ----------

def push_command(spec_path: Path, out: Path) -> str:
    return f"python3 {Path(__file__).resolve()} push {spec_path.resolve()} --pdf {out.resolve()}"


def sync(info: dict, spec_path: Path, out: Path, doc_id: str | None = None, new_doc: bool = False,
         save: bool = False) -> dict:
    """Save a render to GalleyDocs, only when asked (save) or when the user chose auto-save at login."""
    lines: list[str] = []
    cfg = config()
    if not (save or (cfg and cfg.get("auto_save"))):
        if cfg:
            lines.append(f"Galley: not saved. Ask the user; to save it run: {push_command(spec_path, out)}")
        return {"status": "not-saved", "lines": lines}
    if not cfg:
        lines.append("Galley: not set up on this computer. Save through the GalleyDocs connector (save_doc), "
                     "or run galley.py login once.")
        return {"status": "not-set-up", "lines": lines}
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        cfg = config()
        resolved, how, found = resolve(spec, out, cfg, doc_id, new_doc)
        log({"title": spec.get("title", ""), "doc_id": resolved, "method": how, "pdf": str(out),
             "candidates": [c["doc_id"] for c in found]})
        if resolved is None:
            lines.append("Identity: ambiguous")
            for c in found:
                lines.append(f"Candidate: {c['doc_id']} | {c['title']}" + (f" | {c['url']}" if c["url"] else ""))
            lines.append("Galley: not saved. Ask the user whether this is a new version of a candidate, then run: "
                         f"{push_command(spec_path, out)} --doc-id <id>   (or --new-doc)")
            return {"status": "ambiguous", "candidates": found, "lines": lines}
        base = base_revision(cfg, spec, out, resolved, how)
        remember(spec_path, spec, out, resolved, base)
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        lines.append(f"Identity: {resolved} ({how})")
        if not cfg:
            return {"status": "local", "doc_id": resolved, "lines": lines}
        status, res = upload(cfg, resolved, spec, spec_path, info)
        if status in (200, 201):
            rev = int(res["revision"]["number"])
            remember(spec_path, spec, out, resolved, rev)
            word = "unchanged, still" if res.get("unchanged") else "uploaded"
            lines.append(f"Galley: {word} revision {rev}")
            lines.append(f"Galley-URL: {res.get('url', '')}")
            drift = renderer_drift(chrome_version(), str(res["revision"].get("renderer", "")))
            if drift:
                lines.append(drift)
            return {"status": "unchanged" if res.get("unchanged") else "uploaded", "doc_id": resolved,
                    "revision": rev, "url": res.get("url", ""), "lines": lines}
        if status == 409:
            latest = res.get("latest_revision")
            lines.append(f"Galley: conflict: {res.get('error', 'the document changed in GalleyDocs')}")
            lines.append(f"Galley: fetch revision {latest} first: python3 {Path(__file__).resolve()} pull "
                         f"{resolved} --into {spec_path.parent.resolve()}, apply the change again, then render.")
            return {"status": "conflict", "doc_id": resolved, "lines": lines}
        lines.append(f"Galley: error: upload failed (HTTP {status}): {res.get('error', '')}")
        return {"status": "error", "doc_id": resolved, "lines": lines}
    except (GalleyError, OSError, json.JSONDecodeError, KeyError, ValueError) as e:
        lines.append(f"Galley: error: {e}")
        return {"status": "error", "lines": lines}


THEME_CACHE = render.STATE_DIR / "theme.json"


def default_theme() -> dict | None:
    """The colour theme the user chose in GalleyDocs, or None when GalleyDocs is not set up.
    The last answer is cached so renders keep the theme when the server is unreachable."""
    cfg = config()
    if not cfg:
        return None
    try:
        status, res = call(cfg, "GET", "/api/themes", timeout=5)
        if status == 200:
            theme = next((t for t in res.get("themes", []) if t.get("id") == res.get("default_theme_id")), None)
            if theme is not None:
                write_json(THEME_CACHE, {"name": theme["name"], "version": theme["version"], "tokens": theme["tokens"]})
                return theme["tokens"]
    except GalleyError:
        pass
    try:
        return json.loads(THEME_CACHE.read_text(encoding="utf-8")).get("tokens")
    except (OSError, json.JSONDecodeError):
        return None


# ---------- command line ----------

def cmd_login(a) -> None:
    url = a.url.rstrip("/")
    if not url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        sys.exit("galley.py: error: use an https:// URL (http is allowed only for localhost)")
    cfg = {"url": url, "token": a.token, "auto_save": a.auto_save}
    status, res = call(cfg, "GET", "/api/me", timeout=20)
    if status != 200:
        sys.exit(f"galley.py: error: the token was not accepted (HTTP {status}) {res.get('error', '')}")
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    write_json(CONFIG, cfg)
    CONFIG.chmod(0o600)
    how = "Every render is saved automatically." if a.auto_save else "Renders use your theme; save one with --save or galley.py push."
    print(f"Signed in to {url} as {res.get('name') or res.get('email')}. {how}")


def cmd_push(a) -> None:
    """Save an already rendered document (its doc.json and PDF) to GalleyDocs."""
    spec_path, pdf = Path(a.spec).resolve(), Path(a.pdf).resolve()
    if not pdf.is_file():
        sys.exit(f"galley.py: error: {pdf} not found; render first")
    try:
        spec, body_path, _ = render.load(spec_path)
        author = render.resolve_author(a.author or spec.get("author"))
    except render.RenderError as e:
        sys.exit(f"galley.py: error: {e}")
    info = {"title": str(spec["title"]), "author": author, "body": str(body_path), "pdf": str(pdf),
            "rendered_at": datetime.fromtimestamp(pdf.stat().st_mtime).astimezone().isoformat()}
    res = sync(info, spec_path, pdf, doc_id=a.doc_id, new_doc=a.new_doc, save=True)
    for line in res.get("lines", []):
        print(line)
    if res.get("status") in ("error", "conflict", "not-set-up"):
        sys.exit(1)


def cmd_remember(a) -> None:
    """Record a document's identity after saving it elsewhere (the connector's save_doc / create_version)."""
    if not UUID_RE.match(a.doc_id.lower()):
        sys.exit(f"galley.py: error: {a.doc_id!r} is not a document id")
    spec_path, pdf = Path(a.spec).resolve(), Path(a.pdf).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    remember(spec_path, spec, pdf, a.doc_id.lower(), a.revision)
    log({"title": spec.get("title", ""), "doc_id": a.doc_id.lower(), "method": "connector", "pdf": str(pdf), "candidates": []})
    print(f"Identity: {a.doc_id.lower()} (revision {a.revision}) recorded in {spec_path.name} and {MANIFEST}")


def cmd_status(_a) -> None:
    cfg = config()
    print(f"GalleyDocs: {cfg['url']}" if cfg else "GalleyDocs: not set up (renders stay local)")


def cmd_pull(a) -> None:
    cfg = config()
    if not cfg:
        sys.exit("galley.py: error: not set up; run galley.py login first")
    path = f"/api/docs/{a.doc_id}/revisions/{a.revision}" if a.revision else f"/api/docs/{a.doc_id}"
    status, res = call(cfg, "GET", path + "?include=source")
    if status != 200:
        sys.exit(f"galley.py: error: HTTP {status} {res.get('error', '')}")
    rev = res["revision"] if "revision" in res else res["latest"]
    into = Path(a.into).resolve()
    into.mkdir(parents=True, exist_ok=True)
    for name, b64 in (rev["source"].get("assets") or {}).items():
        p = (into / name).resolve()
        p.relative_to(into)  # never write outside the folder
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(base64.b64decode(b64))
    (into / "body.html").write_text(rev["source"]["body"], encoding="utf-8")
    write_json(into / "doc.json", {**rev["source"]["spec"], "body": "body.html", "doc_id": a.doc_id,
                                   "revision": rev["number"]})
    print(f"Wrote revision {rev['number']} of \"{rev['source']['spec'].get('title', '')}\" to {into}/doc.json")


def cmd_log(a) -> None:
    try:
        lines = LOG.read_text(encoding="utf-8").splitlines()[-a.n:]
    except OSError:
        lines = []
    counts: dict[str, int] = {}
    for line in lines:
        e = json.loads(line)
        counts[e["method"]] = counts.get(e["method"], 0) + 1
        print(f"{e['at'][:19]}  {e['method']:<15} {e.get('doc_id') or '-':<36}  {e.get('title', '')}")
    if counts:
        print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("login", help="save the GalleyDocs URL and upload token")
    p.add_argument("--url", required=True)
    p.add_argument("--token", required=True)
    p.add_argument("--auto-save", action="store_true", help="save every render without asking")
    p.set_defaults(fn=cmd_login)
    p = sub.add_parser("push", help="save a rendered document to GalleyDocs")
    p.add_argument("spec")
    p.add_argument("--pdf", required=True)
    p.add_argument("--author")
    who = p.add_mutually_exclusive_group()
    who.add_argument("--doc-id", help="a new version of this document")
    who.add_argument("--new-doc", action="store_true", help="a new document")
    p.set_defaults(fn=cmd_push)
    p = sub.add_parser("remember", help="record the identity returned by the connector")
    p.add_argument("spec")
    p.add_argument("--pdf", required=True)
    p.add_argument("--doc-id", required=True)
    p.add_argument("--revision", type=int, required=True)
    p.set_defaults(fn=cmd_remember)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("pull", help="write a document's source (latest or --revision N) to a folder")
    p.add_argument("doc_id")
    p.add_argument("--into", required=True)
    p.add_argument("--revision", type=int)
    p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("log", help="recent identity decisions")
    p.add_argument("-n", type=int, default=20)
    p.set_defaults(fn=cmd_log)
    a = ap.parse_args()
    try:
        a.fn(a)
    except GalleyError as e:
        sys.exit(f"galley.py: error: {e}")


if __name__ == "__main__":
    main()
