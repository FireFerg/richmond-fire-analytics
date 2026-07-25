from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent.parent
CSS_FILE = ROOT_DIR / "styles" / "main.css"


def load_css():
    css = CSS_FILE.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )