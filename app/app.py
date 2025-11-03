# app/app.py
import os, sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from ba_rag import load_store, retrieve_context, answer_pair

st.set_page_config(page_title="BA Chatbot", page_icon="💬", layout="centered")

# ---------- STYLES ----------
st.markdown("""
<style>
/* Arka plan */
html, body, [data-testid="stAppViewContainer"]{
  background: linear-gradient(90deg, #E57373 0%, #E9FAD9 50%, #C6F3FF 100%) !important;
}

/* Kart */
.chat-card{
  max-width: 860px; margin: 1.5rem auto; background: rgba(255,255,255,0.90);
  border-radius: 20px; box-shadow: 0 12px 35px rgba(0,0,0,0.12);
  padding: 0; border: 1px solid #eee;
}

/* Header band (logo ile aynı hiza, alt köşeler de yuvarlak) */
.header{
  display:flex; align-items:center; gap:.75rem;
  padding:.6rem .9rem; background:#fff; border:1px solid #eee;
  border-radius: 14px; /* üst-alt köşeler dahil */
}
.header h3{ margin:0; font-size:1.02rem; font-weight:800; color:#C62828; } /* kırmızı başlık */

/* Kart içindeki logo yüksekliği */
.chat-card .stImage img{
  max-height:56px; width:auto; border-radius:12px;
}

/* Etiket yazılarını siyah yap */
[data-testid="stWidgetLabel"] > label{ color:#111 !important; font-weight:600; }

/* Mesaj balonları ve içeriklerin rengi */
.bot-bubble, .user-bubble, .details{ color:#111; }
.bot-bubble, .user-bubble{
  border-radius: 14px; padding:.6rem .8rem; font-size:.95rem; max-width:95%;
  border:1px solid #eaeaea;
}
.bot-bubble{ background:#f4f4ff; }
.user-bubble{ background:#d6f7df; margin-left:auto; }

/* Expander başlık ve içi; yazıyı siyah yap */
[data-testid="stExpander"] details summary{
  color:#111 !important; font-weight:600;
}
.details{
  margin-top:.4rem; padding:.8rem; background:#fafafa; border:1px dashed #ddd; border-radius:12px;
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

# Dil seçimi (yalnızca DE/EN)
lang = st.selectbox("Language / Sprache / Dil", ["Deutsch (de)", "English (en)"], index=0)
lang_code = {"Deutsch (de)":"de", "English (en)":"en"}[lang]

# ---------- INPUT ----------
q_placeholder = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)",
}[lang_code]

question = st.text_area(q_placeholder, height=120)
clicked = st.button({"de":"Senden", "en":"Send"}[lang_code])

if clicked:
    if not question.strip():
        st.warning({"de":"Lütfen bir soru yazın.", "en":"Please enter a question."}[lang_code])
    else:
        with st.spinner({"de":"Denke nach...", "en":"Thinking..."}[lang_code]):
            try:
                short_ans, detailed_ans = answer_pair(question, language=lang_code)

                # Kısa cevap
                st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
                st.markdown(
                    f"**{ {'de':'Kurzfassung','en':'Short Answer'}[lang_code] }:**  {short_ans}"
                )
                st.markdown('</div>', unsafe_allow_html=True)

                # Detay
                with st.expander({"de":"Mehr Details anzeigen","en":"Show more details"}[lang_code], expanded=False):
                    st.markdown('<div class="details">', unsafe_allow_html=True)
                    st.markdown(detailed_ans)
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

st.markdown('</div>', unsafe_allow_html=True)  # chat-card kapanış

