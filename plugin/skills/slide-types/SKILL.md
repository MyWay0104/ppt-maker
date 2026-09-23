---
name: slide-types
description: 발표자료 장면(슬라이드) 타입 11종 — title, title-bullets, title-image, title-tags, split, stat, steps, compare, evolution-flow, quote, kindergarten-notice — 의 HTML 구조·CSS 핵심·선택 기준. 장면을 새로 만들거나 형태를 바꿀 때 참조한다. "3번 장면을 compare로 바꿔줘", "이 슬라이드를 단계형으로", "숫자를 크게 강조하는 장면 추가", "비교표로 바꿔", "인용구 장면 넣어줘"처럼 장면 하나의 모양을 다루는 요청이면 ppt-maker 전체 흐름 없이도 이 스킬을 쓴다.
---

# slide-types — 장면 타입 11종

ppt-maker 덱의 장면 하나는 1920×1080 종이 한 장이다. 이 스킬은 "어떤 모양의 종이를 쓸지"와 "그 종이를 HTML로 어떻게 쓰는지"를 정한다. 타입별 상세는 `references/<타입>.md`에 있다. 필요한 타입 파일만 읽는다.

## 1. 장면 공통 규약

모든 장면은 overview.html의 `<!-- SLIDES START -->`와 `<!-- SLIDES END -->` 사이에 둔다.

```html
<section class="scene [타입 보조 클래스]" data-slide="N" data-skill="<타입>" data-scene-id="S07">
  <div class="eyebrow" data-editable="true">구간명 · 2/4</div>       <!-- 내용 장면에 필수(아래 표) -->
  <h2 class="scene-title" data-editable="true">토큰 (Token)</h2>  <!-- 용어 하나·짧은 명사구 -->
  <p class="thesis" data-editable="true">LLM은 글을 토큰 단위로 잘라 읽습니다</p> <!-- 한 줄 요지(문장) -->
  … 타입별 본문 (references/<타입>.md) …
  <p class="source" data-editable="true">출처: …</p>                <!-- 선택: 사실·수치·인용이 있으면 -->
  <aside class="speaker-note">발표 대본</aside>                      <!-- BRIEF speaker_notes: true면 필수 -->
  <div class="deck-footer" data-editable="true">덱 이름 · 소속</div> <!-- 선택: 표지·구간 표지는 생략 가능 -->
</section>
```

| 속성·요소 | 규칙 |
|---|---|
| `class="scene"` | 필수. 보조 클래스(`center`, `quote` 등)는 타입 문서를 따른다 |
| `data-slide` | 1부터 빈틈없는 연번. 장면을 넣거나 빼면 뒤 번호를 모두 다시 매긴다 |
| `data-skill` | 아래 11개 중 하나(`references/allowed-skills.json`). 임의 타입 금지 |
| `data-scene-id` | 기획 문서의 장면 ID(S01, LAB04 …). 순번이 바뀌어도 기획서와 대조하는 열쇠 |
| `data-editable="true"` | 사용자가 Edit로 고칠 글자 요소에 붙인다 |
| `.scene-title` | **용어 하나 또는 짧은 명사구**(12자 안팎, 괄호 부제 제외)로 쓴다. 예: `Python (파이썬)`, `LLM (Large Language Model)`, `RAG의 기본 구조`, `실습 01 · 인증 키 발급`. 비유·설명은 제목에 붙이지 않고 `.thesis`로 내린다(`Python = 말 잘 듣는 비서` → 제목 `Python (파이썬)` + thesis `말 잘 듣는 비서처럼 시킨 일을 그대로 합니다`). "LLM은 대규모 언어 모델입니다" 같은 **문장형 제목은 쓰지 않는다**(모든 타입 공통, 표지·구간 표지·quote 포함). 이유: 청중은 제목에서 "지금 무엇을 다루는지"를 한눈에 잡고, 설명은 그 아래에서 읽는다 |
| `.thesis` | 제목 바로 아래 한 줄. 스토리보드의 "한 줄 요지"(청중에게 남길 한 문장)를 여기에 쓴다. 문장형이며 존댓말 규칙을 따른다. 표지(`title` 타입)는 `.hero-sub`가 같은 역할 |
| `.eyebrow` | 구간 표시. 내용 장면에는 `구간명 · n/N`을 쓰고 목차 장면의 번호와 맞춘다(구간 표지가 있어도 쓴다). 구간 표지 장면은 `n/N`만 |
| 꼬리 순서 | `.source` → `.speaker-note` → `.deck-footer`. 순서를 바꾸지 않는다 |

