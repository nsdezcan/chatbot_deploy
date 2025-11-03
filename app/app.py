# app/app.py
import os, sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from ba_rag import answer_pair  # load_store/retrieve_context'i içeride çağırıyoruz

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="BA Chatbot", page_icon="💬", layout="wide")

# ---------------------- STYLES ---------------------------
st.markdown("""
<style>
/* Genel arka plan: beyaz, sade */
[data-testid="stAppViewContainer"] { background: #fff; }

/* Başlık şeridi — gereksiz bantları kaldır, kompakt yap */
.header-strip{
  display:flex; align-items:center; gap:.6rem;
  padding:.55rem .9rem;
  border:1px solid #eee; border-radius:12px;
  background:#fff; box-shadow:0 2px 10px rgba(0,0,0,.05);
  width:100%; max-width:1080px; margin:1rem auto .5rem auto;
}
.header-title{ margin:0; font-size:1.05rem; font-weight:800; color:#c0171f; }

/* Sayfa düzeni */
.wrapper{ display:grid; grid-template-columns: 280px 1fr; gap:18px; }
.sidebar{
  background:#1f2127; color:#cfd3da; border-radius:12px; padding:16px;
  height:calc(100vh - 120px); position:sticky; top:16px;
}
.sidebar .hint{ color:#9ea4af; font-size:.88rem; margin-top:.6rem; }
.content{ padding:0 10px; }

/* Sohbet alanı */
.chat-area{ max-width:1080px; margin:0 auto 96px auto; }
.bubble-row{ display:flex; align-items:flex-start; gap:.5rem; margin:10px 0; }
.msg { border-radius:14px; padding:.75rem .9rem; border:1px solid #eee; }
.msg.user{
  background:#2b2d34; color:#fff; margin-left:auto; max-width:72%;
}
.msg.bot{
  background:#fff6f6; color:#1d1f24; max-width:80%;
  border-color:#f3d6d6;
}

/* Avatarlar */
.avatar{ width:30px; height:30px; border-radius:50%; object-fit:contain; border:1px solid #eee; background:#fff; }

/* Giriş çubuğu (alta sabit) */
.input-bar{
  position:fixed; bottom:14px; left:50%; transform:translateX(-50%);
  width:min(1080px, 92vw); display:flex; gap:10px;
  background:#fff; padding:10px; border-radius:14px;
  box-shadow:0 8px 24px rgba(0,0,0,.12); border:1px solid #eee;
}
.send-btn button{
  height:54px; border-radius:12px; padding:0 18px; font-weight:700;
  background:#c0171f;
}
.send-btn button:hover{ background:#a0151b; }

/* Expander (detay) kontrastı artır */
.streamlit-expanderHeader{ font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------------------- HEADER ---------------------------
logo = (BASE_DIR.parent/"assets"/"logo_company.png")
st.markdown(
    f"""
    <div class="header-strip">
      <img src="app://{logo.as_posix()}" class="avatar" />
      <h3 class="header-title">💬 Bundesagentur für Arbeit Chatbot</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------- LAYOUT ---------------------------
st.markdown('<div class="wrapper">', unsafe_allow_html=True)

# -- Sidebar
with st.container():
    st.markdown('<div class="sidebar">', unsafe_allow_html=True)
    if logo.exists(): st.image(str(logo), width=44)
    lang = st.selectbox("Sprache / Language", ["Deutsch (de)","English (en)"], index=0)
    lang_code = {"Deutsch (de)":"de","English (en)":"en"}[lang]
    st.markdown('<div class="hint">Hinweis: Antworten werden auf der gewählten Sprache verfasst.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -- Content
st.markdown('<div class="content">', unsafe_allow_html=True)
st.markdown('<div class="chat-area">', unsafe_allow_html=True)

# Session state
if "history" not in st.session_state:
    st.session_state.history = []   # list of dicts: {role: "user"/"bot", "short": str, "detail": str}

# Mesajları çiz
user_avatar = (BASE_DIR.parent/"assets"/"user_avatar.png")
user_img_html = f'<img src="app://{user_avatar.as_posix()}" class="avatar" />' if user_avatar.exists() else ''
bot_img_html  = f'<img src="app://{logo.as_posix()}" class="avatar" />' if logo.exists() else ''

for item in st.session_state.history:
    if item["role"] == "user":
        st.markdown(
            f'<div class="bubble-row"><div class="msg user">{item["short"]}</div>{user_img_html}</div>',
            unsafe_allow_html=True
        )
    else:  # bot
        # Kısa cevap
        st.markdown(
            f'<div class="bubble-row">{bot_img_html}<div class="msg bot"><b>{"Kurzfassung" if lang_code=="de" else "Short Answer"}:</b> {item["short"]}</div></div>',
            unsafe_allow_html=True
        )
        # Uzun cevap (expander)
        with st.expander("Mehr Details anzeigen" if lang_code=="de" else "Show more details", expanded=False):
            st.write(item["detail"])

st.markdown('</div>', unsafe_allow_html=True)  # /chat-area
st.markdown('</div>', unsafe_allow_html=True)  # /content
st.markdown('</div>', unsafe_allow_html=True)  # /wrapper

# ---------------------- INPUT (bottom fixed) -------------
with st.container():
    st.markdown('<div class="input-bar">', unsafe_allow_html=True)
    placeholder = {
        "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
        "en": "Ask a question (e.g., What is a Bildungsgutschein?)"
    }[lang_code]
    q = st.text_area(placeholder, height=54, key="__q__", label_visibility="collapsed")
    send = st.container()
    with send:
        col1, col2 = st.columns([1, .12])
        with col2:
            clicked = st.button("Senden" if lang_code=="de" else "Send", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# İş mantığı
if clicked and q.strip():
    try:
        short_ans, detail_ans = answer_pair(q, language=lang_code)
        # user
        st.session_state.history.append({"role":"user", "short": q, "detail": ""})
        # bot
        st.session_state.history.append({"role":"bot", "short": short_ans, "detail": detail_ans})
        # YENİ: experimental_rerun kaldırıldı. Standart rerun:
        st.rerun()
    except Exception as e:
        st.error(f"Hata: {e}")
