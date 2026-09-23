"""overview.html이 외부 CDN 자산(폰트 등)을 참조하면 topic 안 로컬 파일로 바꾼다.

ppt-maker 덱은 처음부터 오프라인 폰트(assets/fonts/fonts.css)를 쓰므로, 보통은 --check로 "외부 참조 0"만 확인한다.
옛 덱이나 손으로 붙인 CDN 링크를 정리할 때 쓴다.

- 폰트 CDN(Paperlogy·JetBrains Mono·Google Fonts) 링크 → `assets/fonts/fonts.css` 참조로 교체
- 폰트 파일이 topic에 없으면 스킬의 deck-design/assets/fonts/에서 복사
- preconnect 링크 삭제

사용:
    python localize_assets.py topics/<slug> --check    # 남은 외부 참조 수만 센다(0이면 exit 0)
    python localize_assets.py topics/<slug>            # 고친다
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import get_logger, resolve_overview  # noqa: E402  # pyright: ignore[reportMissingImports]

logger = get_logger("localize_assets")

FONTS_SRC = Path(__file__).resolve().parents[3] / "deck-design" / "assets" / "fonts"
FONT_CDN_RE = re.compile(
    r'\n?[ \t]*<link\b[^>]*href="https?://(?:fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.jsdelivr\.net/(?:gh/fonts-archive|npm/@fontsource))[^"]*"[^>]*>',
)
FONT_IMPORT_RE = re.compile(r'@import\s+url\(["\']?https?://[^)]*(?:fonts|fontsource)[^)]*\)\s*;?')
PRECONNECT_RE = re.compile(r'\n?[ \t]*<link rel="preconnect"[^>]*>')
EXTERNAL_RE = re.compile(r'(?:src|href)="(https?://[^"]+)"|url\(["\']?(https?://[^)"\']+)')


def external_refs(text: str) -> list[str]:
    """남은 외부 참조 URL 목록"""
    return [a or b for a, b in EXTERNAL_RE.findall(text)]


def ensure_fonts(topic: Path) -> list[str]:
    """topic assets/fonts/에 폰트가 없으면 복사한다."""
    dest = topic / "assets" / "fonts"
    copied = []
    dest.mkdir(parents=True, exist_ok=True)
    for f in FONTS_SRC.iterdir():
        if f.is_file() and not (dest / f.name).exists():
            shutil.copy2(f, dest / f.name)
            copied.append(f.name)
    return copied


def main() -> int:
    """overview.html을 고치고 남은 외부 참조 수에 따라 종료 코드를 돌려준다."""
    parser = argparse.ArgumentParser(description="CDN 자산 로컬화")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("--check", action="store_true", help="고치지 않고 남은 외부 참조만 센다")
    args = parser.parse_args()

    path = resolve_overview(args.target)
    text = path.read_text(encoding="utf-8")
    if args.check:
        left = external_refs(text)
        logger.info("외부 참조 %d건 %s", len(left), left[:5])
        return 1 if left else 0

    new_text = PRECONNECT_RE.sub("", FONT_CDN_RE.sub("", text))
    new_text = FONT_IMPORT_RE.sub('@import url("assets/fonts/fonts.css");', new_text)
    if 'assets/fonts/fonts.css' not in new_text:
        new_text = re.sub(r'(<style\s+id="scene-styles"\s*>\n?)', r'\1      @import url("assets/fonts/fonts.css");\n', new_text, count=1)
    copied = ensure_fonts(path.parent)
    path.write_text(new_text, encoding="utf-8", newline="\n")
    left = external_refs(new_text)
    logger.info("폰트 복사 %d개: %s", len(copied), ", ".join(copied) or "없음")
    logger.info("남은 외부 참조 %d건 %s", len(left), left[:5])
    logger.info("present.html은 build_present.py로 다시 만든다.")
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
