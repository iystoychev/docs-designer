#!/usr/bin/env python3
"""Local inspector for docs-designer documents.

  inspect_server.py [--port 8765]

Serves the most recently rendered document (~/.docs-designer/last.json) as an
interactive page laid out with the real stylesheet. Hover outlines an element;
clicking it lets you edit its text in place (written back to body.html or
doc.json, then the PDF is re-rendered) or send Claude an instruction about it.

Endpoints (127.0.0.1 only):
  GET  /                     the inspector page for the current document
  GET  /pdf                  the current PDF
  GET  /api/state            {version, title, kind, pdf, spec, ...}
  POST /api/edit             {id, html, version}  edit one element, re-render
  POST /api/ask              {id, instruction, version}  queue an instruction for Claude
  GET  /api/asks?after=N     queued instructions with seq > N
"""
import argparse
import json
import mimetypes
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import render  # noqa: E402

LAST = render.STATE_DIR / "last.json"
LOCK = threading.Lock()          # one edit or render at a time
ASKS: list[dict] = []            # instructions waiting for Claude (seq-numbered)


def current() -> dict:
    try:
        return json.loads(LAST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def version(info: dict) -> str:
    """Changes whenever the spec, the body or the PDF changes on disk."""
    parts = []
    for key in ("spec", "body", "pdf"):
        try:
            parts.append(str(Path(info[key]).stat().st_mtime_ns))
        except (KeyError, OSError):
            parts.append("0")
    return "-".join(parts)


def describe(info: dict, ref: str) -> dict:
    """What an element is, for the instruction sent to Claude."""
    spec, _, body = render.load(Path(info["spec"]))
    if ref.startswith("spec:"):
        field = ref[5:]
        return {"where": f"front page, field \"{field}\" in doc.json", "text": str(spec.get(field) or ""),
                "file": info["spec"], "section": "Front page"}
    if ref.startswith("meta:"):
        label = ref[5:]
        return {"where": f"front page, meta field \"{label}\" in doc.json",
                "text": str((spec.get("meta") or {}).get(label, "")), "file": info["spec"], "section": "Front page"}
    b = blocks.find(body, ref)
    if b is None:
        raise KeyError(ref)
    inner = body[b.inner_start:b.inner_end]
    return {"where": f"<{b.tag}> element {ref} in body.html", "text": blocks.text_of(inner),
            "source": inner.strip(), "file": info["body"], "section": b.section or "(before the first section)"}


def apply_edit(info: dict, ref: str, new_html: str) -> None:
    spec_path = Path(info["spec"])
    if ref.startswith(("spec:", "meta:")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        text = blocks.text_of(new_html)
        if ref.startswith("spec:"):
            field = ref[5:]
            if field not in ("title", "subtitle", "abstract", "outcome"):
                raise KeyError(ref)
            if field == "title" and not text:
                raise ValueError("the title cannot be empty")
            spec[field] = text
        else:
            meta = spec.get("meta") or {}
            if ref[5:] not in meta:
                raise KeyError(ref)
            meta[ref[5:]] = text
            spec["meta"] = meta
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        body_path = Path(info["body"])
        body = body_path.read_text(encoding="utf-8")
        body_path.write_text(blocks.replace(body, ref, new_html), encoding="utf-8")
    render.render(spec_path, Path(info["pdf"]), info.get("author_override"))


class Handler(BaseHTTPRequestHandler):
    server_version = "docs-inspector"

    def log_message(self, fmt, *args):  # keep the mod's log quiet
        pass

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status: int = 200) -> None:
        self._send(status, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _file(self, path: Path, root: Path) -> None:
        try:
            path = path.resolve()
            path.relative_to(root.resolve())  # never serve outside the root
            data = path.read_bytes()
        except (OSError, ValueError):
            return self._send(404, b"not found", "text/plain")
        self._send(200, data, mimetypes.guess_type(path.name)[0] or "application/octet-stream")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        url = urlparse(self.path)
        info = current()
        if url.path == "/api/state":
            return self._json({**info, "version": version(info)} if info else {"empty": True})
        if url.path == "/api/asks":
            after = int((parse_qs(url.query).get("after") or ["0"])[0])
            return self._json([a for a in ASKS if a["seq"] > after])
        if url.path.startswith("/assets/"):
            return self._file(render.ASSETS / unquote(url.path[len("/assets/"):]), render.ASSETS)
        if not info:
            return self._send(200, EMPTY.encode(), "text/html; charset=utf-8")
        if url.path == "/pdf":
            return self._file(Path(info["pdf"]), Path(info["pdf"]).parent)
        if url.path.startswith("/doc/"):
            root = Path(info["spec"]).parent
            return self._file(root / unquote(url.path[len("/doc/"):]), root)
        if url.path in ("/", "/index.html"):
            try:
                page, _ = render.build_page(Path(info["spec"]), info.get("author_override"), inspect=True)
            except render.RenderError as e:
                return self._send(500, f"<p>Cannot build the page: {e}</p>".encode(), "text/html; charset=utf-8")
            page = page.replace("<head>", f'<head><meta name="dd-version" content="{version(info)}">', 1)
            return self._send(200, page.encode(), "text/html; charset=utf-8")
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        try:
            req = self._body()
        except json.JSONDecodeError:
            return self._json({"error": "invalid JSON"}, 400)
        info = current()
        if not info:
            return self._json({"error": "no document has been rendered yet"}, 409)
        if req.get("version") and req["version"] != version(info):
            return self._json({"error": "The document changed since this page loaded. Reload and try again."}, 409)
        ref = str(req.get("id") or "")
        try:
            if url.path == "/api/edit":
                with LOCK:
                    apply_edit(info, ref, str(req.get("html") or ""))
                    return self._json({"ok": True, "version": version(current())})
            if url.path == "/api/ask":
                instruction = str(req.get("instruction") or "").strip()
                if not instruction:
                    return self._json({"error": "Type an instruction first."}, 400)
                with LOCK:
                    ask = {"seq": (ASKS[-1]["seq"] + 1) if ASKS else 1, "id": ref, "instruction": instruction,
                           "title": info["title"], "spec": info["spec"], "pdf": info["pdf"], **describe(info, ref)}
                    ASKS.append(ask)
                    del ASKS[:-200]
                return self._json({"ok": True, "seq": ask["seq"]})
        except KeyError:
            return self._json({"error": f"Unknown element {ref}. Reload the page."}, 404)
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        except render.RenderError as e:
            return self._json({"error": f"Saved, but the render failed: {e}"}, 500)
        self._send(404, b"not found", "text/plain")


EMPTY = """<!doctype html><meta charset="utf-8"><title>docs-designer inspector</title>
<body style="font:15px system-ui;margin:4rem;color:#121417;background:#F6F7F5">
<p>No document yet. Render one with docs-designer and this page will show it.</p>
<script>setInterval(async()=>{const s=await (await fetch('/api/state')).json();if(!s.empty)location.reload()},1500)</script>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765, help="first port to try (the next 20 are tried too)")
    a = ap.parse_args()
    for port in range(a.port, a.port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        sys.exit("inspect_server.py: error: no free port")
    print(f"LISTENING {server.server_address[1]}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
