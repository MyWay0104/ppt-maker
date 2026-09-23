#!/usr/bin/env node
/**
 * export_pdf.mjs — present.html을 1920×1080 PDF로 내보내고, 필요하면 장면 스크린샷을 찍는다.
 *
 * 사용법:
 *   node export_pdf.mjs topics/<slug>               # exports/<slug>.pdf (게이트 C 필요)
 *   node export_pdf.mjs topics/<slug> --shots       # PDF + _work/shots/slide-NN.png
 *   node export_pdf.mjs topics/<slug> --shots-only  # 스크린샷만(검수용, 게이트 C 불필요)
 *   옵션: --slides 1,3-5 (스크린샷 대상), --out <pdf 경로>
 *
 * 게이트 C: BRIEF.md에 export_approved: true가 없으면 PDF를 만들지 않고 exit 4.
 *   사용자가 "최종 확인"이라고 말한 뒤에만 Claude가 BRIEF에 이 값을 쓴다.
 *
 * 검증: PDF 쪽수 = 장면 수, 외부 요청 0건. 어긋나면 exit 1.
 * 종료 코드: 0 성공 / 1 검증 실패 / 2 사용법·환경 오류 / 4 게이트 C
 */
import { mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { EXIT, argValue, gotoScene, log, openPresent, parseSlides, positional, readBrief, resolveTopic } from './lib/pw_common.mjs';

const argv = process.argv.slice(2);
const topic = resolveTopic(positional(argv, ['--slides', '--out']));
const shotsOnly = argv.includes('--shots-only');
const withShots = shotsOnly || argv.includes('--shots');
const slug = path.basename(topic);

// 게이트 C: 스크린샷만 찍는 검수 용도가 아니면 사용자 최종 승인이 있어야 한다
if (!shotsOnly) {
  const brief = readBrief(topic);
  if (String(brief.export_approved).toLowerCase() !== 'true') {
    log.error('게이트 C: BRIEF.md에 export_approved: true가 없다. 사용자가 "최종 확인"한 뒤에만 export한다.');
    log.error('검수용 스크린샷만 필요하면 --shots-only를 쓴다.');
    process.exit(EXIT.GATE_C);
  }
}

/** PDF 바이트에서 쪽 객체(/Type /Page) 수를 센다(/Pages 제외) */
function countPdfPages(buf) {
  const text = buf.toString('latin1');
  return (text.match(/\/Type\s*\/Page(?![a-zA-Z])/g) || []).length;
}

const { browser, page, blocked, sceneCount } = await openPresent(topic);
let failed = false;
try {
  if (!shotsOnly) {
    const out = path.resolve(typeof argValue(argv, '--out') === 'string' ? argValue(argv, '--out') : path.join(topic, 'exports', `${slug}.pdf`));
    mkdirSync(path.dirname(out), { recursive: true });
    await page.pdf({
      path: out,
      width: '1920px',
      height: '1080px',
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: '0', right: '0', bottom: '0', left: '0' },
    });
    const pages = countPdfPages(readFileSync(out));
    if (pages !== sceneCount) {
      log.error(`쪽수 불일치: PDF ${pages}쪽, 장면 ${sceneCount}장 — 넘치는 장면이 다음 쪽으로 밀렸을 수 있다(qa_check.mjs로 확인)`);
      failed = true;
    } else {
      log.info(`PDF: ${path.relative(process.cwd(), out)} (${pages}쪽 = 장면 ${sceneCount}장)`);
    }
  }

  if (withShots) {
    const dir = path.join(topic, '_work', 'shots');
    mkdirSync(dir, { recursive: true });
    const targets = parseSlides(argValue(argv, '--slides'), sceneCount);
    for (const n of targets) {
      await gotoScene(page, n);
      const file = path.join(dir, `slide-${String(n).padStart(2, '0')}.png`);
      await page.screenshot({ path: file, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    }
    log.info(`스크린샷: ${path.relative(process.cwd(), dir)} (${targets.length}장)`);
  }

  if (blocked.length) {
    log.error(`외부 요청 ${blocked.length}건을 막았다(오프라인 규칙 위반):`);
    [...new Set(blocked)].slice(0, 10).forEach((u) => log.error('  - ' + u));
    failed = true;
  } else {
    log.info('외부 요청: 0건');
  }
} finally {
  await browser.close();
}
process.exit(failed ? EXIT.FAIL : EXIT.OK);
