# app/app.py
import sys
from pathlib import Path
import streamlit as st

# ===========================================
# 1️⃣ KLASÖR VE MODÜL YOLLARI
# ===========================================
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from ba_rag import answer_pair

ASSETS = BASE_DIR.parent / "assets"
BOT_AVATAR = ASSETS / "logo_company.png"
USER_AVATAR = ASSETS / "user_avatar.png"

# ===========================================
# 2️⃣ SAYFA AYARI
# ===========================================
st.set_page_config(page_title="Bundesagentur für Arbeit Chatbot", page_icon="💬", layout="wide")

# ===========================================
# 3️⃣ TASARIM (STİL BLOĞU)
# ===========================================
st.markdown("""
<style>
:root{
  --ba-red:#D0021B;
  --text:#1F2937;
  --muted:#6B7280;
  --bg:#FFFFFF;
  --bot-bg:#FFF5F6;
  --bot-border:#FFD6DA;
  --user-bg:#2A2E35;
}

html, body, [data-testid="stAppViewContainer"]{ background:var(--bg)!important; color:var(--text); }
[data-testid="stSidebar"] { background:#17191E; }
[data-testid="stSidebar"] *{ color:#E5E7EB!important; }
[data-testid="stSidebar"] p.small-note{ color:#C7CCD6!important; font-size:12px; }

/* Başlık bandı */
.header-band{
  display:flex; align-items:center; gap:.75rem;
  background:#fff; border:1px solid #eee;
  border-radius:14px; padding:.65rem .9rem;
  box-shadow:0 6px 20px rgba(0,0,0,.06);
  width:100%; max-width:1000px; margin:0 auto;
}
.header-title{ color:var(--ba-red); font-weight:800; }

/* Mesaj akışı */
.msg{ display:flex; gap:.6rem; margin:.6rem 0; }
.msg .avatar{ width:32px; height:32px; border-radius:50%; overflow:hidden; flex:0 0 32px; }
.bubble{
  max-width:780px; padding:.6rem .8rem; border-radius:12px; border:1px solid #eee;
  line-height:1.45; font-size:.95rem;
}
.msg.bot .bubble{ background:var(--bot-bg); border-color:var(--bot-border); color:var(--text); }
.msg.user{ justify-content:flex-end; }
.msg.user .bubble{ background:var(--user-bg); color:#fff; border-color:#282C34; }

/* Expander */
.streamlit-expanderHeader{
  font-weight:700; color:var(--text); background:#F7F7F8; border-radius:10px;
  border:1px solid #EEE;
}
.streamlit-expanderContent{ background:#FCFCFD; border:1px dashed #E5E7EB; border-radius:10px; }

/* Alt giriş barı */
.input-dock{ position:sticky; bottom:8px; z-index:5; background:transparent; padding:.2rem 0; }
.input-row{ display:grid; grid-template-columns: 1fr 56px; gap:.5rem; }
.input-row .send-btn{
  height:56px; border-radius:12px; border:1px solid #e5e7eb;
  background:var(--ba-red); color:#fff; font-weight:700;
}
.input-row textarea{
  border-radius:12px; border:1px solid #E5E7EB;
}
</style>
""", unsafe_allow_html=True)

# ===========================================
# 4️⃣ SIDEBAR
# ===========================================
with st.sidebar:
    if BOT_AVATAR.exists():
        st.image(str(BOT_AVATAR), width=64)
    lang_label = st.selectbox("Sprache / Language", ["Deutsch (de)", "English (en)"], index=0)
    st.markdown('<p class="small-note">Hinweis: Antworten werden auf der gewählten Sprache verfasst.</p>',
                unsafe_allow_html=True)
lang_code = "de" if lang_label.startswith("Deutsch") else "en"

# ===========================================
# 5️⃣ BAŞLIK BÖLÜMÜ
# ===========================================
st.markdown('<div class="header-band">', unsafe_allow_html=True)
cols = st.columns([0.06, 0.94])
with cols[0]:
    if BOT_AVATAR.exists():
        st.image(str(BOT_AVATAR), use_container_width=True)
with cols[1]:
    st.markdown('<span class="header-title">💬 Bundesagentur für Arbeit Chatbot</span>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.write("")

# ===========================================
# 6️⃣ MESAJ GÖSTERİMİ (BALONLAR)
# ===========================================
def render_bot(text: str):
    st.markdown(f"""
    <div class="msg bot">
      <div class="avatar"><img src="app/assets/logo_company.png" style="width:100%"/></div>
      <div class="bubble">{text}</div>
    </div>""", unsafe_allow_html=True)

def render_user(text: str):
    avatar_src = "app/assets/user_avatar.png" if USER_AVATAR.exists() else ""
    st.markdown(f"""
    <div class="msg user">
      <div class="bubble">{text}</div>
      <div class="avatar"><img src="{avatar_src}" style="width:100%"/></div>
    </div>""", unsafe_allow_html=True)

# ===========================================
# 7️⃣ CHAT GEÇMİŞİ
# ===========================================
if "history" not in st.session_state:
    st.session_state["history"] = []  # ("user"|"bot", html)

for role, html in st.session_state["history"]:
    if role == "user":
        render_user(html)
    else:
        render_bot(html)

# ===========================================
# 8️⃣ GİRİŞ ALANI
# ===========================================
placeholder_text = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)"
}[lang_code]

st.markdown('<div class="input-dock">', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="input-row">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 0.12])
    with c1:
        question = st.text_area(placeholder_text, height=90, label_visibility="collapsed")
    with c2:
        send = st.button("➤", type="primary", use_container_width=True, key="send_btn")
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===========================================
# 9️⃣ CEVAP İŞLEME
# ===========================================
if send and question.strip():
    st.session_state["history"].append(("user", question.strip()))
    with st.spinner("Denke nach..." if lang_code=="de" else "Thinking..."):
        try:
            short_ans, detailed = answer_pair(question.strip(), language=lang_code)
            short_html = f"<b>{'Kurzfassung' if lang_code=='de' else 'Short Answer'}:</b> {short_ans}"
            st.session_state["history"].append(("bot", short_html))
            with st.expander("Mehr Details anzeigen" if lang_code=="de" else "Show more details", expanded=False):
                st.markdown(detailed, unsafe_allow_html=True)
        except Exception as e:
            st.session_state["history"].append(("bot", f"<b>Fehler:</b> {e}"))
    st.experimental_rerun()
