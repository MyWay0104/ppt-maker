# title — 제목 장면

## 언제 쓰나

- 오프닝, 구간 표지, 클로징처럼 제목 하나가 메시지의 전부일 때
- 이미지·불릿·태그 없이 글자만으로 임팩트를 줄 때
- 발표 흐름에서 "잠깐 멈춤"과 "주제 전환"을 알릴 때

## HTML 구조

```html
<section class="scene title-scene center" data-slide="1" data-skill="title" data-scene-id="S01">
  <div class="eyebrow" data-editable="true">카테고리 · 서브라벨</div>
  <h1 class="hero-title" data-editable="true">메인 타이틀</h1>
  <p class="hero-sub" data-editable="true">보조 설명 (선택)</p>
  <aside class="speaker-note">첫 장면에서 할 말</aside>
</section>
```

표지·구간 표지는 `.deck-footer`를 생략해도 된다.

구간 표지는 `section-divider` 클래스를 더한다. 내용 장면과 다른 톤(보조 강조색 `--accent-2`를 바탕에 14% 섞고 왼쪽에 보조색 띠)이 되어 "주제가 바뀐다"는 신호가 된다. 제목은 구간명, `.eyebrow`는 `n/N`.

```html
<section class="scene title-scene section-divider" data-slide="3" data-skill="title" data-scene-id="D01">
  <div class="eyebrow" data-editable="true">1/3</div>
  <h1 class="hero-title" data-editable="true">Python과 친해지기</h1>
  <p class="hero-sub" data-editable="true">Python이 무엇이고 내 업무에 왜 쓸모 있는지</p>
  <aside class="speaker-note">…</aside>
</section>
```

구간 표지는 제목 묶음이 장면의 세로 가운데에 오게 한다(위쪽 절반이 비지 않게). 진행 막대 같은 장식은 제목 묶음 안에 둔다.

## CSS 핵심

- `.scene.center` — `justify-content: center; align-items: center; text-align: center`
- `.eyebrow` — 24~32px, weight 500, letter-spacing 6~8px, 대문자, 보조 글자색
- `.hero-title` — 짧은 영문·숫자 제목은 200~280px, 한글 두 단어 이상은 120~160px. weight 800, letter-spacing 음수
- `.hero-sub` — 36~44px, weight 400~500, 보조 글자색
- 배경은 단색 또는 아주 옅은 radial gradient — 제목 자체가 주인공

## 작성 원칙

- 제목은 짧고 강하게 한 줄
- 부제는 한 줄 이내. 길어지면 `title-bullets`로
- 불릿이 필요하면 이 타입이 아니다
- 제목만 크게 보이므로 제목 자체가 의미를 전해야 한다

## title vs title-bullets

| 상황 | 타입 |
|---|---|
| 제목만, 또는 제목 + 짧은 부제 | `title` |
| 제목 + 설명 항목 나열 | `title-bullets` |
