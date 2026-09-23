---
name: ppt-maker
description: 순수 HTML/CSS/JS로 16:9 발표자료(슬라이드 덱)를 처음부터 끝까지 만든다. 사용자가 발표자료, 슬라이드, PPT, 프레젠테이션, 덱, 교안, 강의 자료, 사내교육 자료, 세미나 자료, 독서모임 리딩자료·발제문, 발표 준비를 말하면 파일 형식을 말하지 않아도 이 스킬을 쓴다. "그냥 만들어줘"라고 해도 먼저 intake 질문으로 BRIEF.md를 확정하고, overview.html 목업 → Aim/Edit 검토 루프 → QA → 사용자 "최종 확인" 뒤에만 present.html과 PDF를 낸다. 기존 덱의 장면 수정·검수·PDF 내보내기 요청에도 쓴다.
---

# ppt-maker — 발표자료 제작 오케스트레이터

1920×1080 장면을 가진 발표자료를 순수 HTML로 만든다. **overview.html이 원본**이고, 발표용 `present.html`과 PDF는 거기서 생성한다. 장면 모양은 `slide-types` 스킬, 겉모습은 `deck-design` 스킬을 함께 쓴다.

## 0. 준비

- 작업 폴더(프로젝트 루트) 아래 `topics/<slug>/`가 덱 하나다. 없으면 `topics/`를 만든다.
- 스크립트는 모두 이 스킬 폴더에 있다: `python ${CLAUDE_SKILL_DIR}/scripts/<이름>.py`, `node ${CLAUDE_SKILL_DIR}/scripts/<이름>.mjs`
- Node 의존성(처음 한 번): `npm install --prefix ${CLAUDE_SKILL_DIR}/scripts` → `npx --prefix ${CLAUDE_SKILL_DIR}/scripts playwright install chromium`
- Python은 표준 라이브러리만 쓴다.
- intake를 시작하기 전에 `references/intake.md`를 읽는다. 사람이 있는 세션인지는 4절 1항의 기준(AskUserQuestion 도구 가용성)으로 판정한다. 사용자의 말투로 판정하지 않는다.

## 1. 원칙 5가지

1. **BRIEF 먼저.** 사용자가 "그냥 만들어줘"라고 해도 intake 질문 → BRIEF.md 확정 전에는 HTML을 한 줄도 쓰지 않는다. "알아서", "바로", "질문은 한 번만"은 질문 수를 줄이라는 뜻이지 질문을 생략하라는 뜻이 아니다. `status: confirmed`는 사용자가 AskUserQuestion에서 승인한 뒤에만 쓴다(도구 자체가 없는 무인 실행의 예외는 4절 1항).
2. **overview.html이 원본.** present.html·PDF는 생성물이다. 직접 고치지 않는다.
3. **추측 금지.** 줄거리를 바꾸는 사실·수치·이름은 지어내지 않는다. 선택지와 영향 장면을 붙여 묻는다.
4. **기계 검사와 눈 검수는 별개.** `qa_check` 통과는 검수 완료가 아니다. 스크린샷을 본다.
5. **지우는 것은 보고한다.** 문구·요소·장면을 뺐으면 무엇을 왜 뺐는지 사용자에게 알린다.

## 2. 흐름과 게이트

| # | 단계 | 산출물 | 담당 | 사용자 확인 |
|---|---|---|---|---|
| 0 | intake | `BRIEF.md` (`status: draft`) | 메인(질문 2라운드) + `intake-router`(초안) | **게이트 A** 승인 → `status: confirmed` |
| 1 | 스토리보드 | `_work/storyboard.md` | edu: `edu-designer` / 그 외: 메인 + `domain-expert` 검토 | 장수·흐름 OK? |
| 2 | 시각 계획 | `_work/visual_plan.md` | `slide-designer` | — |
| 3 | 문구 | `_work/copy/<B>.md`, `_work/review/<B>-pre.md` | `content-writer` → `domain-expert`(사실) + `deck-reviewer`(pre) | — |
| 4 | 빌드 | `overview.html` | ≤20장: 메인 직접 / >20장: BLOCK별 `slide-builder` | — |
| 5 | QA | `_work/qa_report.md`, `_work/shots/` | 스크립트 → `deck-reviewer`(post) | **게이트 B** 높음 0건이어야 검토 요청 |
| 6 | Aim/Edit 루프 | overview.html 갱신 | 사용자 Edit(서버 자동 저장) + Aim 요청(메인) | "최종 확인"까지 반복 |
| 7 | export | `present.html`, `exports/<slug>.pdf` | 스크립트 | **게이트 C** "최종 확인" → `export_approved: true` |

