# edit-loop — Aim/Edit 검토 루프

사용자는 브라우저로 overview.html을 보며 두 가지 방법으로 고친다.

| 도구 | 사용자가 하는 일 | 결과 |
|---|---|---|
| **Edit** | 글자를 직접 고치고 Done | 서버가 overview.html에 바로 저장 |
| **Aim** | 요소를 클릭해 셀렉터 복사 → 대화창에 "이거 ~하게 바꿔줘" | Claude가 그 요소를 고친다 |

## 1. 서버 띄우기

```bash
python ${CLAUDE_SKILL_DIR}/scripts/serve_live.py topics/<slug>          # 기본 포트 8765
```

- 주소: `http://127.0.0.1:8765/topics/<slug>/overview.html` (프로젝트 루트를 서빙한다)
- 127.0.0.1에만 열린다. 같은 서버로 `present.html`(발표자 창 포함)도 연다
- 3초마다 `/mtime`을 확인해 Claude가 파일을 고치면 브라우저가 자동으로 새로고침된다(편집 중에는 멈춘다). 보던 장면은 주소 `#N`으로 유지된다
- 서버는 Bash `run_in_background`로 띄우고, 작업이 끝나면 멈춘다
- 띄운 뒤 사용자에게 **주소를 그대로 복사해 브라우저 주소창에 붙여 넣으라고** 한 줄로 안내한다. 대화창의 링크는 환경에 따라 클릭이 안 되고, 파일 탐색기에서 overview.html을 직접 열면(`file://`) Edit 저장이 동작하지 않는다. Windows면 `start http://127.0.0.1:8765/topics/<slug>/overview.html`로 기본 브라우저를 대신 열어 준다

## 2. Edit 패치 형식

브라우저가 `/save`로 보내는 마크다운이다. 저장이 실패하면 같은 내용이 클립보드로 복사되니, 사용자가 대화창에 붙여 넣으면 Claude가 직접 반영한다.

```markdown
# Overview edits — 덱 제목 (2 changes)

## Slide 2 (title-bullets)
- .deck-footer
  OLD: 덱 이름
  NEW: 덱 이름 · 2026

## Slide 3 (stat)
- .chip
  NTH: 2
  OLD: 같은 문구
  NEW: 바뀐 문구
```

- `- 셀렉터`: 요소의 클래스(`.a.b`) 또는 태그 이름
- `NTH`: 같은 장면에 같은 셀렉터·같은 문구가 여럿일 때 몇 번째인지(1부터). 하나뿐이면 생략
- 서버는 `data-slide="N"` 장면 안에서만 찾는다(다른 장면의 같은 문구는 건드리지 않는다)

## 3. 서버 응답과 대응

| 코드 | 뜻 | 대응 |
|---|---|---|
| 200 | 모두 반영 | 없음 |
| 409 | 일부만 반영 | 실패 목록(장면·셀렉터·이유)을 보고 Claude가 나머지를 직접 고친다 |
| 422 | 하나도 반영 못 함 | 대부분 파일이 그사이 바뀐 경우. 새로고침 후 다시 Edit하거나 붙여 넣은 패치를 Claude가 반영 |
| 400 | 다른 topic 페이지 또는 형식 오류 | 서버를 올바른 topic으로 다시 띄운다 |

실패 이유: `장면 없음` / `OLD 문구를 찾지 못함` / `ambiguous: 같은 문구 N곳, NTH 필요` / `NTH 범위 밖`

저장 직전 `overview.html.bak` 한 개가 남는다. 잘못 저장했으면 그것으로 되돌린다.

## 4. Aim 요청 처리

사용자가 `[data-slide="3"] > div.stats > div.stat:nth-of-type(2) > span.stat-value` 같은 셀렉터와 함께 요청하면:

1. `data-slide="3"` 여는 태그를 찾아 그 `<section>` 안에서만 요소를 찾는다.
2. 문구 수정이면 Edit 도구로 그 요소만 고친다. 같은 자리의 alt·aria-label도 함께 본다.
3. 모양 수정이면 가능한 한 scene-styles의 장면 범위 CSS(`[data-slide="3"] .stat:nth-of-type(2) …`)로 고친다. 덱 전체에 해당하면 CSS 패치 파일로.
4. `build_present.py` → `validate_topic.py` → `qa_check.mjs --slides 3` → `export_pdf.mjs topics/<slug> --shots-only`.
5. **고친 장면의 `_work/shots/slide-NN.png`를 Read 도구로 직접 연다.** 폴더 목록(`ls`)만 보거나 qa_check 통과로 갈음하지 않는다. 볼 것: 표지(불릿 점·선)와 본문 겹침, 고아 줄바꿈(`발/표자`처럼 한두 글자만 다음 줄), 세로 무게 중심, 빈 여백 덩어리. 문제가 보이면 고치고 4~5를 다시 한다.
6. 무엇을 바꿨는지와 스크린샷에서 확인한 것을 한두 줄로 보고한다.

이유: 장면 타입을 바꾸면(예: 불릿 → compare) 새 CSS가 처음 화면에 찍힌다. P7 iteration-1에서 스크린샷을 찍고도 열어 보지 않아 표지 `—`가 본문을 덮은 채 보고됐다. 수정 요청은 작아 보여도 눈 검수를 건너뛰지 않는다.

## 4-b. 이미지를 넣거나 바꾸는 요청

"여기 사진 넣어줘", "이 캡처로 바꿔줘", "책 표지 찾아서 넣어줘"는 `references/images.md`를 따른다. 웹에서 찾은 이미지는 후보를 보여 주고 승인받은 것만 넣는다. 넣은 뒤 `qa_check`의 `이미지 축소 과다`를 보고, 스크린샷을 Read로 열어 이미지 속 글자가 읽히는지 확인한다.

## 5. file://로 열었을 때

서버 없이 파일을 직접 열면 저장 서버가 없으므로 Done 시 패치가 곧바로 클립보드로 간다. 발표자 창 동기화도 막힐 수 있다. 가능하면 서버로 연다.
