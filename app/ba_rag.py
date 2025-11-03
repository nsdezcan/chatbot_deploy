# app/ba_rag.py
import os
import glob
from pathlib import Path
from typing import List, Tuple
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from groq import Groq

# -------------------------------------------------------------------
# 1) Veri yükleme ve arama (TF-IDF)
# -------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _read_txt_files() -> List[Tuple[str, str]]:
    """
    data/*.txt dosyalarını (ad, içerik) listesi olarak döndürür.
    """
    docs = []
    for fp in sorted(glob.glob(str(DATA_DIR / "*.txt"))):
        try:
            text = Path(fp).read_text(encoding="utf-8")
            name = Path(fp).name
            # basit temizlik
            text = text.replace("\r", "")
            docs.append((name, text))
        except Exception as e:
            print(f"⚠️ Okunamadı: {fp} ({e})")
    return docs

class SimpleRetrieval:
    """
    TF-IDF tabanlı basit bir arama sınıfı.
    """
    def __init__(self, documents: List[Tuple[str, str]]):
        self.names = [n for n, _ in documents]
        self.docs  = [t for _, t in documents]
        self.vectorizer = TfidfVectorizer(
            stop_words=None, max_df=0.9, min_df=2, ngram_range=(1,2)
        )
        self.doc_mat = self.vectorizer.fit_transform(self.docs)

    def query(self, q: str, top_k: int = 5) -> List[Tuple[str, str]]:
        q_vec = self.vectorizer.transform([q])
        sims = cosine_similarity(q_vec, self.doc_mat)[0]
        idxs = sims.argsort()[::-1][:top_k]
        return [(self.names[i], self.docs[i]) for i in idxs if sims[i] > 0.0]

# -------------------------------------------------------------------
# 2) Groq ile cevap üretimi
# -------------------------------------------------------------------

def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set.")
    return Groq(api_key=api_key)

def _build_system_prompt(language: str) -> str:
    """
    language: 'tr' | 'de' | 'en'
    """
    base = {
        "tr": (
            "Sen BA (Bundesagentur für Arbeit) konularında yardımcı bir asistansın. "
            "Kısa ve net cevap ver; emin değilsen 'emin değilim' de. "
            "Önce 1-2 cümlelik ÖZET, istenirse ayrıntı ver."
        ),
        "de": (
            "Du bist ein hilfreicher Assistent zu Themen der Bundesagentur für Arbeit. "
            "Antworte kurz und präzise; wenn unsicher, sage 'Ich bin mir nicht sicher'. "
            "Zuerst 1–2 Sätze ZUSAMMENFASSUNG, Details auf Wunsch."
        ),
        "en": (
            "You are a helpful assistant for topics of the German Federal Employment Agency (BA). "
            "Answer concisely; if unsure, say 'I'm not sure'. "
            "Provide a 1–2 sentence SUMMARY first, details on request."
        ),
    }
    return base.get(language, base["de"])

def _lang_label(language: str) -> str:
    return {"tr": "Türkçe", "de": "Deutsch", "en": "English"}.get(language, "Deutsch")

def ask_groq_short(question: str, contexts: List[str], language: str) -> str:
    """
    Groq'tan KISA cevap (2-3 cümle) ister.
    """
    client = _get_client()
    system = _build_system_prompt(language)
    ctx_joined = "\n\n---\n\n".join(contexts[:3]) if contexts else ""
    user_msg = (
        f"Soru ({_lang_label(language)}): {question}\n\n"
        f"İlgili bağlamlar (en fazla 3):\n{ctx_joined}\n\n"
        f"Lütfen 2-3 cümlelik kısa yanıt ver."
    )
    resp = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()

def ask_groq_detailed(question: str, contexts: List[str], language: str) -> str:
    """
    Groq'tan DETAYLI cevap ister.
    """
    client = _get_client()
    system = _build_system_prompt(language)
    ctx_joined = "\n\n---\n\n".join(contexts[:8]) if contexts else ""
    user_msg = (
        f"Soru ({_lang_label(language)}): {question}\n\n"
        f"Bağlam parçaları (en fazla 8):\n{ctx_joined}\n\n"
        f"Lütfen kaynaklardaki noktalara dayalı detaylı, adım adım anlatım yap. "
        f"Belirsizse açıkça belirt."
    )
    resp = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=1200,
    )
    return resp.choices[0].message.content.strip()

# -------------------------------------------------------------------
# 3) Dışa sunulan yardımcılar
# -------------------------------------------------------------------

_retrieval_cache = None

def load_store():
    global _retrieval_cache
    if _retrieval_cache is not None:
        return _retrieval_cache

    docs = _read_txt_files()
    if not docs:
        raise RuntimeError(f"data/*.txt bulunamadı. DATA_DIR={DATA_DIR}")
    _retrieval_cache = SimpleRetrieval(docs)
    return _retrieval_cache

def retrieve_context(store: SimpleRetrieval, query: str, top_k: int = 5) -> List[str]:
    items = store.query(query, top_k=top_k)
    return [t for _, t in items]

def answer_pair(question: str, language: str = "de") -> Tuple[str, str]:
    """
    Tek çağrıda (kısa, detaylı) cevap çifti üretir.
    """
    store = load_store()
    ctxs = retrieve_context(store, question, top_k=8)
    short = ask_groq_short(question, ctxs, language)
    detailed = ask_groq_detailed(question, ctxs, language)
    return short, detailed

