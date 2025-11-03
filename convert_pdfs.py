# convert_pdfs.py
from pathlib import Path
from pypdf import PdfReader
import re

RAW_DIR = Path("data_raw")
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

def clean_text(t: str) -> str:
    t = t.replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n\n", t)
    return t.strip()

def pdf_to_txt(pdf_path: Path, out_txt: Path):
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    text = clean_text("\n".join(parts))
    out_txt.write_text(text, encoding="utf-8")
    print(f"✓ {pdf_path.name} -> {out_txt.name} ({len(text)} chars)")

def main():
    mapping = {
        "merkblatt-6-weiterbildung.pdf": "merkblatt-6-weiterbildung.txt",
        "Employee Training Support.pdf": "employee-training-support.txt",
    }
    for pdf_name, txt_name in mapping.items():
        src = RAW_DIR / pdf_name
        dst = OUT_DIR / txt_name
        if not src.exists():
            print(f"⚠️ Bulunamadı: {src}")
            continue
        pdf_to_txt(src, dst)

if __name__ == "__main__":
    main()
