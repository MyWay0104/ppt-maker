"""BLOCK 조각 파일이 덱 규약을 지키는지 검사한다.

빌더 서브에이전트가 만든 `<section class="scene ...">` 조각을 overview.html에 끼우기 전에 확인한다.
검사: 장면 ID 순서, 허용 data-skill(slide-types/references/allowed-skills.json), 발표자 노트,
금지 마크업(인라인 style·br·hex·외부 이미지·영상 프레임워크 흔적), alt 없는 이미지,
scene-styles에 없는 클래스, data-editable 누락, 금지 문자열(deck-rules.json forbidden_strings).

사용:
    python check_fragment.py topics/<slug>/overview.html _work/blocks/B2.html --ids S09 S10 S11
    python check_fragment.py topics/<slug> _work/blocks/B2.html --ids S09,S10 --rules topics/<slug>/deck-rules.json

종료 코드: 0 통과 / 1 문제 있음
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import SCENE_STYLES_RE, attr, get_logger, resolve_overview, strip_comments  # noqa: E402  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]

logger = get_logger("check_fragment")

ALLOWED_SKILLS_PATH = Path(__file__).resolve().parents[3] / "slide-types" / "references" / "allowed-skills.json"
# span·div는 편집 대상 요소 안의 조각인 경우가 많아 data-editable 검사에서 뺀다
TEXT_LEAF_RE = re.compile(r"<(p|h1|h2|h3|li|td|th)\b([^>]*)>([^<>]*[가-힣A-Za-z0-9][^<>]*)</\1>")
# 이 스크립트 자신이 "흔적 0건" grep에 걸리지 않도록 단어를 [a]·[s]로 쪼갠다
FORBIDDEN = (
    (r"\sstyle=\"", "인라인 style 속성"),
    (r"<br\s*/?>", "<br> 태그"),
    (r'src="https?://', "외부 URL 이미지"),
    (r"#[0-9a-fA-F]{3,6}\b(?![^<]*</pre>)", "마크업 안 hex 색"),
    (r"\bdata-(?:st[a]rt|duration|track-index)=", "영상 타이밍 속성"),
    (r'\bclass="[^"]*\bclip\b', "영상 프레임워크 clip 클래스"),
    (r"\bg[s]ap\b", "애니메이션 라이브러리"),
    (r"\scrossorigin\b", "crossorigin 속성(file://에서 이미지 로딩 실패)"),
)


def top_sections(fragment: str) -> list[str]:
    """조각 안 최상위 <section>들을 깊이 계산으로 자른다."""
    out, depth, start = [], 0, 0
    for t in re.finditer(r"<(/?)section\b[^>]*>", fragment):
        if not t.group(1):
            if depth == 0:
                start = t.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                out.append(fragment[start:t.end()])
    return out


def defined_classes(doc: str) -> set[str]:
    """overview.html scene-styles에 정의된 클래스 이름을 모은다."""
    match = SCENE_STYLES_RE.search(strip_comments(doc))
    if not match:
        raise SystemExit('overview.html에 <style id="scene-styles">가 없다.')
    return set(re.findall(r"\.([a-zA-Z][\w-]*)", match.group(1)))


def check_scene(scene: str, css_classes: set[str], rules: dict, allowed_skills: set[str], problems: list[str]) -> None:
    """장면 하나를 검사해 문제를 problems에 담는다."""
    open_tag = scene[: scene.index(">") + 1]
    sid = attr(open_tag, "data-scene-id") or "?"
    skill = attr(open_tag, "data-skill")
    if skill not in allowed_skills:
        problems.append(f"{sid}: data-skill이 없거나 허용값이 아니다({skill or '없음'})")
    if rules.get("speaker_notes_required", True) and '<aside class="speaker-note">' not in scene:
        problems.append(f"{sid}: 발표자 노트(.speaker-note)가 없다")
    for pattern, message in FORBIDDEN:
        if re.search(pattern, scene, re.I if "g[s]ap" in pattern else 0):
            problems.append(f"{sid}: {message}")
    for img in re.findall(r"<img\b[^>]*>", scene):
        if 'alt="' not in img:
            problems.append(f"{sid}: alt 없는 이미지 {img[:60]}")
    allowed = css_classes | set(rules.get("allow_classes", []))
    for cls in sorted({c for a in re.findall(r'class="([^"]+)"', scene) for c in a.split()}):
        if cls not in allowed:
            problems.append(f"{sid}: CSS에 없는 클래스 .{cls}")
    # 코드 블록 안 글자는 pre 자체가 편집 대상이라 뺀다
    scene_no_code = re.sub(r"<pre[^>]*>.*?</pre>", " ", scene, flags=re.S)
    for tag, attrs, text in TEXT_LEAF_RE.findall(scene_no_code):
        if text.strip() and "data-editable" not in attrs and "aria-hidden" not in attrs:
            problems.append(f"{sid}: data-editable 없는 글자 <{tag}>{text.strip()[:20]}")
    for word in rules.get("forbidden_strings", []):
        if word in scene:
            problems.append(f"{sid}: 금지 문자열 {word!r}")


def main() -> int:
    """조각 파일을 검사하고 문제 여부를 종료 코드로 돌려준다."""
    parser = argparse.ArgumentParser(description="BLOCK 조각 검사")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("fragment", type=Path, help="검사할 조각 파일")
    parser.add_argument("--ids", nargs="*", default=None, help="기대하는 장면 ID 순서(공백 또는 쉼표로 구분)")
    parser.add_argument("--rules", type=Path, default=None, help="deck-rules.json")
    args = parser.parse_args()

    doc = resolve_overview(args.target).read_text(encoding="utf-8")
    fragment = args.fragment.read_text(encoding="utf-8")
    css_classes = defined_classes(doc)
    rules = json.loads(args.rules.read_text(encoding="utf-8")) if args.rules else {}
    allowed_skills = set(json.loads(ALLOWED_SKILLS_PATH.read_text(encoding="utf-8"))["skills"])

    scenes = top_sections(fragment)
    ids = [attr(s[: s.index(">") + 1], "data-scene-id") or "?" for s in scenes]
    logger.info("장면 %d개: %s", len(scenes), " ".join(ids))
    problems: list[str] = []
    expected = [x for part in (args.ids or []) for x in part.split(",") if x]
    if expected and ids != expected:
        problems.append(f"장면 ID 순서가 다르다. 기대 {expected} / 실제 {ids}")
    if not scenes:
        problems.append("조각에 <section> 장면이 없다")
    for scene in scenes:
        check_scene(scene, css_classes, rules, allowed_skills, problems)

    if problems:
        logger.info("결과: 문제 %d건", len(problems))
        for item in problems:
            logger.info("  %s", item)
        return 1
    logger.info("결과: 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
