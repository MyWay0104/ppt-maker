#!/usr/bin/env python3
"""
migrate_from_index.py — (1회용) 영상 프레임워크 규약의 index.html 덱을 ppt-maker overview.html로 옮긴다.

사용법:
    python migrate_from_index.py <옛 index.html> topics/<slug> [--extract-patch 01_legacy.css] [--force]

옮기는 규칙:
    - 옛 파일의 <style id="scene-styles"> 내용을 그대로 가져온다
      · 폰트 @font-face 줄은 지우고 첫 줄에 @import url("assets/fonts/fonts.css");
      · 옛 패치 마커(/* >>> XXX-PATCH START >>> */ … END) → /* ===== PATCH START/END ===== */
      · --extract-patch를 주면 패치 내용을 _work/slide_ui/<이름>으로 꺼내 둔다(apply_css_patch.py로 재적용 가능)
    - 장면 <section class="scene …">: id·타이밍 속성·clip 클래스를 지우고 data-slide="N"을 매긴다
    - 장면 사이 BLOCK 주석(<!-- BLOCK:X START/END -->)은 그대로 둔다
    - 루트 래퍼(<div id="root" …>), 캔버스 전용 <style>, <script>는 버린다
    - 결과는 assets/overview.template.html을 채운 topics/<slug>/overview.html

게이트 A: 대상 topic의 BRIEF.md가 confirmed가 아니면 exit 3.
종료 코드: 0 성공 / 1 입력 오류·이미 있음 / 3 BRIEF 미확정
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
logger = logging.getLogger("migrate_from_index")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from build_present import replace_line_placeholder  # noqa: E402  # pyright: ignore[reportMissingImports]
from validate_topic import read_front_matter  # noqa: E402  # pyright: ignore[reportMissingImports]

TEMPLATE = SCRIPT_DIR.parent / "assets" / "overview.template.html"
SCENE_STYLES_RE = re.compile(r'<style\s+id="scene-styles"\s*>(.*?)</style>', re.S)
FONT_FACE_RE = re.compile(r"^[ \t]*@font-face\s*\{[^}]*\}[ \t]*\n", re.M)
OLD_PATCH_RE = re.compile(r"/\*\s*>>>\s*[\w-]*PATCH START\s*>>>\s*\*/(.*?)/\*\s*<<<\s*[\w-]*PATCH END\s*<<<\s*\*/", re.S)
# 옛 타이밍 속성 이름은 이 스크립트가 "흔적 0건" grep에 걸리지 않도록 조립해서 쓴다
REMOVED_ATTRS = ("id", "data-" + "start", "data-duration", "data-track-index", "data-media-" + "start")
INDENT = "      "


def convert_styles(css: str) -> tuple[str, str | None]:
    """장면 CSS를 새 규약으로 바꾼다. (새 CSS, 옛 패치 내용 또는 None)"""
    css = FONT_FACE_RE.sub("", css)
    patch_body = None
    m = OLD_PATCH_RE.search(css)
    if m:
        patch_body = m.group(1).strip("\n")
        css = css[:m.start()] + "/* ===== PATCH START ===== */\n" + m.group(1).rstrip() + "\n" + INDENT + "/* ===== PATCH END ===== */" + css[m.end():]
    else:
        css = css.rstrip() + f"\n{INDENT}/* ===== PATCH START ===== */\n{INDENT}/* ===== PATCH END ===== */\n"
    css = f'{INDENT}@import url("assets/fonts/fonts.css");\n' + css.lstrip("\n")
    return css.rstrip("\n"), patch_body


def convert_open_tag(tag: str, number: int) -> str:
    """장면 여는 태그: 옛 속성·clip 클래스 제거, data-slide 부여."""
    for name in REMOVED_ATTRS:
        tag = re.sub(rf'\s{re.escape(name)}="[^"]*"', "", tag)
    tag = re.sub(r'class="([^"]*)"', lambda m: 'class="' + " ".join(c for c in m.group(1).split() if c != "clip") + '"', tag, count=1)
    if re.search(r'\sdata-slide="', tag):
        return re.sub(r'(\sdata-slide=")[^"]*(")', rf'\g<1>{number}\g<2>', tag, count=1)
    return tag[:-1] + f' data-slide="{number}">'


def extract_slides(doc: str) -> tuple[str, int]:
    """본문에서 장면과 BLOCK 주석만 순서대로 꺼내 새 규약으로 바꾼다. (HTML, 장면 수)"""
    body = doc[doc.index("<body"):]
    pieces: list[str] = []
    number = 0
    depth = 0
    start = 0
    token_re = re.compile(r"<!--\s*BLOCK:\S+\s+(?:START|END)\s*-->|<(/?)section\b[^>]*>")
    for t in token_re.finditer(body):
        if t.group(0).startswith("<!--"):
            if depth == 0:
                pieces.append(t.group(0).strip())
            continue
        if not t.group(1):
            if depth == 0:
                start = t.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                block = body[start:t.end()]
                open_tag = block[: block.index(">") + 1]
                if "scene" not in re.search(r'class="([^"]*)"', open_tag).group(1).split():  # type: ignore[union-attr]
                    continue
                number += 1
                pieces.append(convert_open_tag(open_tag, number) + block[len(open_tag):])
    return "\n\n".join(pieces), number


def main() -> int:
    parser = argparse.ArgumentParser(description="옛 index.html → overview.html (1회용)")
    parser.add_argument("source", type=Path, help="옛 index.html (또는 그 폴더)")
    parser.add_argument("topic", type=Path, help="대상 topics/<slug>")
    parser.add_argument("--extract-patch", default=None, help="옛 패치 내용을 _work/slide_ui/<이 이름>으로 저장")
    parser.add_argument("--force", action="store_true", help="이미 있는 overview.html을 덮어쓴다")
    args = parser.parse_args()

    src = args.source / "index.html" if args.source.is_dir() else args.source
    topic: Path = args.topic
    if not src.is_file():
        logger.error("원본이 없다: %s", src)
        return 1
    brief = read_front_matter(topic / "BRIEF.md") if (topic / "BRIEF.md").is_file() else {}
    if brief.get("status") != "confirmed":
        logger.error("게이트 A: %s/BRIEF.md status가 confirmed가 아니다(현재 %s). BRIEF를 먼저 확정한다.", topic, brief.get("status", "(없음)"))
        return 3
    out = topic / "overview.html"
    if out.exists() and not args.force:
        logger.error("이미 있다: %s (--force로 덮어쓰기)", out)
        return 1

    doc = src.read_text(encoding="utf-8")
    styles = SCENE_STYLES_RE.search(doc)
    if not styles:
        logger.error('원본에 <style id="scene-styles">가 없다 — 이 스크립트의 대상이 아니다')
        return 1
    scene_css, patch_body = convert_styles(styles.group(1))
    slides_html, count = extract_slides(doc)
    if count == 0:
        logger.error("장면을 찾지 못했다")
        return 1

    title = brief.get("title") or ""
    if not title:
        t = re.search(r"<title>(.*?)</title>", doc, re.S)
        title = re.sub(r"\s*·.*$", "", t.group(1)).strip() if t else topic.name
    tpl = TEMPLATE.read_text(encoding="utf-8")
    tpl = tpl.replace("{{TITLE}}", htmlmod.escape(title)).replace("{{SLUG}}", htmlmod.escape(topic.name, quote=True))
    tpl = replace_line_placeholder(tpl, "SCENE_STYLES", scene_css)
    tpl = replace_line_placeholder(tpl, "SLIDES_HTML", slides_html)
    out.write_text(tpl, encoding="utf-8", newline="\n")
    logger.info("생성: %s (장면 %d장)", out, count)

    if patch_body is not None:
        logger.info("옛 패치 구간: %d줄 → PATCH START/END로 변환", patch_body.count("\n") + 1)
        if args.extract_patch:
            dest = topic / "_work" / "slide_ui" / args.extract_patch
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(patch_body + "\n", encoding="utf-8", newline="\n")
            logger.info("패치 내용 저장: %s (apply_css_patch.py로 재적용 가능)", dest)
    logger.info("다음: validate_topic.py → build_present.py → dump_deck_text.py로 원본과 글자 대조")
    return 0


if __name__ == "__main__":
    sys.exit(main())
