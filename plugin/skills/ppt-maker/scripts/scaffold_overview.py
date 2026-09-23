#!/usr/bin/env python3
"""
scaffold_overview.py — BRIEF가 확정된 topic에 첫 overview.html(제목 장면 1장)을 만든다.

사용법:
    python scaffold_overview.py topics/<slug>
    python scaffold_overview.py topics/<slug> --force     # 이미 있는 overview.html을 덮어쓴다(주의)

하는 일:
    1) BRIEF.md status가 confirmed가 아니면 exit 3 (게이트 A — HTML은 BRIEF 확정 뒤에만)
    2) DESIGN.md의 색을 deck-design 2절 매핑표대로 :root 토큰으로 옮긴다
       (front matter `colors:` 또는 본문 `{colors.키}` — #hex 두 형식 모두 읽음)
    3) assets/scene-base.css + 토큰 + 빈 PATCH 구간으로 장면 스타일을 만든다
    4) BRIEF 제목으로 title 장면 1장을 넣어 assets/overview.template.html을 채운다

종료 코드: 0 생성 / 1 이미 있음·입력 오류 / 3 BRIEF 미확정
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
logger = logging.getLogger("scaffold_overview")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from build_present import replace_line_placeholder  # noqa: E402  # pyright: ignore[reportMissingImports]
from validate_topic import read_front_matter  # noqa: E402  # pyright: ignore[reportMissingImports]

ASSETS = SCRIPT_DIR.parent / "assets"

# deck-design 2절: 장면 토큰 ← DESIGN 키(앞에 있는 것 우선)
TOKEN_MAP = [
    ("--accent", ("primary", "accent", "brand"), "#2f6fde"),
    ("--accent-2", ("secondary", "accent-2", "tertiary"), None),  # 없으면 --accent 값을 쓴다
    ("--bg", ("canvas-soft", "canvas", "background"), "#f7f6f3"),
    ("--surface", ("surface", "card"), "#ffffff"),
    ("--text", ("ink", "text", "foreground"), "#1f2328"),
    ("--text-dim", ("ink-muted", "ink-secondary", "ink-soft", "text-muted"), "#5b616b"),
    ("--line", ("hairline", "border", "divider"), "#e3e1dc"),
]
RADIUS_KEYS = ("lg", "card")
HEX = r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b"


def design_colors(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """DESIGN.md에서 색과 둥글기 값을 모은다. front matter가 본문보다 우선."""
    colors: dict[str, str] = {}
    rounded: dict[str, str] = {}
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if fm:
        section = None
        for line in fm.group(1).splitlines():
            top = re.match(r"^([A-Za-z_][\w-]*)\s*:", line)
            if top:
                section = top.group(1)
                continue
            kv = re.match(r"^\s+([A-Za-z_][\w-]*)\s*:\s*[\"']?([^\"'#\s][^\"'\s]*|#[0-9a-fA-F]{3,6})[\"']?", line)
            if not kv:
                continue
            key, val = kv.group(1), kv.group(2)
            if section == "colors" and re.fullmatch(HEX, val):
                colors.setdefault(key, val)
            elif section == "rounded" and re.fullmatch(r"\d+px", val):
                rounded.setdefault(key, val)
    # 본문 형식: `{colors.primary}` — #0075de  또는  {colors.primary} (#0075de)
    for key, val in re.findall(r"\{colors\.([\w-]+)\}`?\s*(?:—|-|\(|:)\s*(" + HEX + ")", text):
        colors.setdefault(key, val)
    for key, val in re.findall(r"\{rounded\.([\w-]+)\}`?\s*(?:—|-|\(|:)\s*(\d+px)", text):
        rounded.setdefault(key, val)
    return colors, rounded


def build_root(colors: dict[str, str], rounded: dict[str, str]) -> tuple[str, list[str]]:
    """:root 블록과 기본값을 쓴 토큰 목록을 돌려준다."""
    lines, defaulted = [], []
    for token, keys, default in TOKEN_MAP:
        val = next((colors[k] for k in keys if k in colors), None)
        if val is None and default is None:
            val = "var(--accent)"  # 보조 강조색이 없는 DESIGN은 강조색 하나로 간다
        elif val is None:
            val = default
            defaulted.append(token)
        lines.append(f"        {token}: {val};")
    radius = next((rounded[k] for k in RADIUS_KEYS if k in rounded), "20px")
    lines += [
        f"        --radius-card: {radius};",
        "        --pad-x: 140px;",
        '        --font-body: "Paperlogy", sans-serif;',
        '        --font-mono: "JetBrains Mono", monospace;',
    ]
    extra = sorted(k for k in colors if not any(k in keys for _, keys, _ in TOKEN_MAP))
    for k in extra:  # 표에 없는 색은 장식 전용으로 옮긴다
        lines.append(f"        --c-{k}: {colors[k]};")
    return "      :root {\n" + "\n".join(lines) + "\n      }", defaulted


def indent(css: str, pad: str = "      ") -> str:
    return "\n".join((pad + line) if line.strip() else "" for line in css.strip("\n").splitlines())


def main() -> int:
    parser = argparse.ArgumentParser(description="첫 overview.html 생성")
    parser.add_argument("topic", type=Path, help="topics/<slug>")
    parser.add_argument("--force", action="store_true", help="이미 있는 overview.html을 덮어쓴다")
    args = parser.parse_args()
    topic: Path = args.topic

    brief_path = topic / "BRIEF.md"
    if not brief_path.is_file():
        logger.error("BRIEF.md가 없다: %s — new_topic.py로 먼저 만든다", brief_path)
        return 1
    brief = read_front_matter(brief_path)
    if brief.get("status") != "confirmed":
        logger.error("게이트 A: BRIEF.md status가 '%s'다. 사용자 승인으로 confirmed가 되기 전에는 HTML을 만들지 않는다.",
                     brief.get("status", "(없음)"))
        return 3
    out = topic / "overview.html"
    if out.exists() and not args.force:
        logger.error("이미 있다: %s — 원본을 덮어쓰지 않는다(정말 새로 만들려면 --force)", out)
        return 1

    design = topic / "DESIGN.md"
    colors, rounded = design_colors(design.read_text(encoding="utf-8")) if design.is_file() else ({}, {})
    root_block, defaulted = build_root(colors, rounded)

    scene_styles = "\n".join([
        '      @import url("assets/fonts/fonts.css");',
        "",
        f"      /* ===== 토큰: DESIGN.md에서 옮김 (deck-design 2절 매핑) ===== */",
        root_block,
        "",
        indent((ASSETS / "scene-base.css").read_text(encoding="utf-8")),
        "",
        "      /* 덱 전체 디자인 수정은 _work/slide_ui/0N_*.css에 쓰고 apply_css_patch.py로 아래 구간에 적용한다(직접 쓰지 않는다) */",
        "      /* ===== PATCH START ===== */",
        "      /* ===== PATCH END ===== */",
    ])

    title = htmlmod.escape(brief.get("title") or topic.name)
    kicker = {"edu": "교육 자료", "reading": "리딩 자료", "general": "발표 자료"}.get(brief.get("type", ""), "")
    sub = htmlmod.escape(brief.get("purpose", ""))
    parts = ['<section class="scene title-scene" data-slide="1" data-skill="title" data-scene-id="S01">']
    if kicker:
        parts.append(f'  <div class="hero-kicker" data-editable="true">{kicker}</div>')
    parts.append(f'  <h1 class="hero-title" data-editable="true">{title}</h1>')
    if sub:
        parts.append(f'  <p class="hero-sub" data-editable="true">{sub}</p>')
    parts.append('  <aside class="speaker-note">(발표자 노트: 인사와 오늘의 목표)</aside>')
    parts.append("</section>")

    tpl = (ASSETS / "overview.template.html").read_text(encoding="utf-8")
    tpl = tpl.replace("{{TITLE}}", title).replace("{{SLUG}}", htmlmod.escape(topic.name, quote=True))
    tpl = replace_line_placeholder(tpl, "SCENE_STYLES", scene_styles)
    tpl = replace_line_placeholder(tpl, "SLIDES_HTML", "\n".join(parts))
    out.write_text(tpl, encoding="utf-8", newline="\n")

    logger.info("생성: %s (title 장면 1장)", out)
    logger.info("토큰: DESIGN에서 %d개 색을 읽음%s", len(colors), f", 기본값 사용 {defaulted}" if defaulted else "")
    logger.info("다음: 스토리보드 → 장면 빌드 → build_present.py → validate_topic.py → qa_check.mjs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
