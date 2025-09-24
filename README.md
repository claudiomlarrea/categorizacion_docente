# Categorizador Docente en Investigación (Streamlit)

Demo de una calculadora que lee un CV (.docx/.pdf/.txt) y asigna puntajes según el valorador proporcionado.

## Archivos
- `app.py`: aplicación principal Streamlit.
- `scoring.py`: configuración de reglas de puntaje y límites por sección.
- `parsers.py`: extracción de texto y heurísticas de conteo.
- `requirements.txt`: dependencias para desplegar en Streamlit Cloud / GitHub.

## Uso local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notas
- La extracción y conteo usan expresiones regulares heurísticas pensadas para el CV de ejemplo. Es normal que requiera ajustes para otros formatos.
- Los topes por ítem y por sección están implementados; se respetan también los topes globales por bloque.


## Despliegue en Streamlit Cloud
1. Subí todos los archivos a la **raíz** del repo.
2. En Streamlit Cloud, al crear la app, elegí como **Main file** `streamlit_app.py` (o `hello_smoke.py` para probar rápido).
3. Logs: `Manage app` → `Logs` para revisar errores de build/carga.
4. Requerimientos: usa `requirements.txt` provisto y `runtime.txt` (`python-3.11`).

