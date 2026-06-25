"""Sonny Angel mascot — pops from random spots, stays 3 seconds, disappears."""
import json
import random

import streamlit.components.v1 as components

MESSAGES = [
    "Irina! 💧 Drink water RIGHT NOW.",
    "Hey — stretch your neck. You've been hunched. 🧘",
    "You're doing amazing. Genuinely. 🌟",
    "Snack break? You deserve it. 🍓",
    "Stand up for 30 seconds. Go. 🚶",
    "Procurement queen mode: ACTIVATED. 👑",
    "Remember to breathe. In. Out. 🌿",
    "You've got this. Every. Single. Item. 💪",
    "Don't forget to blink. Seriously. 👁️",
    "Take a sip of water. Now. 💧",
    "You're building something beautiful. ✨",
    "Go touch some grass after this. 🌱",
    "You're literally the best. No notes. 🤌",
    "Hydration check: failing. Fix it. 💦",
    "One product at a time. You're almost there. 🏁",
]

SONNY_IMAGES = [
    "https://www.sonnyangel.com/renewal/wp-content/uploads/cache/2019/08/Strawberry/3842779761.png",
    "https://www.sonnyangel.com/renewal/wp-content/uploads/2022/05/img_creatures_figure09_n3.png",
    "https://www.sonnyangel.com/renewal/wp-content/uploads/2022/05/img_creatures_figure01_n3.png",
    "https://www.sonnyangel.com/renewal/wp-content/uploads/2023/05/img_cat-life_02.png",
    "https://www.sonnyangel.com/renewal/wp-content/uploads/2023/12/img_candy-store_01.png",
    "https://sonnyangelusa.com/cdn/shop/products/products_thumbnail_sonny-angel-hippers_01_png.png",
    "https://sonnyangelusa.com/cdn/shop/products/products_sonny-angel-hippers_02_png.png",
    "https://worldofmirth.com/cdn/shop/files/Sonny_Angel_Mini_Figure_Vegetable_Series.png",
    "https://m.media-amazon.com/images/I/615ycFsH8VL._AC_UF894,1000_QL80_.jpg",
    "https://m.media-amazon.com/images/I/61Yzgn20JxL._AC_UF894,1000_QL80_.jpg",
    "http://sukoshi.com/cdn/shop/files/Sonny-Angel_-Mini-Figure-Animal-1_1024x1024.png",
    "https://www.didiinspired.com/images/sonny-angel-sweet-series-1-piece-blind-box-mini-figure-p353-3907_image.jpg",
]