게이트는 스크립트가 강제한다. 단, 스크립트는 BRIEF의 값만 볼 뿐 **누가 그 값을 썼는지**는 모른다. 그래서 게이트 A·C의 승인 표시(`status: confirmed`, `export_approved: true`)는 아래 정의를 만족할 때만 스킬이 쓴다.

| 게이트 | 막는 스크립트 | 종료 코드 | 승인 표시를 쓰는 조건(정의의 원본) |
|---|---|---|---|
| A | `scaffold_overview.py`, `build_present.py`, `validate_topic.py` | 3 / 3 / 1 | 사용자가 BRIEF 요약을 보고 AskUserQuestion에서 "승인"을 골랐을 때. 스킬이 추천값으로 채운 BRIEF를 스스로 confirmed로 바꾸지 않는다(AskUserQuestion이 없는 무인 실행만 예외, 4절 1항) |
| B | `qa_check.mjs` | 1 | — (스크립트 결과 그대로) |
| C | `export_pdf.mjs`, `export_pptx.mjs` | 4 | 사용자 발화가 정확히 **"최종 확인"**일 때. "PDF 뽑아줘", "내보내줘", "발표 파일 만들어줘"는 export **요청**이지 최종 확인이 아니다. 이런 요청이 오면 AskUserQuestion으로 "지금 상태를 최종 확인으로 볼까요? (예 / 아니요, 더 검토)"를 묻고, 예일 때만 `export_approved: true`를 쓴다 |

승인 표시를 스킬이 대신 쓰면 게이트는 있으나 마나다. 이 표가 "최종 확인"의 정의이며, 다른 절과 참고 문서는 이 표를 가리킨다.

## 3. 단계별 절차

### 0) intake → `references/intake.md`

1. 기존 topic인지 확인한다(`topics/*/BRIEF.md`). 기존이면 BRIEF를 읽고 해당 단계로 간다.
2. AskUserQuestion 라운드 1(자료 유형·목적·청중·사용 상황) → 라운드 2(장수·톤·디자인 파일·구간 표지·발표자 노트·운영 규칙).
3. 자유 입력(**스토리라인·꼭 넣을 내용**·주제·핵심 메시지·참고자료·지킬 것·시간·사실 경계)을 받는다. 흐름을 받지 못했으면 추천 흐름을 BRIEF 승인 질문에 함께 보여 준다.
4. `python ${CLAUDE_SKILL_DIR}/scripts/new_topic.py --slug <slug> --title "<제목>" --type <edu|reading|general> (--design <DESIGN 파일> | --palette <이름>)`
   - 디자인을 안 정했으면 exit 2와 목록이 나온다. 사용자에게 고르게 한다.
5. `intake-router`에게 참고자료를 읽혀 BRIEF 초안(7절)을 채운다. 7절 "미확정 질문"이 빌 때까지 묻는다.
6. BRIEF 요약(유형·청중·목적·장수·디자인·운영 규칙·미확정 항목)을 보여 주고 AskUserQuestion으로 "승인 / 수정할 것 있음"을 받는다. 승인일 때만 `status: confirmed`로 바꾼다(2절 게이트 A 정의). 사용자가 "질문 한 번만"이라고 했다면 라운드 1·2를 한 번의 AskUserQuestion(최대 4문항)으로 합치고, 이 승인 질문은 그대로 둔다.

### 1) 스토리보드 → `references/storyboard.md`

