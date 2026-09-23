# ppt-maker evals

`evals.json`은 skill-creator 평가 루프용 케이스 3개다. 자동 실행(`claude -p`)에는 AskUserQuestion이 없으므로 케이스 1·2는 SKILL.md 4절 1항 **무인 경로**를 기준으로 판정한다. 사람 세션에서만 확인할 수 있는 기대는 `manual-checklist.md`로 분리했다.

| 파일 | 내용 |
|---|---|
| `evals.json` | 케이스·프롬프트·expectations(skill-creator 스키마 그대로, 임의 키 없음) |
| `rubric.md` | 덱 품질 루브릭 7항목(1~5점). grader가 매기고 벤치마크에 별도 열로 싣는다 |
| `manual-checklist.md` | 사람 세션 라이브 런 확인 항목(게이트 A·C) |

기준 덱(유형별 "이런 느낌" 방향 표본)은 사내 경로를 포함하므로 plugin 밖 저장소 문서 `docs/p7-reference-decks.md`에 둔다. 정답이 아니라 블라인드 비교·루브릭 채점의 참고 자료다.

## 판정 규칙

- **스크립트**: 채점기가 파일·값·transcript 이벤트로 참/거짓을 정한다. 근거(evidence)에 파일 경로·값·이벤트 순번을 적는다.
- **스크립트+grader**: 스크립트가 참/거짓을 못 정하면 `passed: null`로 두고 grader가 transcript·산출물을 읽어 채운다.
- **grader**: 처음부터 사람 판단이 필요한 항목.

대상 topic은 run의 `workdir/topics/`(claude가 작업한 폴더) 아래 BRIEF.md가 있는 폴더 중 입력으로 복사하지 않은 것(케이스 3은 `_sample`)이다. 없으면 topic 관련 항목은 모두 거짓.

### 케이스 1 — edu 8장, 디자인 지정

| # | expectation | 방법 | 규칙 |
|---|---|---|---|
| 1 | 새 topic의 BRIEF.md가 있고 type이 edu, slide_count가 8이다 | 스크립트 | BRIEF front matter `type == edu`, `slide_count == 8`(내용 장수) |
| 2 | BRIEF의 design_source가 DESIGN-Notion.md를 가리킨다 | 스크립트 | `design_source` 값에 `DESIGN-Notion.md` 포함 |
| 3 | BRIEF 확정 근거에 무인 실행 표기가 있고 _work/decisions.md에 [확인 필요] 항목이 1개 이상 있다 | 스크립트 | BRIEF 본문에 `무인` 포함 + decisions.md에 `[확인 필요]` ≥ 1 |
| 4 | overview.html 생성이 BRIEF status: confirmed 기록보다 뒤에 온다(게이트 A 순서) | 스크립트+grader | transcript에서 BRIEF에 `status: confirmed`를 쓴 첫 도구 호출 순번 < overview.html을 만든 첫 도구 호출(`scaffold_overview.py` 실행 또는 overview.html Write) 순번. 둘 중 하나를 못 찾으면 null |
| 5 | edu-designer·content-writer·domain-expert·deck-reviewer 서브에이전트 호출이 transcript에 있다 | 스크립트 | Agent(Task) 도구 입력 `subagent_type`에 네 이름이 모두 나온다 |
| 6 | S02가 목차 장면이고 모든 .scene-title이 명사형이며 S01 밖 구간 표지(title 타입) 장면과 내용 장면 .eyebrow 구간 n/N 표시가 있다 | 스크립트+grader | S02 제목·eyebrow에 `목차`·`차례`·`강의/오늘의 순서`·`흐름`·`Agenda`·`Contents` 같은 구(없으면 null). 제목이 서술형 어미(`다`·`요`·`니다`·`까` 등)로 끝나면 거짓. S01·마지막 장면 밖에 `data-skill="title"` 장면 ≥ 1. S01·S02·마지막·title 장면을 뺀 내용 장면 `.eyebrow`에 `n/N` |
| 7 | 내용 장면(S01 표지·구간 표지 제외)이 8장이다 | 스크립트 | `data-skill != title` 장면 수 == 8. 요청 장수는 내용 장수(storyboard.md 2절) |
| 8 | validate_topic.py가 통과하고 _work/qa_check.json의 높음이 0건이다 | 스크립트 | `validate_topic.py` exit 0 + qa_check.json 높음 0(파일 없으면 거짓) |
| 9 | BRIEF export_approved가 명시적으로 false이고 PDF·PPTX 파일이 없다(게이트 C) | 스크립트 | BRIEF `export_approved == false`(없으면 거짓) + workdir 전체에 `*.pdf`·`*.pptx` 0개 |

### 케이스 2 — reading 12장, 디자인 미지정, "그냥 바로"

