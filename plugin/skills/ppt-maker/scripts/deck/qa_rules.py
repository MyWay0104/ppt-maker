"""topic의 deck-rules.json으로 하우스 룰을 정적으로 검사한다.

qa_check.mjs(레이아웃·명암비·글자 하한)와 겹치지 않는 규칙만 본다: 말투·출처·시간 표기·사내 정보·시각 요소.

deck-rules.json 키:
  require_visual: true면 장면마다 visual_selectors 중 하나가 있어야 한다
  visual_selectors: [".stats", "img", …]  (없으면 기본 목록)
  forbidden_markup: {"이름": "정규식"}  — overview 장면 영역 전체에서 찾는다
  forbidden_patterns: [{"name", "where": "screen|note|source|quote_attrib", "pattern", "except_scenes": [장면 ID]}]
  except_patterns: ["정규식"]  — 이 정규식에 걸리는 부분은 모든 규칙에서 뺀다(오탐 제외 목록)
  max_note_sentences: 6  — 발표자 노트 문장 수 상한(없으면 검사 안 함). 노트는 대본이 아니라 말할 요점이다

사용:
    python qa_rules.py topics/<slug>                      # topics/<slug>/deck-rules.json 자동
    python qa_rules.py topics/<slug> --rules other.json

종료 코드: 0 위반 0 / 1 위반 있음
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import SLIDES_RE, attr, get_logger, plain_text, resolve_overview, scene_spans, split_note  # noqa: E402  # pyright: ignore[reportMissingImports]

logger = get_logger("qa_rules")

SOURCE_RE = re.compile(r'<p class="source"[^>]*>(.*?)</p>', re.S)
QUOTE_ATTRIB_RE = re.compile(r'<[^>]*class="[^"]*\bquote-attrib\b[^"]*"[^>]*>(.*?)</', re.S)
DEFAULT_VISUAL = ["img", ".stats", ".steps", ".compare-grid", ".flow", ".tags", ".split-image", ".image-frame", "svg"]


def visual_regex(selectors: list[str]) -> re.Pattern[str]:
    """'.cls' → class 속성 안 단어, 'tag' → 여는 태그로 바꿔 하나의 정규식으로."""
    parts = []
    for sel in selectors:
        if sel.startswith("."):
            parts.append(r'class="[^"]*\b' + re.escape(sel[1:]) + r'\b')
        else:
            parts.append(r"<" + re.escape(sel) + r"\b")
    return re.compile("|".join(parts) or r"(?!)")


def main() -> int:
    """규칙 위반을 모아 보고한다."""
    parser = argparse.ArgumentParser(description="덱 하우스 룰 검사")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("--rules", type=Path, default=None, help="규칙 JSON (기본: topic의 deck-rules.json)")
    args = parser.parse_args()

    path = resolve_overview(args.target)
    rules_path = args.rules or path.parent / "deck-rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8")) if rules_path.is_file() else {}
    doc = path.read_text(encoding="utf-8")
    spans = scene_spans(doc)
    logger.info("장면 %d개 · %s · 규칙 %s", len(spans), path, rules_path.name if rules_path.is_file() else "(없음)")

    excepts = [re.compile(p) for p in rules.get("except_patterns", [])]

    def scrub(text: str) -> str:
        """오탐 제외 패턴에 걸리는 부분을 지운다."""
        for rx in excepts:
            text = rx.sub(" ", text)
        return text

    visual_rx = visual_regex(rules.get("visual_selectors") or DEFAULT_VISUAL)
    violations: list[str] = []
    counts: dict[str, int] = {}
    for s, e, attrs in spans:
        sid = attr(attrs, "data-scene-id") or attr(attrs, "data-slide") or "?"
        head, note = split_note(doc[s:e])
        targets = {
            "screen": scrub(plain_text(head)),
            "note": scrub(plain_text(note)),
            "source": scrub(plain_text(" ".join(SOURCE_RE.findall(head)))),
        }
        quote_attribs = [scrub(plain_text(q)) for q in QUOTE_ATTRIB_RE.findall(head)]
        for rule in rules.get("forbidden_patterns", []):
            if sid in rule.get("except_scenes", []):
                continue
            where = rule.get("where", "screen")
            texts = quote_attribs if where == "quote_attrib" else [targets.get(where, "")]
            for text in texts:
                found = re.findall(rule["pattern"], text, re.M)
                if found:
                    first = found[0] if isinstance(found[0], str) else found[0][0]
                    counts[rule["name"]] = counts.get(rule["name"], 0) + len(found)
                    violations.append(f"{sid} · {rule['name']} {len(found)}건: {first[:40]}")
        max_note = rules.get("max_note_sentences")
        if max_note and targets["note"].strip():
            # 문장 끝(. ? !) 뒤 공백·끝을 문장 경계로 센다. 코드 속 점(a.b)은 뒤가 공백이 아니라 세지 않는다
            sentences = len(re.findall(r"[.?!](?=\s|$)", targets["note"].strip()))
            if sentences > max_note:
                counts["노트 문장 수"] = counts.get("노트 문장 수", 0) + 1
                violations.append(f"{sid} · 발표자 노트 {sentences}문장 > 상한 {max_note}문장")
        if rules.get("require_visual", False) and not visual_rx.search(head):
            violations.append(f"{sid} · 시각 요소(이미지·도식·표·코드)가 없다")

    slides = SLIDES_RE.search(doc)
    region = slides.group(1) if slides else doc
    for name, pattern in (rules.get("forbidden_markup") or {}).items():
        hits = len(re.findall(pattern, scrub(region)))
        if hits:
            counts[name] = hits
            violations.append(f"마크업 · {name} {hits}건")

    if counts:
        logger.info("위반 요약: %s", ", ".join(f"{k} {v}" for k, v in counts.items()))
    if violations:
        logger.info("위반 %d건", len(violations))
        for item in violations[:60]:
            logger.info("  %s", item)
        return 1
    logger.info("결과: 위반 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
