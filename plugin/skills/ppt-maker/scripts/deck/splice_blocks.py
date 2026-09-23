"""overview.html의 BLOCK 구간을 조각 파일로 바꾸거나 꺼낸다.

overview.html의 SLIDES 영역 안에 `<!-- BLOCK:B2 START -->` … `<!-- BLOCK:B2 END -->` 주석이 있는 topic에서 쓴다.
끼우기 전에 check_fragment.py를 통과시키고, 임시 사본에서 시험 조립을 먼저 한다(--out).
끼운 뒤에는 data-slide 연번을 다시 매긴다(--renumber, 기본 켬).

사용:
    python splice_blocks.py topics/<slug> _work/blocks B2 B3                 # 조각 → overview
    python splice_blocks.py topics/<slug> _work/blocks B2 --extract          # overview → 조각 파일
    python splice_blocks.py topics/<slug> _work/blocks B2 --out /tmp/try.html # 시험 조립(원본 그대로)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import get_logger, resolve_overview, scene_spans  # noqa: E402  # pyright: ignore[reportMissingImports]

logger = get_logger("splice_blocks")


def block_span(doc: str, name: str) -> tuple[int, int]:
    """BLOCK 주석 사이의 시작·끝 위치를 돌려준다."""
    start = re.search(rf"<!--\s*BLOCK:{re.escape(name)}\s+START\s*-->", doc)
    end = re.search(rf"<!--\s*BLOCK:{re.escape(name)}\s+END\s*-->", doc)
    if not start or not end or end.start() < start.end():
        raise SystemExit(f"BLOCK:{name} 주석을 찾지 못했다.")
    return start.end(), end.start()


def renumber(doc: str) -> tuple[str, int]:
    """장면 여는 태그의 data-slide를 1부터 다시 매긴다. 바뀐 개수를 돌려준다."""
    changed = 0
    for n, (s, _e, attrs) in reversed(list(enumerate(scene_spans(doc), 1))):
        tag_end = doc.index(">", s) + 1
        tag = doc[s:tag_end]
        if re.search(r'\bdata-slide="\d+"', tag):
            new_tag = re.sub(r'\bdata-slide="\d+"', f'data-slide="{n}"', tag, count=1)
        else:
            new_tag = tag[:-1] + f' data-slide="{n}">'
        if new_tag != tag:
            changed += 1
            doc = doc[:s] + new_tag + doc[tag_end:]
    return doc, changed


def main() -> int:
    """조각을 끼우거나(--extract면) 꺼낸다."""
    parser = argparse.ArgumentParser(description="BLOCK 조각 조립·추출")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("blocks_dir", type=Path, help="조각 파일 폴더")
    parser.add_argument("names", nargs="+", help="BLOCK 이름 (예: B2 B3 APP)")
    parser.add_argument("--extract", action="store_true", help="overview에서 조각을 꺼내 파일로 저장")
    parser.add_argument("--out", type=Path, default=None, help="결과를 다른 파일에 저장(시험 조립)")
    parser.add_argument("--no-renumber", action="store_true", help="data-slide 다시 매기기를 끈다")
    args = parser.parse_args()

    path = resolve_overview(args.target)
    doc = path.read_text(encoding="utf-8")
    args.blocks_dir.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        start, end = block_span(doc, name)
        target = args.blocks_dir / f"{name}.html"
        if args.extract:
            target.write_text(doc[start:end].strip("\n") + "\n", encoding="utf-8", newline="\n")
            logger.info("BLOCK:%s 추출 → %s (%d자)", name, target, end - start)
            continue
        fragment = target.read_text(encoding="utf-8").strip("\n")
        doc = doc[:start] + "\n" + fragment + "\n" + doc[end:]
        logger.info("BLOCK:%s 교체 (%d자)", name, len(fragment))
    if args.extract:
        return 0
    if not args.no_renumber:
        doc, changed = renumber(doc)
        logger.info("data-slide 다시 매김: %d곳", changed)
    out = args.out or path
    out.write_text(doc, encoding="utf-8", newline="\n")
    logger.info("저장: %s%s", out, " (시험 조립)" if args.out else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
