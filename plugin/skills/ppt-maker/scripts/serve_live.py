#!/usr/bin/env python3
"""
serve_live.py — overview.html 검토용 로컬 서버 + Edit 저장 엔드포인트.

사용법:
    python serve_live.py topics/<slug> [port]

    - 서빙 루트는 프로젝트 루트(topics/의 부모)다. 브라우저 주소:
      http://127.0.0.1:<port>/topics/<slug>/overview.html
    - 127.0.0.1에만 열린다(같은 네트워크의 다른 PC에서 접근 불가).

엔드포인트:
    POST /save   {"patch": "<마크다운 패치>", "page": "/topics/<slug>/overview.html"}
        200  모든 변경 반영
        409  일부만 반영 (applied < changes_requested)
        422  하나도 반영 못 함
        400  요청 형식 오류 또는 다른 topic의 페이지
        응답: {"applied", "changes_requested", "failed": [{slide, selector, reason}], "mtime"}
    GET  /mtime?page=...   {"mtime": "<나노초 문자열>"} — 브라우저가 3초마다 외부 수정 여부를 확인

50th serve-live.py 대비 고친 점:
    1) 블록 경계: <section|div ... data-slide="N"> 여는 태그부터 짝이 맞는 닫는 태그까지
    2) 같은 old가 블록 안에 2개 이상이고 NTH가 없으면 ambiguous로 거부
    3) 결과에 맞는 상태 코드(200/409/422)와 실패 목록
    4) 저장 대상은 overview.html 하나. 저장 전 overview.html.bak 1개를 남긴다
"""
from __future__ import annotations

import argparse
import io
import html as htmlmod
import json
import logging
import re
import shutil
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, unquote, urlparse

# Windows 콘솔(cp949)에서도 한글이 깨지지 않게 출력 인코딩을 UTF-8로 고정
for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        _stream.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="[serve_live] %(message)s")
logger = logging.getLogger("serve_live")

# 닫는 태그가 없는 빈 요소 — 깊이 계산에서 제외한다
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
OPEN_TAG_RE = re.compile(r"<([a-zA-Z][\w-]*)\b([^>]*)>")
SCENE_OPEN_RE = re.compile(r'<(section|div)\b[^>]*\bdata-slide="(\d+)"[^>]*>')


# ─────────────────────────────── 패치 파서 ───────────────────────────────

def parse_patch(patch_text: str) -> list[dict]:
    """overview Edit 패치(마크다운)를 변경 목록으로 바꾼다.

    형식:
        ## Slide 2 (steps)
        - .deck-footer
          NTH: 2          (선택: 같은 셀렉터·같은 문구가 여럿일 때 몇 번째인지)
          OLD: 이전 문구
          NEW: 새 문구
    """
    changes: list[dict] = []
    cur_num: str | None = None
    cur_sel: str | None = None
    cur_nth = 0
    reading: str | None = None
    old_buf: list[str] = []
    new_buf: list[str] = []

    def flush() -> None:
        nonlocal cur_sel, cur_nth, old_buf, new_buf, reading
        if cur_num is not None and cur_sel is not None and old_buf and new_buf:
            changes.append({
                "slide": cur_num,
                "selector": cur_sel,
                "nth": cur_nth,
                "old": "\n".join(old_buf).strip(),
                "new": "\n".join(new_buf).strip(),
            })
        cur_sel, cur_nth, old_buf, new_buf, reading = None, 0, [], [], None

    for line in patch_text.split("\n"):
        m = re.match(r"^## Slide (\d+)", line)
        if m:
            flush()
            cur_num = m.group(1)
            continue
        m = re.match(r"^- (\S+)\s*$", line)
        if m:
            flush()
            cur_sel = m.group(1)
            continue
        m = re.match(r"^\s+NTH: (\d+)\s*$", line)
        if m and reading is None:
            cur_nth = int(m.group(1))
            continue
        m = re.match(r"^\s+OLD: (.*)$", line)
        if m:
            reading, old_buf = "old", [m.group(1)]
            continue
        m = re.match(r"^\s+NEW: (.*)$", line)
        if m:
            reading, new_buf = "new", [m.group(1)]
            continue
        # 여러 줄 이어쓰기(드묾)
        if reading == "old":
            old_buf.append(line)
        elif reading == "new":
            new_buf.append(line)
    flush()
    return changes


# ─────────────────────────────── HTML 탐색 ───────────────────────────────

