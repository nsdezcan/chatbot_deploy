base_dir = "/content/drive/MyDrive/Chatbot_0"

readme_text = """
# Bundesagentur für Arbeit Chatbot 🤖

Bu proje, Bundesagentur für Arbeit (BA) web sitesinden çekilen Almanca içeriklerle
ve ek olarak İngilizce bir PDF kaynağıyla (ör: *Employee Training Support.pdf*)
çalışan, Gemini tabanlı bir RAG (Retrieval-Augmented Generation) chatbotudur.

## Özellikler

- 🇩🇪 Varsayılan dil: Almanca
- 🇬🇧 İkinci dil: İngilizce (arayüz ve cevap)
- Gemini API ile çalışır
- Colab'de embed edilmiş veriler `vectorstore/gemini_store.pkl` içinde gelir
- Streamlit arayüzü görsel bir chat balonu formatındadır
- "Kısa cevap + Detaylandır" akışı vardır
- Anlamadığı durumda öneri sunar

## Klasör Yapısı

```text
Chatbot_0/
├── app/
│   ├── app.py          ← Streamlit arayüzü (main file)
│   └── ba_rag.py       ← vektörlerden context getirip Gemini'ye soran modül
├── assets/
│   └── logo_company.png
├── vectorstore/
│   └── gemini_store.pkl   ← Colab'de oluşturduğumuz gömülü veriler
├── data/                  ← BA sayfalarından çekilen ham txt dosyaları
└── requirements.txt
