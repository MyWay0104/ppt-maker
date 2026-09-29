# diagram — 좌표 없는 인포그래픽

## 언제 쓰나

- 흐름·순환·허브·계층·시간 순서·깔때기처럼 **도형과 글자가 함께 있는 그림**이 메시지일 때
- `steps`(세로 목록)나 `compare`(카드 비교)로는 관계가 안 보일 때

## 핵심 규칙: 글자가 들어가는 그림은 SVG로 그리지 않는다

글자가 있는 인포그래픽은 **HTML 요소 + 미리 만든 부품 클래스**로 만든다. 모델은 좌표(`x`, `y`, `left`, `top`, `transform`)를 한 개도 쓰지 않는다. 배치는 flex·grid·CSS 삼각함수가 계산한다.

이유: SVG `<text>`는 줄바꿈도, 도형 크기에 맞춘 자동 정렬도 없어서 좌표를 머릿속으로 계산해야 한다. 이 계산이 틀리면 글자가 겹치고, 도형 밖으로 삐져나오고, 그림이 한쪽으로 몰린다. 모델의 공간 추론 성능에 따라 결과가 크게 달라지는 지점이라, 계산을 모델에서 브라우저로 옮긴다.

| 허용 | 금지 |
|---|---|
| 아래 부품 6종(`ig-flow`, `ig-cycle`, `ig-cycle has-hub`, `ig-layers`, `ig-timeline`, `ig-funnel`) | 글자가 들어간 손 SVG(`<svg>` 안 `<text>`) |
| 글자 없는 SVG: 아이콘, 장식선, 게이지(`stat`의 `stroke-dasharray`) | `position: absolute` + `top/left` 숫자로 라벨 놓기 |
| 부품 CSS 변수만 바꾸기(`--ig-gap`, `--r`, `--node-w`) | 장면 전용 CSS로 부품 항목 위치를 하나씩 옮기기 |

부품으로 안 되는 그림(지도, 복잡한 네트워크)은 **이미지 자리표시**(`build-rules.md` 4절)로 두고 사용자에게 알린다. 어쩔 수 없이 SVG에 글자를 넣었다면 `qa_check`의 SVG 검사(8절)가 높음 0건이 될 때까지 고친다.

## 부품 고르기

| 메시지 | 부품 | 항목 수 |
|---|---|---|
| A → B → C 순서로 처리된다 | `ig-flow` | 3~5 |
| 끝나면 처음으로 돌아간다 | `ig-cycle` | 3~6 |
| 가운데 하나를 여러 요소가 둘러싼다 | `ig-cycle has-hub` + `.ig-center` | 3~6 |
| 위아래로 쌓인 구조(화면·서버·데이터) | `ig-layers` | 3~5 |
| 날짜·기간 순서 | `ig-timeline` | 3~6 |
| 걸러지며 줄어든다 | `ig-funnel` | 3~5 |

항목 수가 범위를 넘으면 장면을 둘로 나누거나 항목을 묶는다. 부품 크기를 키워 억지로 넣지 않는다.

## HTML 구조 (그대로 복사해 글자만 바꾼다)

공통: 컨테이너에 `ig`와 부품 이름, 항목마다 `.ig-node`, 글자는 항상 자식 요소(`.ig-title` 필수, `.ig-desc` 선택). `.ig-node`에 글자를 직접 넣지 않는다. 강조할 항목 하나에만 `.is-key`.

### ig-flow — 가로 흐름

```html
<section class="scene" data-slide="N" data-skill="diagram" data-scene-id="S09">
  <div class="eyebrow" data-editable="true">구조 · 2/4</div>
  <h2 class="scene-title" data-editable="true">RAG 파이프라인</h2>
  <p class="thesis" data-editable="true">질문이 답이 되기까지 네 단계를 거칩니다</p>
  <ol class="ig ig-flow">
    <li class="ig-node"><span class="ig-title" data-editable="true">질문 입력</span><span class="ig-desc" data-editable="true">자연어로 묻습니다</span></li>
    <li class="ig-node"><span class="ig-title" data-editable="true">벡터 DB 검색</span><span class="ig-desc" data-editable="true">관련 문서를 찾습니다</span></li>
    <li class="ig-node is-key"><span class="ig-title" data-editable="true">컨텍스트 결합</span><span class="ig-desc" data-editable="true">질문과 합칩니다</span></li>
    <li class="ig-node"><span class="ig-title" data-editable="true">LLM 답변</span><span class="ig-desc" data-editable="true">출처와 함께 답합니다</span></li>
  </ol>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

화살표는 CSS가 칸 사이에 그린다. 화살표 요소를 따로 넣지 않는다.

### ig-cycle — 순환 고리

```html
<div class="ig ig-cycle">
  <div class="ig-node is-key"><span class="ig-title" data-editable="true">계획</span><span class="ig-desc" data-editable="true">목표 설정</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">실행</span><span class="ig-desc" data-editable="true">작게 시도</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">점검</span><span class="ig-desc" data-editable="true">결과 측정</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">개선</span><span class="ig-desc" data-editable="true">표준화</span></div>