덱 본문 판정(4~7)은 형식 무관이다: topic의 overview.html이 있으면 그 장면, 없으면 workdir의 `*.html` 장면·`*.pptx` 슬라이드(노트 포함)를 본다. PDF 텍스트는 표준 라이브러리로 뽑을 수 없어 보지 않는다.

| # | expectation | 방법 | 규칙 |
|---|---|---|---|
| 1 | 새 topic의 BRIEF.md가 있고 type이 reading, slide_count가 12다 | 스크립트 | front matter 값 |
| 2 | 디자인을 조용히 고르지 않는다: _work/decisions.md에 디자인·팔레트 선택이 [확인 필요]로 기록된다 | 스크립트 | decisions.md의 한 줄(표 행)에 `[확인 필요]`와 `디자인`·`팔레트`·`palette` 중 하나가 함께 있다 |
| 3 | overview.html 생성이 BRIEF status: confirmed 기록보다 뒤에 온다(게이트 A 순서) | 스크립트+grader | 케이스 1-4와 같음 |
| 4 | 책 쪽수를 지어내지 않는다: 덱 본문(HTML·PPTX)에 p.NN 쪽수가 없거나, 있으면 [확인 필요] 표시와 함께다 | 스크립트+grader | 장 본문·노트에 `p.\s?\d+` 없음 → 참. 있으면 그 장에 `확인 필요`가 있을 때 참, 없으면 null(책 원문 대조는 grader) |
| 5 | 발제 질문 3개가 덱 본문(HTML·PPTX) 또는 스토리보드에 그대로 있다 | 스크립트 | 공백을 무시하고 `트라우마는 존재하지 않는가`·`인정 욕구를 버릴 수 있는가`·`지금 여기를 산다는 것은`이 모두 있다 |
| 6 | 첫 발제 질문 장보다 앞에 저자를 다루는 책 소개 장이 있다 | 스크립트 | 발제 장 = 질문을 하나만 담은 첫 장(표지·목차는 셋을 모두 나열하므로 제외). 그보다 앞(첫 장 제외)에 `저자`·`지은이`·저자 이름이 나오는 장 ≥ 1 |
| 7 | 책 표지·저자 등 이미지 또는 이미지 자리표시가 1곳 이상 있다 | 스크립트 | 장 마크업에 `<img`, `class="…placeholder…"`, PPTX `<p:pic` 중 하나 |
| 8 | S02가 목차 장면이고 모든 .scene-title이 명사형이며 S01 밖 구간 표지(title 타입) 장면과 내용 장면 .eyebrow 구간 n/N 표시가 있다 | 스크립트+grader | 케이스 1-6과 같음 |
| 9 | BRIEF export_approved가 명시적으로 false이고 PDF·PPTX 파일이 없다(게이트 C) | 스크립트 | 케이스 1-9와 같음 |

### 케이스 3 — 기존 덱 장면 수정

입력 원본은 러너가 `inputs_snapshot/`(workdir 밖)에 따로 둔다. 복사할 때 `exports/*.pdf`·`*.pptx`·`_work/shots/`는 빼므로 export 여부를 파일 유무로 판정할 수 있다.

| # | expectation | 방법 | 규칙 |
|---|---|---|---|
| 1 | 2번 장면이 compare 마크업(.compare-grid > .compare-col > .compare-heading + ul.compare-list)이고 제목이 정확히 '세 가지 확인 방법'이다 | 스크립트 | `.compare-grid` 있음 + `.compare-col` ≥ 2개가 모두 `.compare-heading`과 `ul.compare-list`를 가짐 + `.scene-title` 텍스트 == `세 가지 확인 방법` |
| 2 | 원본 2번 장면의 불릿 문구가 모두 2번 장면에 그대로 남아 있다 | 스크립트 | 원본 2번 장면 `li` 문구 각각이 공백 무시하고 새 2번 장면 본문에 있다 |
| 3 | 2번 장면의 data-scene-id S02와 speaker-note가 유지된다 | 스크립트 | `data-scene-id == S02` + `.speaker-note` 텍스트가 원본과 같다 |
| 4 | 1·3번 장면 HTML이 바뀌지 않는다 | 스크립트 | 섹션 HTML을 공백 정규화해 원본과 비교 |
| 5 | 2번 장면 qa_check 높음이 0건이다(표지 겹침 포함) | 스크립트 | 임시 사본에서 `build_present.py` → `qa_check.mjs --slides 2`. 높음 0건(iteration-1의 `—` 표지 겹침을 잡는다) |
| 6 | overview.html을 마지막으로 고친 뒤 스크린샷을 열어 확인했다 | 스크립트 | overview.html을 고친 마지막 Edit/Write 뒤에 이미지 파일 Read 또는 screenshot 도구 호출이 있다 |
| 7 | 새로 export하지 않는다 | 스크립트 | `exports/*.pdf`·`*.pptx` 0개 |

## 실행

도구는 저장소 루트 `tools/evals/`(배포 제외)에 있다. 사용법은 `tools/evals/README.md`.
