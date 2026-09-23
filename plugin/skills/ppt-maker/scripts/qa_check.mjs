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
 *   중간  상자 안 쏠림 카드 안 내용이 위로 붙어 아래 여백이 위보다 60px 이상·2배 초과
 *   중간  세로 빈 띠 위아래 빈 띠가 각 150px 이상이거나 요소 사이가 150px 이상 벌어짐(title·quote 제외)
 *   중간  이미지 축소 과다 원본 대비 0.5배 미만으로 줄여 넣음(캡처 속 글자가 안 읽힐 수 있음)
 *   낮음  이미지 확대 원본을 1.5배 넘게 키움(흐릴 수 있음)
 *   낮음  명암비 확인 필요 — 배경이 그라데이션·이미지라 자동 계산 불가(눈 검수)
 *
 * 기계가 못 잡는 것(세로 무게 중심의 미묘한 쏠림·가로 빈 여백·고아 줄바꿈·격자 간격 불균형)은
 * _work/shots/ 스크린샷으로 deck-reviewer가 따로 본다. 이 스크립트 통과 ≠ 검수 완료.
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
log.info(`QA ${report.slides.filter((s) => s.slide > 0).length}장: 높음 ${높음} · 중간 ${중간} · 낮음 ${낮음} → ${path.relative(process.cwd(), outFile)}`);
if (높음 > 0) {
  log.error('게이트 B: 높음이 0건이 될 때까지 사용자에게 검토를 요청하지 않는다.');
  process.exit(EXIT.FAIL);
}
process.exit(EXIT.OK);
