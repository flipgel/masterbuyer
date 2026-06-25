"""One-shot flying Sonny Angels intro animation — plays once per session on landing."""
import streamlit as st
import streamlit.components.v1 as components

from ui.mascot import SONNY_IMAGES

# Pick 6 images for the intro
_INTRO_IMAGES = SONNY_IMAGES[:6]

_INTRO_HTML = """
<style>
.mb-flyer {
  position: fixed;
  z-index: 9999998;
  width: 80px;
  height: 80px;
  object-fit: contain;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
  opacity: 0;
  pointer-events: none;
}

/* Each figure flies from a different edge */
.mb-flyer-0 { animation: fly0 1.1s ease-out 0.0s forwards; top: 20%%;  left: -100px; }
.mb-flyer-1 { animation: fly1 1.0s ease-out 0.15s forwards; top: 60%%;  right: -100px; }
.mb-flyer-2 { animation: fly2 1.2s ease-out 0.05s forwards; top: -100px; left: 35%%;  }
.mb-flyer-3 { animation: fly3 1.0s ease-out 0.25s forwards; bottom: -100px; right: 25%%; }
.mb-flyer-4 { animation: fly4 1.1s ease-out 0.10s forwards; top: 40%%;  right: -100px; }
.mb-flyer-5 { animation: fly5 1.3s ease-out 0.0s forwards;  bottom: -100px; left: 20%%;  }

/* Fly in → pause → fly out */
@keyframes fly0 {
  0%%   { opacity:0; transform: translate(0,0)     rotate(-20deg) scale(0.5); }
  25%%  { opacity:1; transform: translate(140px,-20px)  rotate(8deg) scale(1.1); }
  60%%  { opacity:1; transform: translate(200px,10px)   rotate(-5deg) scale(1.0); }
  80%%  { opacity:1; transform: translate(220px,5px)    rotate(-5deg) scale(1.0); }
  100%% { opacity:0; transform: translate(400px,80px)   rotate(20deg) scale(0.6); }
}
@keyframes fly1 {
  0%%   { opacity:0; transform: translate(0,0)     rotate(15deg) scale(0.5); }
  25%%  { opacity:1; transform: translate(-130px,20px)  rotate(-8deg) scale(1.1); }
  60%%  { opacity:1; transform: translate(-190px,-10px) rotate(5deg) scale(1.0); }
  80%%  { opacity:1; transform: translate(-200px,-5px)  rotate(5deg) scale(1.0); }
  100%% { opacity:0; transform: translate(-380px,-70px) rotate(-18deg) scale(0.6); }
}
@keyframes fly2 {
  0%%   { opacity:0; transform: translate(0,0)     rotate(10deg) scale(0.5); }
  25%%  { opacity:1; transform: translate(20px,120px)   rotate(-6deg) scale(1.1); }
  60%%  { opacity:1; transform: translate(-10px,170px)  rotate(4deg) scale(1.0); }
  80%%  { opacity:1; transform: translate(-5px,175px)   rotate(4deg) scale(1.0); }
  100%% { opacity:0; transform: translate(-60px,350px)  rotate(-15deg) scale(0.6); }
}
@keyframes fly3 {
  0%%   { opacity:0; transform: translate(0,0)     rotate(-12deg) scale(0.5); }
  25%%  { opacity:1; transform: translate(-30px,-130px) rotate(7deg) scale(1.1); }
  60%%  { opacity:1; transform: translate(10px,-185px)  rotate(-4deg) scale(1.0); }
  80%%  { opacity:1; transform: translate(5px,-190px)   rotate(-4deg) scale(1.0); }
  100%% { opacity:0; transform: translate(70px,-380px)  rotate(16deg) scale(0.6); }
}
@keyframes fly4 {
  0%%   { opacity:0; transform: translate(0,0)     rotate(-18deg) scale(0.5); }
  25%%  { opacity:1; transform: translate(-150px,30px)  rotate(9deg) scale(1.15); }
  60%%  { opacity:1; transform: translate(-220px,-15px) rotate(-4deg) scale(1.0); }
  80%%  { opacity:1; transform: translate(-225px,-10px) rotate(-4deg) scale(1.0); }
  100%% { opacity:0; transform: translate(-420px,-90px) rotate(-22deg) scale(0.5); }
}
@keyframes fly5 {
  0%%   { opacity:0; transform: translate(0,0)     rotate(20deg) scale(0.5); }
  25%%  { opacity:1; transform: translate(40px,-140px)  rotate(-8deg) scale(1.1); }
  60%%  { opacity:1; transform: translate(-5px,-200px)  rotate(5deg) scale(1.0); }
  80%%  { opacity:1; transform: translate(0,-205px)    rotate(5deg) scale(1.0); }
  100%% { opacity:0; transform: translate(-80px,-400px) rotate(-18deg) scale(0.6); }
}
</style>
%s
<script>
(function() {
  function inject() {
    try {
      const pdoc = window.parent.document;
      const style = document.querySelector('style');
      if (style && !pdoc.getElementById('mb-intro-style')) {
        const s = style.cloneNode(true);
        s.id = 'mb-intro-style';
        pdoc.head.appendChild(s);
      }
      document.querySelectorAll('.mb-flyer').forEach(function(el) {
        if (!pdoc.getElementById(el.id)) {
          pdoc.body.appendChild(el.cloneNode(true));
        }
      });
      // clean up after 2.5s
      setTimeout(function() {
        pdoc.querySelectorAll('.mb-flyer').forEach(function(e) { e.remove(); });
        var st = pdoc.getElementById('mb-intro-style');
        if (st) st.remove();
      }, 2600);
    } catch(e) {}
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
</script>
"""


def render_intro() -> None:
    """Inject once-per-session flying Sonny Angels on the landing page."""
    if st.session_state.get("intro_shown"):
        return
    st.session_state["intro_shown"] = True

    imgs_html = "\n".join(
        f'<img id="mb-intro-{i}" class="mb-flyer mb-flyer-{i}" src="{url}" '
        f'onerror="this.style.display=\'none\'">'
        for i, url in enumerate(_INTRO_IMAGES)
    )
    components.html(_INTRO_HTML % imgs_html, height=0, width=0)


