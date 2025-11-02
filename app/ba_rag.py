import os
import pickle
from pathlib import Path
import numpy as np
import google.generativeai as genai

# -------------------------------------------------
# 1) Yol ayarları (Cloud / GitHub için GÖRECELİ yol)
# -------------------------------------------------
# bu dosyanın bulunduğu klasör: /mount/src/chatbot_deploy/app
BASE_DIR = Path(__file__).resolve().parent
# .. = projenin kökü → /mount/src/chatbot_deploy
VECTOR_PATH = (BASE_DIR / ".." / "vectorstore" / "gemini_store.pkl").resolve()

# -------------------------------------------------
# 2) Vektör deposunu yükle
# -------------------------------------------------
def load_store():
    if not VECTOR_PATH.exists():
        raise FileNotFoundError(f"Vektör deposu bulunamadı: {VECTOR_PATH}")
    with open(VECTOR_PATH, "rb") as f:
        store = pickle.load(f)
    return store

# -------------------------------------------------
# 3) En benzer parçaları getir
#    (pkl içindeki key'ler biz Colab’de nasıl kaydettiysek ona uyacak)
# -------------------------------------------------
def retrieve_context(store, query, top_k=4):
    # pkl bazen {"texts": [...], "embeddings": [...]} şeklinde
    # bazen de [{"text": ..., "embedding": ...}, ...] şeklinde olabilir.
    # İkisini de destekleyelim.
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    # Sorguyu embed et
    emb_model = genai.GenerativeModel("models/text-embedding-004")
    q_emb = emb_model.embed_content(query)["embedding"]
    q_emb = np.array(q_emb)

    # 1. format: dict
    if isinstance(store, dict):
        texts = (
            store.get("texts")
            or store.get("chunks")
            or store.get("documents")
        )
        embeds = (
            store.get("embeddings")
            or store.get("vectors")
        )
        embeds = np.array(embeds)
    else:
        # 2. format: list of dicts
        texts = [item["text"] for item in store]
        embeds = np.array([item["embedding"] for item in store])

    # kosinüs benzerliği
    sims = embeds @ q_emb / (np.linalg.norm(embeds, axis=1) * np.linalg.norm(q_emb) + 1e-8)
    idxs = sims.argsort()[::-1][:top_k]

    return [texts[i] for i in idxs]

# -------------------------------------------------
# 4) Prompt oluşturma
# -------------------------------------------------
def build_prompt(user_query, ctx_list, lang="de"):
    joined_ctx = "\n\n".join(ctx_list)
    if lang == "en":
        system = (
            "You are a helpful assistant for the German Federal Employment Agency (BA). "
            "Answer shortly first, then be ready to explain in detail."
        )
    else:
        system = (
            "Du bist ein hilfreicher Assistent der Bundesagentur für Arbeit. "
            "Antworte zuerst kurz und klar auf Deutsch. Danach kannst du Details nennen."
        )
    prompt = f"""{system}

Nutzerfrage:
{user_query}

Relevante Informationen:
{joined_ctx}

Kurze Antwort (2-4 Sätze), dann bei Bedarf Details:
"""
    return prompt

# -------------------------------------------------
# 5) Gemini'den cevap alma
# -------------------------------------------------
def ask_gemini(prompt, model_name="gemini-1.5-flash"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    return resp.text


      
