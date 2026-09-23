# title-bullets — 제목 + 불릿

## 언제 쓰나

- 개념 설명, 요점 정리, 핵심 주장 전개의 가장 기본형
- 이미지 없이 메시지 자체를 앞에 세울 때

## HTML 구조

```html
<section class="scene" data-slide="N" data-skill="title-bullets" data-scene-id="S05">
  <div class="eyebrow" data-editable="true">카테고리</div>
  <h2 class="scene-title" data-editable="true">메인 타이틀</h2>
  <ul class="bullets">
    <li data-editable="true"><strong>강조어</strong> — 설명 항목 1</li>
    <li data-editable="true">설명 항목 2</li>
    <li data-editable="true">설명 항목 3</li>
  </ul>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

## CSS 핵심

- `.scene-title` — 72~120px, weight 800, letter-spacing 음수, 2줄 이내
- `.bullets` — `list-style: none; display: flex; flex-direction: column; gap: 24~28px`
- `.bullets li` — 38~44px, line-height 1.45, `padding-left: 52~56px; position: relative; word-break: keep-all`
- `.bullets li::before` — 왼쪽 표지(점 또는 32×2px 선), `position: absolute`
- `.bullets li strong` — 강조색 + weight 700

## 작성 원칙

- 불릿은 4개 이하, 각 한 문장
- 첫 불릿이 가장 중요한 메시지
- 이미지가 필요해지면 `split`이나 `title-image`로

## 1단 / 2단 판단

2단(`grid-template-columns: 1fr 1fr`)의 목적은 정보를 늘리는 것이 아니라 **같은 양을 더 읽기 쉽게** 하는 것이다.

| 상황 | 배치 |
|---|---|
| 불릿 4개, 길이 비슷 | 2단 권장 |
| 3개지만 각 2줄 이상 | 2단 권장 |
| 두 묶음을 나란히 대조 | 2단 권장 |
| 불릿 2개 이하 / 첫 불릿만 압도적으로 중요 / 위→아래 순서로 읽어야 함 | 1단 |

2단으로도 넘치면 장면을 둘로 나눈다.
