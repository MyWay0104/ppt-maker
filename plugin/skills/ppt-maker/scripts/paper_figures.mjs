#!/usr/bin/env node
/**
 * paper_figures.mjs — 논문 PDF에서 그림(Figure) 후보를 찾아 쪽 이미지로 그리고, 고른 영역을 잘라 PNG로 만든다.
 *
 * 사용법:
 *   # 1) 목록: 쪽마다 PNG를 그리고 "Figure N / Fig. N" 설명 위치를 figures.json에 적는다
 *   node paper_figures.mjs <논문.pdf | https://arxiv.org/abs/2401.00001> --out topics/<slug>/_work/figures [--pages 1-12] [--scale 2]
 *
 *   # 2) 자르기: 쪽 PNG를 눈으로 본 뒤 그림 영역(쪽 PNG 픽셀 좌표)을 잘라 후보 파일로
 *   node paper_figures.mjs <논문.pdf> --out topics/<slug>/_work/figures --crop 3:120,210,980,640 --name fig2-architecture
 *
 * 흐름(ppt-maker references/images.md 3절):
 *   목록 → page-NN.png를 Read로 보고 그림 영역 좌표를 정한다 → --crop → 잘린 PNG를 Read로 확인
 *   → 사용자에게 후보를 보여 주고 승인받은 것만 assets/img/로 옮긴다(출처 줄: "Fig. N, 논문 제목(연도)").
 *
 * 구현:
 *   - pdf.js(pdfjs-dist)를 Playwright Chromium 안에서 돌린다. 브라우저는 가짜 주소 http://pdf.local/로 로컬 파일만 받는다(외부 요청 없음).
 *   - arXiv 주소(abs·pdf)나 http(s) PDF 주소를 주면 PDF를 한 번 내려받아 --out 폴더에 paper.pdf로 둔다.
 *
 * 출력: --out 폴더에 page-NN.png, figures.json(쪽 크기·설명 목록), 자르기 결과 <name>.png
 * 종료 코드: 0 성공 / 2 사용법·입력 오류
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { EXIT, argValue, log } from './lib/pw_common.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PDFJS = path.join(HERE, 'node_modules', 'pdfjs-dist', 'legacy', 'build');
const ORIGIN = 'http://pdf.local';

const argv = process.argv.slice(2);
const input = argv.find((a, i) => !a.startsWith('--') && !['--out', '--pages', '--scale', '--crop', '--name'].includes(argv[i - 1]));
const outDir = argValue(argv, '--out');
const scale = Number(argValue(argv, '--scale') || 2);
const crop = argValue(argv, '--crop');
const cropName = argValue(argv, '--name') || 'figure';

if (!input || !outDir) {
  log.error('사용법: node paper_figures.mjs <논문.pdf | arXiv·PDF 주소> --out <폴더> [--pages 1-12] [--scale 2] [--crop 쪽:x,y,w,h --name 이름]');
  process.exit(EXIT.USAGE);
}
if (!existsSync(path.join(PDFJS, 'pdf.mjs'))) {
  log.error(`pdf.js가 없다: ${PDFJS}\n먼저: npm install --prefix ${HERE}`);
  process.exit(EXIT.USAGE);
}
mkdirSync(outDir, { recursive: true });

/**
 * 입력을 로컬 PDF 경로로 바꾼다. arXiv abs 주소는 pdf 주소로 고쳐 내려받는다.
 * @param {string} src
 * @returns {Promise<string>}
 */
