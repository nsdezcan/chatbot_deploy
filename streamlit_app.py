import streamlit as st
import traceback

# --- SAFE INIT ---
defaults = {
    "lang": "de",
    "vectorstore": None,
    "index_ready": False,
    "chat": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# streamlit_app.py (repo root)
from app.app import *
