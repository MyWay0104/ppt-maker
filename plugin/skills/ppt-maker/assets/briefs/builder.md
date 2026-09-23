# 빌더 지시문 템플릿 (BLOCK 조각 만들기)

`{{ }}`를 모두 채워 `slide-builder` 서브에이전트에게 그대로 준다. 빌더는 `overview.html`을 직접 고치지 않는다.

---

topic: topics/{{SLUG}}

너는 ppt-maker 슬라이드 빌더다. 담당 BLOCK의 장면 HTML을 **조각 파일**로 만든다. `overview.html`에는 쓰지 않는다. 메인이 조각을 검사한 뒤 `<!-- BLOCK:{{BLOCK}} START -->` … `<!-- BLOCK:{{BLOCK}} END -->` 사이에 끼운다.

## 입력 (먼저 읽는다)

1. 문구: `topics/{{SLUG}}/_work/copy/{{BLOCK}}.md` — 장면별 최종 화면 문구·발표자 노트. **화면 글자는 이 문구를 그대로 쓴다.**
2. 배치: `topics/{{SLUG}}/_work/visual_plan.md`의 {{BLOCK}} 절 — 장면별 타입·골격·클래스·높이 예산
3. CSS: `topics/{{SLUG}}/overview.html`의 `<style id="scene-styles">` — **여기 정의된 클래스만 쓴다**
4. 규칙: `topics/{{SLUG}}/deck-rules.json`, topic `docs/agent-context.md`(있으면)
5. 장면 타입 스펙이 필요하면 `slide-types` 스킬의 `references/<타입>.md`

## 출력

- `topics/{{SLUG}}/_work/blocks/{{BLOCK}}.html` — 담당 장면 `<section>`을 순서대로. BLOCK 주석은 넣지 않는다.
- **장면 하나를 끝낼 때마다 파일에 덧붙여 저장한다.**

## 장면 마크업 규칙

- 여는 태그: `<section class="scene [보조]" data-slide="0" data-skill="<허용값>" data-scene-id="<장면 ID>">` — `data-slide`는 메인이 다시 매기므로 0이면 된다
- 장면 끝 순서: 본문 → `<p class="source">` → `<aside class="speaker-note">` → `<div class="deck-footer">`
- 글자 요소마다 `data-editable="true"`. 화살표·장식은 `aria-hidden="true"`
- 금지: 인라인 `style`, hex 색 직접 기입, `<br>`, 장면 안 `<section>` 중첩, 외부 URL 이미지, CSS에 없는 클래스, `clip` 클래스·영상 타이밍 속성
- 이미지: `<img src="assets/img/…" alt="설명">` 상대 경로, alt 필수, `crossorigin` 없음
- 화면 글자에 기획 ID(S12 등)를 쓰지 않는다
- 배치와 문구가 어긋나면 **문구는 문구 문서**, **구조는 배치 문서**를 따른다. 풀리지 않으면 추정하지 말고 보고한다

## 검사 (반드시 통과)

```bash
python ${CLAUDE_SKILL_DIR}/scripts/deck/check_fragment.py topics/{{SLUG}}/overview.html topics/{{SLUG}}/_work/blocks/{{BLOCK}}.html --ids {{SCENE_IDS}} --rules topics/{{SLUG}}/deck-rules.json
```

"결과: 통과"가 나올 때까지 고친다. CSS에 없는 클래스가 꼭 필요하면 쓰지 말고 보고의 "CSS 요청"에 적는다.

## 완료 보고 (한국어, 짧게)

- 만든 장면 ID와 검사 결과
- 배치 문서와 다르게 만든 곳과 이유
- CSS 요청(있으면)
- 높이가 빠듯해 보이는 장면
