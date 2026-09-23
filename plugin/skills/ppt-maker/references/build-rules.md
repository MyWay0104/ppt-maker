# build-rules — overview.html 빌드 규칙

## 1. overview.html 구조

```
<head>
  UI 크롬 스타일(템플릿 그대로, 고치지 않는다)
  <style id="scene-styles">          ← 장면 스타일. present.html로 복사된다
    @import url("assets/fonts/fonts.css");
    :root { --accent … }              ← DESIGN 토큰(deck-design 2절)
    .scene { … }                      ← 장면 기본
    타입별 컴포넌트 CSS
    /* ===== PATCH START ===== */     ← 레이어드 패치 구간(apply_css_patch.py 관리)
    /* ===== PATCH END ===== */
  </style>
<body>
  썸네일 스트립 + 큰 화면
  <!-- SLIDES START -->
  <section class="scene" data-slide="1" …> … </section>
  …
  <!-- SLIDES END -->
  Aim·Edit·저장 JS(템플릿 그대로)
```

- 처음 파일은 `scaffold_overview.py`가 `assets/overview.template.html`로 만든다(BRIEF confirmed 필요).
- 장면 마크업은 `slide-types` 스킬의 공통 규약을 따른다.
- scene-styles에는 `html`, `body` 크기를 고정하는 규칙을 넣지 않는다(overview는 body가 뷰포트 전체).
- scene-styles 안에서 `display`를 `.scene`에 주지 않는다(overview와 present가 각자 정한다).

## 2. 큰 파일 다루기

- 장면 하나를 고칠 때는 `data-slide="N"` 여는 태그를 앵커로 그 `<section>`만 Edit한다.
- 여러 장면을 같은 방식으로 고칠 때는 치환 표(`apply_table.py`)를 쓴다. 손으로 여러 번 Edit하지 않는다.
- 장면을 넣거나 빼면 뒤 장면의 `data-slide`를 모두 다시 매긴다. `data-scene-id`는 바꾸지 않는다.

## 3. CSS 레이어드 패치

- 덱 전체에 걸친 디자인 수정은 `_work/slide_ui/0N_<이름>.css` 파일로 쌓는다(번호 순서 = 적용 순서).
- `python ${CLAUDE_SKILL_DIR}/scripts/deck/apply_css_patch.py topics/<slug>`가 파일들을 이어 붙여 PATCH 구간을 통째로 바꾼다.
- PATCH 구간을 손으로 고치지 않는다. 패치 파일을 고치고 다시 적용한다.
- 이미 적용한 레이어(특히 이식으로 만든 `01_*_legacy.css`)는 기준선으로 두고 고치지 않는다. 새 수정은 기존 최대 번호 + 1 파일로 쌓는다. 되돌릴 때는 그 파일을 지우고 다시 적용한다.
- 뒤 레이어가 앞 레이어를 이기려면 셀렉터 명시도가 **같거나 높아야** 한다. 앞 레이어가 `.scene[data-scene-id="S23"] .x`로 정한 값은 뒤에서 `.x`만으로는 바뀌지 않는다. 덮어쓸 규칙을 `grep`으로 먼저 찾아 같은 셀렉터를 쓴다.
- CSS는 "높이 증감 0"으로 설계한다: 한 요소를 키우면 같은 장면의 간격을 그만큼 줄인다. 수치를 계산해 패치 파일 주석에 남긴다.

## 4. 하우스 룰 (모든 유형 공통)

- 화면 문장의 말투를 덱 전체에서 통일한다(edu 기본은 존댓말 `…합니다`). 명사형 라벨·칩·표 칸은 그대로
- 출처는 청중이 확인할 수 있는 공개 자료만(공식 문서·논문·책). 내부 문서·개인 기록은 출처 줄에 쓰지 않는다
- 사내 주소·모델명·키·계정은 화면과 노트에 쓰지 않는다. 역할 이름으로(예: "사내 추론 서버")
- 근거 없는 수치·가짜 화면·가상의 성공 사례를 실제처럼 넣지 않는다. 자리표시로 두고 대기 목록에 적는다
- 이미지 자리표시(스토리보드 `[이미지 자리: 무엇]`)는 `<div class="image-frame placeholder" data-asset="책 표지"><span>책 표지 이미지</span></div>`로 만든다. 옅은 배경 + 점선 테두리 + 가운데 설명 글자(24px 이상), 비율은 실물에 맞춘다(책 표지 2:3, 인물 1:1 또는 3:4, 화면 캡처 16:9). 사용자가 파일을 주면 `assets/img/`에 두고 `<img>`로 바꾼다. 웹 이미지·논문 그림 후보 찾기와 교체 때 틀 크기 다시 정하기는 `references/images.md`. 남은 자리는 완료 보고의 "자산 대기" 목록에 적는다
- 장면 안 기획 ID(S12 등)·쪽번호·구간 코드를 화면 글자로 두지 않는다(꼬리말의 덱 이름은 괜찮다)
- 시간 표기는 BRIEF `time_display`를 따른다
- 청중 활동(적어 보기·예측해 보기·미니 실습·과제·준비물·스스로 점검)은 사용자가 BRIEF에서 요청했을 때만 넣는다. 요청이 없으면 이해 확인은 강사가 질문을 던지고 스스로 답하는 노트 문장으로 한다(P7 iteration-2 사용자 피드백).
- 1인 진행(`operation: solo`)이면 청중 반응을 요구하는 문장(짝 확인, 손들기, 지목 질문)을 쓰지 않는다. 질문은 던지되 강사가 스스로 답하며 넘어간다. 청중 활동은 적기·고르기·짚기로
- 용어 스타일이 "전문용어 + 우리말 부제"면 제목·본문은 전문용어, 바로 아래 한 줄이 평이한 우리말로 받는다
- 긴 이름은 정의하는 자리 한 곳에만, 나머지는 짧은 이름
- 배치: 한쪽으로 몰지 않고 균형 있게, 요소끼리 붙이지 않는다. 남는 여유는 간격에

## 5. BLOCK 조립 (20장 초과)

1. overview에 `<!-- BLOCK:B1 START -->` … `<!-- BLOCK:B1 END -->` 구간을 둔다(SLIDES 마커 안).
2. `slide-builder`에게 `assets/briefs/builder.md`를 채워 준다. 빌더는 조각 파일(`_work/blocks/B1.html`)만 쓴다.
3. `python ${CLAUDE_SKILL_DIR}/scripts/deck/check_fragment.py topics/<slug>/overview.html _work/blocks/B1.html --ids S05,S06,… --rules topics/<slug>/deck-rules.json` → "결과: 통과"
4. 임시 사본에서 시험 조립 → 문제없으면 `splice_blocks.py`로 실제 조립.
5. 조립 전에 커밋한다(되돌리기 쉬운 지점).

## 6. 서브에이전트와 overview.html

- 원칙: 서브에이전트는 overview.html을 직접 고치지 않는다. 조각·치환 표·검토 보고서만 낸다.
- 예외: 검수 반영 단계에서 메인이 장면 범위를 지정해 위임한 경우만. 이때 서브에이전트는 `_work/fix_log.md`에 장면·요소·전/후를 남긴다.
