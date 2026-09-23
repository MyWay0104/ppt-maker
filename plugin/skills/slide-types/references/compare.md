# compare — 항목 나란히 비교

## 언제 쓰나

- 2~4개 항목을 동시에 비교할 때
- 선택지·옵션·대안을 나란히 보여 줄 때
- 각 항목의 특징을 불릿으로 설명할 때

## HTML 구조

```html
<section class="scene" data-slide="N" data-skill="compare" data-scene-id="S16">
  <div class="eyebrow" data-editable="true">비교</div>
  <h2 class="scene-title" data-editable="true">프레임워크 선택</h2>
  <div class="compare-grid cols-3">
    <div class="compare-col">
      <div class="compare-heading" data-editable="true">React</div>
      <ul class="compare-list">
        <li data-editable="true">생태계가 크다</li>
        <li data-editable="true">자유도가 높다</li>
      </ul>
    </div>
    <div class="compare-col">
      <div class="compare-heading" data-editable="true">Vue</div>
      <ul class="compare-list">
        <li data-editable="true">배우기 쉽다</li>
        <li data-editable="true">공식 도구가 잘 갖춰져 있다</li>
      </ul>
    </div>
    <div class="compare-col">
      <div class="compare-heading" data-editable="true">Svelte</div>
      <ul class="compare-list">
        <li data-editable="true">번들이 작다</li>
        <li data-editable="true">컴파일 단계에서 최적화한다</li>
      </ul>
    </div>
  </div>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

## CSS 핵심

- `.compare-grid` — `display: grid; gap: 32~40px; margin-top: 48px; flex: 1; min-height: 0`
  - `.cols-2` `1fr 1fr` / `.cols-3` `repeat(3, 1fr)`(기본) / `.cols-4` `repeat(4, 1fr)`
- `.compare-col` — 카드(배경 + 옅은 테두리 + `border-radius: 20px; padding: 36~40px`)
- `.compare-heading` — 44~56px, weight 700, `border-bottom: 2px solid var(--accent); padding-bottom: 16px; margin-bottom: 20px`
- `.compare-list li` — 26~32px, line-height 1.4, `padding-left: 40px; position: relative`. 표지는 글자(`—`)가 아니라 폭이 고정된 선으로 그린다: `::before { content: ""; position: absolute; left: 0; top: 0.7em; width: 20px; height: 3px; background: var(--accent) }`. 이유: `—`는 글자 크기만큼(32px 글자면 약 32px) 넓어서 28px 자리에 넣으면 본문과 겹친다(P7 iteration-1 결함). 표지 폭 + 12px 이상을 `padding-left`로 둔다

## compare vs evolution-flow

| 상황 | 타입 |
|---|---|
| A에서 B로 변한 흐름(방향 있음) | `evolution-flow` |
| A·B·C를 동시에 비교(대등 관계) | `compare` |

## 작성 원칙

- 2~4열, 열 제목은 1~2단어
- 열마다 불릿 수를 비슷하게 맞춘다
- 5열 이상은 장면을 나눈다
