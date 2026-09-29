#!/usr/bin/env node
/**
 * qa_check.mjs — present.html의 장면을 하나씩 켜고 기계로 잡을 수 있는 레이아웃 문제를 찾는다.
 *
 * 사용법:
 *   node qa_check.mjs topics/<slug>              # 전체 장면(기본)
 *   node qa_check.mjs topics/<slug> --slides 2,5-7
 *
 * 검사(장면마다):
 *   높음  넘침      장면 내용이 1920×1080 밖으로 나감(scrollWidth/Height, 요소 사각형)
 *   높음  잘림      overflow가 막힌 요소 안에서 글자가 넘침
 *   높음  겹침      같은 부모의 흐름 배치 형제끼리 크게 겹침(작은 쪽 넓이의 10% 이상). SVG 안은 제외
 *   높음  표지 겹침 글자 앞 ::before/::after 표지가 padding-left보다 넓어 본문을 덮음
 *   높음  명암비    WCAG 기준 미달(본문 4.5:1, 큰 글자 3:1)
 *   높음  글자 하한 deck-rules.json min_font_px(기본 24px) 미만
 *                   fig_selectors에 걸리는 인포그래픽 글자는 min_fig_font_px(기본 32px)
 *   높음  외부 요청 http(s) 자원을 불렀음(오프라인 규칙 위반)
 *   높음  글자 겹침 실제 글자 사각형끼리 겹침 — 절대 배치 라벨, SVG 글자, SVG 위 HTML 글자까지(7절)
 *   높음  SVG 글자 잘림·SVG 그림 잘림  글자·도형이 svg 틀 밖으로 나감(8절)
 *   높음  SVG 도형 밖 글자  글자 가운데를 품은 도형 밖으로 글자가 삐져나감(text-anchor 원인 안내)
 *   높음  글자 하한·명암비(SVG)  viewBox 배율을 곱한 실제 크기, fill 대 아래 도형 색으로 계산
 *   중간  SVG 그림 쏠림  그린 내용이 svg 틀 안에서 한쪽으로 몰림 → 맞는 viewBox 값을 제안
 *   중간  그림 위치 쏠림  한 줄을 혼자 차지한 svg·img·.image-frame·.fig가 부모 안에서 가운데가 아님(9절)
 *   중간  고아 줄바꿈  여러 줄 글자의 마지막 줄이 4글자 이하(10절)
 *   중간  격자 간격 불균형·격자 높이 불균형  같은 역할 형제 사이 간격 차이 8px 이상, 같은 줄 상자 높이 차이 8px 이상(11절)
 *   중간  상자 안 쏠림 카드 안 내용이 위로 붙어 아래 여백이 위보다 60px 이상·2배 초과
 *   중간  세로 빈 띠 위아래 빈 띠가 각 150px 이상이거나 요소 사이가 150px 이상 벌어짐(title·quote 제외)
 *   중간  이미지 축소 과다 원본 대비 0.5배 미만으로 줄여 넣음(캡처 속 글자가 안 읽힐 수 있음)
 *   낮음  이미지 확대 원본을 1.5배 넘게 키움(흐릴 수 있음)
 *   낮음  명암비 확인 필요 — 배경이 그라데이션·이미지라 자동 계산 불가(눈 검수)
 *
 * 기계가 못 잡는 것(세로 무게 중심의 미묘한 쏠림·가로 빈 여백·의미 단위 줄바꿈·이미지 속 글자)은
 * _work/shots/ 스크린샷으로 deck-reviewer가 따로 본다. 이 스크립트 통과 ≠ 검수 완료.
 * deck-rules.json options.vision_review가 false(이미지를 못 보는 모델)면 그 항목을 사용자 확인 목록으로 출력한다.
 *
 * 출력: _work/qa_check.json, 요약은 표준 출력. 높음이 1건이라도 있으면 exit 1(게이트 B).
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { EXIT, argValue, gotoScene, log, openPresent, parseSlides, positional, readRules, resolveTopic } from './lib/pw_common.mjs';

const argv = process.argv.slice(2);
const topic = resolveTopic(positional(argv, ['--slides']));
const rules = readRules(topic);
const minFont = Number(rules.min_font_px) || 24;
const minFigFont = Number(rules.min_fig_font_px) || 32;
const figSelectors = Array.isArray(rules.fig_selectors) ? rules.fig_selectors : [];

/**
 * 브라우저 안에서 한 장면을 검사한다. 이 함수는 페이지 문맥에서 실행되므로 바깥 변수를 쓰지 않는다.
 * @returns {Array<{severity:string,type:string,selector:string,detail:string}>}
 */
