"""장면 ID ↔ 순번 매핑표를 overview.html에서 만든다(기획 문서 갱신용).

사용:
    python scene_map.py topics/<slug>
    python scene_map.py topics/<slug> -o topics/<slug>/_work/scene_map.md
"""
from __future__ import annotations

import argparse
import html as htmlmod
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import attr, get_logger, resolve_overview, scene_spans  # noqa: E402  # pyright: ignore[reportMissingImports]

logger = get_logger("scene_map")

TITLE_RE = re.compile(r'<h[12] class="[^"]*(?:scene-title|hero-title)[^"]*"[^>]*>(.*?)</h[12]>', re.S)
BLOCK_RE = re.compile(r"<!--\s*BLOCK:(\S+)\s+START\s*-->")


def main() -> int:
    """순번·data-slide·장면 ID·data-skill·BLOCK·제목 표를 만든다."""
    parser = argparse.ArgumentParser(description="장면 매핑표 생성")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("-o", "--out", type=Path, default=None, help="저장 경로(없으면 화면 출력)")
    args = parser.parse_args()

    doc = resolve_overview(args.target).read_text(encoding="utf-8")
    blocks = [(m.start(), m.group(1)) for m in BLOCK_RE.finditer(doc)]
    rows = ["| 순번 | data-slide | 장면 ID | data-skill | BLOCK | 제목 |", "|---:|---:|---|---|---|---|"]
    for number, (s, e, attrs) in enumerate(scene_spans(doc), 1):
        title_match = TITLE_RE.search(doc[s:e])
        title = htmlmod.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip() if title_match else "-"
        block = next((name for pos, name in reversed(blocks) if pos < s), "-")
        rows.append(f"| {number} | {attr(attrs, 'data-slide') or '-'} | {attr(attrs, 'data-scene-id') or '-'} | `{attr(attrs, 'data-skill') or '-'}` | {block} | {title} |")
    table = "\n".join(rows) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(table, encoding="utf-8", newline="\n")
        logger.info("%d행 → %s", len(rows) - 2, args.out)
    else:
        sys.stdout.write(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
