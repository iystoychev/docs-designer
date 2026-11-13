#!/usr/bin/env python3
"""Turn a Claude Code session transcript (.jsonl) into a clean Markdown conversation.

Keeps what people said: user prompts, Claude's visible replies and answers to
AskUserQuestion. Drops thinking, tool calls, tool output, meta and subagent records.

Usage:
  extract_session.py <session-id | path/to/session.jsonl>
  extract_session.py --latest [--project DIR] [--skip-current]
  extract_session.py --list [--project DIR] [-n 10]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
MAX_CHARS = 6000
NOISE = re.compile(r"<(system-reminder|local-command-[a-z]+|command-[a-z]+)>.*?</\1>", re.S)


def project_dir(project: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(project).resolve()))
    return PROJECTS / slug


def sessions(project: str | None) -> list[Path]:
    roots = [project_dir(project)] if project else [p for p in PROJECTS.iterdir() if p.is_dir()]
    files = [f for r in roots if r.is_dir() for f in r.glob("*.jsonl")]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def resolve(ref: str) -> Path:
    p = Path(ref).expanduser()
    if p.is_file():
        return p
    hits = list(PROJECTS.glob(f"*/{ref}.jsonl"))
    if not hits:
        sys.exit(f"error: no session '{ref}' under {PROJECTS}")
    return hits[0]


def clean(text: str) -> str:
    text = NOISE.sub("", text).strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n\n[… truncated {len(text) - MAX_CHARS} characters …]"
    return text


def block_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def turns(path: Path):
    """Yield (role, timestamp, text) in transcript order."""
    asked = set()  # tool_use ids of AskUserQuestion calls
    for line in path.open(encoding="utf-8"):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = rec.get("type")
        if kind not in ("user", "assistant") or rec.get("isMeta") or rec.get("isSidechain"):
            continue
        content = (rec.get("message") or {}).get("content")
        ts = rec.get("timestamp", "")
        if kind == "assistant":
            for b in content if isinstance(content, list) else []:
                if b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
                    asked.add(b.get("id"))
            text = clean(block_text(content))
            if text:
                yield "Claude", ts, text
            continue
        if isinstance(content, list):
            for b in content:
                if b.get("type") == "tool_result" and b.get("tool_use_id") in asked:
                    text = clean(block_text(b.get("content")))
                    if text:
                        yield "User (answer)", ts, text
        text = clean(block_text(content))
        if text:
            yield "User", ts, text


def first_prompt(path: Path) -> str:
    for role, _, text in turns(path):
        if role == "User":
            return " ".join(text.split())[:90]
    return "(no prompt)"


def fmt_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?", help="session id or path to a .jsonl transcript")
    ap.add_argument("--latest", action="store_true", help="use the most recently modified session")
    ap.add_argument("--skip-current", action="store_true", help="with --latest: skip the newest (usually the running) session")
    ap.add_argument("--list", action="store_true", help="list recent sessions instead of printing one")
    ap.add_argument("--project", help="project directory to search (default: all projects)")
    ap.add_argument("-n", type=int, default=10, help="how many sessions --list shows")
    a = ap.parse_args()

    if a.list:
        for f in sessions(a.project)[: a.n]:
            when = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"{when}  {f.stem}  {first_prompt(f)}")
        return
    if a.latest:
        found = sessions(a.project)[1 if a.skip_current else 0:]
        if not found:
            sys.exit("error: no sessions found")
        path = found[0]
    elif a.session:
        path = resolve(a.session)
    else:
        ap.error("give a session id/path, --latest or --list")

    out = [f"# Session {path.stem}", f"Source: {path}", ""]
    for role, ts, text in turns(path):
        out += [f"## {role} · {fmt_ts(ts)}", "", text, ""]
    print("\n".join(out))


if __name__ == "__main__":
    main()
