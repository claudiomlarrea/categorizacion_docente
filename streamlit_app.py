
import streamlit as st
import pandas as pd
from scoring import RULES, SECTION_LIMITS, sum_with_section_caps
from parsers import extract_text, detect_counts, PDFSupportMissing

st.set_page_config(page_title="Categorizador Docente en Investigación", page_icon="📊", layout="wide")
st.title("📊 Categorizador Docente en Investigación")
st.caption("Lee CV en .docx/.pdf/.txt y aplica el valorador con topes por ítem y sección.")

with st.expander("Instrucciones", expanded=True):
    st.markdown(
        """
        1) Subí tu CV (.docx/.pdf/.txt). Recomendado: .docx.
        2) La app detecta cantidades con expresiones regulares (heurísticas).
        3) Se aplican topes por ítem, sub-sección y sección.
        4) Podés descargar el desglose de ítems en CSV.
        """
    )

uploaded = st.file_uploader("Subí tu CV", type=["docx", "pdf", "txt"])

def compute_scores(counts: dict):
    item_rows = []
    section_totals = {k: 0.0 for k in [
        "formacion", "docencia", "gestion", "otroscargos",
        "ciencia", "proyectos", "extension", "eval", "otras",
        "pubs", "desarrollos", "servicios",
        "redes", "premios"
    ]}

    for key, rule in RULES.items():
        units = counts.get(key, 0)
        raw_points = units * rule.points_per_unit
        capped_points = min(raw_points, rule.max_points)
        section = key.split(":")[0]
        section_totals[section] += capped_points
        item_rows.append({
            "Clave": key,
            "Ítem": rule.label,
            "Unidades detectadas": units,
            "Puntos por unidad": rule.points_per_unit,
            "Puntos (tope ítem)": capped_points,
            "Tope ítem": rule.max_points,
            "Sección": section
        })

    section_totals["formacion"] = min(section_totals["formacion"], SECTION_LIMITS["formacion"])
    totals = sum_with_section_caps(section_totals)
    return pd.DataFrame(item_rows), totals

if uploaded:
    tmp_path = f"/tmp/{uploaded.name}"
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    try:
        text, kind = extract_text(tmp_path)
        st.success(f"Archivo leído como {kind.upper()} – longitud: {len(text)} caracteres")
        counts = detect_counts(text)
        df_items, totals = compute_scores(counts)

        st.subheader("Desglose por ítem")
        st.dataframe(df_items, use_container_width=True)

        st.subheader("Subtotales por sección (con topes)")
        show_keys = [
            "2:Formacion_total",
            "3:Cargos_total",
            "4:CyT_total",
            "5:Producciones_total",
            "6:Otros_total",
            "TOTAL_GENERAL"
        ]
        st.table(pd.DataFrame([(k, totals.get(k, 0)) for k in show_keys], columns=["Sección", "Puntaje"]))

        csv = df_items.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar desglose (CSV)", data=csv, file_name="desglose_items.csv", mime="text/csv")

        with st.expander("Debug: Conteos detectados", expanded=False):
            st.json(counts)

    except PDFSupportMissing:
        st.error("No se pudo leer el PDF porque **pdfplumber** no está instalado en esta instancia. Subí el CV en **.docx** o **.txt** o agregá `pdfplumber` a requirements.txt y reiniciá la app.")
else:
    st.info("Subí un CV de prueba (por ejemplo, el CV_Docente_Ejemplo.docx) para calcular el puntaje.")
