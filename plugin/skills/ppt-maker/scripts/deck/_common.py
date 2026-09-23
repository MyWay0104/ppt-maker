"""scripts/deck/ 도구들이 함께 쓰는 도우미.

- Windows 콘솔에서도 한글이 깨지지 않게 출력 인코딩을 UTF-8로 고정
- topic 폴더 또는 html 파일 경로 → overview.html 경로
- 장면(<section class="scene">) 분리·찾기: 정규식 `.*?</section>` 대신 깊이 계산으로 자른다
- 장면을 화면 부분과 발표자 노트로 나누기
"""
from __future__ import annotations

import html as htmlmod
import io
import logging
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        _stream.reconfigure(encoding="utf-8")

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
from validate_topic import read_front_matter, split_scenes, strip_comments  # noqa: E402,F401  # pyright: ignore[reportMissingImports]

NOTE_MARK = '<aside class="speaker-note">'
SLIDES_RE = re.compile(r"<!--\s*SLIDES START\s*-->(.*?)<!--\s*SLIDES END\s*-->", re.S)
SCENE_STYLES_RE = re.compile(r'<style\s+id="scene-styles"\s*>(.*?)</style>', re.S)


def get_logger(name: str) -> logging.Logger:
    """한 줄 메시지 형식의 로거"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return logging.getLogger(name)


def resolve_overview(path: Path) -> Path:
    """topics/<slug> 폴더면 그 안의 overview.html, html 파일이면 그대로."""
    return path if path.suffix == ".html" else path / "overview.html"


def attr(attrs: str, name: str) -> str | None:
    """여는 태그 속성 문자열에서 name="값"을 꺼낸다."""
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', attrs)
    return m.group(1) if m else None


def scene_spans(doc: str) -> list[tuple[int, int, str]]:
    """문서 안 최상위 scene <section>의 (시작, 끝, 여는 태그 속성) 목록. SLIDES 마커가 있으면 그 안만 본다."""
    base = 0
    region = doc
    m = SLIDES_RE.search(doc)
    if m:
        base, region = m.start(1), m.group(1)
    spans: list[tuple[int, int, str]] = []
    depth = 0
    start = 0
    attrs = ""
    for t in re.finditer(r"<(/?)section\b([^>]*)>", region):
        if not t.group(1):
            if depth == 0:
                start, attrs = t.start(), t.group(2)
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                if "scene" in (attr(attrs, "class") or "").split():
                    spans.append((base + start, base + t.end(), attrs))
    return spans


def find_scene(doc: str, sid: str) -> tuple[int, int] | None:
    """data-scene-id(또는 없으면 data-slide)가 sid인 장면의 (시작, 끝)."""
    for s, e, attrs in scene_spans(doc):
        if attr(attrs, "data-scene-id") == sid or (attr(attrs, "data-scene-id") is None and attr(attrs, "data-slide") == sid):
            return s, e
    return None


def split_note(scene: str) -> tuple[str, str]:
    """장면을 화면 부분과 발표자 노트(이후)로 나눈다."""
    cut = scene.find(NOTE_MARK)
    return (scene[:cut], scene[cut:]) if cut >= 0 else (scene, "")


def plain_text(markup: str) -> str:
    """태그와 코드 블록을 지운 글자만 남긴다."""
    without_code = re.sub(r"<pre[^>]*>.*?</pre>", " ", markup, flags=re.S)
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", without_code))).strip()
