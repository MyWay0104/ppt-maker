"""문구·배치 치환 표(JSON Lines)를 overview.html에 적용한다.

덱 전체를 한 번에 고칠 때 쓴다. 서브에이전트는 표만 만들고, 실제 수정은 이 스크립트가 한다.
`old`는 그 장면 안에서 정확히 한 번 나와야 하며, 하나라도 어긋나면 그 항목만 건너뛰고 보고한다.
3중 게이트: old는 파일에서 직접 추출 → check_tables.py 어긋남 0 → `--dry` 못 찾음 0 → 적용.

표 형식 (한 줄에 장면 하나, sid는 data-scene-id):
  문구(copy):  {"sid": "S09", "title": "새 제목", "source": "출처: …", "replace": [{"where": "screen|note", "old": "…", "new": "…"}]}
               title·source는 생략하거나 null이면 그대로, source가 ""이면 출처 줄 삭제
  배치(visual): {"sid": "S09", "old": "<div …>", "new": "<div …>"}   (노트 앞 화면 부분에서만 치환)

사용:
    python apply_table.py topics/<slug> copy_B1.jsonl --kind copy --dry
    python apply_table.py topics/<slug> visual_spec.jsonl --kind visual --css visual_spec.css

종료 코드: 0 모두 적용(또는 dry에서 못 찾음 0) / 1 못 찾은 항목 있음
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_scene, get_logger, resolve_overview, split_note  # noqa: E402  # pyright: ignore[reportMissingImports]

logger = get_logger("apply_table")

TITLE_RES = (
    re.compile(r'(<h2 class="scene-title"[^>]*>)(.*?)(</h2>)', re.S),
    re.compile(r'(<h1 class="hero-title"[^>]*>)(.*?)(</h1>)', re.S),
)
SOURCE_RE = re.compile(r'(<p class="source"[^>]*>)(.*?)(</p>)', re.S)
PATCH_START = "/* ===== PATCH START ===== */"


def apply_copy(scene: str, item: dict, misses: list[str]) -> str:
    """문구 표 한 줄을 장면에 적용한다."""
    sid = item["sid"]
    head, note = split_note(scene)
    for index, rule in enumerate(item.get("replace") or []):
        old, new, where = rule["old"], rule["new"], rule.get("where", "screen")
        part = note if where == "note" else head
        if part.count(old) != 1:
            misses.append(f"{sid} replace[{index}] {where} {part.count(old)}회: {old[:40]}")
            continue
        if where == "note":
            note = note.replace(old, new)
        else:
            head = head.replace(old, new)
    title = item.get("title")
    if title:
        for regex in TITLE_RES:
            if regex.search(head):
                head = regex.sub(lambda m: m.group(1) + title + m.group(3), head, count=1)
                break
        else:
            misses.append(f"{sid}: 제목 요소가 없다")
    source = item.get("source")
    if source is not None:
        if source == "":
            head, count = re.subn(r'\n[ \t]*<p class="source"[^>]*>.*?</p>', "", head, count=1, flags=re.S)
            if not count:
                misses.append(f"{sid}: 지울 출처 줄이 없다")
        elif SOURCE_RE.search(head):
            head = SOURCE_RE.sub(lambda m: m.group(1) + source + m.group(3), head, count=1)
        else:
            indent = re.search(r"\n([ \t]*)<aside", scene)
            pad = indent.group(1) if indent else "  "
            head = head.rstrip() + f'\n{pad}<p class="source" data-editable="true">{source}</p>\n{pad}'
    return head + note


def apply_visual(scene: str, item: dict, misses: list[str], topic_dir: Path) -> str:
    """배치 표 한 줄을 장면의 화면 부분에 적용한다."""
    sid, old, new = item["sid"], item["old"], item["new"]
    if re.search(r'\sstyle="|#[0-9a-fA-F]{3,6}\b|<br', new):
        misses.append(f"{sid}: new에 인라인 style·hex·<br>가 있다")
        return scene
    missing = [src for src in re.findall(r'src="([^"]+)"', new) if not (topic_dir / src).exists()]
    if missing:
        misses.append(f"{sid}: 없는 파일 {missing}")
        return scene
    head, note = split_note(scene)
    if head.count(old) != 1:
        misses.append(f"{sid}: old {head.count(old)}회")
        return scene
    return head.replace(old, new) + note


def append_css(doc: str, css: str) -> str:
    """scene-styles에 CSS 블록을 넣는다. PATCH 구간이 있으면 그 앞(패치가 마지막 층으로 남도록)."""
    start = doc.index('id="scene-styles"')
    end = doc.index("</style>", start)
    patch = doc.find(PATCH_START, start, end)
    anchor = patch if patch >= 0 else end
    line_start = doc.rfind("\n", 0, anchor) + 1
    body = "".join(f"      {line}\n" if line.strip() else "\n" for line in css.strip("\n").splitlines())
    return doc[:line_start] + body + doc[line_start:]


def main() -> int:
    """표를 읽어 적용하고 못 찾은 항목을 보고한다."""
    parser = argparse.ArgumentParser(description="치환 표 적용")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("tables", type=Path, nargs="+", help="치환 표 JSONL (여러 개면 순서대로)")
    parser.add_argument("--kind", choices=("copy", "visual"), default="copy")
    parser.add_argument("--css", type=Path, default=None, help="함께 넣을 CSS 파일(배치 표와 같이 쓴다)")
    parser.add_argument("--dry", action="store_true", help="파일을 쓰지 않고 확인만")
    args = parser.parse_args()

    path = resolve_overview(args.target)
    doc = path.read_text(encoding="utf-8")
    misses: list[str] = []
    applied = 0
    for table in args.tables:
        for line in table.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            span = find_scene(doc, item["sid"])
            if not span:
                misses.append(f"{item['sid']}: 장면이 없다")
                continue
            scene = doc[span[0]:span[1]]
            new_scene = apply_copy(scene, item, misses) if args.kind == "copy" else apply_visual(scene, item, misses, path.parent)
            doc = doc[:span[0]] + new_scene + doc[span[1]:]
            applied += 1
    if args.css and not args.dry:
        doc = append_css(doc, args.css.read_text(encoding="utf-8"))
    if not args.dry:
        path.write_text(doc, encoding="utf-8", newline="\n")
    logger.info("장면 %d개 처리, 못 찾음 %d건%s", applied, len(misses), " (dry)" if args.dry else "")
    for miss in misses:
        logger.info("  %s", miss)
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