상자(카드·패널) 안 정렬

- 상자 안 내용 묶음은 **세로 가운데**에 둔다(`.box-center` 또는 `display: flex; flex-direction: column; justify-content: center`). 같은 줄 카드끼리 높이가 같아 한쪽이 짧으면 아래가 비어 보이기 때문이다
- 한두 줄짜리 짧은 글은 **가로도 가운데**(`.box-center.text-center`). 목록(`-`·불릿·번호)은 가로 왼쪽 정렬을 유지하고 세로만 가운데
- 카드 머리(`.compare-heading` 등)가 있으면 머리는 위에 고정하고 그 아래 목록 영역(`flex: 1`)만 세로 가운데로 둔다. 카드끼리 머리 기준선이 맞아야 비교가 쉽다
- `qa_check`가 `상자 안 쏠림`(중간)으로 알린다

금지(검증기 `validate_topic.py`가 잡는다)

- 장면 안 인라인 `style="…"` → scene-styles에 클래스나 `[data-slide="N"] .x { … }`로 쓴다
- `<br>` 줄바꿈 → 문장 길이를 줄이거나 `max-width`·`text-wrap: balance`로 푼다
- 영상 프레임워크의 흔적: `clip` 클래스, 시작·길이·트랙 번호 타이밍 속성, 애니메이션 라이브러리, 외부 폰트 CDN
- 글자 크기 24px 미만(인포그래픽 상자 글자는 32px 미만) — `qa_check.mjs`가 높음으로 잡는다

이미지

- topic 폴더 기준 상대 경로(`assets/img/…`)만 쓴다. 외부 URL 금지(PDF·오프라인에서 깨진다)
- `alt`는 필수. 장식용이면 부모에 `aria-hidden="true"`
- `crossorigin` 속성을 붙이지 않는다(`file://`로 열면 이미지가 막힐 수 있다)
- 캡처·그림처럼 안에 글자가 있는 이미지는 원본의 0.5배 이상으로 보이게 틀을 정한다. 틀이 작으면 필요한 부분만 잘라 넣거나 틀을 키운다(`ppt-maker/references/images.md` 4절)

## 2. 타입 표와 선택 기준

| `data-skill` | 메시지의 모양 | 상세 |
|---|---|---|
| `title` | 제목 하나가 메시지의 전부(오프닝·구간 표지·클로징) | `references/title.md` |
| `title-bullets` | 요점을 순서 없이 글로 정리 | `references/title-bullets.md` |
| `title-image` | 대표 이미지·스크린샷 한 장이 중심 | `references/title-image.md` |
| `title-tags` | 키워드 묶음으로 압축 | `references/title-tags.md` |
| `split` | 시각 자료와 해설을 동시에 | `references/split.md` |
| `stat` | 숫자 자체가 메시지(1~3개) | `references/stat.md` |
| `steps` | 순서가 중요한 3~5단계 | `references/steps.md` |
| `compare` | 2~4개 항목을 대등하게 비교 | `references/compare.md` |
| `evolution-flow` | 이전 상태 → 이후 상태(방향 있는 변화) | `references/evolution-flow.md` |
| `quote` | 한 문장을 오래 남기기 | `references/quote.md` |
| `kindergarten-notice` | 유치원·어린이집 학부모 안내 톤 | `references/kindergarten-notice.md` |