- `assets/storyboard.md` 형식으로 장면 표(번호·장면 ID·타입·구간·제목(명사형)·한 줄 요지·시각 요소·노트 요점)를 만든다. S01 표지 다음 S02는 목차, 목차 구간마다 구간 표지(장수와 무관), 요청 장수는 표지를 뺀 내용 장수(`references/storyboard.md` 2절).
- 장수·흐름을 사용자에게 확인받는다. 장수가 바뀌면 BRIEF `slide_count`도 같은 단계에서 고친다.

### 2) 시각 계획

- `slide-designer`가 DESIGN.md → `:root` 토큰(`deck-design` 2절 매핑), 장면별 `data-skill`·배치·글자 크기를 `_work/visual_plan.md`에 적는다.

### 3) 문구

- `content-writer`가 장면별 화면 문구·노트·출처를 `_work/copy/<B>.md`에 쓴다(BRIEF 4절 사실 경계, `deck-rules.json` 준수). 8장짜리 덱이어도 B1 하나로 똑같이 한다.
- `domain-expert`(사실 검증)와 `deck-reviewer`(pre) 검토 → 필수 수정 반영.
- **이 단계는 장수와 관계없이 생략하지 않는다.** 메인이 스토리보드의 한 줄 요지를 그대로 화면 문구로 옮겨 빌드로 넘어가는 것은 금지다. 이유: 내용 오류는 발표에서 가장 비싼 결함이라, 화면에 찍히기 전에 두 검토(사실·문구)를 거친다.

### 4) 빌드 → `references/build-rules.md`

- `python ${CLAUDE_SKILL_DIR}/scripts/scaffold_overview.py topics/<slug>` — BRIEF confirmed가 아니면 exit 3.
- ≤20장: 메인이 SLIDES 마커 사이에 장면을 직접 쓴다.
- >20장: 6~10장 BLOCK(`<!-- BLOCK:B1 START/END -->`)으로 나눈다. BLOCK마다 `slide-builder`가 조각 → `check_fragment.py` 통과 → `splice_blocks.py`로 끼운다. 동시 서브에이전트 ≤3, 진행표 `_work/progress.md`.
- 이미지 자리표시가 있으면 빌드 뒤 `references/images.md` 2·3절로 후보를 찾아 사용자 승인을 받는다(무인 실행은 후보 목록만). 승인 없이 이미지를 넣지 않는다.
- 덱 전체 가로 수정(말투 통일·표기 변경)은 장면을 다시 만들지 않고 치환 표: `check_tables.py` → `apply_table.py --dry`(못 찾음 0) → 적용.

### 5) QA → `references/qa-gate.md`

순서대로 모두 돌린다.

```bash
python ${CLAUDE_SKILL_DIR}/scripts/build_present.py topics/<slug>          # 파생 파일 재생성이 첫 단계
python ${CLAUDE_SKILL_DIR}/scripts/validate_topic.py topics/<slug>
node   ${CLAUDE_SKILL_DIR}/scripts/qa_check.mjs topics/<slug>              # 높음 있으면 exit 1
python ${CLAUDE_SKILL_DIR}/scripts/deck/qa_rules.py topics/<slug>          # deck-rules.json 하우스 룰
node   ${CLAUDE_SKILL_DIR}/scripts/export_pdf.mjs topics/<slug> --shots-only
# → deck-reviewer(post)가 _work/shots/와 dump_deck_text 결과로 눈 검수
python ${CLAUDE_SKILL_DIR}/scripts/build_present.py topics/<slug> --check  # 끝에 최신 확인
```

높음 0건이 되면 사용자에게 검토를 요청한다(게이트 B).

### 6) Aim/Edit 루프 → `references/edit-loop.md`

