# css-patterns — 강조 표시(마커) 패턴

글자 한두 단어를 손으로 표시한 것처럼 강조하는 순수 CSS 패턴 5종이다. 슬라이드는 정지 화면이므로 **표시가 다 그려진 최종 모습**만 쓴다. 외부 라이브러리 없음.

공통 규칙

- 강조는 장면당 1~2곳. 여러 곳에 쓰면 아무것도 강조되지 않는다
- 표시 색은 `--accent` 또는 DESIGN의 보조 강조색. 글자 명암비를 해치지 않게 투명도를 낮춘다
- 인라인 `style`은 쓰지 않는다(검증기 금지). 장면마다 다른 값은 `[data-slide="N"] …` 셀렉터로 scene-styles에 쓴다
- 표시 요소는 장식이므로 `aria-hidden="true"`

## 1. 형광펜 (highlight)

글자 뒤에 반투명 띠. 가장 흔한 방식.

```html
<span class="mh-highlight"><span class="mh-bar" aria-hidden="true"></span><span class="mh-text" data-editable="true">강조할 말</span></span>
```

```css
.mh-highlight { position: relative; display: inline; }
.mh-highlight .mh-bar {
  position: absolute; left: -6px; right: -6px; bottom: 0.08em; height: 0.45em;
  background: var(--marker, #fdd835); opacity: 0.45; border-radius: 3px;
  transform: skewX(-2deg);            /* 손으로 그은 느낌 */
  z-index: 0;
}
.mh-highlight .mh-text { position: relative; z-index: 1; }
```

여러 줄에 걸치면 `.mh-bar` 대신 `background: linear-gradient(transparent 55%, color-mix(in srgb, var(--marker, #fdd835) 45%, transparent) 55%)`를 글자 요소에 직접 준다(`box-decoration-break: clone`).

## 2. 동그라미 (circle)

단어를 손으로 동그라미 친 모양.

```html
<span class="mh-circle"><span class="mh-text" data-editable="true">핵심</span><span class="mh-ring" aria-hidden="true"></span></span>
```

```css
.mh-circle { position: relative; display: inline-block; }
.mh-circle .mh-text { position: relative; z-index: 1; }
.mh-circle .mh-ring {
  position: absolute; top: 50%; left: 50%;
  width: 130%; height: 160%;
  transform: translate(-50%, -50%) rotate(-3deg);
  border: 3px solid var(--marker-2, #e53935); border-radius: 50%;
  pointer-events: none; z-index: 0;
}
.mh-ring.tight   { width: 150%; height: 180%; }                   /* 짧은 단어 */
.mh-ring.rounded { border-radius: 30%; width: 120%; height: 140%; } /* 둥근 사각형 */
.mh-ring.ellipse { width: 150%; height: 130%; }                    /* 가로로 긴 타원 */
```

## 3. 방사선 (burst)

단어에서 사방으로 뻗는 선. 선 길이를 40~80px로 들쭉날쭉하게 해야 손맛이 난다(길이가 같으면 기계적으로 보인다).

```html
<span class="mh-burst"><span class="mh-text" data-editable="true">와!</span><span class="mh-rays" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span></span>
```

```css
.mh-burst { position: relative; display: inline-block; }
.mh-burst .mh-text { position: relative; z-index: 2; }
.mh-burst .mh-rays { position: absolute; top: 50%; left: 50%; width: 0; height: 0; z-index: 1; }
.mh-burst .mh-rays i {
  position: absolute; display: block; width: 3px; left: -1.5px;
  height: var(--len); top: calc(-1 * var(--len) - 0.6em);
  background: var(--accent); transform: rotate(var(--angle)); transform-origin: 50% calc(100% + 0.6em);
}
/* 각도·길이는 인라인 대신 :nth-child로 */
.mh-rays i:nth-child(1) { --angle: 0deg;   --len: 70px; }
.mh-rays i:nth-child(2) { --angle: 45deg;  --len: 55px; }
.mh-rays i:nth-child(3) { --angle: 90deg;  --len: 80px; }
.mh-rays i:nth-child(4) { --angle: 135deg; --len: 45px; }
.mh-rays i:nth-child(5) { --angle: 180deg; --len: 65px; }
.mh-rays i:nth-child(6) { --angle: 225deg; --len: 75px; }
.mh-rays i:nth-child(7) { --angle: 270deg; --len: 50px; }
.mh-rays i:nth-child(8) { --angle: 315deg; --len: 60px; }
```

## 4. 물결 밑줄·취소선 (scribble)

SVG 물결선. 밑줄이 기본이고, 취소선은 위치만 바꾼다.

```html
<span class="mh-scribble"><span class="mh-text" data-editable="true">밑줄 칠 말</span><svg class="mh-wave" viewBox="0 0 500 24" preserveAspectRatio="none" aria-hidden="true"><path d="M0,12 Q31,0 62,12 Q93,24 125,12 Q156,0 187,12 Q218,24 250,12 Q281,0 312,12 Q343,24 375,12 Q406,0 437,12 Q468,24 500,12" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg></span>
```

```css
.mh-scribble { position: relative; display: inline-block; }
.mh-scribble .mh-text { position: relative; z-index: 1; }
.mh-scribble .mh-wave {
  position: absolute; left: 0; bottom: -0.25em; width: 100%; height: 0.4em;
  color: var(--marker, #fdd835); z-index: 0;
}
.mh-scribble.strike .mh-wave { top: 50%; bottom: auto; transform: translateY(-50%); z-index: 2; }
```

물결 조절: 반물결 간격을 25px로 줄이면 촘촘하게, 50px로 늘리면 느슨하게. 진폭은 y 범위(0~24 기본, 0~16 은은하게).

## 5. 엑스 표시 (sketchout)

더 이상 유효하지 않은 말 위에 X자 두 줄. "예전 방식", "옛 가격"에.

```html
<span class="mh-sketchout"><span class="mh-text" data-editable="true">예전 방식</span><span class="mh-lines" aria-hidden="true"><i class="fwd"></i><i class="bwd"></i></span></span>
```

```css
.mh-sketchout { position: relative; display: inline-block; }
.mh-sketchout .mh-lines { position: absolute; inset: 0 -4px; overflow: hidden; z-index: 1; }
.mh-sketchout .mh-lines i {
  position: absolute; display: block; top: 50%; left: 0; width: 100%; height: 3px;
  background: var(--marker-2, #e53935); transform-origin: center;
}
.mh-sketchout .fwd { transform: rotate(-12deg); }
.mh-sketchout .bwd { transform: rotate(12deg); }
```

지운 말도 읽혀야 하므로 선 굵기는 2~3px, 글자는 `--text-dim`으로 한 단계 흐리게 한다.
