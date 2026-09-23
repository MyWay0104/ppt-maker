# stat — 큰 숫자 강조

## 언제 쓰나

- 성과, KPI, 통계 수치를 강조할 때
- 숫자 자체가 메시지의 핵심일 때
- 지표 1~3개를 한 화면에

## HTML 구조

```html
<section class="scene" data-slide="N" data-skill="stat" data-scene-id="S12">
  <div class="eyebrow" data-editable="true">카테고리</div>
  <h2 class="scene-title" data-editable="true">메인 타이틀</h2>
  <div class="stats">
    <div class="stat"><span class="stat-value" data-editable="true">120만</span><span class="stat-label" data-editable="true">월간 활성 사용자</span></div>
    <div class="stat"><span class="stat-value" data-editable="true">40%</span><span class="stat-label" data-editable="true">운영 비용 절감</span></div>
    <div class="stat"><span class="stat-value" data-editable="true">3.2s</span><span class="stat-label" data-editable="true">평균 응답 시간</span></div>
  </div>
  <p class="source" data-editable="true">출처: 2026년 3분기 운영 보고서</p>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

숫자에는 출처가 따라야 한다. 출처 없는 숫자는 문구 단계에서 `[확인 필요]`로 멈춘다.

## CSS 핵심

- `.stats` — `display: grid; grid-template-columns: repeat(3, 1fr); gap: 48~64px; margin-top: 56~64px`
  - 지표 2개면 `repeat(2, 1fr)`, 1개면 가운데 정렬
- `.stat` — 카드형(배경 + 옅은 테두리 + `border-radius`) 또는 선형(`border-top: 2px solid`; `padding-top: 32px`), `display: flex; flex-direction: column`
- `.stat-value` — 96~140px, weight 800, line-height 1, letter-spacing 음수, `font-variant-numeric: tabular-nums`
- `.stat-label` — 24~32px, weight 500~600, line-height 1.4, `margin-top: 16~20px`

## 보조 시각화 (선택)

막대·원형 게이지가 필요하면 별도 요소로 둔다. 너비 같은 값은 인라인 style 대신 scene-styles에 장면 범위로 쓴다.

```html
<div class="stat">
  <span class="stat-value" data-editable="true">120만</span>
  <div class="bar-track"><div class="bar-fill"></div></div>
  <span class="stat-label" data-editable="true">월간 활성 사용자 · 목표 대비 85%</span>
</div>
```

```css
[data-slide="12"] .stat:nth-child(1) .bar-fill { width: 85%; }
```

- `%` 값 → 원형 게이지(SVG `stroke-dasharray`)
- 크기·양 비교 → 막대
- 단일 수치 → 시각화 없이 숫자만

## 작성 원칙

- 숫자는 짧게(120만, 40%, 3.2s), 단위를 붙인다
- 설명은 한 줄
- 4개 이상이면 `compare`·`title-bullets`로 바꾸거나 장면을 나눈다
