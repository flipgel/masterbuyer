#!/bin/bash
set -e
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run app.py --server.port=8501 --server.headless=true --browser.gatherUsageStats=false
