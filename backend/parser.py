from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

def extract(data: bytes, filename: str):
    ext=Path(filename).suffix.lower()
    if ext==".pdf":
        reader=PdfReader(BytesIO(data))
        pages=[p.extract_text() or "" for p in reader.pages]
        text="\n".join(pages).strip()
        if not text:
            raise ValueError("This PDF appears to be scanned or image-only. OCR is required to read it.")
        return text
    if ext in {".txt",".md"}:
        return data.decode("utf-8",errors="ignore").strip()
    raise ValueError("Only PDF, TXT and MD files are supported.")

def clean(text):
    return "\n".join(line.strip() for line in text.replace("\r","\n").splitlines() if line.strip())
