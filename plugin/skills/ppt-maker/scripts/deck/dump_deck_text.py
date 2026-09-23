"""검토 서브에이전트용으로 장면마다 화면 글자·출처·발표자 노트를 마크다운으로 뽑는다.

화면 글자에는 alt·aria-label도 함께 적는다(잔존 검사 범위를 맞추기 위함).

사용:
    python dump_deck_text.py topics/<slug>                       # 표준 출력
    python dump_deck_text.py topics/<slug> -o topics/<slug>/_work/deck_text.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import attr, get_logger, plain_text, resolve_overview, scene_spans, split_note  # noqa: E402  # pyright: ignore[reportMissingImports]

logger = get_logger("dump_deck_text")


def main() -> int:
    """장면마다 순번·장면 ID·타입·화면·alt·노트를 적는다."""
    parser = argparse.ArgumentParser(description="덱 본문 추출")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("-o", "--out", type=Path, default=None, help="저장할 마크다운 경로(없으면 화면 출력)")
    args = parser.parse_args()

    path = resolve_overview(args.target)
    doc = path.read_text(encoding="utf-8")
    spans = scene_spans(doc)
    lines = [f"# {path.parent.name} — 화면 글자와 발표자 노트 ({len(spans)}장)", ""]
    for number, (s, e, attrs) in enumerate(spans, 1):
        scene = doc[s:e]
        head, note = split_note(scene)
        alts = re.findall(r'\s(?:alt|aria-label)="([^"]+)"', head)
        lines += [
            f"## {number}쪽 · {attr(attrs, 'data-scene-id') or '-'} · {attr(attrs, 'data-skill') or '-'}",
            "",
            f"- 화면: {plain_text(head)}",
        ]
        if alts:
            lines.append(f"- 대체 글자: {' / '.join(alts)}")
        lines += [f"- 노트: {plain_text(note)}", ""]
    text = "\n".join(lines)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8", newline="\n")
        logger.info("%d장 → %s", len(spans), args.out)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
