from pathlib import Path
import os
import pickle
import json
import re

import numpy as np
import google.generativeai as genai

# -------------------------------------------------
# 1. Yol ayarları
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
VECTOR_PATH = BASE_DIR.parent / "vectorstore" / "gemini_store.pkl"

# -------------------------------------------------
# 2. API anahtarı
# -------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY ortam değişkeni bulunamadı. "
        "Streamlit Cloud → Settings → Secrets içine GEMINI_API_KEY=\"...\" ekle."
    )

genai.configure(api_key=API_KEY)

EMBED_MODEL = "models/text-embedding-004"
CHAT_MODEL = "gemini-1.5-flash"   # istersen 1.5-pro yapabilirsin

# -------------------------------------------------
# 3. Vektör deposunu yükle
# -------------------------------------------------
def load_store():
    if not VECTOR_PATH.exists():
        raise FileNotFoundError(f"Vektör deposu bulunamadı: {VECTOR_PATH}")
    with VECTOR_PATH.open("rb") as f:
        store = pickle.load(f)
    # store -> Colab’da yaptığımız gibi: [{ "embedding": [...], "text": "...", "source": "ba_page_00.txt" }, ...]
    return store

# -------------------------------------------------
# 4. Embed helpers
# -------------------------------------------------
def embed_text(text: str):
    """Gemini'den 768 boyutlu embedding al."""
    resp = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
    )
    return resp["embedding"]

def cosine(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

# -------------------------------------------------
# 5. En iyi k dokümanı getir
# -------------------------------------------------
def retrieve_context(store, query: str, k: int = 4):
    q_emb = embed_text(query)
    scored = []
    for i, item in enumerate(store):
        d_emb = item["embedding"]
        score = cosine(q_emb, d_emb)
        scored.append((score, i))

    scored.sort(reverse=True, key=lambda x: x[0])
    top = []
    for score, idx in scored[:k]:
        doc = store[idx]
        top.append(
            {
                "text": doc["text"],
                "source": doc.get("source", f"chunk_{idx}"),
                "score": score,
            }
        )
    return top

# -------------------------------------------------
# 6. Prompt oluştur
# -------------------------------------------------
def build_prompt(question: str, docs, lang: str = "de") -> str:
    context_blocks = []
    for i, d in enumerate(docs, start=1):
        context_blocks.append(f"[{i}] Quelle: {d['source']}\n{d['text']}")
    context_text = "\n\n".join(context_blocks)

    if lang == "en":
        system = (
            "You are a helpful assistant of the German Federal Employment Agency (Bundesagentur für Arbeit).\n"
            "Answer ONLY from the given context. If the answer is not there, say so.\n"
            "Return the answer in JSON with two fields:\n"
            "{\n"
            '  "short": "2-3 sentence quick answer",\n'
            '  "long": "well-structured, detailed answer with bullet points and, if possible, references to the context blocks"\n'
            "}\n"
        )
    else:  # default: German
        system = (
            "Du bist ein Assistent der Bundesagentur für Arbeit.\n"
            "Antworte NUR auf Basis des gegebenen Kontextes. Wenn etwas im Kontext nicht steht, schreibe das ehrlich.\n"
            "Gib die Antwort im JSON-Format zurück:\n"
            "{\n"
            '  "short": "2-3 Sätze, sehr kurz",\n'
            '  "long": "ausführliche, gut gegliederte Antwort mit evtl. Aufzählungen und Verweisen auf die Quellen"\n'
            "}\n"
        )

    prompt = (
        f"{system}\n\n"
        f"Kontext-Dokumente:\n{context_text}\n\n"
        f"Frage / Question: {question}\n"
        "WICHTIG: Antworte wirklich im JSON-Format, ohne zusätzlichen Text."
    )
    return prompt

# -------------------------------------------------
# 7. Gemini'den yanıt al
# -------------------------------------------------
def ask_gemini(prompt: str):
    model = genai.GenerativeModel(CHAT_MODEL)
    resp = model.generate_content(prompt)
    txt = resp.text.strip()

    # Gemini bazen başına/sonuna cümle ekliyor, bunu yakalayıp JSON'u çıkarmaya çalışalım
    try:
        start = txt.index("{")
        end = txt.rindex("}") + 1
        json_part = txt[start:end]
        data = json.loads(json_part)
    except Exception:
        # JSON değilse kısa/uzun aynı olsun
        data = {
            "short": txt,
            "long": txt,
        }
    return data

