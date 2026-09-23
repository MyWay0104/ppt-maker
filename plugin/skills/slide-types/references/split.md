# split — 시각 자료 + 해설 분할

## 언제 쓰나

- 스크린샷·차트·다이어그램을 설명할 때
- 시각 자료와 해설을 동시에 보여 줘야 할 때

## HTML 구조 (좌우 분할)

```html
<section class="scene split" data-slide="N" data-skill="split" data-scene-id="S10">
  <div class="eyebrow" data-editable="true">카테고리</div>
  <h2 class="scene-title" data-editable="true">메인 타이틀</h2>
  <div class="split-grid">
    <div class="split-image">
      <img src="assets/img/10-chart.png" alt="월별 처리 건수 막대 차트 — 3월에 두 배" />
    </div>
    <ul class="bullets">
      <li data-editable="true">해설 1</li>
      <li data-editable="true">해설 2</li>
      <li data-editable="true">해설 3</li>
    </ul>
  </div>
  <p class="source" data-editable="true">출처: …</p>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

비율을 바꾸려면 `.split-grid`에 보조 클래스(`wide-left`, `wide-right`)를 두고 scene-styles에서 `grid-template-columns: 3fr 2fr`처럼 정한다.

## CSS 핵심

- `.split-grid` — `display: grid; grid-template-columns: 1fr 1fr; gap: 48~64px; margin-top: 48px; flex: 1; min-height: 0`
- `.split-image` — 이미지 틀. 이미지가 없으면 점선 테두리 + 옅은 배경이 자리 표시
- `.split-image img` — `width: 100%; height: 100%; object-fit: contain`
- 해설 쪽은 `title-bullets`의 `.bullets`를 그대로 쓴다

## 작성 원칙

- 이미지는 **읽을 대상**, 불릿은 **해석**. 불릿이 이미지를 다시 읽어 주지 않게 쓴다
- 이미지가 없으면 `split`이 아니다 → `title-bullets`
- 수치·캡처의 출처가 있으면 `.source`에 적는다
