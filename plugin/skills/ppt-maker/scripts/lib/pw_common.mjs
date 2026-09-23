/**
 * pw_common.mjs — export_pdf.mjs·qa_check.mjs·export_pptx.mjs가 함께 쓰는 Playwright 도우미.
 *
 * - topic 경로 해석, BRIEF front matter·deck-rules.json 읽기
 * - present.html 신선도 확인(overview.html보다 오래됐으면 실패 → build_present.py 먼저)
 * - Chromium 1920×1080 기동, 움직임 줄이기(전환 애니메이션 끔)
 * - 외부 http(s) 요청 차단·기록(오프라인 규칙 위반을 드러낸다)
 * - document.fonts.ready 대기
 */
import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

export const W = 1920;
export const H = 1080;

/** 종료 코드: 0 성공 / 1 검사 실패 / 2 사용법·환경 오류 / 4 게이트 C(export 미승인) */
export const EXIT = { OK: 0, FAIL: 1, USAGE: 2, GATE_C: 4 };

/** 한국어 로그를 한 줄씩 출력한다(console.log 대신 이 함수만 쓴다) */
export const log = {
  info: (...a) => process.stdout.write(a.join(' ') + '\n'),
  error: (...a) => process.stderr.write(a.join(' ') + '\n'),
};

/** 명령줄에서 topic 폴더를 절대 경로로 */
export function resolveTopic(arg) {
  if (!arg) {
    log.error('사용법: node <script> topics/<slug> [옵션]');
    process.exit(EXIT.USAGE);
  }
  const topic = path.resolve(arg);
  if (!existsSync(path.join(topic, 'overview.html'))) {
    log.error(`overview.html이 없다: ${topic}`);
    process.exit(EXIT.USAGE);
  }
  return topic;
}

/** BRIEF.md 맨 위 --- 사이 `키: 값`을 읽는다 */
export function readBrief(topic) {
  const p = path.join(topic, 'BRIEF.md');
  if (!existsSync(p)) return {};
  const m = readFileSync(p, 'utf8').match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!m) return {};
  const out = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*(?:#.*)?$/);
    if (kv) out[kv[1]] = kv[2].replace(/^["']|["']$/g, '');
  }
  return out;
}

/** deck-rules.json (없으면 빈 객체) */
export function readRules(topic) {
  const p = path.join(topic, 'deck-rules.json');
  if (!existsSync(p)) return {};
  try { return JSON.parse(readFileSync(p, 'utf8')); } catch { return {}; }
}

/**
 * present.html이 있고 overview.html보다 새것인지 확인한다.
 * 파생 파일 재생성이 QA의 첫 단계라는 규칙을 스크립트가 강제한다.
 */
export function assertFreshPresent(topic) {
  const present = path.join(topic, 'present.html');
  const overview = path.join(topic, 'overview.html');
  if (!existsSync(present)) {
    log.error(`present.html이 없다 → 먼저: python build_present.py ${path.relative(process.cwd(), topic)}`);
    process.exit(EXIT.USAGE);
  }
  if (statSync(present).mtimeMs + 1 < statSync(overview).mtimeMs) {
    log.error(`present.html이 overview.html보다 오래됐다 → 먼저: python build_present.py ${path.relative(process.cwd(), topic)}`);
    process.exit(EXIT.USAGE);
  }
  return present;
}

/**
 * 브라우저를 띄우고 present.html을 연다.
 * @returns {{browser, page, blocked: string[], sceneCount: number}}
 */
export async function openPresent(topic, { hash = 1 } = {}) {
  const present = assertFreshPresent(topic);
  let browser;
  try {
    browser = await chromium.launch();
  } catch (err) {
    log.error('Chromium을 띄우지 못했다. 설치: npx playwright install chromium');
    log.error(String(err.message || err).split('\n')[0]);
    process.exit(EXIT.USAGE);
  }
  const context = await browser.newContext({
    viewport: { width: W, height: H },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',       // deck.js가 View Transitions·CSS 전환을 끈다 → 캡처가 흔들리지 않는다
  });
  const page = await context.newPage();
  const blocked = [];
  await page.route(/^https?:\/\//, (route) => {   // file://로 연 발표 파일이 밖으로 나가면 모두 막고 기록
    blocked.push(route.request().url());
    return route.abort();
  });
  await page.goto(pathToFileURL(present).href + '#' + hash, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const sceneCount = await page.evaluate(() => document.querySelectorAll('#deck > .scene').length);
  return { browser, page, blocked, sceneCount };
}

/** n번(1부터) 장면으로 이동하고 그려질 때까지 기다린다 */
export async function gotoScene(page, n) {
  await page.evaluate((i) => window.pptDeck.show(i), n - 1);
  await page.waitForFunction((i) => window.pptDeck.current === i, n - 1);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
}

/** "1,3-5" → [1,3,4,5] (범위 밖은 버린다) */
export function parseSlides(spec, count) {
  if (!spec) return Array.from({ length: count }, (_, i) => i + 1);
  const set = new Set();
  for (const part of String(spec).split(',')) {
    const m = part.trim().match(/^(\d+)(?:-(\d+))?$/);
    if (!m) continue;
    const a = Number(m[1]);
    const b = m[2] ? Number(m[2]) : a;
    for (let i = Math.min(a, b); i <= Math.max(a, b); i++) if (i >= 1 && i <= count) set.add(i);
  }
  return [...set].sort((x, y) => x - y);
}

/** 명령줄 인자에서 --name 값 또는 플래그를 읽는다 */
export function argValue(argv, name) {
  const i = argv.indexOf(name);
  if (i === -1) return undefined;
  const v = argv[i + 1];
  return v && !v.startsWith('--') ? v : true;
}

/**
 * 첫 위치 인자(옵션이 아닌 값)를 찾는다. valueOpts에 적힌 옵션 바로 뒤의 값은 건너뛴다.
 * 예) ['--slides', '2', 'topics/a'] → 'topics/a'
 */
export function positional(argv, valueOpts = []) {
  for (let i = 0; i < argv.length; i++) {
    if (valueOpts.includes(argv[i])) { i++; continue; }
    if (!argv[i].startsWith('--')) return argv[i];
  }
  return undefined;
}
