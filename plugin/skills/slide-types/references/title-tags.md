# title-tags — 제목 + 키워드 태그

## 언제 쓰나

- 개념을 짧은 키워드로 압축할 때
- 기술 스택, 핵심 속성, 비교 축, 요약 색인

## HTML 구조

```html
<section class="scene" data-slide="N" data-skill="title-tags" data-scene-id="S03">
  <div class="eyebrow" data-editable="true">카테고리</div>
  <h2 class="scene-title" data-editable="true">메인 타이틀</h2>
  <p class="scene-subtitle" data-editable="true">보조 설명 (선택)</p>
  <div class="tags">
    <span class="tag" data-editable="true">태그1</span>
    <span class="tag" data-editable="true">태그2</span>
    <span class="tag accent" data-editable="true">강조 태그</span>
    <span class="tag" data-editable="true">태그4</span>
  </div>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

## CSS 핵심

- `.tags` — `display: flex; flex-wrap: wrap; gap: 20~24px; margin-top: 56px`
- `.tag` — `padding: 18~20px 32~36px; border-radius: 999px; font-size: 36~42px; font-weight: 700`
  - 배경은 옅은 틴트(`color-mix(in srgb, var(--accent) 10%, transparent)`), 테두리는 옅은 선
- `.tag.accent` — 강조색 배경 + 대비 글자색(명암비 4.5:1 이상)

## 작성 원칙

- 태그 3~5개가 적당(최대 8개, 가독성 확인)
- 각 태그는 짧은 명사구
- 강조 태그는 1개만 — 여러 개면 강조가 사라진다
- 태그가 길어지면 `title-bullets`로
