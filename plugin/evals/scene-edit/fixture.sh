#!/bin/bash
# 빈 작업 폴더(cwd)에 샘플 덱을 깐다.
# $0은 이 파일의 경로다. 글꼴은 용량을 아끼려고 플러그인 원본에서 복사한다.
set -euo pipefail
case_dir="$(cd "$(dirname "$0")" && pwd)"
fonts_dir="$case_dir/../../skills/deck-design/assets/fonts"
cp -r "$case_dir/fixture/topics" .
mkdir -p topics/_sample/assets/fonts topics/_sample/assets/img topics/_sample/exports
cp "$fonts_dir"/* topics/_sample/assets/fonts/