def find_close(html: str, tag: str, pos: int) -> tuple[int, int] | None:
    """pos(여는 태그 바로 뒤)부터 같은 이름 태그의 깊이를 세어 짝이 맞는 닫는 태그의 (시작, 끝)을 찾는다."""
    depth = 1
    pattern = re.compile(r"<(/?)" + re.escape(tag) + r"\b[^>]*?(/?)>", re.IGNORECASE)
    for m in pattern.finditer(html, pos):
        if m.group(1):          # </tag>
            depth -= 1
            if depth == 0:
                return m.start(), m.end()
        elif not m.group(2):    # <tag ...> (자기 닫힘 <tag/> 제외)
            depth += 1
    return None


def find_block(html: str, slide_num: str | int) -> tuple[int, int] | tuple[None, None]:
    """data-slide="N" 장면 요소의 (시작, 끝) 오프셋. 닫는 태그를 못 찾으면 다음 장면 시작을 끝으로 삼는다."""
    target = str(slide_num)
    for m in SCENE_OPEN_RE.finditer(html):
        if m.group(2) != target:
            continue
        start, tag = m.start(), m.group(1)
        close = find_close(html, tag, m.end())
        nxt = next((n.start() for n in SCENE_OPEN_RE.finditer(html, m.end()) if n.group(2) != target), len(html))
        end = close[1] if close and close[1] <= nxt else nxt
        return start, end
    return None, None


