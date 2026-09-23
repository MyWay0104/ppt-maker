#!/usr/bin/env python3
"""
new_topic.py — 새 덱 폴더(topics/<slug>/)를 만든다. overview.html은 만들지 않는다(게이트 A).

사용법:
    python new_topic.py --slug python-basics-edu --title "Python 기초" --type edu --design design-inputs/DESIGN-Notion.md
    python new_topic.py --slug demian-reading --title "데미안 읽기" --type reading --palette warm-editorial --slides 12

만드는 것:
    topics/<slug>/BRIEF.md (status: draft) · DESIGN.md · deck-rules.json(유형 프리셋) · topic.json
    topics/<slug>/{docs, assets/img, assets/fonts(폰트 복사), exports, _work}/

디자인을 지정하지 않으면(--design·--palette 둘 다 없음) 아무것도 만들지 않고 목록을 보여 준 뒤 exit 2.
조용히 아무 파일이나 고르지 않는다.

종료 코드: 0 생성 / 1 이미 있음·입력 오류 / 2 디자인 미지정
"""
from __future__ import annotations

import argparse
import colorsys
import io
import json
import logging
import re
import shutil
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        _stream.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("new_topic")

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / "assets"
FONTS_SRC = SKILL_DIR.parent / "deck-design" / "assets" / "fonts"
PALETTES_DIR = SKILL_DIR.parent / "deck-design" / "references" / "palettes"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")
DEFAULT_SLIDES = {"edu": 24, "reading": 12, "general": 10}


def list_choices(root: Path) -> None:
    """고를 수 있는 디자인 파일과 팔레트를 보여 준다."""
    designs = sorted((root / "design-inputs").glob("DESIGN-*.md"))
    logger.error("디자인을 정하지 않았다. 아래 중 하나를 사용자에게 고르게 한 뒤 다시 실행한다.")
    logger.error("  --design <파일>   (design-inputs/)")
    for d in designs:
        logger.error("      %s", d.relative_to(root).as_posix())
    if not designs:
        logger.error("      (없음 — getdesign.md로 받아 design-inputs/에 넣을 수 있다)")
    logger.error("  --palette <이름>  (내장 팔레트)")
    for p in sorted(PALETTES_DIR.glob("*.md")):
        logger.error("      %s", p.stem)


def luminance(hex_color: str) -> float:
    """WCAG 상대 휘도"""
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def saturation(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)[2]


def hue(hex_color: str) -> float:
    """색상각(0~360도)"""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)[0] * 360


def hue_gap(a: str, b: str) -> float:
    """두 색의 색상각 차이(0~180도)"""
    d = abs(hue(a) - hue(b)) % 360
    return min(d, 360 - d)


def mix(a: str, b: str, t: float) -> str:
    """색 a에서 색 b 쪽으로 t(0~1)만큼 옮긴 색"""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def move_until(color: str, target: str, ok) -> str:
    """color를 target 쪽으로 5%씩 옮기다가 ok(색)가 참이 되는 첫 색을 돌려준다. 끝까지 안 되면 target."""
    for step in range(21):
        moved = mix(color, target, step / 20)
        if ok(moved):
            return moved
    return target


# 어두운 바탕으로 만드는 내장 팔레트(이름이 곧 의도다). 나머지는 밝은 바탕.
DARK_PALETTES = {"dark-premium"}
# 명암비 기준: 본문은 여유 있게 7:1, 보조 글자 4.5:1, 강조색(큰 글자·도형) 3:1
INK_MIN, MUTED_MIN, PRIMARY_MIN = 7.0, 4.5, 3.0
# 강조색이 본문 글자색과 구분돼 보이려면 둘 사이 대비도 이만큼은 있어야 한다
PRIMARY_APART = 1.8
# 보조 강조색은 강조색과 색상각이 이만큼 떨어져야 "다른 색"으로 보인다
SECONDARY_HUE_GAP = 30
# 첫 줄을 이 개수 이하의 명도 조정으로 쓸 수 있으면 다른 줄로 넘어가지 않는다
FIRST_ROW_MAX_ADJUST = 2


