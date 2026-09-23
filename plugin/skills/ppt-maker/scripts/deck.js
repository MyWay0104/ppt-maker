/*
 * deck.js — present.html 발표 런타임 (순수 JS, 외부 라이브러리 없음. build_present.py가 인라인한다)
 *
 * 기능
 *   - 1920×1080 장면을 화면에 맞게 축소(--scale), .scene.active 한 장만 보이기
 *   - 전환: document.startViewTransition 지원 시 사용, 아니면 CSS opacity 전환
 *   - 주소 해시 #N (새로고침해도 같은 장면)
 *   - 키보드: → Space PageDown 다음 / ← PageUp 이전 / Home End / F 풀스크린 / S 발표자 창 / Esc 풀스크린 해제
 *   - 클릭(오른쪽 절반 다음, 왼쪽 절반 이전), 터치 스와이프
 *   - 발표자 창(?presenter): 현재·다음 축소 화면, 발표자 노트, 타이머, 시계
 *   - 두 창 동기화: BroadcastChannel('ppt-maker:<slug>'), 없으면 localStorage 폴백
 *     (file://에서는 창끼리 통신이 막힐 수 있다 → serve_live.py로 http로 연다)
 */
(function () {
  'use strict';

  const W = 1920;
  const H = 1080;
  const deck = document.getElementById('deck');
  const scenes = Array.from(deck.querySelectorAll(':scope > .scene'));
  const slugMeta = document.querySelector('meta[name="ppt-maker-slug"]');
  const slug = slugMeta ? slugMeta.content : location.pathname;
  const isPresenter = new URLSearchParams(location.search).has('presenter');
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const useVT = typeof document.startViewTransition === 'function' && !reduceMotion && !isPresenter;
  let current = 0;

  if (useVT) document.documentElement.classList.add('vt');

  /* ============ 창 사이 통신(무전기) ============ */
  const channelName = 'ppt-maker:' + slug;
  const storageKey = channelName + ':msg';
  const channel = ('BroadcastChannel' in window) ? new BroadcastChannel(channelName) : null;

  /** 다른 창에 메시지를 보낸다. BroadcastChannel이 없으면 localStorage storage 이벤트로 흉내 낸다. */
  function broadcast(msg) {
    if (channel) channel.postMessage(msg);
    else {
      try { localStorage.setItem(storageKey, JSON.stringify({ ...msg, t: Date.now() })); } catch (e) { /* 저장소 막힘 */ }
    }
  }

  /** 다른 창의 메시지를 받는다. */
  function onMessage(handler) {
    if (channel) channel.onmessage = (e) => handler(e.data);
    else window.addEventListener('storage', (e) => {
      if (e.key === storageKey && e.newValue) handler(JSON.parse(e.newValue));
    });
  }

  /* ============ 배율 ============ */
  /** 화면 크기에 맞는 축소 배율을 계산해 CSS 변수 --scale에 넣는다. 작은 쪽 배율을 골라야 종이가 넘치지 않는다. */
  function fit() {
    const scale = Math.min(window.innerWidth / W, window.innerHeight / H);
    document.documentElement.style.setProperty('--scale', String(scale));
    if (isPresenter) fitPresenter();
  }

  /* ============ 장면 전환 ============ */
  /**
   * n번째(0부터) 장면을 보여 준다. 범위를 벗어나면 끝에서 멈춘다.
   * @param {number} n
   * @param {{pushHash?: boolean, notify?: boolean}} [opts] notify=false면 다른 창에 알리지 않는다(메아리 방지)
   */
  function show(n, opts) {
    const { pushHash = true, notify = true } = opts || {};
    if (!scenes.length) return;
    n = Math.max(0, Math.min(scenes.length - 1, n));
    const apply = () => {
      scenes.forEach((s, i) => s.classList.toggle('active', i === n));
      current = n;
      if (isPresenter) renderPresenter();
    };
    if (useVT && n !== current) document.startViewTransition(apply);
    else apply();
    if (pushHash) history.replaceState(null, '', location.pathname + location.search + '#' + (n + 1));
    if (notify) broadcast({ type: 'goto', index: n });
  }

  /** 주소 해시(#5)를 읽어 장면을 정한다. */
  function fromHash() {
    const n = parseInt(location.hash.replace('#', ''), 10);
    show(Number.isFinite(n) ? n - 1 : 0, { pushHash: false, notify: false });
  }

  function toggleFullscreen() {
    if (document.fullscreenElement) document.exitFullscreen();
    else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
  }

  /** S 키: 같은 파일을 ?presenter로 새 창에 연다 */
  function openPresenter() {
    const url = location.pathname + '?presenter#' + (current + 1);
    window.open(url, 'ppt-maker-presenter', 'width=1280,height=800');
  }

  /* ============ 입력 ============ */
  document.addEventListener('keydown', (e) => {
    if (e.target && e.target.isContentEditable) return;
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    switch (e.key) {
      case 'ArrowRight': case ' ': case 'PageDown': show(current + 1); break;
      case 'ArrowLeft': case 'PageUp': show(current - 1); break;
      case 'Home': show(0); break;
      case 'End': show(scenes.length - 1); break;
      case 'f': case 'F': toggleFullscreen(); break;
      case 's': case 'S': if (!isPresenter) openPresenter(); break;
      case 'Escape': if (document.fullscreenElement) document.exitFullscreen(); break;
      default: return;
    }
    e.preventDefault();
  });

  deck.addEventListener('click', (e) => {
    if (e.target.closest('a, button, input, [contenteditable]')) return;
    show(e.clientX > window.innerWidth / 2 ? current + 1 : current - 1);
  });

  let touchX = null;
  document.addEventListener('touchstart', (e) => { touchX = e.touches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', (e) => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 50) show(dx < 0 ? current + 1 : current - 1);
    touchX = null;
  });

  // 다른 창에서 넘기면 따라간다. 받은 메시지는 다시 알리지 않는다.
  onMessage((m) => {
    if (m && m.type === 'goto' && m.index !== current) show(m.index, { notify: false });
  });

  /* ============ 발표자 창 ============ */
  let pv = null;
  let timerStart = Date.now();

  /** 발표자 화면 뼈대를 만든다: 현재 / 다음 / 노트 / 하단 막대(장수·타이머·시계) */
  function buildPresenterUI() {
    document.body.classList.add('presenter');
    const root = document.createElement('div');
    root.id = 'presenter';
    root.innerHTML =
      '<div class="pv-cur"><div class="pv-label">현재</div><div class="pv-frame" id="pv-cur"></div></div>' +
      '<div class="pv-next"><div class="pv-label">다음</div><div class="pv-frame" id="pv-next"></div></div>' +
      '<div class="pv-notes" id="pv-notes"></div>' +
      '<div class="pv-bar">' +
      '<span class="pv-count" id="pv-count"></span>' +
      '<span class="pv-timer" id="pv-timer">00:00</span>' +
      '<button type="button" id="pv-reset">타이머 초기화</button>' +
      '<span class="pv-clock" id="pv-clock"></span>' +
      '</div>';
    document.body.appendChild(root);
    pv = {
      cur: root.querySelector('#pv-cur'),
      next: root.querySelector('#pv-next'),
      notes: root.querySelector('#pv-notes'),
      count: root.querySelector('#pv-count'),
      timer: root.querySelector('#pv-timer'),
      clock: root.querySelector('#pv-clock'),
    };
    root.querySelector('#pv-reset').addEventListener('click', () => { timerStart = Date.now(); tick(); });
    setInterval(tick, 1000);
    tick();
  }

  const pad2 = (n) => String(n).padStart(2, '0');

  /** 1초마다 경과 시간과 현재 시각을 갱신한다 */
  function tick() {
    if (!pv) return;
    const sec = Math.floor((Date.now() - timerStart) / 1000);
    pv.timer.textContent = pad2(Math.floor(sec / 60)) + ':' + pad2(sec % 60);
    const now = new Date();
    pv.clock.textContent = pad2(now.getHours()) + ':' + pad2(now.getMinutes());
  }

  /** 프레임 폭에 맞춰 장면 복제본의 축소 배율을 정한다 */
  function fitPresenter() {
    if (!pv) return;
    [pv.cur, pv.next].forEach((frame) => {
      frame.style.setProperty('--pv-scale', String(frame.clientWidth / W));
    });
  }

  /** 장면 복제본(발표자 노트는 숨김 유지) */
  function cloneScene(i) {
    const c = scenes[i].cloneNode(true);
    c.classList.add('active');
    c.removeAttribute('id');
    return c;
  }

  /** 현재·다음 장면, 노트, 장수를 다시 그린다 */
  function renderPresenter() {
    if (!pv) return;
    pv.cur.replaceChildren(cloneScene(current));
    if (current + 1 < scenes.length) pv.next.replaceChildren(cloneScene(current + 1));
    else {
      const end = document.createElement('div');
      end.className = 'pv-end';
      end.textContent = '마지막 장면입니다';
      pv.next.replaceChildren(end);
    }
    const note = scenes[current].querySelector('.speaker-note');
    const text = note ? note.textContent.trim() : '';
    pv.notes.textContent = text || '(이 장면에는 발표자 노트가 없습니다)';
    pv.notes.classList.toggle('empty', !text);
    pv.count.textContent = (current + 1) + ' / ' + scenes.length;
    fitPresenter();
  }

  /* ============ 시작 ============ */
  if (isPresenter) buildPresenterUI();
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', fromHash);
  fit();
  fromHash();

  // 자동 검사(Playwright)에서 상태를 읽을 수 있게 최소한만 노출한다
  window.pptDeck = { get current() { return current; }, count: scenes.length, show: (n) => show(n) };
})();