헷갈리는 쌍

| 상황 | 고를 타입 |
|---|---|
| 제목 + 짧은 부제만 | `title` / 설명 항목이 하나라도 있으면 `title-bullets` |
| 순서 없는 나열 | `title-bullets` / 순서가 중요하면 `steps` |
| A → B 변화 | `evolution-flow` / A·B·C 대등 비교는 `compare` |
| 이미지 + 설명 | `split` / 이미지가 주인공이고 설명이 1~2줄이면 `title-image` |
| 숫자 4개 이상 | `stat` 대신 `compare`나 `title-bullets`로 나누거나 장면을 둘로 |

## 3. 장면 타입을 바꾸는 절차 ("3번을 compare로")

1. 대상 장면을 확인한다. 사용자가 Aim 셀렉터(`[data-slide="3"] > …`)를 주면 그 장면이다.
2. `references/compare.md`를 읽는다.
3. `<section>` 여는 태그의 `data-slide`·`data-scene-id`는 그대로 두고 `data-skill`만 바꾼다.
4. 본문만 새 타입 구조로 다시 쓴다. 기존 문구는 버리지 않고 **글자 그대로** 새 구조에 옮긴다. 한 항목을 둘로 쪼개거나 말을 바꿔 쓰지 않는다(바꿔 쓰면 사용자가 고른 문구가 사라진다). 새 타입이 열 제목처럼 원문에 없는 문구를 요구하면 그 자리만 새로 쓰고 보고한다. 옮길 자리가 없는 문구도 사용자에게 보고한다(지우면 보고 대상).
5. 꼬리(`.source`·`.speaker-note`·`.deck-footer`)는 그대로 둔다.
6. 새 타입에 필요한 CSS가 scene-styles에 없으면 추가한다. 다른 장면에 영향이 없도록 새 클래스 이름을 쓴다.
7. `validate_topic.py` → `build_present.py` → `qa_check.mjs --slides 3` → `export_pdf.mjs topics/<slug> --shots-only` 순서로 돌린다(스크립트는 `${CLAUDE_SKILL_DIR}/../ppt-maker/scripts/`).
8. **`_work/shots/slide-03.png`를 Read 도구로 직접 열어** 본다. 볼 것: 표지(불릿 점·선)와 본문 겹침, 한두 글자만 다음 줄로 떨어진 줄바꿈, 한 덩어리 말(`발표자 창`)이 두 줄로 갈린 줄바꿈, 위아래 빈 띠. 문제가 보이면 고치고 7~8을 다시 한다. 스크린샷을 열어 보기 전에는 완료로 보고하지 않는다. 이유: 타입을 바꾸면 새 CSS가 처음 화면에 찍히는데, qa_check 통과만 보고 끝냈다가 표지가 본문을 덮은 채 보고된 적이 있다(P7 평가).

## 4. 마크다운 초안에서 타입 감지 (스토리보드·문구 초안을 받을 때)

| 초안 모양 | 타입 |
|---|---|
| `# 제목` + 일반 문장만 | `title` |
| `- 불릿` | `title-bullets` |
| `![](img)`만 | `title-image` |
| `> 태그1, *강조*` | `title-tags` |
| `![](img)` + `- 불릿` | `split` |
| `$ 120만` 다음 줄 설명 | `stat` |
| `1.` `2.` 번호 목록 | `steps` |
| `|| 열 제목` + 불릿 | `compare` |
| `<< 이전` / `>> 이후` | `evolution-flow` |
| `"" 인용문` + `— 출처` | `quote` |

## 5. 새 타입을 추가할 때

1. `references/<새 타입>.md`를 이 문서들과 같은 절 구성(언제 쓰나 / HTML 구조 / CSS 핵심 / 작성 원칙)으로 쓴다.
2. `references/allowed-skills.json`의 `skills`에 이름을 넣는다.
3. 위 2절 표에 한 줄 추가한다.
