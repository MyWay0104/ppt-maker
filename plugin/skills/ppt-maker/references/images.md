# images — 이미지 자리표시·웹 후보·논문 그림·교체

실물 이미지(책 표지, 인물 사진, 제품·화면 캡처, 논문 그림)는 도식보다 설명을 빨리 끝낸다. 대신 **틀린 이미지**(동명이인 사진, 다른 판본 표지, 쓸 수 없는 이미지)는 발표에서 가장 눈에 띄는 오류다. 그래서 이미지는 항상 **후보 → 사용자 승인 → 넣기** 순서로 다룬다. 스킬이 고른 이미지를 승인 없이 덱에 넣지 않는다.

## 1. 자리표시 (스토리보드·빌드)

- 스토리보드 시각 요소 열에 `[이미지 자리: 무엇]`으로 적는다(storyboard.md 2절).
- 빌드는 `<div class="image-frame placeholder" data-asset="책 표지"><span>책 표지 이미지</span></div>`. 옅은 배경 + 점선 테두리 + 가운데 설명 글자(24px 이상). 비율은 실물에 맞춘다(책 표지 2:3, 인물 1:1 또는 3:4, 화면 캡처 16:9, 논문 그림은 원본 비율).
- 남은 자리는 완료 보고의 "자산 대기" 목록에 적는다. 발표 전에 채우지 못하면 자리표시를 지우지 말고 사용자에게 알린다(지우면 보고 대상).

## 2. 웹 이미지 후보 (책 표지·인물 사진·제품 사진)

사람이 있는 세션에서만 넣는다. 무인 실행은 후보 목록만 만들고 자리표시를 유지한다.

1. **찾기** — 이 순서로 찾는다. 앞쪽일수록 이용 조건이 분명하다.
   1. 위키미디어 공용 검색 API(주소·출처 페이지·라이선스를 한 번에 준다):
      `https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch=<검색어>&gsrlimit=5&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&format=json`
      → `imageinfo[0].thumburl`(또는 `url`), `descriptionurl`(출처 페이지), `extmetadata.LicenseShortName`
   2. 출판사·저자·제품의 공식 페이지(보도자료·미디어 킷). 이용 조건은 "확인 필요"로 적고 출처 페이지를 남긴다
   3. 그 밖의 웹 검색 결과는 후보로만. 워터마크가 있거나 로그인이 필요한 이미지는 쓰지 않는다
2. **받기** — 후보마다 `python ${CLAUDE_SKILL_DIR}/scripts/fetch_image.py topics/<slug> --url <이미지 주소> --name <이름> --source-page <출처 페이지> --license "<이용 조건>" --note "<무엇>"`. 후보는 `_work/image_candidates/`에 모이고 `candidates.json`에 출처·크기가 적힌다.
3. **확인** — 받은 파일을 Read로 연다. 인물 사진은 출처 페이지가 그 인물의 문서인지(동명이인 아님), 책 표지는 BRIEF의 판본(한국어판·원서)과 같은지 본다. 확인 못 한 것은 후보에서 뺀다.
4. **승인** — AskUserQuestion으로 장면마다 후보 2~3개를 보여 준다(선택지 설명에 크기·이용 조건·출처 페이지, `preview`에 파일 경로). "자리표시로 둔다"를 항상 선택지에 넣는다.
5. **넣기** — 고른 것만 `fetch_image.py topics/<slug> --promote <이름>` → `assets/img/`로 옮겨지고 `assets/img/SOURCES.md`에 출처가 쌓인다. 장면에는 `<img src="assets/img/<파일>" alt="…">`와 출처 줄(`.source`: `사진: <출처 페이지 이름>, <이용 조건>`)을 넣는다.

무인 실행(AskUserQuestion 없음): 1~3까지 하고 `_work/decisions.md`에 `[확인 필요] 이미지 후보: <장면> — candidates.json 참고`를 남긴다. `--promote`는 하지 않는다.

## 3. 논문 그림 (기술 발표)

논문의 핵심 그림(구조도·모식도·결과 그래프)은 원본을 잘라 후보로 보여 준다. 다시 그리지 않는다(내용 왜곡 위험).

1. 사용자가 준 논문 PDF나 arXiv 주소로 쪽을 그린다:
   `node ${CLAUDE_SKILL_DIR}/scripts/paper_figures.mjs <논문.pdf | https://arxiv.org/abs/XXXX> --out topics/<slug>/_work/figures --pages 1-12 --scale 3`
   → `page-NN.png`, `figures.json`(쪽마다 "Figure N" 설명과 위치)
2. 설명이 있는 쪽의 PNG를 Read로 열어 그림 영역의 픽셀 좌표(x, y, 폭, 높이)를 정한다. 설명 글("Figure 1: …")은 영역에서 뺀다(설명은 장면 문구로 옮긴다).
3. `--crop <쪽>:<x>,<y>,<w>,<h> --name fig1-architecture`(같은 `--scale`)로 자르고, 잘린 PNG를 Read로 연다. 가장자리가 잘렸으면 좌표를 넓혀 다시 자른다.
4. 2절 4~5와 같이 승인받아 넣는다. 잘린 파일은 `fetch_image.py`를 거치지 않으므로 `assets/img/`에 직접 복사하고 `SOURCES.md`에 한 줄 적는다. 출처 줄: `그림: Fig. N, <논문 제목> (<저자>, <연도>)`.

`--scale 3`이면 A4 논문 한 쪽이 약 1836×2376px이라, 쪽 폭의 절반 그림도 900px 안팎이 된다. 장면에서 크게 보여 줄 그림이면 scale을 4로 올린다(흐림 방지).

## 4. 자리표시 → 이미지로 바꿀 때 (가독성)

이미지를 자리표시 크기에 억지로 맞추면 캡처 속 글자가 읽히지 않는다. 틀은 **이미지의 가독성에 맞춰 다시 정한다**.

1. 원본 크기를 본다(`candidates.json`의 width·height 또는 파일). 캡처·논문 그림처럼 안에 글자가 있으면, 장면에서 **원본의 0.5배 이상**으로 보여야 글자가 읽힌다.
2. 자리표시 틀이 그보다 작으면 순서대로 푼다:
   1. 캡처에서 필요한 부분만 잘라 넣는다(가장 좋다 — 틀 그대로 글자가 커진다)
   2. 틀을 키우고 같은 장면의 다른 요소 간격을 줄인다("높이 증감 0", build-rules.md 3절)
   3. 장면 타입을 바꾼다: `split` → `title-image`(이미지가 주인공)로, 설명은 노트로
   4. 장면을 둘로 나눈다(사용자 확인)
3. 비율이 다르면 `object-fit: contain`으로 넣고 남는 여백은 틀 배경으로 둔다. `cover`로 잘라 내지 않는다(글자·얼굴이 잘린다).
4. `qa_check`가 `이미지 축소 과다`(0.5배 미만, 중간)와 `이미지 확대`(1.5배 초과, 낮음)를 알린다. 그 장면의 스크린샷을 Read로 열어 캡처 속 글자가 읽히는지 눈으로 본다.

사용자가 Edit로 직접 이미지를 넣은 뒤 "글자가 안 보인다"고 하면 이 절 2의 순서로 고치고, 무엇을 바꿨는지 보고한다.
