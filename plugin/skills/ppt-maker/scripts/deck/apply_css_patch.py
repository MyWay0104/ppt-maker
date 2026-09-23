"""CSS 레이어드 패치: `_work/slide_ui/0N_*.css` 파일들을 번호 순서로 이어 붙여
overview.html scene-styles 안의 PATCH START/END 구간을 통째로 바꾼다.

- 여러 번 돌려도 결과가 같다(구간 전체를 새로 만든다)
- PATCH 구간이 없으면 scene-styles 끝에 새로 만든다
- 구간을 손으로 고치지 않는다. 패치 파일을 고치고 이 스크립트를 다시 돌린다
- 패치 파일 이름 규칙: 두 자리 번호 + 밑줄 + 이름 (예: 01_spacing.css, 02_b3-figures.css)

사용:
    python apply_css_patch.py topics/<slug>                       # _work/slide_ui/*.css
    python apply_css_patch.py topics/<slug> --dir _work/slide_ui  # 폴더 지정(topic 기준)
    python apply_css_patch.py topics/<slug> --check               # 쓰지 않고 현재 구간과 같은지만(같으면 exit 0)
    python apply_css_patch.py topics/<slug> extra.css             # 번호 파일 뒤에 추가 파일
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import get_logger, resolve_overview  # noqa: E402  # pyright: ignore[reportMissingImports]

log = get_logger("apply_css_patch")

START = "/* ===== PATCH START ===== */"
END = "/* ===== PATCH END ===== */"
INDENT = "      "


def build_block(files: list[Path]) -> str:
    """패치 파일들을 이어 붙인 PATCH 구간 문자열(들여쓰기·마커 포함)."""
    parts = []
    for f in files:
        body = f.read_text(encoding="utf-8").strip("\n")
        parts.append(f"{INDENT}/* --- {f.name} --- */\n{body}")
    inner = "\n\n".join(parts)
    return f"{INDENT}{START}\n" + (inner + "\n" if inner else "") + f"{INDENT}{END}\n"


def current_block(doc: str) -> re.Match[str] | None:
    return re.search(r"[ \t]*" + re.escape(START) + r".*?" + re.escape(END) + r"[ \t]*\n", doc, re.S)


def main() -> int:
    """패치 구간을 만들거나 교체한다."""
    parser = argparse.ArgumentParser(description="CSS 레이어드 패치 적용")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("extra", type=Path, nargs="*", help="번호 파일 뒤에 붙일 추가 CSS")
    parser.add_argument("--dir", default="_work/slide_ui", help="패치 파일 폴더(topic 기준, 기본 _work/slide_ui)")
    parser.add_argument("--check", action="store_true", help="쓰지 않고 현재 구간과 같은지만 확인")
    args = parser.parse_args()

    path = resolve_overview(args.target)
    doc = path.read_text(encoding="utf-8")
    patch_dir = path.parent / args.dir
    files = sorted(p for p in patch_dir.glob("*.css") if re.match(r"^\d{2}_", p.name)) if patch_dir.is_dir() else []
    files += list(args.extra)
    block = build_block(files)
    log.info("패치 파일 %d개: %s", len(files), ", ".join(f.name for f in files) or "없음")

    m = current_block(doc)
    if args.check:
        same = bool(m) and m.group(0) == block
        log.info("현재 PATCH 구간과 %s", "같다" if same else "다르다")
        return 0 if same else 1

    if m:
        doc = doc[:m.start()] + block + doc[m.end():]
        log.info("기존 PATCH 구간을 교체했다")
    else:
        style = re.search(r'(<style\s+id="scene-styles"\s*>.*?)([ \t]*</style>)', doc, re.S)
        if style is None:
            raise SystemExit('<style id="scene-styles">를 찾지 못했다')
        doc = doc[: style.end(1)] + block + doc[style.start(2):]
        log.info("PATCH 구간을 새로 붙였다")
    path.write_text(doc, encoding="utf-8", newline="\n")
    log.info("패치 %d자 → %s", len(block), path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
