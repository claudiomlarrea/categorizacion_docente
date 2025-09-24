
import io
import re
import unicodedata
from typing import Tuple

# We try docx2txt first because it handles tables very well and is fast.
# If it fails, we fall back to python-docx.
def _normalize_text(s: str) -> str:
    # Remove duplicate whitespace, normalize accents, and lowercase
    s = s.replace('\xa0', ' ')           # non‑breaking spaces
    s = unicodedata.normalize("NFKC", s) # normalize width/compatibility
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\r?\n\s*\r?\n+', '\n', s)  # collapse big blank blocks
    return s

def extract_text(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    """
    Returns (text, how_read) where how_read is a short string describing the reader used.
    Supports DOCX (including giant table exports), PDF (optional), and TXT.
    """
    name = (filename or "").lower()
    # TXT
    if name.endswith(".txt"):
        try:
            text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = file_bytes.decode("latin-1", errors="replace")
        return _normalize_text(text), "TXT"
    # DOCX
    if name.endswith(".docx"):
        # 1) docx2txt (best for tables, super fast)
        try:
            import docx2txt
            # docx2txt requires a file path, so write to an in-memory temp file
            # For Streamlit we can pass a BytesIO, but docx2txt wants a path, so save to temp.
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                tmp_path = tmp.name
            text = docx2txt.process(tmp_path)
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            if text and text.strip():
                return _normalize_text(text), "DOCX via docx2txt"
        except Exception:
            pass
        # 2) Fallback: python-docx (reads paragraphs + tables)
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            parts = []
            # paragraphs
            for p in doc.paragraphs:
                t = p.text.strip()
                if t:
                    parts.append(t)
            # tables (walk every cell)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        t = cell.text.strip()
                        if t:
                            parts.append(t)
            text = "\n".join(parts)
            return _normalize_text(text), "DOCX via python-docx"
        except Exception as e:
            return f"[ERROR leyendo DOCX: {e}]", "ERROR"
    # PDF (optional; only if your app added pdfplumber)
    if name.endswith(".pdf"):
        try:
            import pdfplumber
            text = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text.append(page.extract_text() or "")
            return _normalize_text("\n".join(text)), "PDF"
        except Exception as e:
            return f"[ERROR leyendo PDF: {e}]", "ERROR"
    # Fallback: try to decode as text
    try:
        text = file_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = file_bytes.decode("latin-1", errors="replace")
    return _normalize_text(text), "RAW"
