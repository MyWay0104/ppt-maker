"""치환 표를 집계하고, 원문(old)이 overview.html의 해당 장면에 정확히 한 번 나오는지 미리 센다.

apply_table.py --dry와 같은 판정을 하되, 표 파일별·장면별로 어디가 어긋나는지 함께 보여 준다.
치환 3중 게이트의 두 번째 단계: old 직접 추출 → **이 스크립트 어긋남 0** → apply_table --dry → 적용.

사용:
    python check_tables.py topics/<slug> _work/tables            # 폴더 안 *.jsonl 전부
    python check_tables.py topics/<slug> _work/tables --glob "P*.jsonl"

종료 코드: 0 어긋남 0 / 1 어긋남 있음
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_scene, get_logger, resolve_overview, split_note  # noqa: E402  # pyright: ignore[reportMissingImports]

log = get_logger("check_tables")


def main() -> int:
    """표를 읽어 항목 수와 원문 일치 여부를 집계한다."""
    parser = argparse.ArgumentParser(description="치환 표 사전 점검")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("table_dir", type=Path, help="치환 표 폴더(또는 JSONL 파일 하나)")
    parser.add_argument("--glob", default="*.jsonl", help="표 파일 패턴 (기본 *.jsonl)")
    args = parser.parse_args()

    doc = resolve_overview(args.target).read_text(encoding="utf-8")
    tables = [args.table_dir] if args.table_dir.is_file() else sorted(args.table_dir.glob(args.glob))
    total = {"replace": 0, "delete": 0, "title": 0, "miss": 0, "scene": 0}
    problems: list[str] = []

    for path in tables:
        n_rep = n_del = n_title = n_miss = n_scene = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            sid = item["sid"]
            n_scene += 1
            span = find_scene(doc, sid)
            if span is None:
                problems.append(f"{path.name} {sid}: 장면을 찾지 못함")
                n_miss += 1
                continue
            head, note = split_note(doc[span[0]:span[1]])

            if item.get("title"):
                n_title += 1
                # apply_table.py의 TITLE_RES와 같은 조건
                if not re.search(r'<h2 class="scene-title"[^>]*>', head) and not re.search(r'<h1 class="hero-title"[^>]*>', head):
                    problems.append(f"{path.name} {sid}: title을 넣을 요소가 없다")
                    n_miss += 1

            for i, rule in enumerate(item.get("replace") or []):
                n_rep += 1
                if rule.get("new") == "":
                    n_del += 1
                part = note if rule.get("where") == "note" else head
                count = part.count(rule["old"])
                if count != 1:
                    problems.append(f"{path.name} {sid} replace[{i}] {rule.get('where', 'screen')} {count}회: {rule['old'][:50]}")
                    n_miss += 1

        log.info("%-14s 장면 %2d · 치환 %3d(삭제 %2d) · title %d · 어긋남 %d", path.name, n_scene, n_rep, n_del, n_title, n_miss)
        total["replace"] += n_rep
        total["delete"] += n_del
        total["title"] += n_title
        total["miss"] += n_miss
        total["scene"] += n_scene

    log.info("합계: 표 %d개 · 장면 %d · 치환 %d(삭제 %d) · title %d · 어긋남 %d",
             len(tables), total["scene"], total["replace"], total["delete"], total["title"], total["miss"])
    if problems:
        log.info("어긋난 항목 (최대 40개)")
        for p in problems[:40]:
            log.info("  %s", p)
    return 1 if total["miss"] else 0


if __name__ == "__main__":
    sys.exit(main())
