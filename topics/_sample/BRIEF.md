---
status: confirmed
slug: _sample
title: ppt-maker 샘플 덱
type: general
audience: ppt-maker 개발자
purpose: 스크립트·템플릿 회귀 검증용 기준 예시
setting: 배포
duration_min: 3
slide_count: 3
section_dividers: false
speaker_notes: true
tone: 담백한 설명체
design_source: DESIGN.md (ppt-maker 내장 기본값)
rules_preset: general
deliverables: [overview, present, pdf]
export_approved: true
---

# BRIEF — ppt-maker 샘플 덱

## 1. 목적과 핵심 메시지

새 장면 규약(`<section class="scene" data-slide data-skill>` + 꼬리 `.source → .speaker-note → .deck-footer`)의 기준 예시다. serve_live·validate_topic·build_present·export_pdf·qa_check가 이 덱으로 회귀 검증한다.

## 2. 청중

ppt-maker를 고치는 개발자와 Claude.

## 3. 흐름과 장수 배분

| # | 타입 | 내용 |
|---|---|---|
| 1 | title | 제목 |
| 2 | title-bullets | 이 덱으로 확인하는 것 3가지 |
| 3 | stat | 숫자로 보는 캔버스 규칙 |

## 4. 참고 자료와 사실 경계

- 확실: ppt-maker 설계 문서(`docs/research-2026-09-22-pure-html-slides.md`)의 수치
- 추정·금지: 없음

## 5. 지킬 것·금지

- 2·3번 장면의 `.deck-footer` 문구는 같게 둔다(블록 경계 테스트용).
- 본문 글자 24px 이상.

## 6. 디자인 지시

DESIGN.md의 기본 토큰(미색 바탕, 파랑 강조 1색)을 쓴다.

## 7. 미확정 질문

(없음)