- `python ${CLAUDE_SKILL_DIR}/scripts/serve_live.py topics/<slug>` → `http://127.0.0.1:8765/topics/<slug>/overview.html`
- 사용자가 Edit로 고치면 서버가 overview.html에 바로 저장한다(실패하면 빨간 토스트 + 패치가 클립보드로 → 대화창에 붙여 넣는다).
- Aim 셀렉터와 함께 온 요청은 메인이 Edit 도구로 해당 장면(`data-slide="N"` 여는 태그를 앵커로)만 고친다. 고친 뒤 QA 5단계를 다시 돌고, **고친 장면의 PNG를 Read로 열어 본 뒤에만** 완료를 보고한다(`references/edit-loop.md` 4절).

### 7) export

- "최종 확인"의 정의는 2절 게이트 표(C)를 따른다. 정의를 만족하면 BRIEF에 `export_approved: true`를 쓰고:
- `build_present.py` → `node ${CLAUDE_SKILL_DIR}/scripts/export_pdf.mjs topics/<slug>` → `exports/<slug>.pdf`
- PPTX가 요청되면 `node ${CLAUDE_SKILL_DIR}/scripts/export_pptx.mjs topics/<slug>`.
- 발표: 같은 서버에서 `present.html` 열기 → F 풀스크린, S 발표자 창.

## 4. 같은 실수를 막는 규칙

1. 줄거리를 바꾸는 사실은 추측하지 않는다. 선택지 + 영향 장면을 붙여 묻는다. **사람이 있는지는 AskUserQuestion 도구를 쓸 수 있는가로 판정한다.** 도구가 있으면 사람이 있는 세션이다. 이때는 "알아서 해줘"라는 말이 있어도 최소 1회(BRIEF 승인)는 반드시 묻는다. 도구가 없는 무인 실행(예: `claude -p`)일 때만 `_work/decisions.md`에 `[확인 필요]`로 남기고 되돌리기 쉬운 쪽으로 진행한다. 무인 실행에서는 BRIEF 승인을 받을 길이 없으므로, BRIEF 확정 근거에 "무인 실행(AskUserQuestion 없음)"을 적고 `status: confirmed`로 바꿔 빌드·QA까지 간다. 추천값으로 정한 항목은 모두 decisions.md에 `[확인 필요]`로 남겨 다음 사람 세션에서 한 번에 묻는다. `export_approved`는 무인 실행에서 쓰지 않는다 — "최종 확인"은 사람의 발화로만 성립하고, 덱 초안은 사람이 없어도 되돌릴 수 있지만 배포된 PDF는 되돌리기 어렵기 때문이다. 이유: 말투는 "질문을 줄여 달라"는 뜻일 뿐이고, 사람이 있는데 묻지 않으면 게이트 A·C가 스킬의 자기 승인으로 무력해진다(2026-09-23 시운전에서 실제로 두 번 일어남).
2. 기계 검사와 눈 검수는 별개 게이트. `qa_check`는 기본 전체 장면. 기계가 못 잡는 4가지(세로 무게 중심, 빈 여백 덩어리, 고아 줄바꿈, 격자 간격 불균형)는 스크린샷으로 본다.
3. 치환은 표 기반 3중 게이트: old는 대상 파일에서 직접 추출 → `check_tables.py` 어긋남 0 → `apply_table.py --dry` 못 찾음 0 → 적용.
4. 파생 파일(present.html) 재생성이 QA 첫 단계, 끝에 `--check`.
5. 잔존 검사는 본문 + alt·aria-label·title·라벨·HTML/CSS 주석·사양 .md까지. 금지어마다 오탐 제외 목록을 `deck-rules.json` `except_patterns`에 둔다.
6. "지우면 안 되는 목록"(아래 5절)과 압축 우선순위를 지킨다. 요소 삭제는 보고 대상.
7. 삭제 전 의존 관계를 본다(앞뒤 전문, 예고–회수 짝, 캡션–칩, 정의–되짚기). 활동 문장은 주체와 끝맺음이 있는지 본다.
8. 정의 문장은 한 곳만. 확인 못 한 사실은 문장에서 뺀다.
9. 레이아웃 수정은 수치를 계산한 뒤 반영하고 근거(또는 거절 이유)를 적는다. CSS는 "높이 증감 0"으로 설계한다.
10. 여유는 간격에 쓰고 글자를 키우지 않는다. 글자 하한(본문 24px, 인포그래픽 32px) 미만 금지.
11. 문서 속 개수(장수·항목 수)는 인용하지 말고 매번 센다. 장수가 바뀌면 검증 기준도 같은 단계에서 고친다.
12. 문구를 바꾸면 같은 자리의 아이콘·alt·aria-label을 한 묶음으로 본다.
13. 지표가 나빠지면 이전 버전과 대조해 원인부터 찾는다.
14. 조립은 임시 사본에 먼저 시험 조립한다. 문제가 없으면 "조치 불필요"로 닫고 억지 규칙을 만들지 않는다.
15. intake 라운드 2에서 운영 규칙(진행 방식 1인/상호작용, 시간 표기 범위, 용어 스타일)을 묻는다. 청중 활동(적어 보기·예측해 보기·미니 실습·과제·준비물·스스로 점검)은 사용자가 BRIEF에서 요청했을 때만 넣는다. 요청이 없으면 이해 확인은 강사가 질문을 던지고 스스로 답하는 노트 문장으로 한다.
16. 환경 파일(`.env*`)은 읽지 않는다. 비밀값·사내 주소·키를 화면·노트·커밋에 넣지 않는다.

