# app/app.py
import os, sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from ba_rag import load_store, retrieve_context, answer_pair  # mevcut fonksiyonların

st.set_page_config(page_title="BA Chatbot", page_icon="💬", layout="centered")

# ---------- STYLES ----------
st.markdown("""
<style>
/* Arka plan gradyan */
html, body, [data-testid="stAppViewContainer"] {
  background: linear-gradient(90deg, #E57373 0%, #E9FAD9 50%, #C6F3FF 100%) !important;
}

/* Kart */
.chat-card {
  max-width: 860px;
  margin: 1.5rem auto;
  background: rgba(255,255,255,0.95);
  border-radius: 20px;
  box-shadow: 0 12px 35px rgba(0,0,0,0.12);
  padding: 0;
  border: 1px solid #eee;
}

/* Başlık bandı */
.header {
  display:flex; align-items:center; gap:.75rem;
  padding: .90rem 1.10rem;
  border-bottom:1px solid #eee;
  background:#ffffff;
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
}
.header h3 {
  margin:0; 
  font-size:1.10rem; 
  font-weight:800;
  color:#C62828;  /* logoya uygun kırmızı */
}

/* Etiketleri siyah yap */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] > div {
  color:#111 !important;
  font-weight:600 !important;
}

/* Mesaj balonları */
.bot-bubble, .user-bubble {
  border-radius: 14px; 
  padding:.6rem .8rem; 
  font-size:.95rem;
  max-width: 95%; 
  border:1px solid #eaeaea;
}
.bot-bubble { background:#f4f4ff; }
.user-bubble{ background:#d6f7df; margin-left:auto; }

/* Detay paneli */
.details {
  margin-top:.4rem; padding:.8rem; background:#fafafa; 
  border:1px dashed #ddd; border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
logo_path = (BASE_DIR.parent / "assets" / "logo_company.png")

st.markdown('<div class="chat-card">', unsafe_allow_html=True)
cols = st.columns([0.13, 0.87])
with cols[0]:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
with cols[1]:
    st.markdown('<div class="header"><h3>💬 Bundesagentur für Arbeit Chatbot</h3></div>', unsafe_allow_html=True)

# ---------- LANGUAGE (TR kaldırıldı) ----------
lang = st.selectbox("Language / Sprache / Dil", ["Deutsch (de)", "English (en)"], index=0)
lang_code = {"Deutsch (de)":"de", "English (en)":"en"}[lang]

# ---------- INPUT ----------
q_placeholder = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)",
}[lang_code]

question = st.text_area(
    q_placeholder, 
    height=140,
)

clicked = st.button({"de":"Senden", "en":"Send"}[lang_code])

if clicked:
    if not question.strip():
        st.warning({"de":"Bitte eine Frage eingeben.",
                    "en":"Please enter a question."}[lang_code])
    else:
        with st.spinner({"de":"Denke nach...", "en":"Thinking..."}[lang_code]):
            try:
                # Kısa + detaylı
                short_ans, detailed_ans = answer_pair(question, language=lang_code)

                st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
                st.markdown(
                    f"**{ {'de':'Kurzfassung','en':'Short Answer'}[lang_code] }:**  " + short_ans
                )
                st.markdown('</div>', unsafe_allow_html=True)

                with st.expander(
                    {"de":"Mehr Details anzeigen","en":"Show more details"}[lang_code],
                    expanded=False
                ):
                    st.markdown('<div class="details">', unsafe_allow_html=True)
                    st.markdown(detailed_ans)
                    st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

st.markdown('</div>', unsafe_allow_html=True)  # chat-card kapat
