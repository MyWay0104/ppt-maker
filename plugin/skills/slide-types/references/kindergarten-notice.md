# kindergarten-notice — 유치원·어린이집 학부모 안내

## 언제 쓰나

- 유치원·어린이집 학부모 안내, 놀이 기록, 프로젝트 활동 공유, 다음 놀이 예고
- 교사가 찍은 교실·바깥놀이 사진과 관찰 문장을 부드럽고 믿음직하게 보여 줄 때
- 참고 스타일: 연노랑 격자 배경, 흰 데이지, 작은 벌, 크림색 구름·가리비 패널, 주황 라벨, 진파랑 대제목

## 기본 미감

- 배경: `#FBE987` 계열 노랑 + 64px 안팎의 흰 격자. 너무 진한 노랑 금지
- 주색: 진파랑 `#006FB4`, 주황 `#FDB515`, 크림 `#FFF7CE`, 흰 패널
- 글꼴: Paperlogy. 제목 800, 본문 700 이상 — 한글 가독성이 먼저
- 장식: 데이지·벌은 CSS/SVG로 만든다. 무작위 배치 금지, 장면마다 2~5개
- 사진: `assets/img/` 상대 경로. 없으면 `.photo.placeholder`로 따뜻한 패턴만
- 문장: 설명문보다 관찰 기록 톤("아이들이 ~했습니다", "관심을 보였습니다")

## 레이아웃 원형 (보조 클래스)

| 보조 클래스 | 쓰임 | 구조 |
|---|---|---|
| `bee-cover` | 표지 | 곡선 상단 제목 + 큰 구름 패널 + 기간 라벨 + 꽃밭 장식 |
| `notice-story` | 놀이의 시작 | 가운데 흰 점선 패널 + 큰 본문 + 원형 사진 2~3개 |
| `hex-gallery` | 세부 활동 정리 | 왼쪽 설명 목록 + 오른쪽 육각형 사진 묶음 |
| `teacher-note` | 긴 관찰 기록 | 위쪽 사진 띠 + 본문 2단락 + 밑줄 강조 |
| `next-play` | 다음 놀이 예고 | 3열 카드(라벨·사진·교사 지원 계획) |

## HTML 구조

```html
<section class="scene notice-story" data-slide="2" data-skill="kindergarten-notice" data-scene-id="S02">
  <div class="pill-title" data-editable="true">놀이의 시작</div>
  <div class="paper-panel">
    <p class="story-text" data-editable="true">아이들은 바깥놀이에서 … 관심을 보였습니다.</p>
  </div>
  <div class="photo photo-round photo-a"><img src="assets/img/play-01.jpg" alt="모래놀이터에서 두꺼비집을 만드는 아이들" /></div>
  <div class="bee bee-bottom" aria-hidden="true"></div>
  <aside class="speaker-note">대본</aside>
</section>
```

## CSS 필수 블록

```css
.scene.notice-story, .scene.bee-cover, .scene.hex-gallery, .scene.teacher-note, .scene.next-play {
  background-color: #FBE987;
  background-image:
    linear-gradient(rgba(255,255,255,.78) 2px, transparent 2px),
    linear-gradient(90deg, rgba(255,255,255,.78) 2px, transparent 2px);
  background-size: 64px 64px;
  color: #111827;
  word-break: keep-all;
}
.paper-panel {
  background: #fff;
  border: 5px dashed #F6C65B;
  border-radius: 28px;
  box-shadow: 0 10px 0 rgba(255, 181, 21, .18);
}
```

- 구름 표지는 `border-radius: 50%` 원 여러 개를 겹치거나 가상 요소로 만든다
- 육각 사진: `clip-path: polygon(25% 5%, 75% 5%, 100% 50%, 75% 95%, 25% 95%, 0 50%)`
- 꽃과 벌은 `.daisy`, `.bee` 공통 클래스 + `aria-hidden="true"`
- 격자 배경 위 글자는 `qa_check`가 명암비를 자동 계산하지 못한다(낮음·확인 필요) → 스크린샷으로 눈 검수

## 작성 원칙

- 본문 4~8줄. 알림장 톤이라 너무 압축하지 않는다
- 번호 목록은 `1.`, `2.`처럼 짧게, 긴 설명은 다음 장면으로
- 사진은 장면당 4장 이하, 원형·둥근 사각형·육각형 중 한 규칙으로 통일
- 아래 꽃밭 장식은 본문과 겹치지 않게 `bottom: -8px` 근처에 고정
