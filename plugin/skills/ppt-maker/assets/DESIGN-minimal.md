---
name: ppt-maker 기본
description: 따뜻한 미색 바탕에 거의 검정 글자, 구조 강조는 파랑 한 색만 쓰는 담백한 발표용 기본 디자인.
colors:
  primary: "#2f6fde"      # 강조: 핵심 숫자·키커·불릿 점
  canvas: "#f7f6f3"       # 장면 바탕
  surface: "#ffffff"      # 카드·패널
  ink: "#1f2328"          # 본문 글자
  ink-muted: "#5b616b"    # 보조 글자(부제·출처·꼬리말)
  hairline: "#e3e1dc"     # 구분선·카드 테두리
typography:
  body: Paperlogy
  mono: JetBrains Mono
rounded:
  lg: 24px
---

# DESIGN — ppt-maker 기본

`--palette`나 `--design`으로 다른 디자인을 고르지 않았을 때 쓰는 최소 디자인이다. `deck-design` 스킬 2절 매핑표대로 `:root` 토큰이 된다.

- 바탕은 순백 대신 미색(`canvas`)으로 눈부심을 줄인다
- 강조색(`primary`)은 한 장면에 한두 곳만
- 카드는 테두리(`hairline`) + 옅은 그림자로 구분한다. 두꺼운 그림자는 쓰지 않는다
