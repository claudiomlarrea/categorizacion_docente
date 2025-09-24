# Categorizador Docente en Investigación (Streamlit) — v4

- Entrada principal: `streamlit_app.py`
- PDF es **opcional** (lazy import). Si querés soporte PDF, agregá `pdfplumber==0.11.4` a `requirements.txt`.
- Parsers con fallbacks: `python-docx` → `docx2txt` → lectura XML.

## Despliegue en Streamlit Cloud
1. Subí todo a la **raíz** del repo.
2. Elegí `hello_smoke.py` como Main file para probar. Si abre, cambiá a `streamlit_app.py`.
3. Reboot app si queda en "oven".

## Uso local
pip install -r requirements.txt
streamlit run streamlit_app.py