function inspectScene({ n, minFont, minFigFont, figSelectors }) {
  const issues = [];
  const scene = document.querySelector(`#deck > .scene[data-slide="${n}"]`) || document.querySelectorAll('#deck > .scene')[n - 1];
  if (!scene) return [{ severity: '높음', type: '장면 없음', selector: `#${n}`, detail: '' }];
  const W = 1920, H = 1080, TOL = 1;

  // 장면 좌표계: 발표 화면은 축소(scale) 상태이므로 사각형을 장면 기준 1920×1080 좌표로 되돌린다
  const sr = scene.getBoundingClientRect();
  const k = sr.width / W;
  const rel = (r) => ({ x: (r.left - sr.left) / k, y: (r.top - sr.top) / k, w: r.width / k, h: r.height / k });

  /** Aim과 비슷한 짧은 경로 셀렉터 */
  const sel = (el) => {
    const parts = [];
    let cur = el;
    while (cur && cur !== scene && parts.length < 4) {
      let p = cur.tagName.toLowerCase();
      const cls = [...cur.classList].filter((c) => c !== 'active').slice(0, 2);
      if (cls.length) p += '.' + cls.join('.');
      const sib = cur.parentElement ? [...cur.parentElement.children].filter((s) => s.tagName === cur.tagName) : [];
      if (sib.length > 1) p += `:nth-of-type(${sib.indexOf(cur) + 1})`;
      parts.unshift(p);
      cur = cur.parentElement;
    }
    return `[data-slide="${n}"] > ` + parts.join(' > ');
  };
  const add = (severity, type, el, detail) => issues.push({ severity, type, selector: el === scene ? `[data-slide="${n}"]` : sel(el), detail });

  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    if (el.closest('.speaker-note')) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const hasOwnText = (el) => [...el.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim());
  const all = [...scene.querySelectorAll('*')].filter(visible);

  // 1) 넘침: 장면 자체
  if (scene.scrollWidth > W + TOL || scene.scrollHeight > H + TOL) {
    add('높음', '넘침', scene, `장면 내용 크기 ${scene.scrollWidth}×${scene.scrollHeight} > 1920×1080`);
  }
  // 1-b) 넘침: 요소가 캔버스 밖으로(가장 바깥 요소만 보고)
  for (const el of all) {
    const r = rel(el.getBoundingClientRect());
    const out = r.x < -TOL || r.y < -TOL || r.x + r.w > W + TOL || r.y + r.h > H + TOL;
    if (!out) continue;
    const parentOut = el.parentElement && el.parentElement !== scene && (() => {
      const p = rel(el.parentElement.getBoundingClientRect());
      return p.x < -TOL || p.y < -TOL || p.x + p.w > W + TOL || p.y + p.h > H + TOL;
    })();
    if (!parentOut) add('높음', '넘침', el, `캔버스 밖: x=${Math.round(r.x)} y=${Math.round(r.y)} w=${Math.round(r.w)} h=${Math.round(r.h)}`);
  }

  // 2) 잘림: overflow가 막힌 요소에서 내용이 넘침
  for (const el of all) {
    const cs = getComputedStyle(el);
    const clipX = cs.overflowX !== 'visible', clipY = cs.overflowY !== 'visible';
    if (!clipX && !clipY) continue;
    if (!el.textContent.trim()) continue;
    if ((clipX && el.scrollWidth > el.clientWidth + TOL) || (clipY && el.scrollHeight > el.clientHeight + TOL)) {
      add('높음', '잘림', el, `내용 ${el.scrollWidth}×${el.scrollHeight} > 보이는 영역 ${el.clientWidth}×${el.clientHeight}`);
    }
  }

  // 3) 겹침: 같은 부모의 흐름 배치(static/relative) 형제끼리
  //    SVG 안(svg 요소 자신 포함)은 부모로 삼지 않는다. 도형·선·글자가 겹치는 것이 그림의 의도이기 때문이다.
  //    svg 요소 자체는 HTML 형제와 계속 비교되므로 그림이 옆 요소를 덮는 진짜 겹침은 잡힌다.
  const inFlow = (el) => ['static', 'relative', 'sticky'].includes(getComputedStyle(el).position);
  for (const parent of [scene, ...all]) {
    if (parent.closest('svg')) continue;
    const kids = [...parent.children].filter((c) => visible(c) && inFlow(c));
    for (let i = 0; i < kids.length; i++) {
      for (let j = i + 1; j < kids.length; j++) {
        const a = kids[i].getBoundingClientRect(), b = kids[j].getBoundingClientRect();
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox <= 1 || oy <= 1) continue;
        const area = (ox * oy) / (k * k);
        const smaller = Math.min(a.width * a.height, b.width * b.height) / (k * k);
        if (smaller > 0 && area / smaller >= 0.1) {
          add('높음', '겹침', kids[j], `앞 형제(${sel(kids[i]).split(' > ').pop()})와 ${Math.round((area / smaller) * 100)}% 겹침`);
        }
      }
    }
  }

  // 3-b) 표지 겹침: 글자 앞 ::before/::after 표지(불릿 점·선·—)가 들여쓰기 자리보다 넓어 본문을 덮는 경우
  //      형제 요소가 아니라 가상 요소라서 3)이 못 잡는다. 표지 오른쪽 끝 > 본문 시작(padding-left)이면 겹친다.
  //      글자 표지(content: "—")는 width가 auto라 캔버스로 글자 폭을 잰다.
  const measure = document.createElement('canvas').getContext('2d');
  for (const el of all) {
    if (!hasOwnText(el)) continue;
    const cs = getComputedStyle(el);
    const padLeft = parseFloat(cs.paddingLeft) || 0;
    for (const pseudo of ['::before', '::after']) {
      const ps = getComputedStyle(el, pseudo);
      if (ps.content === 'none' || ps.content === 'normal' || ps.display === 'none') continue;
      if (ps.position !== 'absolute' || ps.left === 'auto') continue;
      // 요소 오른쪽 바깥에서 시작하는 장식(흐름 화살표 등)은 글자 앞 표지가 아니다
      if ((parseFloat(ps.left) || 0) >= el.clientWidth) continue;
      let w = parseFloat(ps.width);
      if (!(w > 0)) {
        const txt = ps.content.replace(/^["']|["']$/g, '');
        if (!txt) continue;
        measure.font = `${ps.fontWeight} ${ps.fontSize} ${ps.fontFamily}`;
        w = measure.measureText(txt).width;
      }
      const right = (parseFloat(ps.left) || 0) + (parseFloat(ps.marginLeft) || 0) + w;
      // 표지가 아니라 요소 전체를 덮는 장식(배경 막 등)은 제외
      if (w > el.clientWidth / 2) continue;
      // 표지가 글자 위쪽 자리(padding-top)에 따로 놓였으면 세로로 떨어져 있으니 겹침이 아니다
      const padTop = parseFloat(cs.paddingTop) || 0;
      const psTop = ps.top === 'auto' ? padTop : parseFloat(ps.top) || 0;
      const psH = parseFloat(ps.height) > 0 ? parseFloat(ps.height) : (parseFloat(ps.lineHeight) || parseFloat(ps.fontSize) * 1.2);
      if (psTop + psH <= padTop + TOL) continue;
      if (right > padLeft + TOL) {
        add('높음', '표지 겹침', el, `${pseudo} 표지 오른쪽 끝 ${Math.round(right)}px > 본문 시작 padding-left ${Math.round(padLeft)}px`);
      }
    }
  }

  // 3-c) 세로 빈 띠: 장면은 내용 묶음을 세로 가운데로 모으므로, 묶음이 작으면 위아래에 같은 빈 띠가 생긴다.
  //      쓸 수 있는 높이(padding 안쪽)에서 묶음 높이를 뺀 값이 300px 이상(위아래 각 150px 이상)이면 중간.
  //      표지·인용(title·quote)은 여백이 의도라 뺀다. 고치는 법: 간격·카드 안 여백을 늘린다(글자는 키우지 않는다).
  const skill = scene.getAttribute('data-skill') || '';
  if (!['title', 'quote'].includes(skill)) {
    const ss = getComputedStyle(scene);
    const usable = H - (parseFloat(ss.paddingTop) || 0) - (parseFloat(ss.paddingBottom) || 0);
    const stack = [...scene.children].filter((c) => visible(c) && inFlow(c)).map((c) => rel(c.getBoundingClientRect()));
    if (stack.length) {
      const top = Math.min(...stack.map((r) => r.y)), bottom = Math.max(...stack.map((r) => r.y + r.h));
      const empty = usable - (bottom - top);
      if (empty >= 300) add('중간', '세로 빈 띠', scene, `내용 묶음 ${Math.round(bottom - top)}px / 쓸 수 있는 높이 ${Math.round(usable)}px — 위아래 빈 띠 약 ${Math.round(empty / 2)}px씩`);
      // 가운데 빈 띠: margin-top: auto 등으로 묶음 안 요소 사이가 150px 이상 벌어진 경우
      const sorted = [...stack].sort((a, b) => a.y - b.y);
      for (let i = 1; i < sorted.length; i++) {
        const prevBottom = Math.max(...sorted.slice(0, i).map((r) => r.y + r.h));
        const gap = sorted[i].y - prevBottom;
        if (gap >= 150) add('중간', '세로 빈 띠', scene, `요소 사이 빈 띠 ${Math.round(gap)}px (y=${Math.round(prevBottom)}~${Math.round(sorted[i].y)})`);
      }
    }
  }

  // 4) 명암비·글자 하한: 글자를 직접 가진 요소
  const parse = (c) => {
    // color-mix()의 계산값은 `color(srgb 0.96 0.92 0.82 / 0.5)`(0~1 소수) 형식으로 온다 → 0~255로 바꾼다
    const s = c.match(/color\(srgb\s+([^)]+)\)/);
    if (s) {
      const q = s[1].split(/[\s/]+/).filter(Boolean).map(parseFloat);
      return [q[0] * 255, q[1] * 255, q[2] * 255, q.length > 3 ? q[3] : 1];
    }
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(parseFloat);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  };
  const lum = ([r, g, b]) => {
    const ch = (v) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b);
  };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const over = (top, bottom) => [0, 1, 2].map((i) => top[i] * top[3] + bottom[i] * (1 - top[3]));

  /** 배경색: 조상을 따라 올라가며 반투명 배경을 합성. 그라데이션·이미지를 만나면 null(자동 계산 불가) */
  const backgroundOf = (el) => {
    const layers = [];
    for (let cur = el; cur; cur = cur.parentElement) {
      const cs = getComputedStyle(cur);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      const c = parse(cs.backgroundColor);
      if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
    }
    let base = [255, 255, 255];
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base;
  };

  const isFig = (el) => figSelectors.some((s) => { try { return el.closest(s); } catch { return false; } });
  for (const el of all) {
    if (!hasOwnText(el)) continue;
    if (el.closest('svg')) continue;  // SVG 글자는 viewBox 배율·fill 색을 따로 계산한다(7절)
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize);
    const weight = Number(cs.fontWeight) || 400;
    const limit = isFig(el) ? minFigFont : minFont;
    if (size + 0.01 < limit) add('높음', '글자 하한', el, `${size}px < ${limit}px${isFig(el) ? ' (인포그래픽)' : ''}`);

    const fg = parse(cs.color);
    const bg = backgroundOf(el);
    if (!fg) continue;
    if (!bg) { add('낮음', '명암비 확인 필요', el, '배경이 그라데이션·이미지 — 스크린샷으로 눈 검수'); continue; }
    const r = ratio(over(fg, bg), bg);
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = large ? 3 : 4.5;
    if (r + 1e-6 < need) add('높음', '명암비', el, `${r.toFixed(2)}:1 < ${need}:1 (${large ? '큰 글자' : '본문'})`);
  }
  // 5) 상자 안 쏠림: 배경이나 테두리가 있는 상자(카드)에서 내용 묶음이 위로 붙고 아래가 비는 경우.
  //      같은 줄 카드끼리 높이가 같아 짧은 카드의 아래가 비어 보인다. 아래 빈 공간이 위보다 60px 이상 크고 2배를 넘으면 중간.
  //      고치는 법: 상자에 .box-center(세로 가운데). 카드 머리가 있으면 머리 아래 목록 영역만 가운데(slide-types 1절)
  for (const el of all) {
    if (el === scene || el.closest('svg')) continue;
    const cs = getComputedStyle(el);
    const bg = parse(cs.backgroundColor);
    const boxed = (bg && bg[3] > 0) || parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderLeftWidth) > 0;
    if (!boxed || !el.textContent.trim()) continue;
    const r = rel(el.getBoundingClientRect());
    if (r.h < 150 || r.w > W * 0.9) continue;
    const kids = [...el.children].filter((c) => visible(c) && inFlow(c)).map((c) => rel(c.getBoundingClientRect()));
    if (!kids.length) continue;
    const innerTop = r.y + (parseFloat(cs.borderTopWidth) + parseFloat(cs.paddingTop));
    const innerBottom = r.y + r.h - (parseFloat(cs.borderBottomWidth) + parseFloat(cs.paddingBottom));
    const topGap = Math.min(...kids.map((k2) => k2.y)) - innerTop;
    const bottomGap = innerBottom - Math.max(...kids.map((k2) => k2.y + k2.h));
    if (bottomGap - topGap >= 60 && bottomGap > topGap * 2) {
      add('중간', '상자 안 쏠림', el, `내용 위 여백 ${Math.round(topGap)}px, 아래 여백 ${Math.round(bottomGap)}px — 세로 가운데로`);
    }
  }

  // 6) 이미지 배율: 원본 픽셀 대비 화면 크기. 캡처를 작은 틀에 넣으면 속 글자가 읽히지 않고, 작은 그림을 키우면 흐려진다.
  //    0.5배 미만 축소 → 중간(틀을 키우거나 캡처를 필요한 부분만 잘라 넣는다), 1.5배 초과 확대 → 낮음(더 큰 원본을 찾는다)
  for (const img of scene.querySelectorAll('img')) {
    if (!visible(img) || !img.naturalWidth) continue;
    if (/\.svg(\?|#|$)/i.test(img.getAttribute('src') || '')) continue;  // 벡터는 배율과 무관하게 선명하다
    const shown = rel(img.getBoundingClientRect());
    const ratio = Math.min(shown.w / img.naturalWidth, shown.h / img.naturalHeight);
    const name = (img.getAttribute('src') || '').split('/').pop();
    if (ratio < 0.5) add('중간', '이미지 축소 과다', img, `${name} 원본 ${img.naturalWidth}×${img.naturalHeight} → 화면 ${Math.round(shown.w)}×${Math.round(shown.h)} (${ratio.toFixed(2)}배) — 캡처 속 글자가 읽히는지 스크린샷으로 확인`);
    else if (ratio > 1.5) add('낮음', '이미지 확대', img, `${name} 원본 ${img.naturalWidth}×${img.naturalHeight}를 ${ratio.toFixed(2)}배 키움 — 흐릴 수 있음`);
  }

  // 7) 글자 겹침(위치 방식 무관): 3)은 흐름 배치 형제만 보므로 position:absolute 라벨·SVG 글자끼리·SVG 위 HTML 라벨의
  //    겹침을 못 잡는다. 여기서는 "실제 글자가 그려진 사각형"끼리 비교한다.
  //    HTML은 글자 노드의 줄 사각형(Range.getClientRects), SVG는 글자 요소 사각형. 같은 요소·조상-자손 쌍은 뺀다.
  //    글꼴의 위아래 여유(ascent/descent) 때문에 붙어 있는 줄이 살짝 겹쳐 보이는 것은 세로 18%씩 깎아 무시한다.
  const inSvg = (el) => !!el.closest('svg');
  const textBoxes = [];
  const walker = document.createTreeWalker(scene, NodeFilter.SHOW_TEXT);
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    if (!el || !visible(el)) continue;
    if (inSvg(el)) {
      textBoxes.push({ el, r: rel(el.getBoundingClientRect()) });
    } else {
      const range = document.createRange();
      range.selectNodeContents(t);
      for (const lr of range.getClientRects()) if (lr.width > 0 && lr.height > 0) textBoxes.push({ el, r: rel(lr) });
    }
  }
  const shrink = (r) => ({ x: r.x + 1, y: r.y + r.h * 0.18, w: r.w - 2, h: r.h * 0.64 });
  const seenPair = new Set();
  for (let i = 0; i < textBoxes.length; i++) {
    for (let j = i + 1; j < textBoxes.length; j++) {
      const A = textBoxes[i], B = textBoxes[j];
      if (A.el === B.el || A.el.contains(B.el) || B.el.contains(A.el)) continue;
      const a = shrink(A.r), b = shrink(B.r);
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox <= 2 || oy <= 2) continue;
      const smaller = Math.min(a.w * a.h, b.w * b.h);
      if (smaller <= 0 || (ox * oy) / smaller < 0.15) continue;
      const key = sel(A.el) + '|' + sel(B.el);
      if (seenPair.has(key)) continue;
      seenPair.add(key);
      add('높음', '글자 겹침', B.el,
        `"${B.el.textContent.trim().slice(0, 16)}"이(가) "${A.el.textContent.trim().slice(0, 16)}"(${sel(A.el).split(' > ').pop()})와 겹침 ` +
        `(가로 ${Math.round(ox)}px × 세로 ${Math.round(oy)}px). 고치는 법: 좌표를 옮기지 말고 flex/grid 배치로 바꾸거나(slide-types references/infographic.md), ` +
        `SVG면 두 글자의 y를 글자 크기의 1.4배 이상 떨어뜨린다`);
    }
  }

  // 8) SVG 그림 검사: 모델이 좌표를 직접 쓰는 곳이라 가장 자주 깨진다.
  //    8-a 글자 크기: viewBox 배율을 곱한 실제 화면 크기로 하한을 본다(font-size="20"이 화면에서는 12px일 수 있다)
  //    8-b 잘림: 글자·도형이 svg 보이는 영역 밖으로 나감
  //    8-c 도형 밖 글자: 글자 가운데가 닫힌 도형(rect·circle·ellipse·polygon) 안에 있는데 글자가 도형 밖으로 삐져나감
  //        (가장 흔한 원인: text-anchor="middle" 없이 x에 도형 가운데 좌표를 넣음)
  //    8-d 명암비: 글자색은 fill, 배경은 글자 아래 도형의 fill
  //    8-e 그림 쏠림: 그려진 내용이 svg 틀 안에서 한쪽으로 몰림 → 맞는 viewBox 값을 계산해 알려 준다
  const shapeSel = 'rect, circle, ellipse, polygon';
  const svgs = [...scene.querySelectorAll('svg')].filter((s) => !s.parentElement.closest('svg') && visible(s));
  for (const svg of svgs) {
    const box = rel(svg.getBoundingClientRect());
    const drawn = [...svg.querySelectorAll('rect, circle, ellipse, polygon, polyline, path, line, text, image, use')]
      .filter((e) => { const cs = getComputedStyle(e); return cs.display !== 'none' && cs.visibility !== 'hidden' && !e.closest('defs, marker, clipPath, mask, pattern, symbol'); });
    if (!drawn.length) continue;
    const shapes = drawn.filter((e) => e.matches(shapeSel));
    const svgArea = box.w * box.h;

    // 8-b 잘림(도형·글자 공통, 가장 바깥 한 번만 보고)
    let cut = null;
    for (const e of drawn) {
      const r = rel(e.getBoundingClientRect());
      if (r.w === 0 && r.h === 0) continue;
      const over = Math.max(box.x - r.x, box.y - r.y, r.x + r.w - (box.x + box.w), r.y + r.h - (box.y + box.h));
      if (over > 2 && (!cut || over > cut.over)) cut = { e, over, r };
    }
    if (cut) {
      const isText = cut.e.matches('text, tspan');
      add('높음', isText ? 'SVG 글자 잘림' : 'SVG 그림 잘림', cut.e,
        `${isText ? `"${cut.e.textContent.trim().slice(0, 16)}"` : cut.e.tagName}이(가) svg 틀 밖으로 ${Math.round(cut.over)}px 나감. ` +
        `고치는 법: 아래 'SVG 그림 쏠림' 제안 viewBox를 쓰거나, 요소 좌표를 viewBox 안으로 옮긴다`);
    }

    // 8-a·8-c·8-d 글자 하나씩
    for (const t of [...svg.querySelectorAll('text, tspan')].filter((e) => hasOwnText(e) && visible(e))) {
      const cs = getComputedStyle(t);
      const ctm = t.getScreenCTM();
      const scale = ctm ? Math.hypot(ctm.a, ctm.b) / k : 1;
      const size = parseFloat(cs.fontSize) * scale;
      const limit = isFig(t) ? minFigFont : minFont;
      if (size + 0.01 < limit) {
        add('높음', '글자 하한', t, `SVG 글자 실제 크기 ${size.toFixed(1)}px < ${limit}px (font-size ${cs.fontSize} × viewBox 배율 ${scale.toFixed(2)}). ` +
          `고치는 법: font-size를 ${Math.ceil(limit / scale)} 이상으로`);
      }
      const tr = rel(t.getBoundingClientRect());
      const cx = tr.x + tr.w / 2, cy = tr.y + tr.h / 2;
      // 글자 가운데를 품는 닫힌 도형 중 가장 작은 것(배경판처럼 svg 절반 이상 덮는 도형은 틀로 보지 않는다)
      const holder = shapes
        .map((s) => ({ s, r: rel(s.getBoundingClientRect()) }))
        .filter(({ r }) => cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h && r.w * r.h < svgArea * 0.5)
        .sort((p, q) => p.r.w * p.r.h - q.r.w * q.r.h)[0];
      if (holder) {
        const r = holder.r;
        const out = Math.max(r.x - tr.x, tr.x + tr.w - (r.x + r.w), r.y - tr.y, tr.y + tr.h - (r.y + r.h));
        if (out > 2) {
          const anchor = t.closest('text')?.getAttribute('text-anchor') || getComputedStyle(t).textAnchor;
          add('높음', 'SVG 도형 밖 글자', t,
            `"${t.textContent.trim().slice(0, 16)}"이(가) ${holder.s.tagName} 밖으로 ${Math.round(out)}px 삐져나감` +
            (anchor !== 'middle' ? ` (text-anchor=${anchor || 'start'}: x가 도형 가운데라면 text-anchor="middle" dominant-baseline="central"을 붙인다)` : '') +
            `. 그래도 넘치면 글자를 줄이거나 도형을 키운다(도형 폭 ≥ 글자 수 × font-size + 좌우 여백 48)`);
        }
      }
      // 명암비: fill 대 (글자 아래 칠해진 도형 fill → 없으면 svg 바깥 배경)
      const fg = parse(cs.fill);
      if (!fg) continue;
      const under = shapes
        .filter((s) => (s.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING) && parse(getComputedStyle(s).fill)?.[3] > 0)
        .map((s) => ({ s, r: rel(s.getBoundingClientRect()) }))
        .filter(({ r }) => cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h)
        .sort((p, q) => p.r.w * p.r.h - q.r.w * q.r.h)[0];
      let bg = backgroundOf(svg);
      if (under) {
        const f = parse(getComputedStyle(under.s).fill);
        const op = parseFloat(getComputedStyle(under.s).fillOpacity);
        const fa = [f[0], f[1], f[2], f[3] * (isNaN(op) ? 1 : op)];
        bg = bg ? over(fa, bg) : (fa[3] >= 1 ? fa.slice(0, 3) : null);
      }
      if (!bg) { add('낮음', '명암비 확인 필요', t, '배경이 그라데이션·이미지 — 스크린샷으로 눈 검수'); continue; }
      const fo = parseFloat(cs.fillOpacity);
      const cr = ratio(over([fg[0], fg[1], fg[2], fg[3] * (isNaN(fo) ? 1 : fo)], bg), bg);
      const large = size >= 24 || (size >= 18.66 && (Number(cs.fontWeight) || 400) >= 700);
      const need = large ? 3 : 4.5;
      if (cr + 1e-6 < need) add('높음', '명암비', t, `SVG 글자 ${cr.toFixed(2)}:1 < ${need}:1 (fill 대 아래 도형 색)`);
    }

    // 8-e 그림 쏠림: 작은 아이콘·장식선은 뺀다
    if (box.w >= 300 && box.h >= 150) {
      const rs = drawn.map((e) => rel(e.getBoundingClientRect())).filter((r) => r.w > 0 || r.h > 0);
      const L = Math.min(...rs.map((r) => r.x)), R = Math.max(...rs.map((r) => r.x + r.w));
      const T = Math.min(...rs.map((r) => r.y)), B = Math.max(...rs.map((r) => r.y + r.h));
      const gl = L - box.x, gr = box.x + box.w - R, gt = T - box.y, gb = box.y + box.h - B;
      const offX = Math.abs(gl - gr) > Math.max(24, box.w * 0.04);
      const offY = Math.abs(gt - gb) > Math.max(24, box.h * 0.06);
      if (offX || offY) {
        const bb = svg.getBBox();
        const pad = Math.round(Math.max(bb.width, bb.height) * 0.04) + 8;
        const vb = [bb.x - pad, bb.y - pad, bb.width + pad * 2, bb.height + pad * 2].map((v) => Math.round(v));
        add('중간', 'SVG 그림 쏠림', svg,
          `그린 내용이 틀 안에서 한쪽으로 몰림(여백 왼쪽 ${Math.round(gl)} / 오른쪽 ${Math.round(gr)} / 위 ${Math.round(gt)} / 아래 ${Math.round(gb)}px). ` +
          `고치는 법: 좌표를 하나씩 옮기지 말고 svg의 viewBox를 "${vb.join(' ')}"로 바꾼다(preserveAspectRatio는 기본값 유지)`);
      }
    }
  }

  // 9) 그림 위치 쏠림: 한 줄을 혼자 차지한 그림(svg·img·.image-frame·.fig)이 부모 안에서 가운데가 아닌 경우.
  //    split처럼 옆에 다른 요소가 나란히 있으면 의도한 배치라 뺀다.
  for (const f of all.filter((e) => (e.matches('svg, img, .image-frame, .fig') && !e.parentElement.closest('svg')))) {
    const p = f.parentElement;
    if (!p) continue;
    const fr = rel(f.getBoundingClientRect());
    if (fr.w < 300) continue;
    const beside = [...p.children].some((c) => {
      if (c === f || !visible(c) || c.matches('.speaker-note')) return false;
      const cr = rel(c.getBoundingClientRect());
      return Math.min(cr.y + cr.h, fr.y + fr.h) - Math.max(cr.y, fr.y) > 10;  // 세로로 겹치는 형제 = 나란히 놓임
    });
    if (beside) continue;
    const pcs = getComputedStyle(p);
    const pr = rel(p.getBoundingClientRect());
    const inL = pr.x + (parseFloat(pcs.borderLeftWidth) || 0) + (parseFloat(pcs.paddingLeft) || 0);
    const inR = pr.x + pr.w - (parseFloat(pcs.borderRightWidth) || 0) - (parseFloat(pcs.paddingRight) || 0);
    const gl = fr.x - inL, gr = inR - (fr.x + fr.w);
    if (gl + gr < 48 || Math.abs(gl - gr) <= 24) continue;
    add('중간', '그림 위치 쏠림', f,
      `부모 안에서 왼쪽 ${Math.round(gl)}px / 오른쪽 ${Math.round(gr)}px 비어 가운데가 아님. ` +
      `고치는 법: 그림에 .fig-center 클래스(display:block; margin-inline:auto)를 붙인다. 부모가 flex 세로 배치면 align-self: center`);
  }

  // 10) 고아 줄바꿈: 여러 줄 글자 덩어리의 마지막 줄이 4글자 이하(qa-gate 3절 3항을 기계로).
  //     글자 하나하나의 줄 위치를 재서 줄을 나눈다. 안에 블록 자식이 있는 요소는 자식이 따로 검사된다.
  const blockish = (e) => !['inline', 'contents', 'none'].includes(getComputedStyle(e).display);
  for (const el of all) {
    if (inSvg(el) || !hasOwnText(el) || !blockish(el)) continue;
    if ([...el.querySelectorAll('*')].some((d) => visible(d) && blockish(d))) continue;
    const lines = [];   // [{top, n}]
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    for (let t = tw.nextNode(); t; t = tw.nextNode()) {
      const s = t.textContent;
      for (let i = 0; i < s.length; i++) {
        if (/\s/.test(s[i])) continue;
        range.setStart(t, i); range.setEnd(t, i + 1);
        const r = range.getClientRects()[0];
        if (!r) continue;
        const top = rel(r).y, h = rel(r).h;
        const line = lines.find((l) => Math.abs(l.top - top) < h * 0.5);
        if (line) { line.n += 1; line.text += s[i]; } else lines.push({ top, n: 1, text: s[i] });
      }
    }
    if (lines.length < 2) continue;
    lines.sort((a, b) => a.top - b.top);
    const last = lines[lines.length - 1];
    if (last.n <= 4) {
      add('중간', '고아 줄바꿈', el,
        `${lines.length}줄 중 마지막 줄이 "${last.text}"(${last.n}자)뿐. 고치는 법: 문장을 줄이거나 어순을 바꾼다. ` +
        `폭을 바꿀 때는 "높이 증감 0"으로(글자 크기는 줄이지 않는다)`);
    }
  }

  // 11) 격자 간격·높이 불균형: 같은 역할(태그 + 첫 클래스가 같은) 형제가 한 줄(또는 한 열)에 3개 이상 있을 때
  //     사이 간격 차이가 8px 이상이면 중간(qa-gate 3절 4항을 기계로). 상자(배경·테두리) 형제가 같은 줄에서
  //     높이가 8px 이상 다르면 중간. 장면 바로 아래 요소(제목·요지·본문 묶음)는 역할이 달라 뺀다.
  const role = (e) => e.tagName + '.' + (e.classList[0] || '');
  const boxedEl = (e) => { const cs = getComputedStyle(e); const b = parse(cs.backgroundColor); return (b && b[3] > 0) || parseFloat(cs.borderTopWidth) > 0; };
  for (const parent of all) {
    if (parent === scene || inSvg(parent)) continue;
    const kids = [...parent.children].filter((c) => visible(c) && inFlow(c) && !c.matches('.speaker-note'));
    if (kids.length < 2) continue;
    const groups = new Map();
    for (const c of kids) { const g = groups.get(role(c)) || []; g.push({ e: c, r: rel(c.getBoundingClientRect()) }); groups.set(role(c), g); }
    for (const items of groups.values()) {
      if (items.length < 2) continue;
      // 같은 줄(윗변 ±4px)과 같은 열(왼변 ±4px)로 나눈다
      const bucket = (key) => {
        const out = [];
        for (const it of items) { const b = out.find((o) => Math.abs(key(o[0].r) - key(it.r)) <= 4); if (b) b.push(it); else out.push([it]); }
        return out;
      };
      for (const row of bucket((r) => r.y)) {
        row.sort((a, b) => a.r.x - b.r.x);
        if (row.length >= 3) {
          const gaps = row.slice(1).map((it, i) => it.r.x - (row[i].r.x + row[i].r.w));
          if (Math.max(...gaps) - Math.min(...gaps) >= 8) add('중간', '격자 간격 불균형', parent, `같은 줄 ${role(row[0].e).toLowerCase()} 사이 간격 ${gaps.map(Math.round).join('/')}px. 고치는 법: 부모에 gap 하나로 간격을 주고 개별 margin을 지운다`);
        }
        const boxes = row.filter((it) => boxedEl(it.e));
        if (boxes.length >= 2) {
          const hs = boxes.map((it) => it.r.h);
          if (Math.max(...hs) - Math.min(...hs) >= 8) add('중간', '격자 높이 불균형', parent, `같은 줄 상자 높이 ${hs.map(Math.round).join('/')}px. 고치는 법: 부모를 grid(align-items: stretch)로 두고 상자 안 내용은 .box-center로`);
        }
      }
      for (const col of bucket((r) => r.x)) {
        if (col.length < 3) continue;
        col.sort((a, b) => a.r.y - b.r.y);
        const gaps = col.slice(1).map((it, i) => it.r.y - (col[i].r.y + col[i].r.h));
        if (gaps.some((g) => g < -1)) continue;   // 겹친 열은 여러 줄 격자(행 버킷에서 본다)
        if (Math.max(...gaps) - Math.min(...gaps) >= 8) add('중간', '격자 간격 불균형', parent, `같은 열 ${role(col[0].e).toLowerCase()} 사이 간격 ${gaps.map(Math.round).join('/')}px. 고치는 법: 부모에 gap 하나로 간격을 주고 개별 margin을 지운다`);
      }
    }
  }
  return issues;
}

