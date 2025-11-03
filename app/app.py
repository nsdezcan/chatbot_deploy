# app/app.py
import os, sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from ba_rag import load_store, retrieve_context, answer_pair

st.set_page_config(page_title="BA Chatbot", page_icon="💬", layout="wide")

# ---------- PATHS ----------
ASSETS = BASE_DIR.parent / "assets"
BOT_AVATAR = ASSETS / "logo_company.png"   # BA logosu
USER_AVATAR = ASSETS / "user_avatar.png"   # kullanıcı ikonu

# ---------- STYLES ----------
st.markdown("""
<style>
:root {
  --ba-red: #C61F1F;
  --ink: #222;               /* ana metin */
  --muted: #5b5b5b;          /* ikincil metin */
  --bubble-user: #2f2f2f;    /* kullanıcı balon koyu gri */
  --bubble-bot: #ffefef;     /* bot balon açık kırmızı */
  --card: #ffffff;           /* kart/beyaz */
  --border: #eaeaea;
}

/* Tüm uygulama arka planı beyaz ve sade */
html, body, [data-testid="stAppViewContainer"] {
  background: #ffffff !important;
  color: var(--ink);
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: #1f1f24 !important;
}
[data-testid="stSidebar"] * { color: #e9e9ea !important; }
[data-testid="stSidebar"] .sidebar-note {
  color: #cfcfd6 !important;  /* okunurluk için daha açık */
  font-size: 0.9rem;
}

/* Üst Başlık */
.header-wrap {
  max-width: 980px;
  margin: 12px auto 6px auto;
}
.header-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;        /* tüm köşeler yuvarlak */
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;         /* yükseklik azalttık */
  box-shadow: 0 4px 18px rgba(0,0,0,.05);
}
.header-title {
  font-weight: 800;
  color: var(--ba-red);       /* logo kırmızısı */
  font-size: 1.05rem;
}

/* Chat alan kartı */
.chat-wrap {
  max-width: 980px;
  margin: 4px auto 96px auto;
}

/* Mesaj satırı */
.msg {
  display: grid;
  grid-template-columns: 36px 1fr;
  align-items: start;
  gap: 10px;
  margin: 10px 0 14px 0;
}
.msg .avatar {
  width: 36px; height: 36px; border-radius: 50%;
  overflow: hidden; border: 1px solid var(--border);
  background: #fff;
}
.msg .avatar img { width: 100%; height: 100%; object-fit: cover; }

/* Baloncuklar */
.bubble {
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--border);
  line-height: 1.55;
  color: var(--ink);
}
.bubble.user {
  background: var(--bubble-user);
  color: #fff;                         /* koyu zemin üzerinde beyaz metin */
}
.bubble.bot {
  background: var(--bubble-bot);
}

/* Kısa cevap etiketi */
.short-tag {
  display: inline-block;
  font-weight: 700;
  margin-right: 6px;
}

/* Expander (detay) – siyah metin, okunur */
.streamlit-expanderHeader { color: var(--ink) !important; font-weight: 700; }
div[data-testid="stExpander"] {
  border: 1px dashed var(--border); border-radius: 12px; background: #fafafa;
}

/* Giriş çubuğu alta sabit */
.input-bar {
  position: fixed;
  left: 260px;                 /* sidebar genişliği ~ */
  right: 24px;
  bottom: 18px;
  z-index: 999;
}
@media (max-width: 1000px) {
  .input-bar { left: 12px; right: 12px; }
}
.input-row {
  display: grid;
  grid-template-columns: 1fr 48px;
  gap: 8px;
}
.input-field textarea {
  border-radius: 999px !important;
  border: 1px solid var(--border) !important;
  background: #222831 !important;
  color: #eaeef2 !important;
}
.send-btn button {
  height: 48px; border-radius: 999px !important;
  background: var(--ba-red) !important;
  color: #fff !important; font-weight: 700;
  border: 1px solid #b71a1a !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    if BOT_AVATAR.exists():
        st.image(str(BOT_AVATAR), width=56)
    st.selectbox("Sprache / Language", ["Deutsch (de)", "English (en)"], key="lang",
                 help=None, index=0)
    st.markdown(
        "<div class='sidebar-note'>Hinweis: Antworten werden auf der gewählten Sprache verfasst.</div>",
        unsafe_allow_html=True
    )

lang_code = "de" if st.session_state.get("lang","Deutsch (de)").startswith("Deutsch") else "en"

# ---------- HEADER ----------
st.markdown(
    f"""
    <div class="header-wrap">
      <div class="header-card">
        <img src="app:///{BOT_AVATAR.as_posix()}" width="28" height="28" />
        <div class="header-title">💬 Bundesagentur für Arbeit Chatbot</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- HELPERS ----------
def render_msg(role: str, html: str):
    """role: 'user' | 'bot'"""
    avatar = USER_AVATAR if role == "user" else BOT_AVATAR
    bubble_cls = "bubble user" if role == "user" else "bubble bot"
    st.markdown(
        f"""
        <div class="msg">
          <div class="avatar"><img src="app:///{avatar.as_posix()}" /></div>
          <div class="{bubble_cls}">{html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------- CHAT (tek-shot) ----------
# chat geçmişini görmek için küçük bir oturum listesi tutalım
if "history" not in st.session_state:
    st.session_state["history"] = []   # list[("user"|"bot", html)]

# mesaj geçmişini çiz
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for role, html in st.session_state["history"]:
    render_msg(role, html)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- INPUT BAR (alta sabit) ----------
ph = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)",
}[lang_code]

with st.container():
    st.markdown('<div class="input-bar">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 0.12], gap="small")
    with c1:
        user_q = st.text_area(ph, height=48, label_visibility="collapsed", key="q",
                              placeholder=ph)
    with c2:
        send = st.button("➤", use_container_width=True, key="send")
    st.markdown('</div>', unsafe_allow_html=True)

if send and user_q.strip():
    # hemen kullanıcı mesajını ekranda göster
    st.session_state["history"].append(("user", user_q.strip()))
    with st.spinner("Denke nach..." if lang_code == "de" else "Thinking..."):
        try:
            short_ans, detailed_ans = answer_pair(user_q.strip(), language=lang_code)
            # kısa yanıt balon içinde
            short_html = f"<span class='short-tag'>{'Kurzfassung' if lang_code=='de' else 'Short Answer'}:</span> {short_ans}"
            st.session_state["history"].append(("bot", short_html))

            # detay expander (altına koyacağız)
            with st.expander("Mehr Details anzeigen" if lang_code=="de" else "Show more details", expanded=False):
                st.markdown(detailed_ans, unsafe_allow_html=True)

        except Exception as e:
            st.session_state["history"].append(("bot", f"<strong>Fehler:</strong> {e}"))

    st.experimental_rerun()




