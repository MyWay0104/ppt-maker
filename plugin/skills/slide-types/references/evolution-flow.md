# evolution-flow — 이전 상태 → 이후 상태

## 언제 쓰나

- 기존 상태와 개선 상태를 한 화면에서 대비할 때
- 입력 → 결과처럼 가운데 변화 축이 핵심일 때
- before/after를 나열이 아니라 인과 흐름으로 보여 줄 때

## HTML 구조

```html
<section class="scene" data-slide="N" data-skill="evolution-flow" data-scene-id="S18">
  <div class="eyebrow" data-editable="true">개선</div>
  <h2 class="scene-title" data-editable="true">검색 경험이 어떻게 바뀌었나</h2>
  <div class="flow">
    <div class="flow-col">
      <div class="flow-label" data-editable="true">기존</div>
      <div class="flow-heading" data-editable="true">목록 중심</div>
      <ul class="flow-list">
        <li data-editable="true">결과 목록이 길게 이어진다</li>
        <li data-editable="true">먼저 읽을 답이 눈에 띄지 않는다</li>
      </ul>
    </div>
    <div class="flow-arrow" aria-hidden="true">→</div>
    <div class="flow-col after">
      <div class="flow-label" data-editable="true">개선</div>
      <div class="flow-heading" data-editable="true">답 중심</div>
      <ul class="flow-list">
        <li data-editable="true">핵심 답이 먼저 보인다</li>
        <li data-editable="true">다음 클릭이 자연스럽게 이어진다</li>
      </ul>
    </div>
  </div>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

## CSS 핵심

- `.flow` — `display: grid; grid-template-columns: 1fr 120px 1fr; gap: 40px; margin-top: 48~56px; flex: 1; max-height: 620px`
- `.flow-col` — 카드(`border-radius: 24px; padding: 44px 40px; display: flex; flex-direction: column`)
- `.flow-col.after` — 강조색 테두리·옅은 강조 배경으로 "도착 상태"를 드러낸다
- `.flow-label` — 알약 배지(24~28px, letter-spacing 3px, `padding: 8px 20px; border-radius: 999px`). `.after`의 배지는 강조색 배경 + 대비 글자색
- `.flow-heading` — 44~56px, weight 700, line-height 1.2
- `.flow-list li` — 26~32px, line-height 1.4, `padding-left: 40px; position: relative`. 표지는 글자(`—`)가 아니라 폭이 고정된 선으로 그린다: `::before { content: ""; position: absolute; left: 0; top: 0.7em; width: 20px; height: 3px; background: var(--accent) }`. 이유: `—`는 글자 크기만큼(32px 글자면 약 32px) 넓어서 28px 자리에 넣으면 본문과 겹친다(P7 iteration-1 결함). 표지 폭 + 12px 이상을 `padding-left`로 둔다
- `.flow-arrow` — 가운데 정렬, 80px, weight 200, 강조색
- 이미지가 필요하면 `.flow-col` 안에 `.flow-image { aspect-ratio: 16/9 }`

## 작성 원칙

- 왼쪽은 출발 상태, 오른쪽은 도착 상태만
- 좌우 불릿 수가 같을 필요는 없지만 대응 관계가 느껴지게
- 좌우 제목은 명사형보다 **상태형**("목록 중심" / "답 중심")
- 변화 이유·과정 설명이 길면 다음 장면으로 나눈다

## 쓰지 말아야 할 때

- 이미지 한 장과 설명 몇 줄이면 충분 → `split`·`title-image`
- 4단계 이상 시간 순서 → `steps`
- 3개 이상 동시 비교 → `compare`
