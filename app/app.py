# app/app.py
import sys
import base64
from pathlib import Path
import streamlit as st

# ===========================================
# 1) YOLLAR / MODÜLLER
# ===========================================
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from ba_rag import answer_pair  # ba_rag.py değişmedi

ASSETS = BASE_DIR.parent / "assets"
BOT_AVATAR_PATH = ASSETS / "logo_company.png"     # kurum logosu (bot)
USER_AVATAR_PATH = ASSETS / "user_avatar.png"     # kullanıcı avatarı


def _to_b64(p: Path) -> str:
    try:
        data = p.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return ""


BOT_AVATAR_B64 = _to_b64(BOT_AVATAR_PATH)
USER_AVATAR_B64 = _to_b64(USER_AVATAR_PATH)

# ===========================================
# 2) SAYFA
# ===========================================
st.set_page_config(
    page_title="Bundesagentur für Arbeit Chatbot",
    page_icon="💬",
    layout="wide",
)

# ===========================================
# 3) STİL (Açık tema + görünür kontroller)
# ===========================================
st.markdown(
    """
<style>
:root{
  --ba-red:#D0021B;
  --text:#1F2937;
  --muted:#6B7280;
  --bg:#FFFFFF;
  --bg-light:#F5F6F7;
  --bot-bg:#FFF5F6;
  --bot-border:#FFD6DA;
  --user-bg:#EAF2FF;         /* kullanıcı balonu ve textarea zemini */
  --user-border:#D6E6FF;
  --user-text:#111827;       /* siyah yazı */
}

/* === Genel Arka Planlar === */
html, body, [data-testid="stAppViewContainer"]{
  background:var(--bg)!important;
  color:var(--text)!important;
}

/* === Üst üstteki siyah barı grile yaklaştır / boşluğu daralt === */
header[data-testid="stHeader"]{
  background:var(--bg-light)!important;
  border-bottom:1px solid #E3E4E6!important;
}
header[data-testid="stHeader"] *{ color:#111827!important; }
[data-testid="stAppViewContainer"] > .main .block-container {
  padding-top: 0.4rem !important;  /* “bant” etkisini küçült */
  margin-top: 0 !important;
}

/* === Sidebar === */
[data-testid="stSidebar"] {
  background: var(--bg-light)!important;
  border-right: 1px solid #E3E4E6;
}
[data-testid="stSidebar"] *{
  color: #1F2937!important;
}
[data-testid="stSidebar"] p.small-note{
  color:#555!important;
  font-size:12px;
  margin-top:.5rem;
}

/* Selectbox içi yazıyı görünür yap */
[data-baseweb="select"] div, 
[data-baseweb="select"] span, 
[data-baseweb="select"] input{
  color:#111827 !important;
}
[data-baseweb="select"] svg{
  color:#111827 !important;
}

/* === Başlık Alanı === */
.header-band{
  display:flex; align-items:center; gap:.75rem;
  background:#fff;
  border:1px solid #E3E4E6;
  border-radius:14px;
  padding:.65rem .9rem;
  box-shadow:0 2px 8px rgba(0,0,0,.05);
  width:100%;
  max-width:1000px;
  margin:0 auto .8rem;
}
.header-title{
  color:var(--ba-red);
  font-weight:800;
}

/* === Mesaj Balonları === */
.msg{ display:flex; gap:.6rem; margin:.6rem 0; }
.msg .avatar{ width:32px; height:32px; border-radius:50%; overflow:hidden; flex:0 0 32px; }
.msg .avatar img{ width:100%; height:100%; object-fit:cover; display:block; }
.bubble{
  max-width:780px;
  padding:.6rem .8rem;
  border-radius:12px;
  border:1px solid #eee;
  line-height:1.45;
  font-size:.95rem;
}
.msg.bot .bubble{
  background:var(--bot-bg);
  border-color:var(--bot-border);
  color:var(--text);
}
.msg.user{ justify-content:flex-end; }
.msg.user .bubble{
  background:var(--user-bg);
  color:var(--user-text);
  border-color:var(--user-border);
}

/* === Expander === */
.streamlit-expanderHeader{
  font-weight:700;
  color:var(--text);
  background:#F7F7F8;
  border-radius:10px;
  border:1px solid #EEE;
}
.streamlit-expanderContent{
  background:#FCFCFD;
  border:1px dashed #E5E7EB;
  border-radius:10px;
}

/* === Alt Giriş Alanı === */
.input-dock{
  position:sticky;
  bottom:8px;
  z-index:5;
  background:transparent;
  padding:.2rem 0;
}
.input-row{
  display:grid;
  grid-template-columns: 1fr 56px;
  gap:.5rem;
}

/* === Giriş kutusu: kullanıcı balonuyla aynı renk, siyah yazı === */
.input-row textarea{
  background:var(--user-bg) !important;     /* açık mavi-gri */
  color:var(--user-text) !important;        /* siyah yazı */
  border:1px solid var(--user-border) !important;
  border-radius:12px !important;
  padding:.6rem .8rem !important;
  font-size:.95rem !important;
  line-height:1.5 !important;
  transition:all .2s ease-in-out;
}
.input-row textarea:focus{
  border-color:#9ac3ff !important;
  box-shadow:0 0 0 2px rgba(154,195,255,.35) !important;
  outline:none !important;
}

/* === Gönder butonu === */
.input-row .send-btn, button[kind="primary"]{
  background:var(--ba-red)!important;
  color:#fff!important;
  font-weight:700!important;
  border-radius:12px!important;
  height:56px!important;
  width:56px!important;
  border:none!important;
}
.input-row .send-btn:hover, button[kind="primary"]:hover{
  background:#b7181f!important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ===========================================
# 4) SIDEBAR
# ===========================================
with st.sidebar:
    if BOT_AVATAR_B64:
        st.image(BOT_AVATAR_PATH.as_posix(), width=64)

    lang_label = st.selectbox("Sprache / Language", ["Deutsch (de)", "English (en)"], index=0)

    # Kısa / uzun cevap seçimi
    if lang_label.startswith("Deutsch"):
        mode_label = "Antwortlänge"
        mode_opt = st.radio(mode_label, ["Kurz", "Lang"], index=0, horizontal=True)
    else:
        mode_label = "Answer length"
        mode_opt = st.radio(mode_label, ["Short", "Long"], index=0, horizontal=True)

    st.markdown(
        '<p class="small-note">Hinweis: Antworten werden auf der gewählten Sprache verfasst.</p>',
        unsafe_allow_html=True,
    )

lang_code = "de" if lang_label.startswith("Deutsch") else "en"
mode_code = "long" if mode_opt in ("Long", "Lang") else "short"

# ===========================================
# 5) BAŞLIK
# ===========================================
st.markdown('<div class="header-band">', unsafe_allow_html=True)
c1, c2 = st.columns([0.06, 0.94])
with c1:
    if BOT_AVATAR_B64:
        st.image(BOT_AVATAR_PATH.as_posix(), use_container_width=True)
with c2:
    st.markdown('<span class="header-title">💬 Bundesagentur für Arbeit Chatbot</span>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ===========================================
# 6) MESAJ RENDER
# ===========================================
def render_bot(html_text: str):
    img_tag = f'<img src="data:image/png;base64,{BOT_AVATAR_B64}"/>' if BOT_AVATAR_B64 else ""
    st.markdown(
        f"""
    <div class="msg bot">
      <div class="avatar">{img_tag}</div>
      <div class="bubble">{html_text}</div>
    </div>""",
        unsafe_allow_html=True,
    )


def render_user(text: str):
    img_tag = f'<img src="data:image/png;base64,{USER_AVATAR_B64}"/>' if USER_AVATAR_B64 else ""
    st.markdown(
        f"""
    <div class="msg user">
      <div class="bubble">{text}</div>
      <div class="avatar">{img_tag}</div>
    </div>""",
        unsafe_allow_html=True,
    )


# ===========================================
# 7) DURUM / GEÇMİŞ
# ===========================================
if "history" not in st.session_state:
    st.session_state.history = []

for role, html in st.session_state.history:
    if role == "user":
        render_user(html)
    else:
        render_bot(html)

# ===========================================
# 8) GİRİŞ
# ===========================================
placeholder_text = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)",
}[lang_code]
q_key = f"q_{lang_code}"
if q_key not in st.session_state:
    st.session_state[q_key] = ""

st.markdown('<div class="input-dock">', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="input-row">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 0.12])
    with c1:
        st.session_state[q_key] = st.text_area(
            placeholder_text,
            height=90,
            label_visibility="collapsed",
            value=st.session_state[q_key],
            key=f"txt_{q_key}",
        )
    with c2:
        send = st.button("➤", use_container_width=True, key="send_btn", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ===========================================
# 9) CEVAP
# ===========================================
if send and st.session_state[q_key].strip():
    question = st.session_state[q_key].strip()
    st.session_state.history.append(("user", question))
    st.session_state[q_key] = ""
    with st.spinner("Denke nach..." if lang_code == "de" else "Thinking..."):
        try:
            short_ans, detailed = answer_pair(question, language=lang_code)

            if mode_code == "long":
                title = "Ausführliche Antwort" if lang_code == "de" else "Detailed Answer"
                long_html = f"<b>{title}:</b><br>{detailed}"
                st.session_state.history.append(("bot", long_html))
            else:
                short_html = f"<b>{'Kurzfassung' if lang_code=='de' else 'Short Answer'}:</b> {short_ans}"
                st.session_state.history.append(("bot", short_html))
                with st.expander(
                    "Mehr Details anzeigen" if lang_code == "de" else "Show more details",
                    expanded=False,
                ):
                    st.markdown(detailed, unsafe_allow_html=True)
        except Exception as e:
            st.session_state.history.append(("bot", f"<b>Fehler:</b> {e}"))
    st.rerun()

