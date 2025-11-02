
import os
import sys
import streamlit as st

sys.path.append(os.path.dirname(__file__))
from ba_rag import load_store, retrieve_context, build_prompt, ask_gemini

st.set_page_config(page_title="BA Chatbot", page_icon="💬", layout="centered")

# Arka plan stili (raw string sayesinde 90deg sorunsuz)
st.markdown(r'''
<style>
body {
  background: linear-gradient(90deg, #E57373 0%, #E9FAD9 50%, #C6F3FF 100%);
}
.chat-container {
  max-width: 720px;
  margin: 1.5rem auto;
  background: #ffffffdd;
  border-radius: 20px;
  box-shadow: 0 12px 35px rgba(0,0,0,0.12);
  padding: 0;
}
.header-bar {
  background: #fff;
  border-bottom: 1px solid #eee;
  padding: 0.7rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.header-title {
  font-weight: 600;
  font-size: 1.0rem;
}
.msg-bot {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.7rem;
}
.msg-user {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.7rem;
}
.bubble-bot {
  background: #f4f4ff;
  border-radius: 14px;
  padding: 0.4rem 0.7rem;
  max-width: 85%;
  border: 1px solid #ececff;
  font-size: 0.92rem;
}
.bubble-user {
  background: #d6f7df;
  border-radius: 14px;
  padding: 0.4rem 0.7rem;
  max-width: 85%;
  font-size: 0.92rem;
}
</style>
''', unsafe_allow_html=True)

# Basit test
st.write("✅ Stil başarıyla yüklendi.")