const { browser, page, blocked, sceneCount } = await openPresent(topic);
const report = { topic: path.relative(process.cwd(), topic), generated: new Date().toISOString(), min_font_px: minFont, min_fig_font_px: minFigFont, slides: [], summary: { 높음: 0, 중간: 0, 낮음: 0 } };
try {
  for (const n of parseSlides(argValue(argv, '--slides'), sceneCount)) {
    await gotoScene(page, n);
    const issues = await page.evaluate(inspectScene, { n, minFont, minFigFont, figSelectors });
    report.slides.push({ slide: n, issues });
    for (const it of issues) report.summary[it.severity] = (report.summary[it.severity] || 0) + 1;
  }
} finally {
  await browser.close();
}
if (blocked.length) {
  report.slides.unshift({ slide: 0, issues: [...new Set(blocked)].map((u) => ({ severity: '높음', type: '외부 요청', selector: '-', detail: u })) });
  report.summary.높음 += new Set(blocked).size;
}

const outDir = path.join(topic, '_work');
mkdirSync(outDir, { recursive: true });
const outFile = path.join(outDir, 'qa_check.json');
writeFileSync(outFile, JSON.stringify(report, null, 2) + '\n', 'utf8');

for (const s of report.slides) {
  for (const it of s.issues) log.info(`[${it.severity}] #${s.slide} ${it.type} — ${it.selector} — ${it.detail}`);
}
const { 높음, 중간, 낮음 } = report.summary;
if (rules.options && rules.options.vision_review === false) {
  // 비전 없음 모드(SKILL.md 4절 19항): 기계가 못 보는 항목은 통과로 두지 않고 사람에게 넘긴다
  const scenes = report.slides.filter((s) => s.slide > 0).map((s) => s.slide);
  report.vision_review = false;
  report.user_check = { scenes, items: ['세로 무게 중심의 미묘한 쏠림', '빈 여백 덩어리', '의미 단위 줄바꿈', '이미지 속 글자 가독성'] };
  writeFileSync(outFile, JSON.stringify(report, null, 2) + '\n', 'utf8');
  log.info(`비전 없음 모드: 눈 검수 미실시 — 사용자 확인 필요(${report.user_check.items.join('·')}) · 장면 ${scenes.join(', ')}`);
}
log.info(`QA ${report.slides.filter((s) => s.slide > 0).length}장: 높음 ${높음} · 중간 ${중간} · 낮음 ${낮음} → ${path.relative(process.cwd(), outFile)}`);
if (높음 > 0) {
  log.error('게이트 B: 높음이 0건이 될 때까지 사용자에게 검토를 요청하지 않는다.');
  process.exit(EXIT.FAIL);
}
process.exit(EXIT.OK);
