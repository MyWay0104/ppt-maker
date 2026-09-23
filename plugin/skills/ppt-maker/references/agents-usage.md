# agents-usage — 서브에이전트 사용법

플러그인으로 설치하면 에이전트 이름 앞에 `ppt-maker:`가 붙는다(예: `ppt-maker:domain-expert`).

## 1. 공통 규약

- 호출 프롬프트 첫 줄은 항상 `topic: topics/<slug>`
- 에이전트는 topic의 `docs/agent-context.md`가 있으면 가장 먼저 읽는다(도메인 고정 정보)
- 장면 하나를 끝낼 때마다 출력 파일에 덧붙여 저장한다(중단돼도 이어서)
- overview.html은 고치지 않는다. 예외는 `build-rules.md` 6절
- 동시 실행은 3개 이하
- 작은 문구 수정은 멈춘 에이전트를 깨우지 말고 메인이 직접 고친다

## 2. 에이전트 7개

| 에이전트 | 단계 | 입력 | 출력 |
|---|---|---|---|
| `intake-router` | 0 intake | 사용자 요청 요약, 참고자료 경로, DESIGN.md | BRIEF.md 본문 초안 + 미확정 질문 |
| `edu-designer` | 1 스토리보드(edu) | BRIEF.md | `_work/storyboard.md`(역방향 설계, 인지부하·시간 검토) |
| `domain-expert` | 1·3 검토 | `domain`, `role`, `input`, `output` | `_work/review/<이름>.md` |
| `content-writer` | 3 문구 | storyboard, visual_plan, BRIEF 4절 | `_work/copy/<B>.md` |
| `slide-designer` | 2 시각 계획 | DESIGN.md, storyboard | `_work/visual_plan.md` |
| `slide-builder` | 4 빌드(>20장) | `assets/briefs/builder.md` 채운 지시문 | `_work/blocks/<B>.html` |
| `deck-reviewer` | 3 pre / 5 post | copy 또는 shots + dump | `_work/review/<B>-pre.md` / `-post.md` |

## 3. 호출 예

```text
topic: topics/python-basics-edu
domain: Python
role: 코드 검토
input: topics/python-basics-edu/_work/copy/B1.md
output: topics/python-basics-edu/_work/review/B1-python.md
장면 S04~S09의 예제 코드가 Python 3.12에서 그대로 실행되는지, 변수 이름이 설명과 맞는지 본다.
```

`role` 값: `코드 검토` / `사실 검증` / `개념 순서`

## 4. 도메인 전문가 만들기 (자주 쓰는 분야)

1. `assets/agent-domain-expert.md`를 복사해 `{{DOMAIN}}`, `{{ROLE}}`, `{{FIXED_CONTEXT}}`, `{{CHECKLIST}}`를 채운다.
2. 프로젝트의 `.claude/agents/<domain>-expert.md`로 저장한다(플러그인 폴더가 아니라 사용자 프로젝트에).
3. 사용자에게 알린다: "새 에이전트는 다음 세션부터(또는 `/agents` 새로고침 후) 보입니다. 지금은 `domain-expert`에 domain 인자로 진행할까요?"

## 5. 지시문 템플릿 (`assets/briefs/`)

| 파일 | 쓰는 곳 |
|---|---|
| `builder.md` | `slide-builder`에게 BLOCK 조각을 맡길 때 |
| `review-pre.md` | 빌드 전 문구·배치 수정안 검토 |
| `review-final.md` | 사용자 검토 직전 마지막 검토(시각 A·B + 내용) |

`{{ }}`를 모두 채워서 준다. 채우지 못한 칸이 있으면 부르지 말고 먼저 정한다.
