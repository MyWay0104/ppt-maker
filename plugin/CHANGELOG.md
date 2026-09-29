# 변경 기록

이 파일은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고, 버전은 [유의적 버전](https://semver.org/lang/ko/)을 따른다.

## [Unreleased]

모델이 바뀌어도(예: Claude 밖의 모델로 돌 때) 그림 장면이 깨지지 않도록 좌표 계산을 모델에서 브라우저로 옮겼다.

### 추가
- `diagram` 장면 타입과 좌표 없는 인포그래픽 부품 6종(`ig-flow`, `ig-cycle`, `ig-cycle has-hub`, `ig-layers`, `ig-timeline`, `ig-funnel`) — `assets/infographic.css`, `slide-types/references/diagram.md`. 새 덱은 `scaffold_overview.py`가 넣는다
- qa_check 7절 `글자 겹침`: 위치 방식과 무관하게(절대 배치 라벨·SVG 글자·SVG 위 HTML 글자) 실제 글자 사각형끼리 비교
- qa_check 8절 SVG 검사: `SVG 글자 잘림`·`SVG 그림 잘림`, `SVG 도형 밖 글자`(text-anchor 원인 안내), viewBox 배율을 곱한 실제 글자 크기, fill 기준 명암비, `SVG 그림 쏠림`(맞는 viewBox 값 제안)
- qa_check 9절 `그림 위치 쏠림`: 한 줄을 혼자 차지한 그림이 가운데가 아닐 때 `.fig-center` 안내
- SKILL.md 4절 17~19항: 좌표 금지, qa 메시지의 고치는 법 따르기, 비전 없음 모드(이미지를 못 보는 모델)의 눈 검수 처리
- qa_check 10절 `고아 줄바꿈`(마지막 줄 4글자 이하), 11절 `격자 간격 불균형`·`격자 높이 불균형` — 눈 검수 4항목 중 2개를 기계 검사로
- `deck-rules.json` `options.vision_review`(기본 true). false면 qa_check가 기계로 못 보는 항목을 `user_check`로 내고, 스킬·deck-reviewer는 스크린샷을 열지 않고 사용자 확인으로 넘긴다

### 변경
- qa_check 표지 겹침 검사가 요소 오른쪽 바깥의 장식(흐름 화살표)을 표지로 오인하지 않는다
- qa_check 4절 글자 하한·명암비가 SVG 글자를 CSS 크기·color로 잘못 재던 것을 8절로 옮겼다
- "PNG를 Read로 열어야 완료" 지시(edit-loop·slide-types·deck-reviewer·qa-gate·images·review-final)가 비전 없음 모드에서는 사용자 확인으로 바뀐다

## [1.0.0] - 2026-09-24

첫 배포 버전. 실제 사용(시운전·라이브 런)과 평가에서 나온 결함을 고쳤다.

### 추가
- 목차 장면·구간 표지(`.section-divider`)·내용 장면 `.eyebrow` 구간 n/N 표시, 명사형 짧은 제목 규칙
- intake 필수 질문: 스토리라인·꼭 넣을 내용. 장수 질문의 추천값은 내용 장수
- reading 덱 기본 흐름: 발제 앞에 책·저자·핵심 개념 소개와 이미지 자리표시
- 보조 강조색 `--accent-2` 자동 배정, 상자 안 세로 가운데 정렬 `.box-center`
- 이미지 후보 → 사용자 승인 → 넣기 흐름(`fetch_image.py`), 논문 그림 추출(`paper_figures.mjs`)
- qa_check 검사 항목: 표지 겹침, 세로 빈 띠, 상자 안 쏠림, 이미지 축소 과다
- 발표자 노트 문장 수 상한(`max_note_sentences`)
- `claude plugin eval` 케이스 `evals/scene-edit`(장면 수정 회귀 시험)
- 라이선스: 플러그인 MIT(`LICENSE`), 글꼴 SIL OFL 1.1 고지(`skills/deck-design/assets/fonts/OFL.txt`)

### 변경
- 게이트 A·C 승인 판정: 사람이 있는 세션인지는 AskUserQuestion 도구 가용성으로 본다. 스킬이 추천값 BRIEF를 스스로 `confirmed`로 바꾸거나 "PDF 뽑아줘"를 "최종 확인"으로 해석하지 않는다
- 청중 활동은 사용자가 요청할 때만 넣는다
- 장면 타입을 바꾼 뒤에는 스크린샷 PNG를 반드시 열어 눈 검수한다
- 장면 타입을 바꿀 때 기존 문구는 글자 그대로 옮긴다(항목을 쪼개거나 바꿔 쓰지 않는다)
- 검토 서버 안내에 브라우저에서 여는 방법을 적었다

### 고침
- qa_check 겹침 검사가 SVG 안의 의도된 도형·글자 겹침을 높음으로 보고하던 문제
- compare·evolution-flow 장면의 구분 기호가 본문과 겹치던 사양 결함(28px 자리에 32px 글자)
- color-mix 배경의 명암비를 잘못 계산하던 문제(`color(srgb …)` 해석)

## [0.1.0] - 2026-09-23

### 추가
- overview.html 템플릿, Aim/Edit 저장 서버(`serve_live.py`), topic 검증기(`validate_topic.py`), 샘플 덱
- 발표 런타임과 `present.html` 생성(`build_present.py`), PDF·PPTX 내보내기, QA 스크립트(`qa_check.mjs`)
- 스킬 3개(`ppt-maker`·`slide-types`·`deck-design`)와 서브에이전트 7개
- 덱 도구(`scripts/deck/`), topic 생성(`new_topic.py`), 옛 덱 이식 스크립트
