# ppt-maker

**순수 HTML/CSS/JS로 16:9 발표자료를 만드는 Claude Code 플러그인**입니다.
"발표자료 만들어줘"라고 말하면 Claude가 질문으로 요구사항을 정리한 뒤 목업을 만들고, 브라우저에서 고치고, 발표하고, PDF까지 뽑아 줍니다.

```
intake 질문 → BRIEF.md 확정 → overview.html 목업 → Aim/Edit 검토 → QA → present.html(발표자 뷰) → PDF
```

- 교육 교안, 독서모임 리딩자료·발제문, 세미나·일반 발표에 맞춘 규칙이 들어 있습니다.
- 파워포인트 없이 브라우저 하나로 발표합니다. 글꼴(Paperlogy·JetBrains Mono)이 함께 들어 있어 인터넷 없이도 똑같이 보입니다.
- 사용자가 승인해야 다음 단계로 넘어가는 **게이트 3개**가 있어서, Claude가 멋대로 끝까지 만들어 버리지 않습니다.

## 목차

1. [필요한 것](#1-필요한-것)
2. [설치](#2-설치)
3. [빠른 시작](#3-빠른-시작)
4. [전체 흐름과 게이트](#4-전체-흐름과-게이트)
5. [검토 루프: Aim과 Edit](#5-검토-루프-aim과-edit)
6. [발표하기](#6-발표하기)
7. [PDF·PPTX 내보내기](#7-pdfpptx-내보내기)
8. [이미 만든 덱 고치기](#8-이미-만든-덱-고치기)
9. [구성 요소](#9-구성-요소)
10. [업데이트·삭제](#10-업데이트삭제)
11. [문제 해결](#11-문제-해결)
12. [개발자용: 검사와 평가](#12-개발자용-검사와-평가)
13. [라이선스](#13-라이선스)

## 1. 필요한 것

| 항목 | 버전 | 쓰는 곳 |
|---|---|---|
| [Claude Code](https://code.claude.com/docs) | 2.1.280에서 확인 | 플러그인 실행 |
| Node.js | 18 이상 (24.15에서 확인) | QA·스크린샷·PDF·PPTX (Playwright Chromium) |
| Python | 3 (3.11.9에서 확인) | topic 생성·검증·검토 서버. 표준 라이브러리만 써서 `pip install`은 필요 없습니다 |
| 브라우저 | Chrome·Edge 등 | 검토·발표 |

Windows 11에서 개발하고 확인했습니다. macOS·Linux에서도 같은 명령으로 동작하도록 만들었지만 직접 확인하지는 않았습니다.

## 2. 설치

Claude Code 안에서 두 줄을 입력합니다.

```
/plugin marketplace add MyWay0104/ppt-maker
/plugin install ppt-maker@ppt-maker
```

- 첫 줄은 이 GitHub 저장소를 "플러그인 가게(마켓플레이스)"로 등록하고, 둘째 줄은 그 가게에서 `ppt-maker`를 설치합니다.
- 터미널에서 하려면 `claude plugin marketplace add MyWay0104/ppt-maker` → `claude plugin install ppt-maker@ppt-maker`를 씁니다.
- 설치가 끝나면 Claude Code를 다시 시작하거나 `/reload-plugins`를 입력합니다.

### Node 의존성 (처음 한 번)

PDF·QA에 쓰는 Playwright와 Chromium이 필요합니다. **처음 덱을 만들 때 Claude가 스스로 설치**하므로 보통은 아무것도 안 해도 됩니다. 직접 설치하려면 설치된 플러그인 폴더에서 실행합니다.

```bash
# 설치 위치: <Claude 설정 폴더>/plugins/cache/ppt-maker/ppt-maker/<버전>/
#   Windows  %USERPROFILE%\.claude\plugins\cache\ppt-maker\ppt-maker\1.0.0
#   macOS/Linux  ~/.claude/plugins/cache/ppt-maker/ppt-maker/1.0.0
S=~/.claude/plugins/cache/ppt-maker/ppt-maker/1.0.0/skills/ppt-maker/scripts
npm install --prefix "$S"
npx --prefix "$S" playwright install chromium
```

> 플러그인을 새 버전으로 업데이트하면 폴더 이름(`<버전>`)이 바뀌므로 위 설치를 한 번 더 합니다(Claude에게 맡겨도 됩니다).

### 권한 요청 줄이기 (선택)

기본 권한 설정에서는 Claude가 플러그인 폴더의 스크립트를 읽고 `python`·`node`로 실행할 때마다 **승인 창**이 뜹니다. 기본 설정으로 "QA 돌려줘"를 한 번 요청해 보니 승인 요청이 5번 나왔습니다(플러그인 폴더 읽기 2번, 명령 실행 3번).

- 승인 창에서 **"다시 묻지 않기"** 옵션을 고르면 같은 종류의 요청은 다음부터 뜨지 않습니다.
- 플러그인 폴더 **읽기** 승인은 덱 폴더의 `.claude/settings.json`에 플러그인 설치 폴더를 **절대 경로**로 적어 두면 뜨지 않습니다(절대 경로로 직접 확인함. `~` 표기는 확인하지 않음).
  ```json
  {
    "permissions": {
      "additionalDirectories": ["C:/Users/<사용자>/.claude/plugins/cache/ppt-maker"]
    }
  }
  ```
- `python`·`node` **실행**을 미리 허용하는 규칙(`"allow": ["Bash(python *)", "Bash(node *)"]`)은 비대화형 시험(`claude -p`)에서는 효과를 확인하지 못했습니다. 대화형으로 쓸 때 위의 "다시 묻지 않기"를 쓰는 것을 권합니다.

## 3. 빠른 시작

1. 덱을 모아 둘 **빈 폴더**를 만들고 그 폴더에서 Claude Code를 엽니다. 덱은 그 아래 `topics/<이름>/`에 생깁니다.
2. 이렇게 말합니다.
   ```
   "LLM의 원리와 활용사례" 발표자료 8장 만들어줘
   ```
   "발표자료·슬라이드·PPT·교안·발제문" 같은 말이면 파일 형식을 말하지 않아도 `ppt-maker` 스킬이 뜹니다. 직접 부르려면 `/ppt-maker:ppt-maker`.
3. Claude가 **질문 2라운드**를 합니다(자료 유형·청중·목적 → 장수·톤·디자인·스토리라인·발표자 노트 등). 답하면 요약(BRIEF)을 보여 주고 승인을 묻습니다.
4. 승인하면 스토리보드 → 문구 → 빌드 → QA가 이어지고, 끝나면 **검토 주소**를 알려 줍니다.
5. 브라우저에서 고치고(5절), 마음에 들면 **"최종 확인"**이라고 말합니다. 발표 파일과 PDF가 나옵니다.

> "알아서 해줘"라고 해도 질문은 건너뛰지 않고 수만 줄입니다. 주제만 보고 만들면 청중·목적이 어긋난 초안이 나오고, 그걸 고치는 비용이 질문 몇 개보다 크기 때문입니다.

### 디자인 지정

- 내장 팔레트 9종 중에서 고르거나(질문할 때 추천이 나옵니다), [getdesign.md](https://getdesign.md) 형식의 `DESIGN-*.md` 파일을 주면 그 색·글꼴 느낌을 옮깁니다.
  ```
  발표자료 10장 만들어줘. 디자인은 design-inputs/DESIGN-Notion.md 써줘.
  ```
- "색이 답답해", "좀 더 세련되게" 같은 요청은 `deck-design` 스킬이 받습니다.

## 4. 전체 흐름과 게이트

| 단계 | 하는 일 | 결과물 (`topics/<이름>/`) |
|---|---|---|
| 0. intake | 질문으로 요구사항 정리 | `BRIEF.md` |
| 1. 스토리보드 | 목차·구간·장면 순서 | `_work/storyboard.md` |
| 2~3. 시각 계획·문구 | 장면 타입 결정, 문구 작성 → 사실 검증 → 사전 검토 | `_work/` |
| 4. 빌드 | 장면 HTML 작성 | `overview.html` |
| 5. QA | 넘침·겹침·명암비·글자 크기 자동 검사 + 스크린샷 눈 검수 | `_work/qa_check.json`, `_work/shots/` |
| 6. 검토 | Aim/Edit로 사용자가 고침 | `overview.html` |
| 7. 내보내기 | 발표 파일·PDF·PPTX | `present.html`, `exports/` |

**게이트**는 스크립트가 직접 막는 관문입니다. Claude가 규칙을 잊어도 스크립트가 거부합니다.

| 게이트 | 열리는 조건 | 막는 것 |
|---|---|---|
| A | 사용자가 BRIEF 요약을 **승인** | 승인 전에는 `overview.html`을 만들지 않음 |
| B | QA "높음" 문제 0건 | 그 전에는 사용자에게 검토를 요청하지 않음 |
| C | 사용자가 정확히 **"최종 확인"**이라고 말함 | 그 전에는 PDF·PPTX를 내보내지 않음. "PDF 뽑아줘"는 요청이지 확인이 아니라서 Claude가 되묻습니다 |

## 5. 검토 루프: Aim과 Edit

1. Claude가 검토 서버를 띄우고 주소를 알려 줍니다. **주소를 복사해 브라우저 주소창에 붙여 넣습니다.**
   ```
   http://127.0.0.1:8765/topics/<이름>/overview.html
   ```
   파일 탐색기에서 `overview.html`을 더블클릭해 열면(`file://`) 보이기는 해도 **Edit 저장이 안 됩니다.** 서버를 거쳐야 저장 요청이 파일에 닿습니다.
2. **Edit**: 화면 위 `Edit` 버튼 → 글자를 고치고 `Done`. 바로 파일에 저장되고 직전 판은 `overview.html.bak`으로 남습니다.
3. **Aim**: `Aim` 버튼 → 고칠 요소를 클릭하면 그 요소의 선택자가 복사됩니다 → 대화창에 붙여 넣고 말합니다.
   ```
   [data-slide="3"] > .stats  이거 조금 더 크게
   ```
   Claude는 그 요소만 새 CSS 파일(`_work/slide_ui/0N_*.css`)로 고치고 QA를 다시 돌립니다. 원래 CSS는 건드리지 않아서 되돌리기 쉽습니다.
4. 만족하면 **"최종 확인"**이라고 말합니다.

## 6. 발표하기

1. 같은 서버에서 `http://127.0.0.1:8765/topics/<이름>/present.html`을 엽니다.
2. 키

   | 키 | 동작 |
   |---|---|
   | `→` `Space` / `←` | 다음 / 이전 |
   | `Home` / `End` | 처음 / 끝 |
   | `F` | 전체 화면 |
   | `S` | 발표자 창(현재·다음 장면, 노트, 타이머, 시계) |
   | `Esc` | 전체 화면 해제 |

3. 다른 PC로 가져갈 때는 **폴더째** 복사합니다. `present.html` 한 파일만 가져가면 글꼴이 그 PC 기본 글꼴로 바뀌어 줄바꿈이 달라지고 글자가 넘칠 수 있습니다.
   ```
   가져갈 폴더/
   ├── present.html
   └── assets/
       ├── fonts/   ← 글꼴 + fonts.css
       └── img/     ← 이미지를 넣었다면
   ```

`present.html`은 `overview.html`에서 만들어지는 파일이라 직접 고치지 않습니다. 고칠 때는 항상 `overview.html`(검토 화면)에서 고칩니다.

## 7. PDF·PPTX 내보내기

"최종 확인" 뒤에 Claude가 실행합니다. 직접 할 때는 다음과 같습니다(`$S`는 2절의 scripts 폴더).

```bash
python "$S/build_present.py" topics/<이름>          # present.html 다시 만들기
node   "$S/export_pdf.mjs"   topics/<이름>          # → exports/<이름>.pdf
node   "$S/export_pptx.mjs"  topics/<이름>          # → exports/<이름>.pptx (장면 그림 + 발표자 노트)
node   "$S/export_pdf.mjs"   topics/<이름> --shots-only   # 검수용 스크린샷만(게이트 C 불필요)
```

- PDF는 장면 수와 같은 쪽수(1920×1080)로 나오고 글꼴이 파일 안에 들어가서 어느 PC에서나 같게 보입니다.
- `BRIEF.md`에 `export_approved: true`가 없으면 스크립트가 exit 4로 거부합니다(게이트 C).

## 8. 이미 만든 덱 고치기

덱 폴더가 있는 곳에서 말하면 됩니다.

```
topics/my-deck 덱에서 [data-slide="2"] > ul.bullets 이 부분을 compare 장면으로 바꿔줘
3번 장면 제목을 '세 가지 확인 방법'으로 고쳐줘
6쪽 카드가 위로 쏠려 보여
```

장면 타입을 바꾸면 기존 문구는 글자 그대로 새 구조로 옮기고, 스크린샷을 직접 열어 확인한 뒤에 보고합니다.

**장면 타입 11종**: `title` · `title-bullets` · `title-image` · `title-tags` · `split` · `stat` · `steps` · `compare` · `evolution-flow` · `quote` · `kindergarten-notice`. 각 타입의 마크업은 `plugin/skills/slide-types/references/`에 있습니다.

`topics/_sample/`은 3장짜리 예시 덱입니다. 이 저장소를 clone했다면 `python plugin/skills/ppt-maker/scripts/serve_live.py topics/_sample` 로 바로 열어 볼 수 있습니다.

## 9. 구성 요소

```
plugin/
├── .claude-plugin/plugin.json
├── skills/
│   ├── ppt-maker/      ← 전체 흐름 오케스트레이터 (/ppt-maker:ppt-maker)
│   │   ├── scripts/    ← topic 생성·검증·검토 서버·QA·PDF·PPTX 스크립트
│   │   ├── references/ ← intake·스토리보드·빌드·QA·검토 루프 절차
│   │   └── assets/     ← 템플릿·장면 기본 CSS·유형별 규칙(edu/reading/general)
│   ├── slide-types/    ← 장면 타입 11종 마크업과 타입 변경 절차
│   └── deck-design/    ← 색·글꼴·여백 디자인 지식, 팔레트 9종, 오프라인 글꼴
├── agents/             ← 서브에이전트 7종
└── evals/              ← claude plugin eval 회귀 시험
```

| 서브에이전트 | 역할 |
|---|---|
| `intake-router` | 요청·참고자료·DESIGN 파일을 읽고 BRIEF 초안과 미확정 질문 목록 작성 |
| `edu-designer` | 교육 교안의 교수설계(학습 목표 → 확인 방법 → 활동) |
| `content-writer` | 장면 문구·발표자 노트 작성 |
| `domain-expert` | 분야 전문가 관점의 사실 검증 |
| `slide-designer` | DESIGN을 색 토큰으로 옮기고 장면별 타입·배치·글자 크기 계획 |
| `slide-builder` | 20장이 넘는 덱을 6~10장 묶음으로 나눠 장면 HTML 작성 |
| `deck-reviewer` | 사전·사후 검토(스크린샷 눈 검수 포함) |

## 10. 업데이트·삭제

터미널에서 실행합니다(Claude Code 안에서는 `/plugin` 화면에서 같은 일을 할 수 있습니다).

```bash
claude plugin marketplace update ppt-maker      # 가게 목록 새로 받기
claude plugin update ppt-maker@ppt-maker        # 플러그인 새 버전 설치
claude plugin uninstall ppt-maker@ppt-maker     # 삭제
```

업데이트 뒤에는 2절의 Node 의존성 설치를 한 번 더 합니다. 변경 내용은 [`plugin/CHANGELOG.md`](plugin/CHANGELOG.md)에 있습니다.

## 11. 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| Edit로 고친 게 저장되지 않음 | `file://`로 열었음 | 검토 서버 주소(`http://127.0.0.1:8765/...`)로 엽니다 |
| PDF 명령이 exit 4 | 게이트 C가 닫혀 있음 | 검토를 마치고 "최종 확인"이라고 말합니다 |
| 덱 만들기가 exit 3 | 게이트 A(BRIEF 승인 전) | 질문에 답하고 BRIEF를 승인합니다 |
| `Cannot find package 'playwright'` | Node 의존성 없음 | 2절 "Node 의존성"을 실행합니다 |
| `Executable doesn't exist ... chromium` | Chromium 미설치 | `npx --prefix "$S" playwright install chromium` |
| 다른 PC에서 글자가 넘침 | `present.html`만 복사함 | `assets/` 폴더째 복사합니다 |
| 기호(화살표 등)가 PC마다 다르게 보임 | Paperlogy에 없는 글자는 그 PC의 글꼴로 그려짐 | `→` `↔`처럼 Paperlogy에 있는 기호를 씁니다 |
| 스킬이 뜨지 않음 | 설치 뒤 다시 읽지 않음 | `/reload-plugins` 또는 Claude Code 재시작, `/plugin`에서 사용(enabled) 상태 확인 |

## 12. 개발자용: 검사와 평가

이 저장소를 clone해서 고칠 때 쓰는 명령입니다.

```bash
claude --plugin-dir ./plugin                      # 설치 없이 이 폴더의 플러그인으로 실행(/reload-plugins로 변경 반영)
claude plugin validate ./plugin                   # 플러그인 구조 검사
claude plugin validate .                          # 마켓플레이스 검사
python -m unittest discover -s plugin/skills/ppt-maker/scripts/tests   # 회귀 테스트
```

### 회귀 시험 (claude plugin eval)

`plugin/evals/scene-edit/`는 "샘플 덱 2번 장면을 compare 타입으로 바꾸기"를 3회 실행하고, 플러그인이 있을 때와 없을 때를 비교해 채점합니다(1회 약 $0.5).

```bash
claude plugin eval ./plugin --scaffold --allow-tools Edit Write --threshold 0.8
```

| 채점 항목 | 방식 |
|---|---|
| compare 마크업, 제목, 원문 불릿 3개 보존, 장면 ID·발표자 노트 유지, 1·3번 장면 불변 | 파일 정규식 |
| PDF·PPTX를 멋대로 내보내지 않음 | 파일 없음 확인 |
| 돌리지 못한 QA를 통과했다고 말하지 않음 | LLM 판정 |
| 플러그인 스킬이 불렸는지 | 도구 호출 지표(점수 제외) |

- `--scaffold`는 케이스의 `fixture.sh`(샘플 덱을 작업 폴더에 까는 스크립트)를 실행합니다. Windows에서는 Git Bash가 필요합니다.
- **Windows 네이티브에서는 Bash 권한을 주는 eval이 돌지 않습니다**(샌드박스 미지원). 그래서 이 케이스는 Bash 없이 파일 수정만 채점하고, QA 스크립트 결과는 채점하지 않습니다. WSL2나 Linux·macOS에서는 Bash를 허용해 QA까지 넣을 수 있습니다.

## 13. 라이선스

- 플러그인 코드와 문서: [MIT](LICENSE)
- 글꼴: [SIL Open Font License 1.1](plugin/skills/deck-design/assets/fonts/OFL.txt)
  - Paperlogy — Copyright © 2024 PT& ([공식 페이지](https://freesentation.blog/paperlogyfont))
  - JetBrains Mono — Copyright 2020 The JetBrains Mono Project Authors ([GitHub](https://github.com/JetBrains/JetBrainsMono))