def _normalize(fragment: str) -> str:
    """비교용 정규화: 엔티티 풀기, <br/>→<br>, 공백 뭉치 → 한 칸."""
    s = htmlmod.unescape(fragment)
    s = re.sub(r"<br\s*/?>", "<br>", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()


def _selector_matches(tag: str, attrs: str, selector: str) -> bool:
    """단순 셀렉터(.a.b 또는 태그 이름)가 여는 태그와 맞는지."""
    if selector.startswith("."):
        want = [c for c in selector.split(".") if c]
        m = re.search(r'\bclass="([^"]*)"', attrs)
        have = set(m.group(1).split()) if m else set()
        return all(c in have for c in want)
    return tag.lower() == selector.lower()


def find_candidates(block: str, selector: str, old: str) -> list[tuple[int, int]]:
    """블록 안에서 셀렉터가 맞고 안쪽 HTML이 old와 같은 요소들의 (안쪽 시작, 안쪽 끝) 목록. 첫 여는 태그(장면 자신)는 건너뛴다."""
    want = _normalize(old)
    found: list[tuple[int, int]] = []
    first = OPEN_TAG_RE.search(block)
    scan_from = first.end() if first else 0
    for m in OPEN_TAG_RE.finditer(block, scan_from):
        tag, attrs = m.group(1), m.group(2)
        if tag.lower() in VOID_TAGS or attrs.rstrip().endswith("/"):
            continue
        if not _selector_matches(tag, attrs, selector):
            continue
        close = find_close(block, tag, m.end())
        if not close:
            continue
        if _normalize(block[m.end():close[0]]) == want:
            found.append((m.end(), close[0]))
    return found


def apply_changes(html: str, changes: list[dict]) -> tuple[str, int, list[dict]]:
    """변경을 차례로 적용한다. (새 HTML, 적용 수, 실패 목록)을 돌려준다."""
    applied = 0
    failed: list[dict] = []
    for ch in changes:
        def fail(reason: str) -> None:
            failed.append({"slide": ch["slide"], "selector": ch["selector"], "old": ch["old"], "new": ch["new"], "reason": reason})

        start, end = find_block(html, ch["slide"])
        if start is None:
            fail("장면 없음")
            continue
        block = html[start:end]
        cands = find_candidates(block, ch["selector"], ch["old"])
        if not cands:
            fail("OLD 문구를 찾지 못함")
            continue
        if len(cands) > 1 and not ch.get("nth"):
            fail(f"ambiguous: 같은 문구 {len(cands)}곳, NTH 필요")
            continue
        idx = (ch.get("nth") or 1) - 1
        if idx >= len(cands):
            fail(f"NTH {ch['nth']} 범위 밖(후보 {len(cands)}곳)")
            continue
        in_s, in_e = cands[idx]
        inner = block[in_s:in_e]
        lead = inner[: len(inner) - len(inner.lstrip())]      # 태그 안쪽 앞뒤 공백은 보존
        trail = inner[len(inner.rstrip()):]
        new_block = block[:in_s] + lead + ch["new"] + trail + block[in_e:]
        html = html[:start] + new_block + html[end:]
        applied += 1
    return html, applied, failed


# ─────────────────────────────── HTTP 서버 ───────────────────────────────

class LiveServer(ThreadingHTTPServer):
    """저장 대상 overview 경로·브라우저 경로·저장 잠금을 함께 들고 있는 서버."""

    def __init__(self, address: tuple[str, int], handler, overview: Path, page_path: str) -> None:
        super().__init__(address, handler)
        self.overview = overview
        self.page_path = page_path
        self.save_lock = threading.Lock()


class LiveHandler(SimpleHTTPRequestHandler):
    """정적 파일 + /save + /mtime. overview 경로·잠금은 서버 객체에 둔다."""

    @property
    def live(self) -> LiveServer:
        """타입이 정해진 서버 객체(BaseServer → LiveServer)."""
        return cast(LiveServer, self.server)

    server_version = "ppt-maker-serve-live"

    def end_headers(self) -> None:
        # 편집 결과가 바로 보이도록 캐시를 끈다
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _reply_json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _page_ok(self, page: str | None) -> bool:
        """요청한 페이지가 이 서버가 맡은 overview인지. page가 없으면(명령줄 도구) 허용한다."""
        return page is None or unquote(page) == self.live.page_path

    def _mtime(self) -> str:
        return str(self.live.overview.stat().st_mtime_ns)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/mtime":
            page = parse_qs(url.query).get("page", [None])[0]
            if not self._page_ok(page):
                self._reply_json(404, {"error": "이 서버가 맡은 topic이 아님"})
                return
            self._reply_json(200, {"mtime": self._mtime()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/save":
            self._reply_json(404, {"error": "알 수 없는 엔드포인트"})
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            self._reply_json(400, {"error": "빈 요청"})
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            patch = data.get("patch", "")
            page = data.get("page")
        except (ValueError, AttributeError) as exc:
            self._reply_json(400, {"error": f"JSON 형식 오류: {exc}"})
            return
        if not self._page_ok(page):
            self._reply_json(400, {"error": f"다른 topic의 페이지({page})는 저장하지 않음. 대상: {self.live.page_path}"})
            return
        changes = parse_patch(patch or "")
        if not changes:
            self._reply_json(422, {"applied": 0, "changes_requested": 0, "failed": [], "error": "패치에서 변경을 찾지 못함"})
            return

        with self.live.save_lock:
            path: Path = self.live.overview
            # 저장 직전에 파일을 다시 읽는다(Claude가 그사이 고쳤을 수 있음). 줄바꿈은 그대로 보존
            with path.open("r", encoding="utf-8", newline="") as f:
                original = f.read()
            new_html, applied, failed = apply_changes(original, changes)
            if applied > 0:
                shutil.copyfile(path, path.with_name(path.name + ".bak"))
                with path.open("w", encoding="utf-8", newline="") as f:
                    f.write(new_html)
            mtime = self._mtime()

        requested = len(changes)
        code = 200 if applied == requested else (409 if applied > 0 else 422)
        logger.info("save: %d/%d 반영, 실패 %d → %d", applied, requested, len(failed), code)
        for f in failed:
            logger.info("  실패 #%s %s: %s", f["slide"], f["selector"], f["reason"])
        self._reply_json(code, {"applied": applied, "changes_requested": requested, "failed": failed, "mtime": mtime})

    def log_message(self, format: str, *args) -> None:  # noqa: A002 (표준 시그니처)
        logger.debug(format, *args)


def resolve_root(topic_dir: Path) -> Path:
    """topics/<slug> 형태면 프로젝트 루트(topics의 부모)를, 아니면 topic 폴더 자체를 서빙 루트로."""
    return topic_dir.parent.parent if topic_dir.parent.name == "topics" else topic_dir


def make_server(topic_dir: Path, port: int = 8765, host: str = "127.0.0.1") -> LiveServer:
    """테스트에서도 쓰는 서버 생성기. port=0이면 빈 포트를 고른다."""
    topic_dir = topic_dir.resolve()
    overview = topic_dir / "overview.html"
    if not overview.is_file():
        raise FileNotFoundError(f"overview.html 없음: {overview}")
    root = resolve_root(topic_dir)
    page_path = "/" + overview.relative_to(root).as_posix()
    return LiveServer((host, port), partial(LiveHandler, directory=str(root)), overview, page_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="overview.html 검토 서버 + Edit 저장")
    parser.add_argument("topic", type=Path, help="topics/<slug> 폴더")
    parser.add_argument("port", type=int, nargs="?", default=8765, help="포트 (기본 8765)")
    args = parser.parse_args()
    try:
        server = make_server(args.topic, args.port)
    except (FileNotFoundError, OSError) as exc:
        logger.error("%s", exc)
        return 1
    logger.info("열기: http://127.0.0.1:%d%s", server.server_address[1], server.page_path)
    logger.info("Edit 저장 대상: %s (저장 전 .bak 1개)", server.overview)
    logger.info("멈추려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("종료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
