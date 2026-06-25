"""Render a product image via Streamlit's native image component.

Serper Shopping returns images as base64 data URIs; organic pages (og:image) return
regular http(s) URLs. Rendering both through st.image (decoding the data URI to raw
bytes first) instead of a hand-rolled <img src="data:..."> tag avoids depending on the
browser/host accepting inline data URIs inside raw HTML — st.image serves the bytes
through Streamlit's own media endpoint, which works regardless of CSP configuration.
"""
import base64

import streamlit as st


def render_product_image(image_url: str | None, width: int | None = None) -> None:
    if not image_url:
        return
    try:
        if image_url.startswith("data:"):
            _, _, b64_payload = image_url.partition(",")
            image_bytes = base64.b64decode(b64_payload)
            st.image(image_bytes, width=width)
        else:
            st.image(image_url, width=width)
    except Exception:
        pass
