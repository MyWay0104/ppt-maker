# steps — 순서 있는 단계

## 언제 쓰나

- 순서가 있는 프로세스, 워크플로, 파이프라인, 절차
- `evolution-flow`와 달리 3단계 이상이 필요할 때

## HTML 구조

```html
<section class="scene" data-slide="N" data-skill="steps" data-scene-id="S14">
  <div class="eyebrow" data-editable="true">프로세스</div>
  <h2 class="scene-title" data-editable="true">배포 파이프라인</h2>
  <ol class="steps">
    <li class="step"><div class="step-num" data-editable="true">1</div><div class="step-body" data-editable="true">코드 커밋</div></li>
    <li class="step"><div class="step-num" data-editable="true">2</div><div class="step-body" data-editable="true">CI 테스트 실행</div></li>
    <li class="step"><div class="step-num" data-editable="true">3</div><div class="step-body" data-editable="true">스테이징 배포</div></li>
    <li class="step"><div class="step-num" data-editable="true">4</div><div class="step-body" data-editable="true">프로덕션 릴리스</div></li>
  </ol>
  <aside class="speaker-note">대본</aside>
  <div class="deck-footer" data-editable="true">덱 이름</div>
</section>
```

## CSS 핵심

- `.steps` — `list-style: none; display: flex; flex-direction: column; gap: 28px; margin-top: 56px; position: relative`
- `.step` — `display: flex; align-items: center; gap: 32px`
- `.step-num` — 원형 표지 `72×72px; border-radius: 50%; background: var(--accent); color: var(--bg)`, 가운데 정렬, 36px weight 800, `flex-shrink: 0`
- `.step-body` — 38~44px, weight 500, line-height 1.4
- 연결선 — `.steps::before`로 왼쪽 세로선(`left: 36px; top: 36px; bottom: 36px; width: 2px`)
- 가로 배치가 필요하면 `.steps.horizontal { flex-direction: row }` + 연결선을 가로로

## steps vs title-bullets vs evolution-flow

| 상황 | 타입 |
|---|---|
| 순서가 중요한 단계 흐름 | `steps` |
| 순서 없는 나열 | `title-bullets` |
| 두 상태 비교(before/after) | `evolution-flow` |

## 작성 원칙

- 3~5단계가 적당, 각 단계는 한 줄
- 순서가 중요하지 않으면 `title-bullets`
