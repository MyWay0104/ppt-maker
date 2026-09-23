#!/usr/bin/env python3
"""
build_present.py — overview.html(원본)에서 발표용 present.html을 만든다.

사용법:
    python build_present.py topics/<slug>          # present.html 생성
    python build_present.py topics/<slug> --check  # 현재 present.html이 최신인지만 확인

하는 일:
    1) overview.html의 <style id="scene-styles"> 내용과 SLIDES START/END 사이 <section class="scene">을 꺼낸다
    2) 장면이 data-slide 1..N 연번인지 확인한다(아니면 실패)
    3) 편집 흔적(data-editable, contenteditable, spellcheck)을 지운다
    4) assets/present.template.html에 deck.css·deck.js와 함께 끼워 넣는다

종료 코드: 0 성공 / 1 추출·검증 실패 또는 --check에서 최신 아님 / 3 BRIEF 미확정(게이트 A)
"""
from __future__ import annotations

import argparse
import html as htmlmod
import io
import logging
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        _stream.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("build_present")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from validate_topic import read_front_matter, split_scenes, strip_comments  # noqa: E402  # pyright: ignore[reportMissingImports]

TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "present.template.html"
DECK_CSS_PATH = SCRIPT_DIR / "deck.css"
DECK_JS_PATH = SCRIPT_DIR / "deck.js"

SCENE_STYLES_RE = re.compile(r'<style\s+id="scene-styles"\s*>(.*?)</style>', re.S)
SLIDES_RE = re.compile(r"<!--\s*SLIDES START\s*-->(.*?)<!--\s*SLIDES END\s*-->", re.S)
EDIT_ATTR_RE = re.compile(r'\s(?:data-editable|contenteditable|spellcheck)(?:="[^"]*")?(?=[\s>/])')
SLUG_META_RE = re.compile(r'<meta\s+name="ppt-maker-slug"\s+content="([^"]*)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)


class BuildError(Exception):
    """추출·검증 실패"""


def replace_line_placeholder(template: str, name: str, content: str) -> str:
    """한 줄에 혼자 있는 {{NAME}}만 치환한다. 주석 속 설명용 표기는 건드리지 않는다(50th sync_overview.py에서 가져옴)."""
    pattern = re.compile(rf"^[ \t]*\{{\{{{name}\}}\}}[ \t]*$", re.M)
    if not pattern.search(template):
        raise BuildError(f"템플릿에서 단독 줄 자리표시자 {{{{{name}}}}}를 찾지 못했다.")
    return pattern.sub(lambda _m: content, template, count=1)


def strip_edit_attrs(fragment: str) -> str:
    """여는 태그 안의 편집용 속성만 지운다(본문 글자는 건드리지 않는다)."""
    return re.sub(r"<[a-zA-Z][^>]*>", lambda m: EDIT_ATTR_RE.sub("", m.group(0)), fragment)


def build(topic: Path) -> tuple[str, int]:
    """present.html 내용과 장면 수를 돌려준다."""
    overview_path = topic / "overview.html"
    if not overview_path.is_file():
        raise BuildError(f"{overview_path}: 없음")
    raw = overview_path.read_text(encoding="utf-8")
    src = strip_comments(raw)          # 주석 속 태그 글자 오인 방지

    styles = SCENE_STYLES_RE.search(src)
    if not styles:
        raise BuildError(f"{overview_path}: <style id=\"scene-styles\">를 찾지 못했다")
    slides = SLIDES_RE.search(src)
    if not slides:
        raise BuildError(f"{overview_path}: SLIDES START/END 마커를 찾지 못했다")

    scenes = split_scenes(slides.group(1))
    if not scenes:
        raise BuildError(f"{overview_path}: SLIDES 영역에 장면이 없다")
    for i, (attrs, _) in enumerate(scenes, start=1):
        m = re.search(r'\bdata-slide="(\d+)"', attrs)
        if not m or m.group(1) != str(i):
            raise BuildError(f"{overview_path}: {i}번째 장면의 data-slide가 {m.group(1) if m else '(없음)'} — 1부터 연번이어야 한다")

    slides_html = "\n\n".join(strip_edit_attrs(html) for _, html in scenes)

    brief = read_front_matter(topic / "BRIEF.md") if (topic / "BRIEF.md").is_file() else {}
    title = brief.get("title") or ""
    if not title:
        t = TITLE_RE.search(raw)
        title = re.sub(r"\s*·\s*Overview\s*$", "", t.group(1)).strip() if t else topic.name
    slug_m = SLUG_META_RE.search(raw)
    slug = slug_m.group(1) if slug_m else topic.name

    out = TEMPLATE_PATH.read_text(encoding="utf-8")
    out = out.replace("__SLUG__", htmlmod.escape(slug, quote=True)).replace("__TITLE__", htmlmod.escape(title))
    out = replace_line_placeholder(out, "DECK_CSS", DECK_CSS_PATH.read_text(encoding="utf-8").rstrip())
    out = replace_line_placeholder(out, "SCENE_STYLES", styles.group(1).strip("\n"))
    out = replace_line_placeholder(out, "SLIDES_HTML", slides_html)
    out = replace_line_placeholder(out, "DECK_JS", DECK_JS_PATH.read_text(encoding="utf-8").rstrip())
    return out, len(scenes)


def main() -> int:
    parser = argparse.ArgumentParser(description="overview.html → present.html")
    parser.add_argument("topic", type=Path, help="topics/<slug> 폴더")
    parser.add_argument("--check", action="store_true", help="파일을 쓰지 않고 present.html이 최신인지만 확인")
    args = parser.parse_args()
    topic: Path = args.topic

    brief = read_front_matter(topic / "BRIEF.md") if (topic / "BRIEF.md").is_file() else {}
    if brief.get("status") != "confirmed":
        logger.error("BRIEF.md status가 confirmed가 아니다 — 게이트 A (현재: %s)", brief.get("status", "(없음)"))
        return 3
    try:
        content, scene_count = build(topic)
    except BuildError as exc:
        logger.error("실패: %s", exc)
        return 1

    target = topic / "present.html"
    if args.check:
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != content:
            logger.error("present.html이 최신이 아니다 — python build_present.py %s 로 다시 만든다", topic)
            return 1
        logger.info("present.html 최신: %s", target)
        return 0

    target.write_text(content, encoding="utf-8", newline="\n")
    logger.info("생성: %s (장면 %d장)", target, scene_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