</div>
```

첫 항목이 12시, 시계 방향으로 놓인다. 항목 수(3~6)에 맞춰 반지름과 상자 크기가 자동으로 바뀐다. 6개일 때는 `.thesis`를 빼야 높이가 맞는다.

### ig-cycle has-hub — 가운데 허브

```html
<div class="ig ig-cycle has-hub">
  <div class="ig-center"><span class="ig-title" data-editable="true">Agent</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">LLM</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">도구</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">메모리</span></div>
  <div class="ig-node"><span class="ig-title" data-editable="true">계획</span></div>
</div>
```

`.ig-center`는 하나만, 어느 순서에 두어도 된다(항목 순번에서 빠진다).

### ig-layers — 계층 구조

```html
<ol class="ig ig-layers">
  <li class="ig-node"><span class="ig-title" data-editable="true">화면</span>
    <ul class="ig-chips"><li class="ig-chip" data-editable="true">채팅 UI</li><li class="ig-chip" data-editable="true">대시보드</li></ul></li>
  <li class="ig-node is-key"><span class="ig-title" data-editable="true">Agent</span>
    <ul class="ig-chips"><li class="ig-chip" data-editable="true">계획</li><li class="ig-chip" data-editable="true">도구 호출</li></ul></li>
  <li class="ig-node"><span class="ig-title" data-editable="true">데이터</span>
    <ul class="ig-chips"><li class="ig-chip" data-editable="true">벡터 DB</li><li class="ig-chip" data-editable="true">로그</li></ul></li>
</ol>
```

### ig-timeline — 시간 순서

```html
<ol class="ig ig-timeline">
  <li class="ig-node"><span class="ig-when" data-editable="true">1월</span><span class="ig-title" data-editable="true">파일럿</span><span class="ig-desc" data-editable="true">한 팀에서 시험</span></li>
  <li class="ig-node is-key"><span class="ig-when" data-editable="true">6월</span><span class="ig-title" data-editable="true">정식 운영</span><span class="ig-desc" data-editable="true">전사 공개</span></li>
  <li class="ig-node"><span class="ig-when" data-editable="true">12월</span><span class="ig-title" data-editable="true">회고</span><span class="ig-desc" data-editable="true">성과 정리</span></li>
</ol>
```

### ig-funnel — 깔때기

```html
<ol class="ig ig-funnel">
  <li class="ig-node"><span class="ig-title" data-editable="true">전체 문서 1만 건</span></li>
  <li class="ig-node"><span class="ig-title" data-editable="true">키워드 통과 2천 건</span></li>
  <li class="ig-node"><span class="ig-title" data-editable="true">의미 검색 상위 50건</span></li>
</ol>
```

## 글자 수 상한 (넘으면 문구를 줄인다. 글자 크기를 줄이지 않는다)

| 부품 | `.ig-title` | `.ig-desc` |
|---|---|---|
| ig-flow (4개 기준) | 8자 | 10자(한 줄). 두 줄이면 마지막 줄이 5자 이상 |
| ig-cycle · has-hub | 5자 | 7자 |
| ig-layers | 6자 | 칩 하나 8자, 칩 5개 이하 |
| ig-timeline (5개 기준) | 6자 | 8자 |
| ig-funnel | 16자 | 쓰지 않음 |

항목 수가 적으면 조금 늘어나도 된다. 판정은 `qa_check`의 `잘림`·`글자 겹침`·`고아 줄바꿈`이 한다.

## CSS

- 부품 CSS는 `ppt-maker/assets/infographic.css`에 있다. 새 덱은 `scaffold_overview.py`가 scene-styles에 넣는다.
- 이 파일이 없던 기존 덱은 `infographic.css`를 `_work/slide_ui/0N_infographic.css`(기존 최대 번호 + 1)로 복사하고 `apply_css_patch.py`로 적용한다.
- 부품 CSS는 고치지 않는다. 장면마다 조정이 필요하면 CSS 변수만 바꾼다: `[data-slide="N"] .ig-flow { --ig-gap: 56px; }`, `[data-slide="N"] .ig-cycle { --r: 240px; }`

## 쓰지 말아야 할 때

- 순서 있는 3~5단계를 글로 설명 → `steps`
- 두 상태 대비 → `evolution-flow`
- 대등한 2~4개 비교 → `compare`
- 숫자가 주인공 → `stat`
