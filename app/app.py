import os
import sys
from pathlib import Path

import streamlit as st

# -------------------------------------------------
# Yol ayarları
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from ba_rag import load_store, retrieve_context, build_prompt, ask_gemini  # noqa: E402

# -------------------------------------------------
# Sayfa ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="BA Chatbot",
    page_icon="💬",
    layout="wide",
)

# -------------------------------------------------
# CSS – senin istediğin gradient + kutu tasarımı
# -------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(90deg, #E57373 0%, #E9FAD9 50%, #C6F3FF 100%);
    }
    .chat-shell {
        max-width: 850px;
        margin: 1.5rem auto 3.5rem auto;
        background: rgba(255, 255, 255, 0.92);
        border-radius: 20px;
        box-shadow: 0 12px 35px rgba(0,0,0,0.12);
        padding: 1.2rem 1.5rem 1.5rem 1.5rem;
    }
    .chat-header {
        display: flex;
        gap: .7rem;
        align-items: center;
        border-bottom: 1px solid #eee;
        padding-bottom: .5rem;
        margin-bottom: 1.0rem;
    }
    .chat-title {
        font-size: 1.05rem;
        font-weight: 600;
    }
    .answer-box {
        background: #f4f4ff;
        border: 1px solid #ececff;
        border-radius: 14px;
        padding: .6rem .8rem;
        margin-top: 1rem;
        font-size: 0.92rem;
    }
    .source-pill {
        display: inline-block;
        background: #ffffff;
        border: 1px solid #ddd;
        border-radius: 999px;
        padding: 3px 11px 4px 11px;
        font-size: 0.68rem;
        margin: 3px 5px 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Üst kutu
# -------------------------------------------------
st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

logo_path = BASE_DIR.parent / "assets" / "logo_company.png"

col_logo, col_title = st.columns([0.13, 0.87], vertical_alignment="center")
with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), use_column_width=True)
    else:
        st.markdown("💬")

with col_title:
    st.markdown(
        '<div class="chat-header"><div class="chat-title">Bundesagentur für Arbeit Chatbot</div></div>',
        unsafe_allow_html=True,
    )

# -------------------------------------------------
# Vektör deposunu yükle
# -------------------------------------------------
try:
    store = load_store()
except Exception as e:
    st.error(f"Vektör deposu yüklenemedi: {e}")
    st.stop()

# -------------------------------------------------
# Dil seçimi
# -------------------------------------------------
lang = st.selectbox("🗣 Sprache / Language", ["Deutsch", "English"], index=0)
lang_code = "de" if lang == "Deutsch" else "en"

# -------------------------------------------------
# Soru alanı
# -------------------------------------------------
default_q = (
    "Was ist ein Bildungsgutschein und wie kann ich ihn bekommen?"
    if lang_code == "de"
    else "What is a Bildungsgutschein and how can I obtain it?"
)

question = st.text_area(
    "Bir soru yaz (örnek: *Bildungsgutschein nedir?*)"
    if lang_code == "de"
    else "Type your question (e.g. *What is a Bildungsgutschein?*)",
    value=default_q,
    height=110,
)

# -------------------------------------------------
# Buton
# -------------------------------------------------
if st.button("Gönder" if lang_code == "de" else "Send"):
    if not question.strip():
        st.warning("Lütfen bir soru yaz." if lang_code == "de" else "Please type a question.")
    else:
        with st.spinner("Gemini düşünüyor..." if lang_code == "de" else "Gemini is thinking..."):
            # 1) en iyi 4 parçayı al
            docs = retrieve_context(store, question, k=4)
            # 2) prompt oluştur
            prompt = build_prompt(question, docs, lang=lang_code)
            # 3) gemini'ye sor
            result = ask_gemini(prompt)

        short_ans = result.get("short", "")
        long_ans = result.get("long", "")

        # kısa cevap
        st.markdown(f'<div class="answer-box">{short_ans}</div>', unsafe_allow_html=True)

        # uzun cevap
        with st.expander(
            "📄 Detaylı yanıtı göster" if lang_code == "de" else "📄 Show detailed answer"
        ):
            st.write(long_ans)

        # kullanılan parçaları göster
        if docs:
            st.caption("📎 Kullanılan belgeler / Sources")
            for d in docs:
                st.markdown(
                    f"<span class='source-pill'>{d.get('source', 'source')} · {d['score']:.2f}</span>",
                    unsafe_allow_html=True,
                )

# shell'i kapat
st.markdown("</div>", unsafe_allow_html=True)
