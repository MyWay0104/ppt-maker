"""웹 이미지 후보를 내려받아 출처와 함께 기록하고, 사용자가 승인한 후보만 덱 자산으로 옮긴다.

이미지를 덱에 바로 넣지 않는다. 후보 폴더(_work/image_candidates/)에 모으고, 사용자가 AskUserQuestion에서
고른 것만 --promote로 assets/img/에 옮긴다(references/images.md 2절). 덱은 로컬 파일만 참조하므로 오프라인에서도 열린다.

사용:
    # 후보 받기(출처 페이지·이용 조건은 사람이 확인할 수 있게 함께 적는다)
    python fetch_image.py topics/<slug> --url https://upload.wikimedia.org/…/cover.jpg --name cover-1 \\
        --source-page https://commons.wikimedia.org/wiki/File:… --license "CC BY-SA 4.0" --note "책 표지(한국어판)"

    # 후보 목록 보기
    python fetch_image.py topics/<slug> --list

    # 승인된 후보를 assets/img/로 옮기고 assets/img/SOURCES.md에 출처 한 줄을 남긴다
    python fetch_image.py topics/<slug> --promote cover-1

종료 코드: 0 성공 / 1 받기 실패(이미지가 아님·너무 큼·HTTP 오류) / 2 사용법 오류
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import struct
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("fetch_image")

MAX_BYTES = 15 * 1024 * 1024
USER_AGENT = "ppt-maker/0.1 (slide image candidate fetch; offline deck builder)"
EXT_BY_TYPE = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}


def image_size(data: bytes) -> tuple[int, int] | None:
    """PNG·JPEG·GIF·WebP 머리에서 (가로, 세로)를 읽는다. 모르는 형식이면 None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return w, h
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = data[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def candidates_path(topic: Path) -> Path:
    return topic / "_work" / "image_candidates" / "candidates.json"


def load_candidates(topic: Path) -> list[dict]:
    p = candidates_path(topic)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_candidates(topic: Path, items: list[dict]) -> None:
    p = candidates_path(topic)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch(topic: Path, args: argparse.Namespace) -> int:
    """이미지를 받아 후보 폴더에 두고 candidates.json에 기록한다."""
    req = urllib.request.Request(args.url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            ctype = res.headers.get_content_type()
            data = res.read(MAX_BYTES + 1)
    except OSError as err:
        logger.error("받기 실패: %s (%s)", args.url, err)
        return 1
    if ctype not in EXT_BY_TYPE:
        logger.error("이미지가 아니다: content-type=%s — 이미지 파일 주소(원본 파일 링크)를 준다", ctype)
        return 1
    if len(data) > MAX_BYTES:
        logger.error("너무 크다(%d MB 초과). 더 작은 해상도 주소를 찾는다", MAX_BYTES // 1024 // 1024)
        return 1
    size = image_size(data)
    folder = candidates_path(topic).parent
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{args.name}{EXT_BY_TYPE[ctype]}"
    dest.write_bytes(data)
    items = [c for c in load_candidates(topic) if c["name"] != args.name]
    items.append({
        "name": args.name,
        "file": dest.name,
        "url": args.url,
        "source_page": args.source_page or "",
        "license": args.license or "확인 필요",
        "note": args.note or "",
        "width": size[0] if size else None,
        "height": size[1] if size else None,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "approved": False,
    })
    save_candidates(topic, items)
    logger.info("후보 저장: %s (%s, %s)", dest, f"{size[0]}×{size[1]}" if size else "크기 모름", args.license or "이용 조건 확인 필요")
    return 0


def list_candidates(topic: Path) -> int:
    items = load_candidates(topic)
    if not items:
        logger.info("후보 없음: %s", candidates_path(topic))
        return 0
    for c in items:
        logger.info("%s %s · %s×%s · %s · %s · 출처 %s", "✔" if c.get("approved") else "·", c["name"],
                    c.get("width"), c.get("height"), c.get("license"), c.get("note"), c.get("source_page") or c.get("url"))
    return 0


def promote(topic: Path, name: str) -> int:
    """승인된 후보를 assets/img/로 옮기고 SOURCES.md에 출처를 남긴다."""
    items = load_candidates(topic)
    item = next((c for c in items if c["name"] == name), None)
    if item is None:
        logger.error("후보가 없다: %s (--list로 이름 확인)", name)
        return 2
    src = candidates_path(topic).parent / item["file"]
    dst_dir = topic / "assets" / "img"
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst_dir / item["file"])
    item["approved"] = True
    save_candidates(topic, items)
    sources = dst_dir / "SOURCES.md"
    head = "" if sources.exists() else "# 이미지 출처\n\n| 파일 | 설명 | 출처 페이지 | 이용 조건 |\n|---|---|---|---|\n"
    with sources.open("a", encoding="utf-8") as f:
        f.write(head + f"| {item['file']} | {item['note']} | {item['source_page'] or item['url']} | {item['license']} |\n")
    logger.info("옮김: assets/img/%s — 장면에 <img src=\"assets/img/%s\" alt=\"…\">와 출처 줄을 넣는다", item["file"], item["file"])
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="웹 이미지 후보 받기·승인 후 자산으로 옮기기")
    parser.add_argument("topic", help="topics/<slug>")
    parser.add_argument("--url", help="이미지 파일 주소")
    parser.add_argument("--name", help="후보 이름(영문·숫자·-)")
    parser.add_argument("--source-page", help="이미지가 실린 페이지(사람이 이용 조건을 확인할 곳)")
    parser.add_argument("--license", help="이용 조건(예: CC BY-SA 4.0, 출판사 보도자료, 확인 필요)")
    parser.add_argument("--note", help="무엇의 이미지인지")
    parser.add_argument("--list", action="store_true", help="후보 목록")
    parser.add_argument("--promote", metavar="NAME", help="승인된 후보를 assets/img/로")
    args = parser.parse_args()

    topic = Path(args.topic)
    if not (topic / "BRIEF.md").exists():
        logger.error("topic 폴더가 아니다(BRIEF.md 없음): %s", topic)
        return 2
    if args.list:
        return list_candidates(topic)
    if args.promote:
        return promote(topic, args.promote)
    if not args.url or not args.name:
        logger.error("--url과 --name이 필요하다(또는 --list / --promote)")
        return 2
    return fetch(topic, args)


if __name__ == "__main__":
    sys.exit(main())
