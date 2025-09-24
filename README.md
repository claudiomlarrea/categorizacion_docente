# Categorizador Docente en Investigación (Streamlit)

Lee CV (.docx/.pdf/.txt) y asigna puntajes según el valorador.

## Archivos
- streamlit_app.py (entrypoint)
- app.py
- scoring.py
- parsers.py (con fallback a docx2txt y extracción XML si falta python-docx)
- requirements.txt
- runtime.txt
- hello_smoke.py
- README.md

## Uso local
pip install -r requirements.txt
streamlit run streamlit_app.py

## Despliegue en Streamlit Cloud
- Subí todo a la raíz del repo.
- Elegí `streamlit_app.py` como Main file (o `hello_smoke.py` para smoke test).
- Reboot app si queda en "oven".