def assign_roles(row: list[str], dark: bool) -> tuple[dict[str, str], list[str]]:
    """팔레트 한 줄에 역할(바탕·글자·강조…)을 배정한다.

    기준에 못 미치는 색은 명도만 옮겨 맞추고, 옮긴 사실을 두 번째 반환값에 적는다.
    """
    row = [c.upper() for c in row]
    by_lum = sorted(row, key=luminance)
    # far: 바탕 쪽 끝색, near: 글자 쪽 끝색
    far, near = ("#000000", "#FFFFFF") if dark else ("#FFFFFF", "#000000")
    adjustments: list[str] = []

    # 바탕: 가장 밝은(어두운) 색. 끝색에 충분히 가깝지 않으면(진한 노랑 등) 중립 쪽으로 옮긴다
    base = by_lum[0] if dark else by_lum[-1]
    canvas = move_until(base, far, (lambda c: luminance(c) <= 0.02) if dark else (lambda c: luminance(c) >= 0.8))
    if canvas != base:
        adjustments.append(f"canvas {base} → {canvas} (바탕으로 쓰기에 {'밝아' if dark else '어두워'} 중립 쪽으로 옮김)")

    # 글자: 반대쪽 끝색. 대비가 모자라면 검정(흰색) 쪽으로 옮긴다
    ink_src = by_lum[-1] if dark else by_lum[0]
    ink = move_until(ink_src, near, lambda c: contrast(c, canvas) >= INK_MIN)
    if ink != ink_src:
        adjustments.append(f"ink {ink_src} → {ink} (대비 {INK_MIN:g}:1 맞춤)")

    # 강조: 남은 색 중 바탕 대비 3:1을 넘고 글자색과도 구분되는(1.8:1) 가장 채도 높은 색.
    # 없으면 채도 높은 색부터 명도를 조금씩(어두운 쪽·밝은 쪽 모두) 옮겨 두 조건을 맞춘다
    rest = sorted((c for c in row if c not in (base, ink_src)), key=saturation, reverse=True)

    def primary_ok(c: str) -> bool:
        return contrast(c, canvas) >= PRIMARY_MIN and contrast(c, ink) >= PRIMARY_APART

    passing = [c for c in rest if primary_ok(c)]
    if passing:
        primary = passing[0]
    else:
        src, primary = next(((c, moved) for c in rest for step in range(1, 21) for moved in
                             (mix(c, near, step / 20), mix(c, far, step / 20)) if primary_ok(moved)),
                            (rest[0], move_until(rest[0], near, lambda c: contrast(c, canvas) >= PRIMARY_MIN)))
        adjustments.append(f"primary {src} → {primary} (바탕 대비 {PRIMARY_MIN:g}:1·글자색과 구분 {PRIMARY_APART:g}:1 맞춤)")

    # 보조 강조: 강조색과 색상각이 30도 이상 떨어진 색 중 가장 채도 높은 색. 바탕 대비 3:1이 모자라면 명도만 옮긴다.
    # 그런 색이 없으면(단색조 팔레트) 강조색을 글자색 쪽으로 35% 옮겨 톤만 다르게 만든다. 칩·번호·구간 표지 장식에 쓴다
    rest = [c for c in rest if c != primary]
    far_hue = [c for c in rest if hue_gap(c, primary) >= SECONDARY_HUE_GAP and saturation(c) >= 0.2]
    if far_hue:
        src = far_hue[0]
        secondary = move_until(src, near, lambda c: contrast(c, canvas) >= PRIMARY_MIN)
        if secondary != src:
            adjustments.append(f"secondary {src} → {secondary} (바탕 대비 {PRIMARY_MIN:g}:1 맞춤)")
        rest = [c for c in rest if c != src]
    else:
        secondary = move_until(mix(primary, ink, 0.35), near, lambda c: contrast(c, canvas) >= PRIMARY_MIN)
        adjustments.append(f"secondary {secondary} (색상이 다른 색이 없어 강조색을 글자색 쪽으로 옮겨 만듦)")

    # 보조 글자: 남은 색 중 대비 4.5:1을 넘는 가장 차분한(채도 낮은) 색. 없으면 글자색과 바탕 사이에서 만든다
    passing = sorted((c for c in rest if contrast(c, canvas) >= MUTED_MIN), key=saturation)
    if passing:
        muted = passing[0]
    else:
        muted = next((c for c in (mix(ink, canvas, t / 20) for t in range(12, -1, -1))
                      if contrast(c, canvas) >= MUTED_MIN), ink)
        adjustments.append(f"ink-muted {muted} (팔레트에 대비 {MUTED_MIN:g}:1 색이 없어 ink와 canvas 사이에서 만듦)")

    # 구분선: 바탕과 살짝만 다른 팔레트 색(대비 1.1~2:1). 없으면 바탕에 글자색을 15% 섞는다(장식이라 조정으로 치지 않음)
    rest = [c for c in rest if c != muted]
    subtle = [c for c in rest if 1.1 <= contrast(c, canvas) <= 2.0]
    hairline = min(subtle, key=lambda c: contrast(c, canvas)) if subtle else mix(canvas, ink, 0.15)

    surface = mix(canvas, ink, 0.08) if dark else "#FFFFFF"
    roles = {"primary": primary, "secondary": secondary, "canvas": canvas, "surface": surface,
             "ink": ink, "ink-muted": muted, "hairline": hairline}
    return roles, adjustments


