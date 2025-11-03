# app/ba_rag.py
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -------------------------------------------------
# Yollar
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"   # …/chatbot_deploy/data

# -------------------------------------------------
# Küçük bir “store” yapısı
# -------------------------------------------------
@dataclass
class Store:
    file_names: List[str]
    texts: List[str]
    vectorizer: TfidfVectorizer
    matrix: np.ndarray


def _read_txt_files() -> Tuple[List[str], List[str]]:
    """data/ içindeki .txt dosyalarını oku."""
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"data klasörü bulunamadı: {DATA_DIR}")

    file_names, texts = [], []
    for p in sorted(DATA_DIR.glob("*.txt")):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = p.read_text(encoding="latin-1")
        file_names.append(p.name)
        texts.append(text)
    if not texts:
        raise RuntimeError("data/ klasöründe .txt dosyası yok. Lütfen ekleyin.")
    return file_names, texts


# -------------------------------------------------
# PUBLIC: load_store / retrieve_context
# -------------------------------------------------
def load_store() -> Store:
    """TXT’leri okuyup TF-IDF matrisi hazırla."""
    file_names, texts = _read_txt_files()

    vectorizer = TfidfVectorizer(
        strip_accents="unicode",
        lowercase=True,
        ngram_range=(1, 2),     # unigram + bigram
        max_df=0.95,
        min_df=2,
    )
    matrix = vectorizer.fit_transform(texts)

    return Store(
        file_names=file_names,
        texts=texts,
        vectorizer=vectorizer,
        matrix=matrix,
    )


def retrieve_context(store: Store, query: str, k: int = 4) -> List[str]:
    """Sorgu için en benzer k doküman parçasını getir (doküman bazlı)."""
    q_vec = store.vectorizer.transform([query])
    sims = cosine_similarity(q_vec, store.matrix).ravel()
    top_idx = sims.argsort()[::-1][:k]
    return [store.texts[i] for i in top_idx if sims[i] > 0]


# -------------------------------------------------
# Groq istemcisi ve yanıt üretimi (MODEL FALLBACK'lı)
# -------------------------------------------------
def _groq_client() -> Groq:
    key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key") or os.getenv("GROQ")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY boş. Streamlit Cloud → App → Settings → Secrets içine ekleyin."
        )
    return Groq(api_key=key)


# Kullanılabilir modeller (ilk çalışanı kullanırız, hata olursa sıradakine düşer)
MODEL_PREFERENCE = [
    "llama-3.1-8b-instant",      # hızlı/ucuz ve aktif
    "llama-3.1-70b-instant",     # daha güçlü (hesapta açıksa)
    "mixtral-8x7b-32768",        # yedek
]


def _pick_model() -> str:
    return MODEL_PREFERENCE[0]


def _lang_system_msg(lang: str) -> str:
    """Yanıt dili için sistem talimatı."""
    if lang == "de":
        return (
            "Du bist ein hilfreicher Assistent der Bundesagentur für Arbeit. "
            "Antworte knapp, korrekt und sachlich auf Deutsch."
        )
    if lang == "tr":
        return (
            "Sen Almanya Federal İş Ajansı (BA) konusunda yardımcı bir asistansın. "
            "Cevapları Türkçe, doğru ve net yaz."
        )
    # en
    return (
        "You are a helpful assistant specialized in the German Federal Employment Agency (BA). "
        "Answer clearly and correctly in English."
    )


def _build_context_block(docs: List[str], max_chars: int = 3000) -> str:
    """Toplanan bağlamı tek blokta birleştir (kırp)."""
    joined = "\n\n---\n\n".join(docs)
    return joined[:max_chars]


def _chat_complete(system: str, user: str, max_tokens: int = 800, temperature: float = 0.2) -> str:
    """Modeli seçip çağırır; hata olursa listedeki bir sonraki modele düşer."""
    client = _groq_client()
    tried = []

    for model in MODEL_PREFERENCE:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            tried.append((model, str(e)))
            continue

    # Hepsi hata verirse özet bilgi dökelim:
    msgs = "\n".join([f"- {m}: {err}" for m, err in tried])
    raise RuntimeError(f"Tüm Groq model çağrıları başarısız oldu:\n{msgs}")


# -------------------------------------------------
# PUBLIC: answer_pair
# -------------------------------------------------
def answer_pair(question: str, language: str = "de") -> Tuple[str, str]:
    """
    Kısa + detaylı iki yanıt döndür.
    language: "de" | "en" | "tr"
    """
    store = load_store()
    docs = retrieve_context(store, question, k=4)
    context = _build_context_block(docs)

    sys_prompt = _lang_system_msg(language)

    user_short = (
        "KISA cevap ver (1-3 cümle). Eğer bağlam yeterli değilse 'Emin değilim' de.\n\n"
        f"Frage/Question/Soru: {question}\n\n"
        f"Kontext/Context/Bağlam:\n{context}"
    )

    user_detail = (
        "DETAYLI cevap ver (madde madde veya kısa paragraflar). "
        "Cevapta mümkünse kaynak bağlamdan alıntıları anlamca özetle. "
        "Bilmediğin kısımları tahmin etme.\n\n"
        f"Frage/Question/Soru: {question}\n\n"
        f"Kontext/Context/Bağlam:\n{context}"
    )

    short_ans = _chat_complete(system=sys_prompt, user=user_short)
    detailed_ans = _chat_complete(system=sys_prompt, user=user_detail)

    return short_ans, detailed_ans
