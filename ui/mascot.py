"""Mascot that pops up from random screen locations with dynamic animations."""
import json
import random

import streamlit.components.v1 as components

MESSAGES = [
    "Irina! 💧 Drink water RIGHT NOW.",
    "Hey — stretch your neck. You've been hunched. 🧘",
    "You're doing amazing. Genuinely. 🌟",
    "Snack break? You deserve it. 🍓",
    "Stand up for 30 seconds. Go. I'll wait. 🚶",
    "Procurement queen mode: ACTIVATED. 👑",
    "Remember to breathe. Slowly. In. Out. 🌿",
    "You've got this. Every single item on that list. 💪",
    "Don't forget to blink. Seriously. 👁️",
    "Take a sip of water. Now. 💧",
    "You're building something beautiful. ✨",
    "Go touch some grass after this. 🌱",
    "You're literally the best. No notes. 🤌",
    "Hydration check: failing. Fix it. 💦",
    "One product at a time. You're almost there. 🏁",
]

_MASCOT_HTML = """
<style>
/* hide Streamlit chrome that clashes with mascot */
[data-testid="manage-app-button"],
[data-testid="stDeployButton"],
.stDeployButton,
section[data-testid="stSidebar"] ~ div > div > button[title="Manage app"] {
  display: none !important;
}

#mb-wrap {
  position: fixed;
  z-index: 2147483647;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 175px;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transform: scale(0) rotate(-20deg);
}
#mb-wrap.mb-visible {
  opacity: 1;
  pointer-events: auto;
}
#mb-wrap.mb-pop {
  animation: mb-popin 0.6s cubic-bezier(.17,.89,.32,1.6) forwards;
}
#mb-wrap.mb-vanish {
  animation: mb-popout 0.35s cubic-bezier(.55,0,.45,1) forwards;
}
@keyframes mb-popin {
  0%%   { opacity:0; transform: scale(0) rotate(-25deg); }
  60%%  { opacity:1; transform: scale(1.18) rotate(6deg); }
  78%%  { transform: scale(0.9) rotate(-3deg); }
  90%%  { transform: scale(1.05) rotate(2deg); }
  100%% { opacity:1; transform: scale(1) rotate(0deg); }
}
@keyframes mb-popout {
  0%%   { opacity:1; transform: scale(1); }
  40%%  { transform: scale(1.1) rotate(8deg); }
  100%% { opacity:0; transform: scale(0) rotate(-15deg); }
}

#mb-bubble {
  background: #FFE500;
  color: #0D0D0D;
  border: 3px solid #0D0D0D;
  border-radius: 14px;
  padding: 13px 17px;
  font-family: Outfit, system-ui, sans-serif;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
  text-align: center;
  max-width: 170px;
  box-shadow: 5px 5px 0 #0D0D0D;
  position: relative;
  margin-bottom: 10px;
}
.mb-bubble-below {
  order: 2;
  margin-bottom: 0 !important;
  margin-top: 10px;
}
#mb-bubble::after {
  content: '';
  position: absolute;
  bottom: -15px;
  left: 50%%;
  transform: translateX(-50%%);
  border: 8px solid transparent;
  border-top-color: #0D0D0D;
}
#mb-bubble::before {
  content: '';
  position: absolute;
  bottom: -11px;
  left: 50%%;
  transform: translateX(-50%%);
  border: 6px solid transparent;
  border-top-color: #FFE500;
  z-index: 1;
}
.mb-bubble-below::after {
  bottom: auto; top: -15px;
  border-top-color: transparent;
  border-bottom-color: #0D0D0D;
}
.mb-bubble-below::before {
  bottom: auto; top: -11px;
  border-top-color: transparent;
  border-bottom-color: #FFE500;
}

#mb-bear {
  font-size: 70px;
  line-height: 1;
  filter: drop-shadow(0 4px 10px rgba(0,0,0,0.3));
  animation: mb-bob 2s ease-in-out infinite;
}
@keyframes mb-bob {
  0%%,100%% { transform: translateY(0) rotate(-3deg) scaleX(1); }
  25%%      { transform: translateY(-10px) rotate(4deg) scaleX(1.04); }
  75%%      { transform: translateY(-4px) rotate(-2deg) scaleX(0.97); }
}

#mb-dismiss {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 24px;
  height: 24px;
  border-radius: 50%%;
  background: #0D0D0D;
  color: #FFE500;
  font-size: 13px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.4);
}
</style>

<div id="mb-wrap">
  <div id="mb-bubble">
    <span id="mb-text"></span>
    <div id="mb-dismiss">✕</div>
  </div>
  <div id="mb-bear">🧸</div>
</div>

<script>
(function() {
  const messages = %s;
  let idx = %d;
  let hideTimer, nextTimer;

  const SPOTS = [
    { right:'24px', bottom:'80px', top:'auto', left:'auto' },
    { left:'24px',  bottom:'80px', top:'auto', right:'auto' },
    { right:'24px', top:'90px',  bottom:'auto', left:'auto' },
    { left:'24px',  top:'90px',  bottom:'auto', right:'auto' },
    { right:'24px', top:'40%%', bottom:'auto', left:'auto' },
    { left:'24px',  top:'40%%', bottom:'auto', right:'auto' },
    { left:'50%%',  bottom:'80px', top:'auto', right:'auto', transform:'translateX(-50%%)' },
    { left:'50%%',  top:'90px',  bottom:'auto', right:'auto', transform:'translateX(-50%%)' },
  ];

  function getWrap() {
    try { return window.parent.document.getElementById('mb-wrap'); }
    catch(e) { return document.getElementById('mb-wrap'); }
  }

  function getDoc() {
    try { return window.parent.document; }
    catch(e) { return document; }
  }

  function lift() {
    const src = document.getElementById('mb-wrap');
    const pdoc = getDoc();
    if (src && !pdoc.getElementById('mb-wrap')) {
      // inject styles into parent
      const styleEl = document.querySelector('style');
      if (styleEl) pdoc.head.appendChild(styleEl.cloneNode(true));
      pdoc.body.appendChild(src.cloneNode(true));
    }
  }

  function placeAtRandomSpot(wrap) {
    const spot = SPOTS[Math.floor(Math.random() * SPOTS.length)];
    wrap.style.right     = spot.right     || '';
    wrap.style.left      = spot.left      || '';
    wrap.style.top       = spot.top       || '';
    wrap.style.bottom    = spot.bottom    || '';
    wrap.style.transform = spot.transform || '';

    // Flip bubble below bear when appearing near top edge
    const bubble = wrap.querySelector('#mb-bubble');
    const bear   = wrap.querySelector('#mb-bear');
    if (bubble && bear) {
      if (spot.top && spot.top !== 'auto') {
        bubble.classList.add('mb-bubble-below');
        wrap.style.flexDirection = 'column-reverse';
      } else {
        bubble.classList.remove('mb-bubble-below');
        wrap.style.flexDirection = 'column';
      }
    }
  }

  function show() {
    const wrap = getWrap();
    if (!wrap) return;

    // reset animation state
    wrap.classList.remove('mb-pop', 'mb-vanish', 'mb-visible');
    void wrap.offsetWidth; // reflow

    // pick a spot and update message
    placeAtRandomSpot(wrap);
    const txt = wrap.querySelector('#mb-text');
    if (txt) txt.textContent = messages[idx %% messages.length];
    idx++;

    wrap.classList.add('mb-visible', 'mb-pop');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hide, 9000);
  }

  function hide() {
    const wrap = getWrap();
    if (!wrap) return;
    wrap.classList.remove('mb-pop');
    wrap.classList.add('mb-vanish');
    setTimeout(() => wrap.classList.remove('mb-visible', 'mb-vanish'), 400);
  }

  function scheduleNext() {
    const delay = 20000 + Math.random() * 15000; // 20-35s — keeps it surprising
    nextTimer = setTimeout(() => { show(); scheduleNext(); }, delay);
  }

  function init() {
    lift();
    const wrap = getWrap();
    if (!wrap) return;

    wrap.addEventListener('click', function(e) {
      e.stopPropagation();
      if (e.target.id === 'mb-dismiss' || e.target.closest('#mb-dismiss')) {
        hide(); return;
      }
      clearTimeout(hideTimer);
      clearTimeout(nextTimer);
      show();
      scheduleNext();
    });

    // first pop: 1.5-3s after load
    setTimeout(() => { show(); scheduleNext(); }, 1500 + Math.random() * 1500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
"""


def render_mascot() -> None:
    start_idx = random.randint(0, len(MESSAGES) - 1)
    components.html(
        _MASCOT_HTML % (json.dumps(MESSAGES), start_idx),
        height=0, width=0,
    )