_MASCOT_HTML = """
<style>
[data-testid="manage-app-button"],
[data-testid="stDeployButton"],
.stDeployButton { display: none !important; }

#mb-wrap {
  position: fixed;
  z-index: 2147483647;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 160px;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transform: scale(0) rotate(-20deg);
}
#mb-wrap.mb-visible { opacity: 1; pointer-events: auto; }
#mb-wrap.mb-pop {
  animation: mb-popin 0.55s cubic-bezier(.17,.89,.32,1.7) forwards;
}
#mb-wrap.mb-vanish {
  animation: mb-popout 0.3s cubic-bezier(.55,0,.45,1) forwards;
}
@keyframes mb-popin {
  0%%   { opacity:0; transform: scale(0) rotate(-20deg); }
  55%%  { opacity:1; transform: scale(1.2) rotate(7deg); }
  75%%  { transform: scale(0.88) rotate(-4deg); }
  90%%  { transform: scale(1.06) rotate(2deg); }
  100%% { opacity:1; transform: scale(1) rotate(0deg); }
}
@keyframes mb-popout {
  0%%   { opacity:1; transform: scale(1); }
  35%%  { transform: scale(1.12) rotate(10deg); }
  100%% { opacity:0; transform: scale(0) rotate(-18deg); }
}

#mb-bubble {
  background: #FFE500;
  color: #0D0D0D;
  border: 3px solid #0D0D0D;
  border-radius: 14px;
  padding: 11px 15px;
  font-family: Outfit, system-ui, sans-serif;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.4;
  text-align: center;
  max-width: 155px;
  box-shadow: 4px 4px 0 #0D0D0D;
  position: relative;
  margin-bottom: 8px;
}
#mb-bubble::after {
  content: '';
  position: absolute;
  bottom: -14px; left: 50%%;
  transform: translateX(-50%%);
  border: 7px solid transparent;
  border-top-color: #0D0D0D;
}
#mb-bubble::before {
  content: '';
  position: absolute;
  bottom: -10px; left: 50%%;
  transform: translateX(-50%%);
  border: 6px solid transparent;
  border-top-color: #FFE500;
  z-index: 1;
}
#mb-bubble.bubble-below { order: 2; margin-bottom: 0; margin-top: 8px; }
#mb-bubble.bubble-below::after  { bottom:auto; top:-14px; border-top-color:transparent; border-bottom-color:#0D0D0D; }
#mb-bubble.bubble-below::before { bottom:auto; top:-10px; border-top-color:transparent; border-bottom-color:#FFE500; }

#mb-figure {
  height: 100px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 6px 12px rgba(0,0,0,0.28));
  animation: mb-bob 1.6s ease-in-out infinite;
}
@keyframes mb-bob {
  0%%,100%% { transform: translateY(0) rotate(-2deg); }
  40%%      { transform: translateY(-10px) rotate(4deg); }
  70%%      { transform: translateY(-4px) rotate(-2deg); }
}

#mb-dismiss {
  position: absolute;
  top: -10px; right: -10px;
  width: 22px; height: 22px;
  border-radius: 50%%;
  background: #0D0D0D;
  color: #FFE500;
  font-size: 12px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 10;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.3);
}
</style>

<div id="mb-wrap">
  <div id="mb-bubble">
    <span id="mb-text"></span>
    <div id="mb-dismiss">✕</div>
  </div>
  <img id="mb-figure" src="" alt="Sonny Angel"
       onerror="this.style.display='none'; this.nextElementSibling.style.display='block'">
  <span id="mb-fallback" style="display:none;font-size:72px;line-height:1;animation:mb-bob 1.6s ease-in-out infinite;">🧸</span>
</div>

<script>
(function() {
  const messages = %s;
  const images   = %s;
  let msgIdx = %d;
  let imgIdx = Math.floor(Math.random() * images.length);
  let hideTimer, nextTimer;

  const SPOTS = [
    { right:'22px', bottom:'70px',  top:'auto',  left:'auto'  },
    { left:'22px',  bottom:'70px',  top:'auto',  right:'auto' },
    { right:'22px', top:'80px',    bottom:'auto', left:'auto'  },
    { left:'22px',  top:'80px',    bottom:'auto', right:'auto' },
    { right:'22px', top:'38%%',    bottom:'auto', left:'auto'  },
    { left:'22px',  top:'38%%',    bottom:'auto', right:'auto' },
    { left:'50%%',  bottom:'70px', top:'auto',  right:'auto', xform:'translateX(-50%%)' },
    { left:'50%%',  top:'80px',   bottom:'auto', right:'auto', xform:'translateX(-50%%)' },
  ];

  function getDoc()  { try { return window.parent.document; } catch(e) { return document; } }
  function getWrap() { return getDoc().getElementById('mb-wrap'); }

  function lift() {
    const src  = document.getElementById('mb-wrap');
    const pdoc = getDoc();
    if (src && !pdoc.getElementById('mb-wrap')) {
      const st = document.querySelector('style');
      if (st) pdoc.head.appendChild(st.cloneNode(true));
      pdoc.body.appendChild(src.cloneNode(true));
    }
    // preload images
    images.forEach(u => { const i = new Image(); i.src = u; });
  }

  function place(wrap) {
    const spot = SPOTS[Math.floor(Math.random() * SPOTS.length)];
    Object.assign(wrap.style, {
      right: spot.right || '', left: spot.left || '',
      top: spot.top || '',     bottom: spot.bottom || '',
      transform: spot.xform || ''
    });
    const bubble = wrap.querySelector('#mb-bubble');
    const isTop  = spot.top && spot.top !== 'auto';
    if (bubble) {
      bubble.classList.toggle('bubble-below', isTop);
      wrap.style.flexDirection = isTop ? 'column-reverse' : 'column';
    }
  }

  function show() {
    const wrap = getWrap();
    if (!wrap) return;

    wrap.classList.remove('mb-pop', 'mb-vanish', 'mb-visible');
    void wrap.offsetWidth;

    place(wrap);

    const txt = wrap.querySelector('#mb-text');
    const fig = wrap.querySelector('#mb-figure');
    const fb  = wrap.querySelector('#mb-fallback');
    if (txt) txt.textContent = messages[msgIdx %% messages.length];
    if (fig) {
      fig.style.display = 'block';
      fig.src = images[imgIdx %% images.length];
      if (fb) fb.style.display = 'none';
    }
    msgIdx++; imgIdx++;

    wrap.classList.add('mb-visible', 'mb-pop');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hide, 3000);
  }

  function hide() {
    const wrap = getWrap();
    if (!wrap) return;
    wrap.classList.remove('mb-pop');
    wrap.classList.add('mb-vanish');
    setTimeout(() => wrap.classList.remove('mb-visible', 'mb-vanish'), 320);
  }

  function scheduleNext() {
    const delay = 165000 + Math.random() * 30000;  // 2.75–3.25 min
    nextTimer = setTimeout(() => { show(); scheduleNext(); }, delay);
  }

  function init() {
    lift();
    const wrap = getWrap();
    if (!wrap) return;
    wrap.addEventListener('click', e => {
      if (e.target.closest('#mb-dismiss')) { hide(); return; }
      clearTimeout(hideTimer); clearTimeout(nextTimer);
      show(); scheduleNext();
    });
    setTimeout(() => { show(); scheduleNext(); }, 1200 + Math.random() * 1000);
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init();
})();
</script>
"""


def render_mascot() -> None:
    start_idx = random.randint(0, len(MESSAGES) - 1)
    components.html(
        _MASCOT_HTML % (json.dumps(MESSAGES), json.dumps(SONNY_IMAGES), start_idx),
        height=0, width=0,
    )
