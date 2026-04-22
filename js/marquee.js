// Dual-band scrolling marquee engine.
// Usage: initMarquee({ images: ["images/foo.webp", ...] })
// The calling page must provide:
//   <div class="marquee top"><div class="track" id="track-top"></div></div>
//   <div class="marquee bottom"><div class="track" id="track-bottom"></div></div>

function initMarquee({ images }) {
  const TOP_DURATION = 95;
  const BOT_DURATION = 115;
  const SPIN_HALF    = 1.2;
  const IDLE_MS      = 40;   // mousemove silence treated as end-of-drag (trackpad grace window)
  const FLICK_VEL    = 200;  // px/s — only flicks trigger early release

  function shuffled(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function buildTrack(el, srcs) {
    srcs.concat(srcs).forEach(src => {
      const img = document.createElement('img');
      img.src      = src;
      img.decoding = 'async';
      img.loading  = 'eager';
      el.appendChild(img);
    });
  }

  const pool   = shuffled(images);
  const trackTop = document.getElementById('track-top');
  const trackBot = document.getElementById('track-bottom');
  buildTrack(trackTop, pool.slice(0, 6));
  buildTrack(trackBot, pool.slice(6));

  let topHW = 1, botHW = 1;
  let topSpeed = 0, botSpeed = 0;
  let topDisp = 0, botDisp = 0;

  function wrapTop() {
    while (topDisp >       0) topDisp -= topHW;
    while (topDisp < -topHW) topDisp += topHW;
  }
  function wrapBot() {
    while (botDisp >       0) botDisp -= botHW;
    while (botDisp < -botHW) botDisp += botHW;
  }
  function applyTransform() {
    trackTop.style.transform = `translateX(${topDisp}px)`;
    trackBot.style.transform = `translateX(${botDisp}px)`;
  }

  let dragging  = false;
  let prevDragX = 0;
  let prevVelX  = 0;
  let prevVelT  = 0;
  let dragVel   = 0;
  let grabDir   = 1;
  let spin      = 0;
  let dragIdleTimer = null;
  let earlyReleased = false;
  let startX = 0, startY = 0, locked = null;

  function pDown(x, clientY) {
    clearTimeout(dragIdleTimer); dragIdleTimer = null;
    earlyReleased = false;
    dragging  = true;
    prevDragX = x;
    prevVelX  = x;
    prevVelT  = performance.now();
    dragVel   = 0;
    spin      = 0;
    grabDir   = clientY < window.innerHeight / 2 ? 1 : -1;
    startX    = x;
    startY    = clientY;
    locked    = null;
    document.body.classList.add('dragging');
  }

  function scheduleIdleCheck() {
    clearTimeout(dragIdleTimer);
    dragIdleTimer = setTimeout(() => {
      dragIdleTimer = null;
      if (!dragging || earlyReleased) return;
      if (Math.abs(dragVel) > FLICK_VEL) {
        earlyReleased = true;
        dragging = false;
        spin = dragVel * grabDir;
        document.body.classList.remove('dragging');
      }
    }, IDLE_MS);
  }

  function pMove(x, y) {
    if (earlyReleased) {
      earlyReleased = false;
      dragging  = true;
      prevDragX = x;
      prevVelX  = x;
      prevVelT  = performance.now();
      dragVel   = 0;
      spin      = 0;
      startX    = x;
      startY    = y;
      locked    = null;
      document.body.classList.add('dragging');
      return;
    }
    if (!dragging) return;

    // Direction lock: once the gesture clears a small threshold, classify it
    // as horizontal (carousel) or vertical (page-flip). Vertical gestures
    // abandon the drag silently so a swipe-up to navigate doesn't also
    // drive the carousel sideways.
    if (locked === null) {
      const dx = x - startX, dy = y - startY;
      if (Math.hypot(dx, dy) > 10) {
        if (Math.abs(dy) > Math.abs(dx)) {
          dragging = false;
          dragVel  = 0;
          clearTimeout(dragIdleTimer); dragIdleTimer = null;
          document.body.classList.remove('dragging');
          locked = 'v';
          return;
        }
        locked = 'h';
      }
    }

    const now   = performance.now();
    const delta = x - prevDragX;
    prevDragX   = x;

    const velDt = (now - prevVelT) / 1000;
    if (velDt > 0.004) {
      dragVel  = (x - prevVelX) / velDt;
      prevVelX = x;
      prevVelT = now;
    }

    topDisp += delta * grabDir;
    botDisp -= delta * grabDir;
    wrapTop(); wrapBot();
    applyTransform();
    scheduleIdleCheck();
  }

  function pUp() {
    clearTimeout(dragIdleTimer); dragIdleTimer = null;
    if (earlyReleased) { earlyReleased = false; return; }
    if (!dragging) return;
    dragging = false;
    spin = dragVel * grabDir;
    document.body.classList.remove('dragging');
  }

  document.addEventListener('mousedown',  e => { e.preventDefault(); pDown(e.clientX, e.clientY); });
  document.addEventListener('mousemove',  e => pMove(e.clientX, e.clientY));
  document.addEventListener('mouseup',    ()  => pUp());
  document.addEventListener('mouseleave', ()  => pUp());

  document.addEventListener('touchstart', e => pDown(e.touches[0].clientX, e.touches[0].clientY), { passive: true });
  document.addEventListener('touchmove',  e => pMove(e.touches[0].clientX, e.touches[0].clientY), { passive: true });
  document.addEventListener('touchend',   ()  => pUp());

  let lastT = 0;

  function frame(now) {
    const dt = Math.min(0.05, (now - lastT) / 1000);
    lastT = now;

    if (!dragging) {
      if (spin !== 0) {
        spin *= Math.pow(0.5, dt / SPIN_HALF);
        if (Math.abs(spin) < 0.5) spin = 0;
      }
      topDisp += (-topSpeed + spin) * dt;
      botDisp += ( botSpeed - spin) * dt;
      wrapTop(); wrapBot();
      applyTransform();
    }

    requestAnimationFrame(frame);
  }

  const allImgs = [...document.querySelectorAll('.track img')];
  Promise.all(allImgs.map(img =>
    img.decode().catch(() => new Promise(res => {
      img.addEventListener('load',  res, { once: true });
      img.addEventListener('error', res, { once: true });
    }))
  )).then(() => {
    topHW    = trackTop.scrollWidth / 2;
    botHW    = trackBot.scrollWidth / 2;
    topSpeed = topHW / TOP_DURATION;
    botSpeed = botHW / BOT_DURATION;
    topDisp  = 0;
    botDisp  = -botHW;
    document.body.classList.add('ready');
    requestAnimationFrame(t => { lastT = t; frame(t); });
  });

  setTimeout(() => document.body.classList.add('ready'), 4000);
}
