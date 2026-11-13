"""Find the editable blocks of a body fragment and edit them in place.

A block is a text-bearing element (paragraph, list item, heading, table cell,
caption...) that holds no other block. Its id is its position in document
order ("b0", "b1", ...), so the same body always yields the same ids. Both the
inspector page (which tags each block with data-dd) and the edit endpoint
(which rewrites one block's inner HTML) use this one index.
"""
import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser

BLOCK_TAGS = {"p", "li", "h2", "h3", "h4", "td", "th", "dt", "dd", "caption",
              "cite", "figcaption", "pre", "blockquote", "div"}
VOID_TAGS = {"br", "img", "hr", "wbr", "input", "meta", "link", "source", "col"}
INLINE_KEEP = {"strong", "b", "em", "i", "code", "a", "br"}


@dataclass
class Block:
    id: str
    tag: str
    tag_end: int      # offset just after the start tag's name (where an attribute can go)
    inner_start: int  # offset of the first character inside the element
    inner_end: int    # offset of its end tag
    section: str      # text of the nearest preceding h2


class _Indexer(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", source)]
        self.stack: list[dict] = []
        self.found: list[tuple[int, dict]] = []
        self.section = ""
        self._h2_text: list[str] | None = None

    def _offset(self) -> int:
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            return
        start = self._offset()
        text = self.get_starttag_text() or ""
        node = {"tag": tag, "start": start, "inner": start + len(text),
                "name_end": start + 1 + len(tag), "has_block": False}
        if tag in BLOCK_TAGS:
            for parent in self.stack:
                parent["has_block"] = True
        self.stack.append(node)
        if tag == "h2":
            self._h2_text = []

    def handle_data(self, data):
        if self._h2_text is not None:
            self._h2_text.append(data)

    def handle_endtag(self, tag):
        if not any(n["tag"] == tag for n in self.stack):
            return
        end = self._offset()
        while self.stack:
            node = self.stack.pop()
            if node["tag"] == tag:
                break
        if tag == "h2" and self._h2_text is not None:
            self.section = " ".join("".join(self._h2_text).split())
            self._h2_text = None
        if node["tag"] in BLOCK_TAGS and not node["has_block"]:
            # a div is only a block when it holds text directly (a callout's text is in its <p>)
            if node["tag"] == "div" and not self.source[node["inner"]:end].strip():
                return
            self.found.append((node["start"], {**node, "end": end, "section": self.section}))


def index(body: str) -> list[Block]:
    parser = _Indexer(body)
    parser.feed(body)
    parser.close()
    ordered = sorted(parser.found, key=lambda item: item[0])
    return [Block(id=f"b{i}", tag=n["tag"], tag_end=n["name_end"], inner_start=n["inner"],
                  inner_end=n["end"], section=n["section"]) for i, (_, n) in enumerate(ordered)]


def annotate(body: str) -> str:
    """Return the body with data-dd="<id>" on every block's start tag."""
    out, last = [], 0
    for b in index(body):
        out.append(body[last:b.tag_end])
        out.append(f' data-dd="{b.id}"')
        last = b.tag_end
    out.append(body[last:])
    return "".join(out)


def find(body: str, block_id: str) -> Block | None:
    return next((b for b in index(body) if b.id == block_id), None)


def text_of(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


class _Sanitizer(HTMLParser):
    """Keep text and a few inline tags from edited HTML; drop everything else."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0  # inside <script>/<style>: drop the contents too

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            if href.startswith(("http://", "https://", "mailto:", "#")):
                self.out.append(f'<a href="{html.escape(href, quote=True)}">')
            else:
                self.out.append("<a>")
        elif tag == "br":
            self.out.append("<br>")
        elif tag in INLINE_KEEP:
            self.out.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag in INLINE_KEEP and tag != "br":
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data, quote=False))


def sanitize_inline(fragment: str) -> str:
    s = _Sanitizer()
    s.feed(fragment)
    s.close()
    return re.sub(r"[ \t\r\n\xa0]+", " ", "".join(s.out)).strip()


def replace(body: str, block_id: str, new_inner: str) -> str:
    """Replace one block's inner HTML. A <pre> takes plain text and keeps its <code>."""
    b = find(body, block_id)
    if b is None:
        raise KeyError(block_id)
    if b.tag == "pre":
        code = html.escape(new_inner.strip("\n"), quote=False)
        inner = f"<code>{code}</code>"
    else:
        inner = sanitize_inline(new_inner)
    return body[:b.inner_start] + inner + body[b.inner_end:]
