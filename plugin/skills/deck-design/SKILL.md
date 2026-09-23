---
name: deck-design
description: 발표자료(슬라이드 덱)의 색·글꼴·여백·배치 디자인 지식. DESIGN-*.md(getdesign.md 산출물)를 장면 CSS의 :root 토큰으로 옮기는 방법, 내장 팔레트 9종, 시각 스타일 8종, 한글 슬라이드 타이포그래피, 강조 표시 CSS 패턴, 오프라인 폰트(Paperlogy·JetBrains Mono)를 담는다. "색이 답답해", "글자가 작아 보여", "좀 더 세련되게", "디자인 톤 바꿔줘", "이 DESIGN 파일 적용해줘", "팔레트 골라줘"처럼 덱의 겉모습을 정하거나 고치는 요청이면 ppt-maker 전체 흐름 없이도 이 스킬을 쓴다.
---

# deck-design — 덱 디자인 지식

장면의 모양(타입)은 `slide-types` 스킬이, **겉모습(색·글꼴·여백)**은 이 스킬이 맡는다. 필요한 참고 문서만 읽는다.

| 필요한 것 | 읽을 파일 |
|---|---|
| 디자인 파일이 없을 때 기본 방향, 흔한 AI 디자인 버릇 | `references/house-style.md` |
| 분위기에 맞는 이름 붙은 스타일 8종 | `references/visual-styles.md` |
| 글꼴 고르기·크기·굵기·한글 조판 | `references/typography.md` |
| 형광펜·동그라미·밑줄 같은 강조 표시 CSS | `references/css-patterns.md` |
| 색 조합 9종 | `references/palettes/<이름>.md` |

## 1. 디자인 출처를 정하는 순서

1. topic의 `DESIGN.md`가 있으면 그것이 기준이다(BRIEF `design_source`에 기록돼 있다).
2. 없으면 사용자에게 묻는다. 조용히 아무 파일이나 고르지 않는다.
   - `design-inputs/`의 `DESIGN-*.md` 중 하나 고르기
   - getdesign.md로 참고 사이트의 디자인 파일을 새로 받기
   - 내장 팔레트 9종 중 하나 고르기(`references/palettes/`)
3. 고른 결과를 `DESIGN.md`로 topic에 복사하고 BRIEF `design_source`에 출처를 적는다.

## 2. DESIGN → `:root` 토큰 매핑

getdesign.md 형식의 DESIGN 파일은 색 이름이 거의 같다. front matter(`colors:` 아래 `키: "#hex"`)에 있거나, 본문에 `` `{colors.키}` — #hex `` 꼴로 적혀 있다. 두 곳을 모두 찾아 아래 표로 옮긴다.

| 장면 토큰 | DESIGN 키 (앞에 있는 것 우선) | 쓰임 |
|---|---|---|
| `--accent` | `primary` → `accent` → `brand` | 강조 1색(키커·핵심 숫자·불릿 점). overview UI 강조색도 이것을 따른다 |
| `--accent-2` | `secondary` → `accent-2` → `tertiary` (없으면 `--accent`) | 보조 강조(칩·번호·구간 표지 톤·도식의 두 번째 계열). 강조색 하나만 쓰면 덱이 단조로워진다(P7 사용자 피드백). 구조색(글자·바탕)으로는 쓰지 않는다 |
| `--bg` | `canvas-soft` → `canvas` → `background` | 장면 바탕 |
| `--surface` | `surface` → `card` | 카드·패널 |
| `--text` | `ink` → `text` → `foreground` | 본문 글자 |
| `--text-dim` | `ink-muted` → `ink-secondary` → `ink-soft` → `text-muted` | 부제·출처·꼬리말 |
| `--line` | `hairline` → `border` → `divider` | 구분선·카드 테두리 |
| `--radius-card` | `rounded.lg` → `rounded.card` | 카드 모서리 |

규칙

- 표에 없는 색(스티커색·보조 강조색 등)은 `--c-<키>` 이름으로 옮기되, **구조에는 쓰지 않고 장식에만** 쓴다.
- DESIGN이 웹 글꼴(예: 특정 회사 전용 서체)을 지정해도 파일이 없으면 쓰지 않는다. 한글 본문은 동봉한 `Paperlogy`, 코드는 `JetBrains Mono`로 둔다. 원래 서체의 느낌은 굵기·자간으로 흉내 낸다.
- 옮긴 뒤 `--text`/`--bg`, `--text-dim`/`--bg`, `--accent`/`--bg` 명암비를 확인한다(본문 4.5:1, 24px 이상 큰 글자 3:1). 미달이면 명도를 조정하고 BRIEF 6절에 조정 사실을 적는다.
- 어두운 바탕(`--bg` 명도가 낮음)이면 `typography.md`의 "어두운 바탕" 보정을 적용한다.

`scaffold_overview.py`가 이 표대로 첫 `:root`를 만든다. 사람이 고칠 때도 이 표를 따른다.

## 3. 오프라인 폰트

- 원본: 이 스킬의 `assets/fonts/`(Paperlogy 400·500·600·700·800, JetBrains Mono 400, `fonts.css`)
- `new_topic.py`가 topic의 `assets/fonts/`로 복사하고, 장면 스타일 첫 줄이 `@import url("assets/fonts/fonts.css");`로 읽는다.
- `font-display: block` — 대체 글꼴로 먼저 그렸다가 바뀌면 줄바꿈이 튄다.
- 외부 CDN(`fonts.googleapis.com` 등)은 금지. `validate_topic.py`와 `export_pdf.mjs`가 잡는다.
- 새 글꼴이 꼭 필요하면 woff2 파일을 topic `assets/fonts/`에 넣고 `fonts.css`에 `@font-face`를 추가한다. 배포 가능한 라이선스(OFL 등)인지 먼저 확인한다.

## 4. 슬라이드 디자인 기본값

| 항목 | 기본 |
|---|---|
| 캔버스 | 1920×1080, 좌우 여백 120~160px(`--pad-x`) |
| 글자 하한 | 본문 24px, 인포그래픽 상자 글자 32px(`deck-rules.json`) |
| 제목 | 72~120px, weight 800, letter-spacing 음수 |
| 본문 | 36~44px, weight 500~600, line-height 1.4~1.5 |
| 강조색 | 한 장면에 한두 곳 |
| 여유 공간 | 남는 여유는 **간격**에 쓰고 글자를 키우지 않는다 |

색이 답답하다·세련되게 같은 요청은 먼저 `house-style.md`의 "되묻기 목록"으로 원인을 찾고, 한 번에 한 가지(바탕 명도, 강조색 채도, 여백)만 바꿔 스크린샷으로 비교한다.
