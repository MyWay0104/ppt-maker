# 사전 검토 지시문 템플릿 (빌드 전)

`deck-reviewer`에게 준다(mode: pre). **적용 전 수정안(문구·배치)**을 보는 단계다.

---

topic: topics/{{SLUG}}
mode: pre

너는 deck-reviewer다. `{{TITLE}}` 발표자료에 적용할 수정안을 **적용 전에** 검토한다.

## 읽을 것

1. 문구: `topics/{{SLUG}}/_work/copy/{{BLOCK}}.md`
2. 배치: `topics/{{SLUG}}/_work/visual_plan.md` (있으면)
3. 원문 대조가 필요할 때만: `python ${CLAUDE_SKILL_DIR}/scripts/deck/dump_deck_text.py topics/{{SLUG}}` 결과
4. `topics/{{SLUG}}/BRIEF.md` 4절(사실 경계)·5절(지킬 것), `deck-rules.json`

## 이번 수정 요청 (검토 기준)

{{사용자 요청을 번호로 적는다}}

## 볼 것

1. 문장이 자연스럽고 장면 사이 말투가 일관된가(BRIEF `tone`)
2. 제목이 장면 내용을 정확히 대표하는가, 비슷한 제목이 겹치지 않는가
3. 활동·실습 안내가 따라 하기 쉬운가(순서, 주체, 끝맺음), 노트가 대본으로 자연스러운가
4. 사실 경계가 유지되는가, 새로 틀린 정보가 생기지 않았는가
5. 하우스 룰 위반이 남지 않는가(`deck-rules.json`)
6. 지운 문장이 있다면 앞뒤 의존(예고–회수, 정의–되짚기)이 끊기지 않았는가

## 출력

`topics/{{SLUG}}/_work/review/{{BLOCK}}-pre.md`

- "## 수정 요청" 표: 번호 · 장면 · 현재(수정안 문구) · 요청(정확한 새 문구) · 필수/권장 · 이유
- "## 보류(사용자 확인)"
- 끝에 "수정 필요: 필수 N · 권장 N"

장면 하나를 끝낼 때마다 출력 파일에 덧붙여 저장한다.
