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
