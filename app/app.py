# app/app.py
from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from ba_rag import answer_pair  # load_store / retrieve_context içeride çağrılıyor

st.set_page_config(page_title="BA Chatbot", page_icon="💬", layout="centered")

# =========================
# 🎨 Global Stil
# =========================
st.markdown("""
<style>
/* Arka planı beyaza çek, genel tipografi */
html, body, [data-testid="stAppViewContainer"]{
  background:#ffffff !important;
  color:#111 !important;
  font-size:16px;
}

/* Streamlit birincil kırmızı (BA kırmızısı) */
:root{
  --ba-red:#C62828; /* Agenturrot'a yakın */
}
button[kind="primary"], [data-testid="baseButton-primary"]{
  background:var(--ba-red) !important;
  border-color:var(--ba-red) !important;
}
button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover{
  opacity:.92;
}

/* Ana kapsayıcı ve üst başlık bandı */
.ba-container{
  max-width: 900px;
  margin: 1rem auto 0 auto;
}
.ba-header{
  display:flex; align-items:center; gap:.75rem;
  padding:.65rem .9rem; background:#fff; border:1px solid #eee;
  border-radius:14px;
  box-shadow:0 8px 24px rgba(0,0,0,.06);
}
.ba-header h3{
  margin:0; font-weight:800; color:var(--ba-red);
  font-size:1.05rem;
}

/* Logo hizası */
.ba-logo img{ max-height:56px; width:auto; border-radius:12px;}

/* Etiketleri koyu yap (erişilebilirlik) */
label, [data-testid="stWidgetLabel"] > label{ color:#222 !important; font-weight:600; }

/* ChatMessage iç metinleri daha okunur yap */
[data-testid="stChatMessageContent"]{ color:#111 !important; }

/* Expander başlığı/ içi koyu renk */
[data-testid="stExpander"] details summary{
  color:#111 !important; font-weight:600;
}
.exp-body{ background:#fafafa; border:1px dashed #ddd; border-radius:12px; padding:.8rem; }

/* Chat input alt sabit; Streamlit bunu zaten sabitliyor, sadece genişlik ayarı */
.block-container{ padding-top: 0 !important; }

/* Yardımcı küçük metin */
.subtle{
  color:#555; font-size:.9rem;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🧭 Sidebar: Dil seçimi (sade)
# =========================
with st.sidebar:
    st.image(str((BASE_DIR.parent/"assets"/"logo_company.png")), width=96)
    st.markdown("### Sprache / Language")
    lang_name = st.selectbox(
        " ",
        ["Deutsch (de)", "English (en)"],
        index=0,
        label_visibility="collapsed"
    )
    lang_code = {"Deutsch (de)":"de", "English (en)":"en"}[lang_name]
    st.markdown(
        "<div class='subtle'>Hinweis: Antworten werden auf der gewählten Sprache verfasst.</div>",
        unsafe_allow_html=True
    )

# =========================
# 🧱 Üst başlık
# =========================
st.markdown("<div class='ba-container'>", unsafe_allow_html=True)
cols = st.columns([0.12, 0.88])
with cols[0]:
    st.markdown("<div class='ba-logo'>", unsafe_allow_html=True)
    st.image(str((BASE_DIR.parent/"assets"/"logo_company.png")), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with cols[1]:
    st.markdown("<div class='ba-header'><h3>💬 Bundesagentur für Arbeit Chatbot</h3></div>", unsafe_allow_html=True)
st.write("")  # küçük boşluk

# =========================
# 💬 Sohbet Geçmişi
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []  # each item: {"role": "user"/"assistant", "content": "...", "detail": optional}

# Daha önceki mesajları çiz
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("detail"):
            with st.expander("Mehr Details anzeigen" if lang_code=="de" else "Show more details"):
                st.markdown(f"<div class='exp-body'>{msg['detail']}</div>", unsafe_allow_html=True)

# =========================
# ⌨️ Altta sabit giriş alanı
# =========================
prompt_placeholder = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)",
}[lang_code]

user_input = st.chat_input(prompt_placeholder)

if user_input:
    # 1) Kullanıcı mesajını göster & kaydet
    st.session_state.messages.append({"role":"user", "content":user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2) Bot düşünürken spinner
    with st.chat_message("assistant"):
        with st.spinner("Denke nach..." if lang_code=="de" else "Thinking..."):
            short_ans, detailed_ans = answer_pair(user_input, language=lang_code)

        # Kısa yanıt (yüksek kontrast)
        st.markdown(f"**{'Kurzfassung' if lang_code=='de' else 'Short Answer'}:** {short_ans}")

        # Detay expander
        with st.expander("Mehr Details anzeigen" if lang_code=="de" else "Show more details"):
            st.markdown(f"<div class='exp-body'>{detailed_ans}</div>", unsafe_allow_html=True)

    # 3) Bot mesajını geçmişe ekle
    st.session_state.messages.append({
        "role":"assistant",
        "content": f"**{'Kurzfassung' if lang_code=='de' else 'Short Answer'}:** {short_ans}",
        "detail": detailed_ans
    })

st.markdown("</div>", unsafe_allow_html=True)  # .ba-container kapanış