## 5. 지우면 안 되는 것과 압축 순서

지우면 안 되는 것(명시 지시 없이는)

- 장면 제목, 발표자 노트, 출처 줄이 필요한 수치·인용의 출처
- 이미지 자리표시(캡처가 들어올 자리)
- BRIEF 5절 "지킬 것"에 적힌 요소
- 이해를 돕는 장치(정의 한 줄, 용어의 우리말 부제, 단계 번호)

장면이 넘칠 때 순서

1. **삭제**: 중복 문장, 장식 문구
2. **압축**: 문장 줄이기(같은 덱의 다른 장면 요지를 가져와 길이를 맞춘다. 새로 지어내지 않는다)
3. **CSS**: 장면 전용 간격·배치 조정(글자는 하한 이상 유지)
4. **재구성**: 타입 바꾸기 또는 장면 나누기(사용자 확인)

덱마다 빼는 순서가 정해져 있으면 `deck-rules.json`의 `overflow_drop_order`를 따른다.

## 6. 참고 문서

| 파일 | 내용 |
|---|---|
| `references/intake.md` | 질문 2라운드·자유 입력·BRIEF 필드·유형 프리셋 |
| `references/storyboard.md` | 스토리보드 표·장수 배분·BLOCK 나누기 |
| `references/build-rules.md` | 장면 마크업·CSS 레이어드 패치·하우스 룰·BLOCK 조립 |
| `references/edit-loop.md` | serve_live 사용법·패치 형식·Aim 요청 처리·실패 대응 |
| `references/qa-gate.md` | QA 순서·심각도·눈 검수 체크리스트·보고서 형식 |
| `references/images.md` | 이미지 자리표시, 웹 이미지 후보(승인 후 넣기), 논문 그림 잘라내기, 자리표시 → 이미지 교체 때 가독성 |
| `references/agents-usage.md` | 서브에이전트 7개 호출 방법·도메인 전문가 만들기 |
| `references/card-news-spec.md` | (범위 밖) 카드뉴스 스펙 보관 |
| `assets/` | BRIEF·스토리보드·DESIGN 최소판·deck-rules 프리셋·에이전트·지시문 템플릿 |

## 7. 완료 보고 전 확인

- `validate_topic.py` 통과, `qa_check` 높음 0, `build_present.py --check` 최신
- 눈 검수: 새로 만들었거나 고친 장면의 PNG를 Read로 열어 봤다(목록 확인·qa_check 통과로 갈음하지 않는다). 결과와 보류 항목을 `_work/qa_report.md`에 적었다
- 지운 요소·바꾼 결정을 보고했다
- "최종 확인" 전에는 export하지 않았다
- 끝에 `git status`를 보고한다(커밋·push는 사용자 규칙을 따른다)