def design_from_palette(name: str) -> str:
    """내장 팔레트로 DESIGN.md를 만든다.

    첫 줄이 팔레트를 대표하는 색이므로, 첫 줄을 명도 조정 FIRST_ROW_MAX_ADJUST개 이하로 쓸 수 있으면 첫 줄을 쓴다.
    그보다 많이 고쳐야 하면 조정이 가장 적은 줄(같으면 앞줄)을 쓴다.
    결과는 항상 명암비 기준(본문 7:1·보조 4.5:1·강조 3:1)을 넘는다.
    """
    path = PALETTES_DIR / f"{name}.md"
    if not path.is_file():
        raise SystemExit(f"팔레트가 없다: {name} (목록은 --palette 없이 실행)")
    rows = [re.findall(r"#[0-9A-Fa-f]{6}", line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if len(r) >= 4]
    if not rows:
        raise SystemExit(f"팔레트에서 색 묶음을 찾지 못했다: {path}")
    dark = name in DARK_PALETTES
    trials = [(assign_roles(r, dark), i) for i, r in enumerate(rows)]
    if len(trials[0][0][1]) <= FIRST_ROW_MAX_ADJUST:
        (roles, adjustments), index = trials[0]
    else:
        (roles, adjustments), index = min(trials, key=lambda x: (len(x[0][1]), x[1]))

    canvas = roles["canvas"]
    checks = [f"- {label} {roles[label]} / canvas = {contrast(roles[label], canvas):.2f}:1"
              for label in ("ink", "ink-muted", "primary", "secondary")]
    colors = "".join(f'  {key}: "{value}"\n' for key, value in roles.items())
    return (
        "---\n"
        f"name: 팔레트 {name}\n"
        f"description: 내장 팔레트 {name}의 {index + 1}번째 줄에서 new_topic.py가 자동으로 만든 디자인.\n"
        f"colors:\n{colors}"
        "typography:\n  body: Paperlogy\n  mono: JetBrains Mono\n"
        "rounded:\n  lg: 20px\n"
        "---\n\n"
        f"# DESIGN — 팔레트 {name}\n\n"
        f"원본 팔레트: `deck-design/references/palettes/{name}.md` {index + 1}번째 줄 {' '.join(rows[index])}\n\n"
        f"바탕: {'어두운 바탕(typography.md의 어두운 바탕 보정 적용)' if dark else '밝은 바탕'}\n\n"
        "명암비:\n" + "\n".join(checks) + "\n\n"
        "명도 조정:\n" + ("\n".join(f"- {a}" for a in adjustments) if adjustments else "- 없음(팔레트 색 그대로)") + "\n"
    )


def fill(template: str, values: dict[str, str]) -> str:
    for key, val in values.items():
        template = template.replace("{{" + key + "}}", val)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description="새 덱 topic 폴더 생성")
    parser.add_argument("--slug", required=True, help="폴더 이름(영문 소문자·숫자·-·_)")
    parser.add_argument("--title", required=True, help="덱 제목")
    parser.add_argument("--type", required=True, choices=("edu", "reading", "general"), help="자료 유형(프리셋)")
    parser.add_argument("--design", type=Path, help="DESIGN-*.md 경로")
    parser.add_argument("--palette", help="내장 팔레트 이름")
    parser.add_argument("--slides", type=int, default=None, help="목표 장수(기본: 유형별)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="프로젝트 루트(기본: 현재 폴더)")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not SLUG_RE.match(args.slug):
        logger.error("slug는 영문 소문자로 시작하고 소문자·숫자·-·_만 쓴다: %s", args.slug)
        return 1
    if not args.design and not args.palette:
        list_choices(root)
        return 2
    if args.design and args.palette:
        logger.error("--design과 --palette 중 하나만 준다.")
        return 1

    topic = root / "topics" / args.slug
    if topic.exists():
        logger.error("이미 있다: %s — 기존 topic이면 BRIEF.md를 읽고 이어서 작업한다.", topic)
        return 1

    if args.design:
        design_path = args.design if args.design.is_absolute() else (root / args.design)
        if not design_path.is_file():
            logger.error("DESIGN 파일이 없다: %s", design_path)
            return 1
        design_text = design_path.read_text(encoding="utf-8")
        design_source = design_path.relative_to(root).as_posix() if design_path.is_relative_to(root) else design_path.name
    else:
        design_text = design_from_palette(args.palette)
        design_source = f"palette:{args.palette}"

    rules = json.loads((ASSETS / f"deck-rules.{args.type}.json").read_text(encoding="utf-8"))
    slides = args.slides or DEFAULT_SLIDES[args.type]
    speaker_notes = "true" if rules.get("speaker_notes_required") else "false"

    for sub in ("docs", "assets/img", "assets/fonts", "exports", "_work"):
        (topic / sub).mkdir(parents=True, exist_ok=True)
    for f in FONTS_SRC.iterdir():
        if f.is_file():
            shutil.copy2(f, topic / "assets" / "fonts" / f.name)
    (topic / "exports" / ".gitkeep").touch()

    values = {"SLUG": args.slug, "TITLE": args.title, "TYPE": args.type, "SLIDE_COUNT": str(slides),
              "SPEAKER_NOTES": speaker_notes, "DESIGN_SOURCE": design_source}
    (topic / "BRIEF.md").write_text(fill((ASSETS / "BRIEF.md").read_text(encoding="utf-8"), values), encoding="utf-8", newline="\n")
    (topic / "DESIGN.md").write_text(design_text, encoding="utf-8", newline="\n")
    (topic / "deck-rules.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (topic / "topic.json").write_text(json.dumps({
        "slug": args.slug, "title": args.title, "type": args.type, "rules_preset": args.type,
        "design_source": design_source, "created": date.today().isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    logger.info("생성: %s", topic.relative_to(root).as_posix())
    logger.info("  BRIEF.md(status: draft) · DESIGN.md(%s) · deck-rules.json(%s) · topic.json · 폰트 %d개",
                design_source, args.type, len(list((topic / 'assets' / 'fonts').iterdir())))
    logger.info("다음: intake로 BRIEF를 채우고 사용자 승인 → status: confirmed → scaffold_overview.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
