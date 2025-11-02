
import os
import pickle
import numpy as np
import google.generativeai as genai

VECTOR_PATH = "/content/drive/MyDrive/Chatbot_0/vectorstore/gemini_store.pkl"

def load_store():
    if not os.path.exists(VECTOR_PATH):
        raise FileNotFoundError(f"Vektör deposu bulunamadı: {VECTOR_PATH}")
    with open(VECTOR_PATH, "rb") as f:
        store = pickle.load(f)
    return store

def _ensure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)

def embed_query(text: str) -> np.ndarray:
    _ensure_gemini()
    resp = genai.embed_content(model="models/text-embedding-004", content=text)
    return np.array(resp["embedding"], dtype="float32")

def retrieve_context(store, query: str, k: int = 4):
    q_emb = embed_query(query)
    sims = []
    for item in store:
        d_emb = item["embedding"]
        num = float(np.dot(q_emb, d_emb))
        den = float((np.linalg.norm(q_emb) * np.linalg.norm(d_emb)) + 1e-10)
        sim = num / den
        sims.append(sim)
    sims = np.array(sims)
    top_idx = sims.argsort()[::-1][:k]
    ctx_parts = [store[i]["text"] for i in top_idx]
    context = "\n\n".join(ctx_parts)
    return context

def build_prompt(user_query: str, context: str, lang: str = "de", short: bool = True):
    if lang == "de":
        system_short = "Du bist ein Assistent der Bundesagentur für Arbeit. Antworte kurz, klar und höflich auf Deutsch."
        system_long  = "Du bist ein Assistent der Bundesagentur für Arbeit. Antworte ausführlich, strukturiert, mit Beispielen und nenne weitere Schritte auf Deutsch."
    else:
        system_short = "You are an assistant of the German Federal Employment Agency. Answer briefly, clearly and politely in English."
        system_long  = "You are an assistant of the German Federal Employment Agency. Answer in detail, structured, with examples and suggest next steps in English."

    system = system_short if short else system_long

    parts = [
        system,
        "",
        "Relevant context (retrieved from BA pages):",
        context,
        "",
        "User question:",
        user_query,
        "",
        "If the question is unclear or not covered, ask the user to clarify and propose 2-3 related options."
    ]
    prompt = "\n".join(parts)
    return prompt

def ask_gemini(prompt: str):
    _ensure_gemini()
    model = genai.GenerativeModel("gemini-1.5-pro")
    resp = model.generate_content(prompt)
    return resp.text
