import streamlit as st
import pandas as pd
from io import BytesIO
from scoring import RULES, SECTION_LIMITS, GLOBAL_LIMITS, ItemRule, sum_with_section_caps, clamp
from parsers import extract_text, detect_counts

st.set_page_config(page_title="Categorizador Docente en Investigación", page_icon="📊", layout="wide")

st.title("📊 Categorizador Docente en Investigación")
st.caption("Versión demo – lectura de CV en .docx/.pdf/.txt y cálculo automático según el valorador.")

with st.expander("Instrucciones", expanded=True):
    st.markdown(
        """
        1) Subí tu CV en formato **.docx**, **.pdf** o **.txt** (recomendado .docx).
        2) La app extrae conteos mediante heurísticas (regex) y asigna puntaje con topes por ítem, sub-sección y sección.
        3) Revisá la tabla de desglose, los subtotales por sección y el **Total General**.
        4) Podés **descargar** el desglose en CSV.
        """
    )

uploaded = st.file_uploader("Subí tu CV", type=["docx", "pdf", "txt"])

def compute_scores(counts: dict):
    # Calcula puntajes por item (clamp por item) y acumula por sub-sección
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
        # determinar sección por el prefijo
        section = key.split(":")[0]
        section_totals[section] += capped_points
        item_rows.append({
            "Clave": key,
            "Ítem": rule.label,
            "Unidades detectadas": units,
            "Puntos por unidad": rule.points_per_unit,
            "Puntos (c/ tope ítem)": capped_points,
            "Tope ítem": rule.max_points,
            "Sección": section
        })

    # Aplicar tope de acumulación sección 2 (formación)
    section_totals["formacion"] = min(section_totals["formacion"], SECTION_LIMITS["formacion"])

    # Aplicar límites globales 3,4,5,6 y total general
    totals = sum_with_section_caps(section_totals)

    return pd.DataFrame(item_rows), totals

if uploaded:
    tmp_path = f"/tmp/{uploaded.name}"
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    text, kind = extract_text(tmp_path)
    st.success(f"Archivo leído como {kind.upper()} – longitud: {len(text)} caracteres")

    counts = detect_counts(text)

    df_items, totals = compute_scores(counts)

    st.subheader("Desglose por ítem")
    st.dataframe(df_items, use_container_width=True)

    st.subheader("Subtotales por sección (con topes aplicados)")
    show_keys = [
        "2:Formacion_total",
        "3:Cargos_total",
        "4:CyT_total",
        "5:Producciones_total",
        "6:Otros_total",
        "TOTAL_GENERAL"
    ]
    subtotal_pairs = [(k, totals.get(k, 0)) for k in show_keys]
    st.table(pd.DataFrame(subtotal_pairs, columns=["Sección", "Puntaje"]))


    # Descargar CSV
    csv = df_items.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar desglose (CSV)", data=csv, file_name="desglose_items.csv", mime="text/csv")

    with st.expander("Debug: Conteos detectados", expanded=False):
        st.json(counts)

else:
    st.info("Subí un CV de prueba para calcular el puntaje. Sugerencia: usar el CV_Docente_Ejemplo.docx que compartimos.")
