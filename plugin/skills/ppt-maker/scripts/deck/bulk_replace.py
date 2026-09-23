"""낱말 치환 목록(JSON)으로 overview.html과 CSS 패치 파일의 표현을 한꺼번에 바꾼다.

장면별 문장 치환은 apply_table.py, "덱 전체에서 이 낱말을 저 낱말로"는 이 스크립트를 쓴다.
속성값(src·href)과 HTML 주석은 건드리지 않고, 글자 노드·alt·aria-label·title 속성·CSS 주석만 바꾼다.
잔존 검사 범위(본문 + alt/aria-label/title + 주석)를 한 번에 맞추기 위함이다.

목록 형식 (JSON 배열):
  [{"old": "옛 낱말", "new": "새 낱말", "regex": false, "note": "왜 바꾸나"}]

사용:
    python bulk_replace.py topics/<slug> _work/bulk_map.json --dry
    python bulk_replace.py topics/<slug> _work/bulk_map.json --css topics/<slug>/_work/slide_ui/*.css

종료 코드: 0 성공 / 1 목록 오류
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import get_logger, resolve_overview  # noqa: E402  # pyright: ignore[reportMissingImports]

log = get_logger("bulk_replace")

TEXT_ATTRS = ("alt", "aria-label", "title")


def compile_rules(items: list[dict]) -> list[tuple[re.Pattern[str], str, str]]:
    """목록을 (정규식, 새 값, 표시 이름)으로 바꾼다."""
    rules = []
    for it in items:
        pat = it["old"] if it.get("regex") else re.escape(it["old"])
        rules.append((re.compile(pat), it["new"], it["old"]))
    return rules


def sub_all(text: str, rules, counts: dict[str, int]) -> str:
    """규칙을 차례로 적용하고 규칙별 횟수를 센다."""
    for rx, new, name in rules:
        text, n = rx.subn(new, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text


def replace_html(doc: str, rules, counts: dict[str, int]) -> str:
    """글자 노드와 alt·aria-label·title 속성만 바꾼다. <style>·<script>·주석·다른 속성은 그대로."""
    out: list[str] = []
    pos = 0
    protected = re.compile(r"<!--.*?-->|<(style|script)\b[^>]*>.*?</\1>|<[^>]+>", re.S)
    for m in protected.finditer(doc):
        out.append(sub_all(doc[pos:m.start()], rules, counts))          # 태그 사이 글자
        token = m.group(0)
        if token.startswith("<") and not token.startswith("<!--") and m.group(1) is None:
            # 여는 태그의 글자 속성만
            token = re.sub(
                r'(\s(?:' + "|".join(TEXT_ATTRS) + r')=")([^"]*)(")',
                lambda a: a.group(1) + sub_all(a.group(2), rules, counts) + a.group(3),
                token,
            )
        out.append(token)
        pos = m.end()
    out.append(sub_all(doc[pos:], rules, counts))
    return "".join(out)


def main() -> int:
    """목록을 읽어 overview.html과 CSS 파일에 적용한다."""
    parser = argparse.ArgumentParser(description="낱말 일괄 치환")
    parser.add_argument("target", type=Path, help="topics/<slug> 또는 overview.html")
    parser.add_argument("mapping", type=Path, help="치환 목록 JSON")
    parser.add_argument("--css", type=Path, nargs="*", default=[], help="함께 바꿀 CSS 파일(주석 속 낱말 포함)")
    parser.add_argument("--dry", action="store_true", help="파일을 쓰지 않고 횟수만")
    args = parser.parse_args()

    try:
        rules = compile_rules(json.loads(args.mapping.read_text(encoding="utf-8")))
    except (ValueError, KeyError, re.error) as exc:
        log.error("목록 오류: %s", exc)
        return 1

    path = resolve_overview(args.target)
    counts: dict[str, int] = {}
    new_doc = replace_html(path.read_text(encoding="utf-8"), rules, counts)
    n_html = sum(counts.values())
    css_total = 0
    for css in args.css:
        c: dict[str, int] = {}
        new_css = sub_all(css.read_text(encoding="utf-8"), rules, c)
        css_total += sum(c.values())
        for k, v in c.items():
            counts[k] = counts.get(k, 0) + v
        if not args.dry and c:
            css.write_text(new_css, encoding="utf-8", newline="\n")
    if not args.dry:
        path.write_text(new_doc, encoding="utf-8", newline="\n")

    for name, n in counts.items():
        log.info("  %s → %d곳", name, n)
    log.info("overview %d곳 · CSS %d곳%s", n_html, css_total, " (dry)" if args.dry else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
