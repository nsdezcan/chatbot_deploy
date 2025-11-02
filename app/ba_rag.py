import os
import pickle
from pathlib import Path
import numpy as np
import google.generativeai as genai


# -------------------------------------------------
# 1) Yol ayarı – çok basit
#    Çalışma dizini = repo kökü
#    /mount/src/chatbot_deploy/vectorstore/gemini_store.pkl
# -------------------------------------------------
REPO_ROOT = Path(".").resolve()
VECTOR_PATH = REPO_ROOT / "vectorstore" / "gemini_store.pkl"


def load_store():
    """Pickle ile kaydedilmiş vektör deposunu yükler."""
    if not VECTOR_PATH.exists():
        raise FileNotFoundError(f"Vektör deposu bulunamadı: {VECTOR_PATH}")
    with open(VECTOR_PATH, "rb") as f:
        store = pickle.load(f)
    return store


def _ensure_api_key():
    # Streamlit Secrets'te KEY adını şöyle kaydettik:
    # GOOGLE_API_KEY = "...."
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY bulunamadı. Streamlit Secrets'e ekle.")
    genai.configure(api_key=api_key)


def retrieve_context(store, query: str, top_k: int = 4):
    """Sorgu için en benzer top_k metni döndürür."""
    _ensure_api_key()

    # Sorguyu embed et
    emb_model = genai.GenerativeModel("models/text-embedding-004")
    q_emb = emb_model.embed_content(query)["embedding"]
    q_emb = np.array(q_emb, dtype="float32")

    # Depo iki farklı formatta olabilir, ikisini de destekle
    if isinstance(store, dict):
        texts = (
            store.get("texts")
            or store.get("chunks")
            or store.get("documents")
        )
        embeds = store.get("embeddings") or store.get("vectors")
        embeds = np.array(embeds, dtype="float32")
    else:
        # list of {"text": ..., "embedding": ...}
        texts = [item["text"] for item in store]
        embeds = np.array([item["embedding"] for item in store], dtype="float32")

    # kosinüs benzerliği
    sims = embeds @ q_emb / (
        np.linalg.norm(embeds, axis=1) * np.linalg.norm(q_emb) + 1e-8
    )
    idxs = sims.argsort()[::-1][:top_k]
    return [texts[i] for i in idxs]


def build_prompt(user_query: str, ctx_list, lang: str = "de") -> str:
    ctx = "\n\n".join(ctx_list)

    if lang == "en":
        system = (
            "You are a helpful assistant for the German Federal Employment Agency (BA). "
            "First give a short, clear answer, then be ready to give details."
        )
    else:
        system = (
            "Du bist ein hilfreicher Assistent der Bundesagentur für Arbeit. "
            "Antworte zuerst kurz und klar auf Deutsch. Danach kannst du Details geben."
        )

    prompt = f"""{system}

Nutzerfrage / User question:
{user_query}

Relevante Informationen aus den Dokumenten:
{ctx}

Kurze Antwort (2–4 Sätze). Danach, falls Nutzer 'Details' isterse, ayrıntılı anlat:
"""
    return prompt


def ask_gemini(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    _ensure_api_key()
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    return resp.text
