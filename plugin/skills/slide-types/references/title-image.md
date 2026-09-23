# title-image — 제목 + 대표 이미지

## 언제 쓰나

- 큰 제목과 대표 이미지 한 장이 메시지의 중심일 때
- 제품·서비스 소개, 스크린샷 소개, 표지형 장면

## HTML 구조

```html
<section class="scene title-image" data-slide="N" data-skill="title-image" data-scene-id="S08">
  <div class="eyebrow" data-editable="true">카테고리</div>
  <h2 class="scene-title" data-editable="true">메인 타이틀</h2>
  <p class="scene-subtitle" data-editable="true">보조 설명 (선택)</p>
  <div class="image-frame">
    <img src="assets/img/08-dashboard.png" alt="대시보드 첫 화면 — 오늘 할 일 세 칸" />
  </div>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

## CSS 핵심

- `.scene.title-image` — `align-items: center; text-align: center`
- `.image-frame` — `width: 100%; max-width: 1400px; aspect-ratio: 16/9; margin-top: 48px`, 모서리 둥글기 선택
- `.image-frame img` — `width: 100%; height: 100%; object-fit: contain`
- 이미지가 아직 없으면 `.image-frame`의 옅은 배경 + 점선 테두리가 자리 표시 역할

## 배치

- 위에서 아래로: eyebrow → 제목 → 부제 → 이미지. 모두 가운데 정렬
- 이미지는 `position: absolute`를 피하고 흐름 안에서 크기를 관리한다

## 작성 원칙

- 제목이 주인공, 이미지는 증거
- 이미지는 topic의 `assets/img/` 아래, 파일명은 `번호-설명.확장자`(예: `08-dashboard.png`)
- 부제는 1~2줄
- 이미지가 강하면 제목은 더 짧게, 약하면 제목을 더 분명하게
