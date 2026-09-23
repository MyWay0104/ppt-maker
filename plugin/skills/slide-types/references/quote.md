# quote — 한 문장 강조·인용

## 언제 쓰나

- 핵심 메시지를 강하게 남기고 싶을 때
- 인용구, 명언, 사용자 피드백, 책의 한 구절
- 발표 흐름에서 잠깐 멈추고 리듬을 줄 때

## HTML 구조

```html
<section class="scene quote" data-slide="N" data-skill="quote" data-scene-id="S20">
  <div class="eyebrow" data-editable="true">카테고리 · 인사이트</div>
  <div class="quote-mark" aria-hidden="true">"</div>
  <p class="quote-body" data-editable="true">좋은 디자인은 <em>가능한 한 적게</em> 디자인하는 것이다</p>
  <p class="quote-attrib" data-editable="true">— 디터 람스</p>
  <aside class="speaker-note">대본</aside>
</section>
```

책 인용(독서모임 리딩자료)은 출처에 쪽수를 반드시 붙인다: `— 『책 제목』, p.42`

## CSS 핵심

- `.scene.quote` — `justify-content: center; align-items: center; text-align: center`
- `.quote-mark` — 200~240px, weight 900, 강조색, `opacity: 0.35; line-height: 0.7`
- `.quote-body` — 72~96px, weight 600~700, line-height 1.35, `max-width: 1500px; word-break: keep-all; text-wrap: balance`
- `.quote-body em` — `font-style: normal`, 강조색
- `.quote-attrib` — 28~36px, weight 500, 보조 글자색, letter-spacing 2~4px, `margin-top: 40~48px`

## 작성 원칙

- 인용 문장은 1~2줄
- 출처가 없어도 된다(자기 메시지 강조용). 단 남의 말이면 출처 필수
- 불릿·태그를 섞지 않는다
- 긴 문장은 핵심만 발췌하고, 발췌했다는 사실을 발표자 노트에 적는다
