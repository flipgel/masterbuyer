"""A cute, purely decorative mascot that pops in with reminders for Irina."""
import json

import streamlit.components.v1 as components

MESSAGES = [
    "Irina, drink some water! 💧",
    "You're doing great — take a breath. 🌿",
    "Stretch time! 🧘",
    "Don't forget to eat something yummy. 🍓",
    "Sending you a little hug. 🤍",
    "Go touch some grass after this. 🌱",
    "Procurement queen at work. 👑",
]

_MASCOT_HTML = """
<style>
#mb-mascot { position:fixed; bottom:18px; right:18px; z-index:999999;
     font-family:sans-serif; display:flex; align-items:flex-end; gap:8px; cursor:pointer; }
#mb-bubble { background:#fff; border:1px solid #D4A843; border-radius:12px;
     padding:8px 12px; font-size:13px; color:#1E3A5F; max-width:220px;
     box-shadow:0 2px 8px rgba(0,0,0,0.12); display:none; }
#mb-face { font-size:34px; animation:mb-bob 2.4s ease-in-out infinite; }
@keyframes mb-bob { 0%%,100%% { transform: translateY(0); } 50%% { transform: translateY(-6px); } }
@keyframes mb-fade-in { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }
</style>
<div id="mb-mascot">
  <div id="mb-bubble"></div>
  <div id="mb-face">🧸</div>
</div>
<script>
(function () {
  const messages = %s;
  let idx = 0;

  // Streamlit components render in a same-origin iframe; lift the mascot into the
  // real page so it floats over everything instead of being boxed into this iframe.
  let targetDoc = document;
  try {
    if (window.parent && window.parent.document && !window.parent.document.getElementById("mb-mascot")) {
      const styleEl = document.querySelector("style").cloneNode(true);
      const mascotEl = document.getElementById("mb-mascot").cloneNode(true);
      window.parent.document.body.appendChild(styleEl);
      window.parent.document.body.appendChild(mascotEl);
      targetDoc = window.parent.document;
    } else if (window.parent && window.parent.document) {
      targetDoc = window.parent.document;
    }
  } catch (e) {
    targetDoc = document;
  }

  const bubble = targetDoc.getElementById("mb-bubble");
  const wrap = targetDoc.getElementById("mb-mascot");
  if (!bubble || !wrap) return;

  function showMessage() {
    bubble.textContent = messages[idx %% messages.length];
    bubble.style.display = "block";
    bubble.style.animation = "mb-fade-in 0.4s ease-out";
    idx += 1;
    setTimeout(() => { bubble.style.display = "none"; }, 6000);
  }

  wrap.onclick = showMessage;
  setTimeout(showMessage, 1500);
  setInterval(showMessage, 25000);
})();
</script>
"""


def render_mascot() -> None:
    """Mount the mascot once per page load. Purely client-side, survives Streamlit reruns."""
    components.html(_MASCOT_HTML % json.dumps(MESSAGES), height=0, width=0)
