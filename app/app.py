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
from ba_rag import answer_pair  # <-- BA_RAG.PY aynen kalsın

ASSETS = BASE_DIR.parent / "assets"
BOT_AVATAR_PATH = ASSETS / "logo_company.png"      # kurum logosu (bot)
USER_AVATAR_PATH = ASSETS / "user_avatar.png"      # kullanıcı avatarı

# Base64'e çevirme fonksiyonu (Hata kontrolü iyileştirildi)
def _to_b64(p: Path) -> str:
    try:
        data = p.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception as e:
        print(f"Avatar yüklenemedi: {p}. Hata: {e}")
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
# 3) STİL (GÜNCELLENDİ)
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

html, body, [data-testid="stAppViewContainer"]{
    background:var(--bg)!important;
    color:var(--text);
}
[data-testid="stSidebar"] { background:#17191E; }
[data-testid="stSidebar"] *{ color:#E5E7EB!important; }
[data-testid="stSidebar"] p.small-note{
    color:#CDD3DD!important;
    font-size:12px;
}

/* DEĞİŞİKLİK 1: Gereksiz başlık bandı (header-band) kaldırıldı. */

/* Mesaj balonları */
.msg{ display:flex; gap:.6rem; margin:.6rem 0; }
.msg .avatar{
    width:32px;
    height:32px;
    border-radius:50%;
    overflow:hidden;
    flex:0 0 32px;
}
.msg .avatar img{
    width:100%;
    height:100%;
    object-fit:cover;
    display:block;
}
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
    color:#fff;
    border-color:#282C34;
}

/* Expander */
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

/* DEĞİŞİKLİK 2: Karmaşık .input-dock, .input-row stilleri kaldırıldı. */
/* st.chat_input'ı ana temaya uydurmak için KÜÇÜK bir ayar */
[data-testid="stChatInput"] {
    border-top: 1px solid #EEEEEE;
    background: var(--bg);
}
[data-testid="stChatInput"] textarea{
    border-radius: 12px;
    border-color: #E5E7EB;
}
[data-testid="stChatInput"] button{
    border-radius: 12px;
    background: var(--ba-red);
    color: #fff;
}
[data-testid="stChatInput"] button:hover,
[data-testid="stChatInput"] button:focus{
    background: #A90115; /* Kırmızının koyu tonu */
    color: #fff;
}
</style>
""", unsafe_allow_html=True)

# ===========================================
# 4) SIDEBAR (DEĞİŞİKLİK YOK)
# ===========================================
with st.sidebar:
    if BOT_AVATAR_B64:
        st.image(BOT_AVATAR_PATH.as_posix(), width=64)
    lang_label = st.selectbox("Sprache / Language", ["Deutsch (de)", "English (en)"], index=0)
    st.markdown('<p class="small-note">Hinweis: Antworten werden auf der gewählten Sprache verfasst.</p>',
                unsafe_allow_html=True)
lang_code = "de" if lang_label.startswith("Deutsch") else "en"

# ===========================================
# 5) BAŞLIK (DEĞİŞİKLİK 3: Bu bölüm kaldırıldı)
# ===========================================
# st.markdown('<div class="header-band">', ...) # <-- KALDIRILDI
# c1, c2 = st.columns([0.06, 0.94])             # <-- KALDIRILDI
# ... (içeriği de kaldırıldı)

# ===========================================
# 6) MESAJ RENDER (DEĞİŞİKLİK YOK)
# ===========================================
def render_bot(html_text: str):
    img_tag = f'<img src="data:image/png;base64,{BOT_AVATAR_B64}"/>' if BOT_AVATAR_B64 else ""
    st.markdown(f"""
    <div class="msg bot">
      <div class="avatar">{img_tag}</div>
      <div class="bubble">{html_text}</div>
    </div>""", unsafe_allow_html=True)

def render_user(text: str):
    img_tag = f'<img src="data:image/png;base64,{USER_AVATAR_B64}"/>' if USER_AVATAR_B64 else ""
    st.markdown(f"""
    <div class="msg user">
      <div class="bubble">{text}</div>
      <div class="avatar">{img_tag}</div>
    </div>""", unsafe_allow_html=True)

# ===========================================
# 7) DURUM / GEÇMİŞ (DEĞİŞİKLİK YOK)
# ===========================================
if "history" not in st.session_state:
    st.session_state.history = []  # list[tuple(role, html)]

# Geçmişi render et
for role, html in st.session_state.history:
    if role == "user":
        render_user(html)
    else:
        # Bot'un cevabı expander içerebilir, bu yüzden
        # html'i bir liste olarak kontrol edelim (güvenli yöntem)
        if isinstance(html, list):
            render_bot(html[0])
            with st.expander(html[1], expanded=False):
                st.markdown(html[2], unsafe_allow_html=True)
        else:
            render_bot(html)

# ===========================================
# 8) GİRİŞ (DEĞİŞİKLİK 4: Tamamen st.chat_input ile değiştirildi)
# ===========================================
placeholder_text = {
    "de": "Frage eingeben (z. B. Was ist ein Bildungsgutschein?)",
    "en": "Ask a question (e.g., What is a Bildungsgutschein?)"
}[lang_code]

# st.markdown('<div class="input-dock">', ...) # <-- KALDIRILDI
# ... (tüm st.columns, st.text_area, st.button kodları kaldırıldı)

# YENİ VE BASİT GİRİŞ YÖNTEMİ
if prompt := st.chat_input(placeholder_text):
    
    # 1. Kullanıcının sorusunu kaydet ve ekrana bas
    st.session_state.history.append(("user", prompt))
    render_user(prompt) # Ekranda hemen göster

    # 2. Bot cevabını oluştur
    with st.spinner("Denke nach..." if lang_code == "de" else "Thinking..."):
        try:
            short_ans, detailed = answer_pair(prompt, language=lang_code)
            
            # Kısa cevabı hazırla
            short_html = f"<b>{'Kurzfassung' if lang_code=='de' else 'Short Answer'}:</b> {short_ans}"
            
            # Detaylar için expander başlığı
            expander_label = "Mehr Details anzeigen" if lang_code=="de" else "Show more details"
            
            # Cevabı ve expander'ı BİRLİKTE kaydet
            # Bu, st.rerun() sonrası expander'ın kaybolmamasını sağlar
            st.session_state.history.append(
                ("bot", [short_html, expander_label, detailed])
            )
            
            # Yeni cevabı hemen ekrana bas
            render_bot(short_html)
            with st.expander(expander_label, expanded=False):
                st.markdown(detailed, unsafe_allow_html=True)

        except Exception as e:
            error_html = f"<b>Fehler:</b> {e}"
            st.session_state.history.append(("bot", error_html))
            render_bot(error_html)

    # DEĞİŞİKLİK 5: st.rerun() kaldırıldı.
    # st.chat_input() ve st.session_state kullanımı
    # rerun'a olan ihtiyacı ortadan kaldırır.

