"""Local intake and source change detection; these never approve knowledge claims."""
from __future__ import annotations

import hashlib
import gzip
import json
import re
import unicodedata
import zlib
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import brotli

from .library import Library, load_state


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", unescape(text)).split())


class VisibleText(HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def visible_text(html: str) -> str:
    parser = VisibleText()
    parser.feed(html)
    return normalize(" ".join(parser.parts))


def fetch_text(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ValueError("Only public HTTPS sources without credentials are supported")
    post = re.fullmatch(r"https://(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)/status/(\d+)/?", url)
    if post:
        # Official public embed endpoint. No cookies, account login or mirror services.
        endpoint = f"https://cdn.syndication.twimg.com/tweet-result?id={post[2]}&lang=en&token=0"
        with urlopen(Request(endpoint, headers={"User-Agent": "OpenMentor/0.1"}), timeout=20) as response:
            payload = json.loads(response.read(1024 * 1024))
        if payload.get("id_str") != post[2] or payload.get("user", {}).get("screen_name", "").casefold() != post[1].casefold():
            raise ValueError("X did not return this public post with the expected author")
        if not isinstance(payload.get("text"), str) or not payload["text"].strip():
            raise ValueError("X returned no public post text")
        return normalize(payload["text"])
    req = Request(url, headers={"User-Agent": "OpenMentor/0.1 (public source change check)", "Accept": "text/html,text/plain"})
    with urlopen(req, timeout=20) as response:
        if urlparse(response.url).scheme != "https":
            raise ValueError("Source redirected outside HTTPS")
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
            raise ValueError(f"Import this format manually: {content_type}")
        data = response.read(4 * 1024 * 1024 + 1)
        if len(data) > 4 * 1024 * 1024:
            raise ValueError("Source is larger than 4 MiB; import a scoped text extract")
        encoding = response.headers.get("Content-Encoding", "identity").lower().strip()
        try:
            if encoding == "br":
                data = brotli.decompress(data)
            elif encoding == "gzip":
                data = gzip.decompress(data)
            elif encoding == "deflate":
                data = zlib.decompress(data)
            elif encoding not in {"identity", ""}:
                raise ValueError(f"Unsupported content encoding: {encoding}")
        except (brotli.error, zlib.error, OSError, EOFError) as exc:
            raise ValueError(f"Invalid {encoding} source response") from exc
        if len(data) > 4 * 1024 * 1024:
            raise ValueError("Decoded source is larger than 4 MiB; import a scoped text extract")
        charset = response.headers.get_content_charset()
        if not charset and content_type != "text/plain":
            declared = re.search(br'charset\s*=\s*["\x27]?([A-Za-z0-9_-]+)', data[:8192], re.I)
            charset = declared[1].decode("ascii") if declared else None
        try:
            text = data.decode(charset or "utf-8")
        except UnicodeDecodeError:
            if charset or content_type == "text/plain":
                raise
            # Legacy HTML with no charset (including older author essays).
            text = data.decode("windows-1252")
        except LookupError as exc:
            raise ValueError(f"Unsupported source charset: {charset}") from exc
    return visible_text(text) if content_type != "text/plain" else normalize(text)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class Updates:
    def __init__(self, library: Library):
        self.library = library
        self.root = library.state_dir

    def _save(self, state: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.root / "state.json.tmp"
        temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        temp.replace(self.root / "state.json")

    def _snapshot(self, source_id: str, text: str) -> str:
        digest = sha256(text)
        path = self.root / "revisions" / source_id / (digest + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(text)
        return digest

    def missing_excerpts(self, source_id: str, text: str) -> list[str]:
        normalized = normalize(text)
        return [e["id"] for e in self.library.evidence.values()
                if e["source_id"] == source_id and e["verification"]["status"] == "reviewed"
                and normalize(e["excerpt"]) not in normalized]

    def ingest(self, source_id: str, path: Path) -> dict:
        self.library.source(source_id)
        path = Path(path)
        if path.suffix.lower() not in {".txt", ".md", ".vtt", ".srt"}:
            raise ValueError("Import UTF-8 .txt/.md/.vtt/.srt files")
        text = normalize(path.read_text(encoding="utf-8-sig"))
        if not text:
            raise ValueError("Source text is empty")
        digest = self._snapshot(source_id, text)
        return {"source_id": source_id, "revision": digest, "missing_excerpts": self.missing_excerpts(source_id, text),
                "status": "imported_pending_review", "note": "导入不改变证据核验状态；官方字幕也需核对说话人、上下文和定位。"}

    def check(self, source_id: str) -> dict:
        source = self.library.source(source_id)
        if source["refresh"]["mode"] == "manual":
            return {"source_id": source_id, "status": "manual_check_required", "url": source["url"]}
        state = load_state(self.root)
        previous = state.get(source_id, {})
        accepted = previous.get("accepted_sha256") or source["content_sha256"]
        try:
            text = fetch_text(source["url"])
            digest = self._snapshot(source_id, text)
            missing = self.missing_excerpts(source_id, text)
            status = "accepted" if accepted == digest and not missing else ("changed" if accepted else "unreviewed_revision")
            result = {**previous, "status": status, "accepted_sha256": accepted, "latest_sha256": digest,
                      "missing_excerpts": missing, "last_checked_at": timestamp()}
            result.pop("error", None)
        except (OSError, ValueError, UnicodeError, HTTPException) as exc:
            result = {**previous, "status": "unavailable", "error": str(exc), "last_checked_at": timestamp()}
        state[source_id] = result
        self._save(state)
        return {"source_id": source_id, **result}

    def accept(self, source_id: str, revision: str, reviewer: str) -> dict:
        self.library.source(source_id)
        if not re.fullmatch(r"[a-f0-9]{64}", revision) or not reviewer.strip():
            raise ValueError("A SHA-256 revision and named reviewer are required")
        path = self.root / "revisions" / source_id / (revision + ".txt")
        if not path.is_file():
            raise ValueError("Unknown revision; fetch or import it first")
        text = path.read_text()
        if sha256(text) != revision:
            raise ValueError("Snapshot integrity check failed")
        missing = self.missing_excerpts(source_id, text)
        if missing:
            raise ValueError("Reviewed excerpts absent from this revision: " + ", ".join(missing))
        state = load_state(self.root)
        result = {"status": "accepted", "accepted_sha256": revision, "latest_sha256": revision,
                  "last_checked_at": timestamp(), "accepted_at": timestamp(), "reviewer": reviewer,
                  "note": "确认资料版本；不自动确认 pending/disputed 证据或其事实正确性。"}
        state[source_id] = result
        self._save(state)
        return {"source_id": source_id, **result}

    def import_x(self, person: str, path: Path) -> dict:
        """Import a documented public-post export into a private review inbox."""
        profile = self.library.person(person)
        payload = json.loads(Path(path).read_text())
        posts = payload.get("posts") if isinstance(payload, dict) else None
        if not isinstance(posts, list) or not posts:
            raise ValueError("Expected a nonempty posts array; see docs/SOURCES.md")
        seen, draft = set(), []
        for post in posts:
            if not isinstance(post, dict) or not all(isinstance(post.get(k), str) and post[k].strip() for k in ("url", "author", "published_at", "text")):
                raise ValueError("Each post requires url, author, published_at and text")
            match = re.fullmatch(r"https://(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)/status/(\d+)/?", post["url"])
            if not match or match[1].casefold() != post["author"].lstrip("@").casefold():
                raise ValueError("Post author must match its canonical X URL")
            datetime.fromisoformat(post["published_at"].replace("Z", "+00:00"))
            if match[2] in seen:
                raise ValueError("Duplicate post id: " + match[2])
            seen.add(match[2])
            draft.append({**post, "status": "pending", "origin_verified": False})
        text = json.dumps({"person_id": profile["id"], "posts": draft}, ensure_ascii=False, indent=2)
        digest = sha256(text)
        target = self.root / "inbox" / (digest + ".json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n")
        return {"status": "pending_review", "post_count": len(draft), "path": str(target.resolve()),
                "note": "URL 与作者格式校验不证明本人身份和原文真实性；核对后再贡献知识包。"}
