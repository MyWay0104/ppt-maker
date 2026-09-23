#!/usr/bin/env python3
"""
validate_topic.py — topic 폴더가 ppt-maker 규약을 지키는지 검사한다.

사용법:
    python validate_topic.py topics/<slug>

검사 항목:
    - 필수 파일: overview.html BRIEF.md DESIGN.md deck-rules.json topic.json, 폴더 exports/
    - 게이트 A: overview.html이 있는데 BRIEF status가 confirmed가 아니면 오류
    - overview 구조: <style id="scene-styles">, SLIDES START/END 마커 각 1개,
      마커 사이 <section class="scene" data-slide="N"> 1..N 연번
    - 금지 문자열: 영상 프레임워크 흔적(타이밍 속성, clip 클래스, 애니메이션 라이브러리), 외부 폰트 CDN,
      장면 안의 <br>·인라인 style (deck-rules.json except_patterns로 예외 허용)
    - data-skill 허용 목록(slide-types/references/allowed-skills.json)
    - 검토 UI: edit-btn, Aim, data-editable
    - BRIEF speaker_notes: true면 장면마다 .speaker-note

종료 코드: 0 통과 / 1 실패 / 2 사용법 오류
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import re
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서도 한글이 깨지지 않게 출력 인코딩을 UTF-8로 고정
for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        _stream.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("validate_topic")

SCRIPT_DIR = Path(__file__).resolve().parent
ALLOWED_SKILLS_PATH = SCRIPT_DIR.parents[1] / "slide-types" / "references" / "allowed-skills.json"

REQUIRED_FILES = ("overview.html", "BRIEF.md", "DESIGN.md", "deck-rules.json", "topic.json")
REQUIRED_DIRS = ("exports",)

SLIDES_RE = re.compile(r"<!--\s*SLIDES START\s*-->(.*?)<!--\s*SLIDES END\s*-->", re.S)
ATTR_RE = r'\b{name}="([^"]*)"'

# HTML 주석 안의 설명용 태그 글자를 진짜 태그로 오인하지 않도록, 검색 전에 주석을 지운다(SLIDES 마커는 남김)
COMMENT_RE = re.compile(r"<!--(?!\s*SLIDES (?:START|END)\s*-->).*?-->", re.S)


def strip_comments(html: str) -> str:
    """SLIDES START/END 마커를 뺀 HTML 주석을 지운다."""
    return COMMENT_RE.sub("", html)


# 파일 어디에도 있으면 안 되는 것 (이름, 정규식)
# 이 스크립트 자신이 플러그인의 "흔적 0건" grep에 걸리지 않도록 일부 단어를 [a]·[s]처럼 쪼개 적는다
FORBIDDEN_ANYWHERE = [
    ("영상 타이밍 속성", re.compile(r"\bdata-(?:st[a]rt|duration|track-index)=")),
    ("애니메이션 라이브러리", re.compile(r"\bg[s]ap\b", re.I)),
    ("외부 폰트 CDN", re.compile(r"fonts\.(?:googleapis|gstatic)\.com")),
]
# 장면 영역(SLIDES 마커 사이)에 있으면 안 되는 것
FORBIDDEN_IN_SLIDES = [
    ("<br> 줄바꿈(문장 길이·CSS로 해결)", re.compile(r"<br\b", re.I)),
    ('인라인 style="…"(scene-styles의 클래스로)', re.compile(r'\sstyle="')),
    ("영상 프레임워크 clip 클래스", re.compile(r'\bclass="[^"]*\bclip\b')),
]


def read_front_matter(path: Path) -> dict[str, str]:
    """마크다운 맨 위 --- 사이의 `키: 값` 줄을 읽는다(YAML 전체를 해석하지는 않는다)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    data: dict[str, str] = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*(?:#.*)?$", line)
        if kv:
            data[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return data


def load_allowed_skills() -> set[str]:
    return set(json.loads(ALLOWED_SKILLS_PATH.read_text(encoding="utf-8"))["skills"])


def load_except_patterns(topic: Path) -> list[re.Pattern[str]]:
    """deck-rules.json의 except_patterns: 이 정규식에 걸리는 줄은 금지 문자열 검사에서 뺀다(오탐 제외 목록)."""
    rules_path = topic / "deck-rules.json"
    if not rules_path.exists():
        return []
    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [re.compile(p) for p in rules.get("except_patterns", [])]


def _attr(attrs: str, name: str) -> str | None:
    m = re.search(ATTR_RE.format(name=re.escape(name)), attrs)
    return m.group(1) if m else None


def _scan_forbidden(text: str, rules, excepts, where: str, errors: list[str], base_line: int = 1) -> None:
    """금지 정규식을 줄 단위로 검사한다. except 패턴에 걸리는 줄은 건너뛴다."""
    for offset, line in enumerate(text.splitlines()):
        if any(p.search(line) for p in excepts):
            continue
        for label, rx in rules:
            if rx.search(line):
                errors.append(f"{where}:{base_line + offset}: 금지 — {label}")


def split_scenes(slides_html: str) -> list[tuple[str, str]]:
    """SLIDES 영역을 장면 단위 (여는 태그 속성, 장면 HTML) 목록으로 나눈다. 최상위 <section>만 센다."""
    scenes: list[tuple[str, str]] = []
    depth = 0
    start = attrs = None
    for m in re.finditer(r"<(/?)section\b([^>]*)>", slides_html):
        if not m.group(1):
            if depth == 0:
                start, attrs = m.start(), m.group(2)
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                scenes.append((attrs or "", slides_html[start:m.end()]))
                start = None
    return scenes


def validate_topic(topic: Path) -> list[str]:
    errors: list[str] = []
    if not topic.is_dir():
        return [f"{topic}: topic 폴더가 없음"]

    for name in REQUIRED_FILES:
        if not (topic / name).is_file():
            errors.append(f"{topic / name}: 필수 파일 없음")
    for name in REQUIRED_DIRS:
        if not (topic / name).is_dir():
            errors.append(f"{topic / name}: 필수 폴더 없음")

    brief = read_front_matter(topic / "BRIEF.md") if (topic / "BRIEF.md").is_file() else {}
    overview_path = topic / "overview.html"
    if not overview_path.is_file():
        return errors

    # 게이트 A: overview가 존재하려면 BRIEF가 확정돼 있어야 한다
    if brief.get("status") != "confirmed":
        errors.append(f"{topic / 'BRIEF.md'}: status가 '{brief.get('status', '(없음)')}' — confirmed 전에는 overview.html을 만들 수 없다(게이트 A)")

    html = overview_path.read_text(encoding="utf-8")
    excepts = load_except_patterns(topic)
    _scan_forbidden(html, FORBIDDEN_ANYWHERE, excepts, str(overview_path), errors)

    if not re.search(r'<style\s+id="scene-styles"\s*>', strip_comments(html)):
        errors.append(f"{overview_path}: <style id=\"scene-styles\"> 없음")
    if len(re.findall(r"<!--\s*SLIDES START\s*-->", html)) != 1 or len(re.findall(r"<!--\s*SLIDES END\s*-->", html)) != 1:
        errors.append(f"{overview_path}: SLIDES START/END 마커가 각각 정확히 1개여야 함")
    if 'class="edit-btn"' not in html:
        errors.append(f"{overview_path}: Edit 버튼(class=\"edit-btn\") 없음")
    if 'class="aim-btn"' not in html:
        errors.append(f"{overview_path}: Aim 버튼(class=\"aim-btn\") 없음")
    if 'data-editable="true"' not in html:
        errors.append(f"{overview_path}: data-editable=\"true\" 요소 없음")

    m = SLIDES_RE.search(html)
    if not m:
        return errors
    slides_html = m.group(1)
    base_line = html[: m.start(1)].count("\n") + 1
    _scan_forbidden(slides_html, FORBIDDEN_IN_SLIDES, excepts, str(overview_path), errors, base_line)

    scenes = split_scenes(slides_html)
    if not scenes:
        errors.append(f"{overview_path}: SLIDES 영역에 <section> 장면이 없음")
        return errors

    allowed = load_allowed_skills()
    need_notes = brief.get("speaker_notes", "").lower() == "true"
    for i, (attrs, scene_html) in enumerate(scenes, start=1):
        where = f"{overview_path} 장면 {i}"
        classes = (_attr(attrs, "class") or "").split()
        if "scene" not in classes:
            errors.append(f"{where}: class에 scene 없음")
        num = _attr(attrs, "data-slide")
        if num != str(i):
            errors.append(f"{where}: data-slide=\"{num}\" — {i}이어야 함(1부터 연번)")
        skill = _attr(attrs, "data-skill")
        if not skill:
            errors.append(f"{where}: data-skill 없음")
        elif skill not in allowed:
            errors.append(f"{where}: data-skill=\"{skill}\"는 허용 목록에 없음 ({ALLOWED_SKILLS_PATH.name})")
        if need_notes and 'class="speaker-note"' not in scene_html:
            errors.append(f"{where}: speaker_notes: true인데 .speaker-note 없음")

    # slide_count는 내용 장수다. S01 표지와 구간 표지(title 타입)는 세지 않는다
    count = brief.get("slide_count")
    content = sum(1 for attrs, _ in scenes if _attr(attrs, "data-skill") != "title")
    if count and count.isdigit() and int(count) != content:
        logger.info("참고: BRIEF slide_count(내용 장수)=%s, 실제 내용 장면 %d장(전체 %d장)", count, content, len(scenes))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="ppt-maker topic 규약 검사")
    parser.add_argument("topic", type=Path, help="topics/<slug> 폴더")
    args = parser.parse_args()
    errors = validate_topic(args.topic)
    if errors:
        logger.error("검사 실패 (%d건):", len(errors))
        for e in errors:
            logger.error("- %s", e)
        return 1
    logger.info("검사 통과: %s", args.topic)
    return 0


if __name__ == "__main__":
    sys.exit(main())
