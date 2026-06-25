"""A very-in-your-face mascot that pops in from the bottom of the screen."""
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
    "Irina says: take a sip of water. Now. 💧",
    "You're building something beautiful. ✨",
    "A little sunshine wouldn't hurt. Step outside? ☀️",
]

_MASCOT_HTML = """
<style>
#mb-wrap {
  position: fixed;
  bottom: -240px;
  right: 28px;
  z-index: 999999;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 180px;
  cursor: pointer;
  transition: none;
}
#mb-wrap.mb-show {
  animation: mb-bounce-in 0.55s cubic-bezier(.17,.67,.35,1.4) forwards;
}
#mb-wrap.mb-hide {
  animation: mb-slide-out 0.4s ease-in forwards;
}
@keyframes mb-bounce-in {
  0%%   { bottom: -240px; }
  60%%  { bottom: 28px; }
  75%%  { bottom: 12px; }
  88%%  { bottom: 34px; }
  100%% { bottom: 22px; }
}
@keyframes mb-slide-out {
  from { bottom: 22px; opacity: 1; }
  to   { bottom: -240px; opacity: 0; }
}
#mb-bubble {
  background: #FFE500;
  color: #0D0D0D;
  border: 3px solid #0D0D0D;
  border-radius: 12px;
  padding: 12px 16px;
  font-family: Outfit, sans-serif;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.35;
  text-align: center;
  max-width: 170px;
  box-shadow: 4px 4px 0 #0D0D0D;
  position: relative;
  margin-bottom: 8px;
}
#mb-bubble::after {
  content: '';
  position: absolute;
  bottom: -14px;
  left: 50%%;
  transform: translateX(-50%%);
  border: 7px solid transparent;
  border-top-color: #0D0D0D;
}
#mb-bubble::before {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%%;
  transform: translateX(-50%%);
  border: 6px solid transparent;
  border-top-color: #FFE500;
  z-index: 1;
}
#mb-bear {
  font-size: 72px;
  line-height: 1;
  animation: mb-bob 1.8s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.25));
}
@keyframes mb-bob {
  0%%, 100%% { transform: translateY(0) rotate(-2deg); }
  50%%       { transform: translateY(-8px) rotate(3deg); }
}
#mb-dismiss {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 22px;
  height: 22px;
  border-radius: 50%%;
  background: #0D0D0D;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
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
  let timer;

  function getWrap() {
    try { return window.parent.document.getElementById('mb-wrap'); }
    catch(e) { return document.getElementById('mb-wrap'); }
  }

  function lift() {
    const src = document.getElementById('mb-wrap');
    const tgt = getWrap();
    if (src && !window.parent.document.getElementById('mb-wrap')) {
      const styleEl = document.querySelector('style');
      if (styleEl) window.parent.document.head.appendChild(styleEl.cloneNode(true));
      window.parent.document.body.appendChild(src.cloneNode(true));
    }
  }

  function show() {
    const wrap = getWrap();
    if (!wrap) return;
    const txt = wrap.querySelector('#mb-text') || wrap;
    if (txt.id === 'mb-text') txt.textContent = messages[idx %% messages.length];
    idx++;
    wrap.classList.remove('mb-hide');
    wrap.classList.add('mb-show');
    clearTimeout(timer);
    timer = setTimeout(hide, 8000);
  }

  function hide() {
    const wrap = getWrap();
    if (!wrap) return;
    wrap.classList.remove('mb-show');
    wrap.classList.add('mb-hide');
  }

  function init() {
    lift();
    const wrap = getWrap();
    if (!wrap) return;
    wrap.addEventListener('click', function(e) {
      if (e.target.id === 'mb-dismiss') { hide(); return; }
      show();
    });
    const dis = wrap.querySelector('#mb-dismiss');
    if (dis) dis.addEventListener('click', function(e) { e.stopPropagation(); hide(); });
    setTimeout(show, 1200);
    setInterval(show, 28000);
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
        height=0,
        width=0,
    )
