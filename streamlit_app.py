import streamlit as st
import pandas as pd
from pathlib import Path

# Módulos del proyecto
from scoring import RULES, SECTION_LIMITS, sum_with_section_caps
from parsers import extract_text, detect_counts, PDFSupportMissing
from report import build_docx_report

# ---------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Categorizador Docente en Investigación",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Categorizador Docente en Investigación")
st.caption("Lee CV en .docx/.pdf/.txt y aplica el valorador con topes por ítem y sección.")

with st.expander("📋 Instrucciones", expanded=True):
    st.markdown(
        """
        1) Subí tu CV (.docx/.pdf/.txt). Recomendado: **.docx**.  
        2) La app detecta cantidades con expresiones regulares (heurísticas).  
        3) Se aplican topes por ítem, sub-sección y sección.  
        4) Podés descargar el **desglose en CSV** o un **informe .docx**.  

        **Nota:** archivos **.doc** (Word 97-2003) no están soportados. Convertir a .docx o PDF.
        """
    )

# ---------------------------------------------------------------------
# Función de cálculo de puntajes a partir de los conteos detectados
# ---------------------------------------------------------------------
def compute_scores(counts: dict):
    item_rows = []
    # Suma por sección (las claves de sección son la parte antes de ":")
    section_totals = {}

    for key, rule in RULES.items():
        units = counts.get(key, 0)
        raw_points = units * rule.points_per_unit
        capped_points = min(raw_points, rule.max_points)
        section = key.split(":")[0]

        section_totals[section] = section_totals.get(section, 0.0) + capped_points

        item_rows.append({
            "Clave": key,
            "Sección": section,
            "Ítem": rule.label,
            "Unidades detectadas": units,
            "Puntos por unidad": rule.points_per_unit,
            "Tope ítem": rule.max_points,
            "Puntos (tope ítem)": capped_points,
        })

    # Ejemplo de tope por sección si existe en SECTION_LIMITS
    for sec, limit in SECTION_LIMITS.items():
        if sec in section_totals:
            section_totals[sec] = min(section_totals[sec], limit)

    totals = sum_with_section_caps(section_totals)  # devuelve 2:,3:,4:,5:,6: y TOTAL_GENERAL
    return pd.DataFrame(item_rows), totals

# ---------------------------------------------------------------------
# Uploader (hotfix para que siempre quede visible)
# ---------------------------------------------------------------------
st.subheader("Subí tu CV")
uploaded = st.file_uploader(
    label="Arrastrá y soltá o hacé clic en **Browse files**",
    type=("docx", "pdf", "txt"),
    accept_multiple_files=False,
    key="cv_uploader",
)

# Si no hay archivo, detenemos la ejecución aquí para que el uploader no desaparezca
if uploaded is None:
    st.info("👉 Elegí un archivo (.docx recomendado).")
    st.stop()

# ---------------------------------------------------------------------
# Procesamiento del archivo
# ---------------------------------------------------------------------
try:
    tmp_path = Path("/tmp") / uploaded.name
    tmp_path.write_bytes(uploaded.getbuffer())

    text, kind = extract_text(str(tmp_path))
    st.success(f"Archivo leído como **{kind.upper()}** – longitud: {len(text)} caracteres")

    # Detectar conteos y calcular puntajes
    counts = detect_counts(text)
    df_items, totals = compute_scores(counts)

    # ------------------ UI de resultados ------------------
    st.subheader("Desglose por ítem")
    st.dataframe(df_items, use_container_width=True)

    st.subheader("Subtotales por sección (con topes)")
    show_keys = [
        "2:Formacion_total",
        "3:Cargos_total",
        "4:CyT_total",
        "5:Producciones_total",
        "6:Otros_total",
        "TOTAL_GENERAL",
    ]
    subt = pd.DataFrame([(k, totals.get(k, 0)) for k in show_keys], columns=["Sección", "Puntaje"])
    st.table(subt)

    # Descarga CSV
    csv = df_items.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar desglose (CSV)",
        data=csv,
        file_name="desglose_items.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Informe Word
    with st.expander("📄 Generar informe en Word", expanded=True):
        col1, col2 = st.columns(2)
        docente = col1.text_input("Nombre del docente (opcional)")
        institucion = col2.text_input("Institución (opcional)")
        report_bytes = build_docx_report(
            df_items,
            totals,
            meta={"docente": docente, "institucion": institucion},
        )
        nombre_archivo = "Informe_Valorador.docx" if not docente else f"Informe_Valorador_{docente.replace(' ', '_')}.docx"
        st.download_button(
            "⬇️ Descargar informe en Word (.docx)",
            data=report_bytes,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    # Debug opcional
    with st.expander("🔧 Debug: Conteos detectados", expanded=False):
        st.json({"how_read": kind, "counts": counts})

except PDFSupportMissing:
    st.error(
        "No se pudo leer el PDF porque **pdfplumber** no está instalado en esta instancia. "
        "Subí el CV en **.docx** o **.txt** o agregá `pdfplumber` a requirements.txt y reiniciá la app."
    )
except ValueError as ve:
    st.error(str(ve))
except Exception as e:
    st.error(f"Error inesperado: {e}")