async function resolvePdf(src) {
  if (!/^https?:\/\//i.test(src)) {
    if (!existsSync(src)) {
      log.error(`PDF가 없다: ${src}`);
      process.exit(EXIT.USAGE);
    }
    return path.resolve(src);
  }
  const url = src.replace(/arxiv\.org\/abs\//i, 'arxiv.org/pdf/');
  const dest = path.join(outDir, 'paper.pdf');
  if (existsSync(dest)) return dest;
  log.info(`내려받기: ${url}`);
  const res = await fetch(url, { redirect: 'follow' });
  const type = res.headers.get('content-type') || '';
  if (!res.ok || !type.includes('pdf')) {
    log.error(`PDF를 받지 못했다: HTTP ${res.status}, content-type=${type}`);
    process.exit(EXIT.USAGE);
  }
  writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
  writeFileSync(path.join(outDir, 'source.txt'), `${src}\n`, 'utf-8');
  return dest;
}

/**
 * "1-3,5" 같은 쪽 범위를 번호 배열로. 비우면 전체.
 * @param {string|undefined} spec
 * @param {number} count
 */
function pageList(spec, count) {
  if (!spec) return Array.from({ length: count }, (_, i) => i + 1);
  const out = new Set();
  for (const part of spec.split(',')) {
    const [a, b] = part.split('-').map(Number);
    for (let n = a; n <= (b || a); n++) if (n >= 1 && n <= count) out.add(n);
  }
  return [...out].sort((x, y) => x - y);
}

const pdfPath = await resolvePdf(input);
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  // 가짜 주소로 pdf.js 파일과 논문 PDF만 내준다. 그 밖의 요청은 막는다
  await page.route('**/*', (route) => {
    const url = new URL(route.request().url());
    if (url.origin !== ORIGIN) return route.abort();
    if (url.pathname === '/') return route.fulfill({ contentType: 'text/html', body: '<!doctype html><meta charset="utf-8"><body></body>' });
    if (url.pathname === '/paper.pdf') return route.fulfill({ contentType: 'application/pdf', body: readFileSync(pdfPath) });
    const file = path.join(PDFJS, path.basename(url.pathname));
    if (existsSync(file)) return route.fulfill({ contentType: 'text/javascript', body: readFileSync(file) });
    return route.fulfill({ status: 404, body: '' });
  });
  await page.goto(`${ORIGIN}/`);

  const count = await page.evaluate(async (origin) => {
    const lib = await import(`${origin}/pdf.mjs`);
    lib.GlobalWorkerOptions.workerSrc = `${origin}/pdf.worker.mjs`;
    window.__doc = await lib.getDocument(`${origin}/paper.pdf`).promise;
    return window.__doc.numPages;
  }, ORIGIN);

  /** 브라우저 안에서 한 쪽을 그려 PNG(base64)와 그림 설명 위치를 돌려준다. crop이 있으면 그 영역만 */
  const renderPage = (n, box) => page.evaluate(async ({ n, scale, box }) => {
    const p = await window.__doc.getPage(n);
    const vp = p.getViewport({ scale });
    const canvas = document.createElement('canvas');
    canvas.width = Math.ceil(vp.width);
    canvas.height = Math.ceil(vp.height);
    await p.render({ canvasContext: canvas.getContext('2d'), viewport: vp }).promise;
    const text = await p.getTextContent();
    const captions = [];
    for (const it of text.items) {
      if (!/^\s*(Figure|Fig\.)\s*\d+/i.test(it.str)) continue;
      const [x, y] = vp.convertToViewportPoint(it.transform[4], it.transform[5]);
      captions.push({ text: it.str.trim().slice(0, 120), x: Math.round(x), y: Math.round(y) });
    }
    let out = canvas;
    if (box) {
      out = document.createElement('canvas');
      out.width = box.w;
      out.height = box.h;
      out.getContext('2d').drawImage(canvas, box.x, box.y, box.w, box.h, 0, 0, box.w, box.h);
    }
    return { png: out.toDataURL('image/png').split(',')[1], width: canvas.width, height: canvas.height, captions };
  }, { n, scale, box });

  if (crop) {
    const m = crop.match(/^(\d+):(\d+),(\d+),(\d+),(\d+)$/);
    if (!m) {
      log.error('--crop 형식: 쪽:x,y,w,h (쪽 PNG 픽셀 좌표, 같은 --scale 기준)');
      process.exit(EXIT.USAGE);
    }
    const [n, x, y, w, h] = m.slice(1).map(Number);
    const r = await renderPage(n, { x, y, w, h });
    const dest = path.join(outDir, `${cropName}.png`);
    writeFileSync(dest, Buffer.from(r.png, 'base64'));
    log.info(`잘라냄: ${dest} (${w}×${h}, ${n}쪽)`);
  } else {
    const pages = pageList(argValue(argv, '--pages'), count);
    const report = { pdf: pdfPath, scale, pages: [] };
    for (const n of pages) {
      const r = await renderPage(n, null);
      const name = `page-${String(n).padStart(2, '0')}.png`;
      writeFileSync(path.join(outDir, name), Buffer.from(r.png, 'base64'));
      report.pages.push({ page: n, file: name, width: r.width, height: r.height, captions: r.captions });
      if (r.captions.length) log.info(`${n}쪽: ${r.captions.map((c) => c.text.slice(0, 40)).join(' | ')}`);
    }
    writeFileSync(path.join(outDir, 'figures.json'), JSON.stringify(report, null, 2), 'utf-8');
    const total = report.pages.reduce((s, p) => s + p.captions.length, 0);
    log.info(`${pages.length}쪽을 그렸다 · 그림 설명 ${total}개 → ${path.join(outDir, 'figures.json')}`);
  }
} finally {
  await browser.close();
}
