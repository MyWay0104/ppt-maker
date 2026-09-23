#!/usr/bin/env node
/**
 * export_pptx.mjs — present.html의 장면을 한 장씩 캡처해 16:9 PPTX로 만든다(선택 산출물).
 *
 * 사용법:
 *   node export_pptx.mjs topics/<slug>                    # exports/<slug>.pptx
 *   node export_pptx.mjs topics/<slug> --out <경로> --no-notes
 *
 * - 장면 이미지 한 장이 슬라이드 한 장을 꽉 채운다(글자 편집이 되는 PPTX가 아니다)
 * - 발표자 노트(.speaker-note)를 PPT 노트로 옮긴다
 * - 게이트 C: BRIEF.md export_approved: true가 없으면 exit 4
 * - 슬라이드 수 = 장면 수, 외부 요청 0건을 확인한다
 *
 * 종료 코드: 0 성공 / 1 검증 실패 / 2 사용법·환경 오류 / 4 게이트 C
 */
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import pptxgen from 'pptxgenjs';
import { EXIT, argValue, gotoScene, log, openPresent, positional, readBrief, resolveTopic } from './lib/pw_common.mjs';

const argv = process.argv.slice(2);
const topic = resolveTopic(positional(argv, ['--out']));
const slug = path.basename(topic);
const includeNotes = !argv.includes('--no-notes');

const brief = readBrief(topic);
if (String(brief.export_approved).toLowerCase() !== 'true') {
  log.error('게이트 C: BRIEF.md에 export_approved: true가 없다. 사용자가 "최종 확인"한 뒤에만 export한다.');
  process.exit(EXIT.GATE_C);
}

const out = path.resolve(typeof argValue(argv, '--out') === 'string' ? argValue(argv, '--out') : path.join(topic, 'exports', `${slug}.pptx`));
const tmp = mkdtempSync(path.join(os.tmpdir(), 'ppt-maker-pptx-'));
const { browser, page, blocked, sceneCount } = await openPresent(topic);
const captures = [];
try {
  for (let n = 1; n <= sceneCount; n++) {
    await gotoScene(page, n);
    const file = path.join(tmp, `slide-${String(n).padStart(2, '0')}.png`);
    await page.screenshot({ path: file, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    const note = includeNotes
      ? await page.evaluate((i) => document.querySelectorAll('#deck > .scene')[i]?.querySelector('.speaker-note')?.textContent?.trim() || '', n - 1)
      : '';
    captures.push({ file, note });
  }
} finally {
  await browser.close();
}

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';            // 13.333 × 7.5 인치 = 16:9
pptx.title = brief.title || slug;
pptx.subject = slug;
pptx.lang = 'ko-KR';
for (const { file, note } of captures) {
  const slide = pptx.addSlide();
  slide.addImage({ path: file, x: 0, y: 0, w: 13.333, h: 7.5 });
  if (note) slide.addNotes(note);
}
mkdirSync(path.dirname(out), { recursive: true });
await pptx.writeFile({ fileName: out });
rmSync(tmp, { recursive: true, force: true });

let failed = false;
if (captures.length !== sceneCount) {
  log.error(`슬라이드 수 불일치: ${captures.length} / 장면 ${sceneCount}`);
  failed = true;
}
if (blocked.length) {
  log.error(`외부 요청 ${blocked.length}건을 막았다(오프라인 규칙 위반): ${[...new Set(blocked)].slice(0, 5).join(', ')}`);
  failed = true;
}
log.info(`PPTX: ${path.relative(process.cwd(), out)} (${captures.length}장${includeNotes ? ', 노트 포함' : ''})`);
process.exit(failed ? EXIT.FAIL : EXIT.OK);
