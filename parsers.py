# parsers.py
# v2025-09-29 — Reglas estrictas para Formación y mejor detección de Producciones.

from __future__ import annotations
import io, re, unicodedata
from typing import List, Tuple, Dict
import pandas as pd

# ---------------------------------------------------------------------
# Excepción para soporte PDF opcional (la usa streamlit_app.py)
# ---------------------------------------------------------------------
class PDFSupportMissing(Exception):
    pass

# ---------------------------------------------------------------------
# Normalización de texto
# ---------------------------------------------------------------------
def _strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")

def _norm(s: str) -> str:
    s = s.replace("\x0c", "\n")  # saltos de página PDF
    s = _strip_accents(s)
    s = s.lower()
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s

# ---------------------------------------------------------------------
# Lectura de archivos
# ---------------------------------------------------------------------
def extract_text(uploaded_file) -> Tuple[str, str]:
    """Devuelve (texto_normalizado, tipo: DOCX|PDF|TXT)."""
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.read()

    if name.endswith(".docx"):
        import docx2txt
        text = docx2txt.process(io.BytesIO(raw)) or ""
        return _norm(text), "DOCX"

    if name.endswith(".pdf"):
        try:
            import pdfplumber  # lazy import
        except Exception as e:
            raise PDFSupportMissing("pdfplumber_not_installed") from e
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            pages = [(p.extract_text() or "") for p in pdf.pages]
        return _norm("\n".join(pages)), "PDF"

    if name.endswith(".txt"):
        return _norm(raw.decode("utf-8", errors="ignore")), "TXT"

    if name.endswith(".doc"):
        # viejo Word 97-2003: no lo procesamos para evitar falsos positivos
        raise ValueError("Los archivos .doc (97-2003) no se soportan. Convertir a .docx o PDF.")

    # fallback
    return _norm(raw.decode("utf-8", errors="ignore")), "TXT"

# ---------------------------------------------------------------------
# Utilidades de búsqueda contextual
# ---------------------------------------------------------------------
def _find_with_context(
    text: str,
    core_pattern: str,
    must_in_window: List[str] | None = None,
    forbid_left: List[str] | None = None,
    window: int = 80,
) -> int:
    """
    Cuenta ocurrencias del patrón principal siempre que:
      - en la ventana +/- 'window' haya alguna palabra obligatoria (must_in_window),
      - y a la izquierda inmediata NO aparezcan palabras de exclusión (forbid_left).
    """
    must_in_window = must_in_window or []
    forbid_left = forbid_left or []

    count = 0
    for m in re.finditer(core_pattern, text, flags=re.I):
        i0, i1 = m.span()
        left = text[max(0, i0 - window):i0]
        win = text[max(0, i0 - window):min(len(text), i1 + window)]

        if any(bad in left for bad in forbid_left):
            continue
        if must_in_window and not any(req in win for req in must_in_window):
            continue
        count += 1
    return count

def _count_distinct_isbn(text: str) -> int:
    # ISBN como proxy robusto de libros / capítulos
    raw_isbns = re.findall(r"\bisbn[^0-9]*([0-9\- ]{8,20})", text, flags=re.I)
    clean = set(re.sub(r"[^0-9X]", "", s.upper()) for s in raw_isbns if s.strip())
    return len(clean)

# ---------------------------------------------------------------------
# Detectores por ítem
# (solo devuelven "unidades"; los puntos y topes los maneja scoring.py)
# ---------------------------------------------------------------------

# --- Formación --------------------------------------------------------
def _count_doctorados(text: str) -> int:
    core = r"\bdoctorad[oa]\b|\bph\.?d\b"
    must = ["titulo", "egres", "obtuvo", "acredit", "universidad", "resol", "res.", "facultad", "anio", "año", "20", "19"]
    forbid = ["director", "coordinador", "comite", "comité", "jurado", "docente", "catedra", "cohorte"]
    return _find_with_context(text, core, must_in_window=must, forbid_left=forbid, window=90)

def _count_maestrias(text: str) -> int:
    core = r"\bmaestr(i|í)a\b|\bmagister\b|\bm\.?sc\b"
    must = ["titulo", "egres", "obtuvo", "acredit", "universidad", "resol", "facultad", "diploma", "20", "19"]
    forbid = ["director", "coordinador", "comite", "comité", "jurado", "docente", "programa", "curso", "materia"]
    return _find_with_context(text, core, must_in_window=must, forbid_left=forbid, window=90)

def _count_especializaciones(text: str) -> int:
    core = r"\bespecializacion\b|\bespecializaci[oó]n\b"
    must = ["titulo", "egres", "obtuvo", "universidad", "resol", "acredit", "diploma", "20", "19"]
    forbid = ["curso", "director", "coordinador", "comite", "docente", "programa"]
    return _find_with_context(text, core, must_in_window=must, forbid_left=forbid, window=90)

def _count_diplomaturas(text: str) -> int:
    # >200 hs: buscamos “diplomatura” + horas o certificado
    blocks = re.findall(r"(diplomatura[^\n]{0,120})", text, flags=re.I)
    c = 0
    for b in blocks:
        if re.search(r"(200|300|400)\s*h", b) or re.search(r"certificad", b):
            c += 1
    return c

def _count_segundo_grado(text: str) -> int:
    # Segundo título de grado: buscamos otra carrera de grado con “titulo/egreso” y Universidad
    # Heurística conservadora (0, 1 o 2 normalmente).
    pats = re.findall(r"(licenciatura|abogacia|abogac[ií]a|ingenier[ií]a|contador|medicina|arquitectura)", text)
    # evitamos contar menciones docentes o de cargos
    base = _find_with_context(
        text,
        r"(licenciatura|ingenier[ií]a|contador|medicina|arquitectura|abogac[ií]a|profesorado)\b",
        must_in_window=["titulo", "egres", "obtuvo", "universidad", "facultad", "diploma", "resol"],
        forbid_left=["docente", "catedra", "adjunto", "titular"],
        window=90,
    )
    return max(0, base - 1)  # descontamos el primero (requisito de ingreso)

def _count_cursos_posgrado(text: str) -> int:
    # contabiliza cursos >40 hs con evaluación
    blocks = re.findall(r"(curso[^\n]{0,120})", text)
    c = 0
    for b in blocks:
        if re.search(r"(posgrado|pos-grado|postgrado)", b) and \
           (re.search(r">?\s*40\s*h", b) or re.search(r"evalua", b)):
            c += 1
    return c

def _count_posdoc(text: str) -> int:
    return _find_with_context(text, r"\bposdoc|posdoctorad[oa]\b", must_in_window=["acredit", "universidad", "institut", "20", "19"], window=90)

def _count_idiomas(text: str) -> int:
    return _find_with_context(text, r"\b(b2|c1|c2|intermedio|avanzado|upper)\b", must_in_window=["certif", "idioma", "examen", "cambridge", "ielts", "toefl"], window=60)

def _count_estancias(text: str) -> int:
    return _find_with_context(text, r"\b(estancia|pasant[ií]a)\b", must_in_window=["i+d", "investigacion", "investigación", "laboratorio", "centro", "universidad"], window=90)

# --- Cargos (detectamos de manera conservadora) -----------------------
def _count_docencia_por_rango(text: str, rango: str) -> int:
    return _find_with_context(text, rf"\b{rango}\b", must_in_window=["docente", "catedra", "universidad", "cargo"], window=50)

def _count_docencia_titular(text: str) -> int:  return _count_docencia_por_rango(text, "titular")
def _count_docencia_asociado(text: str) -> int: return _count_docencia_por_rango(text, "asociad[oa]")
def _count_docencia_adjunto(text: str) -> int:  return _count_docencia_por_rango(text, "adjunt[oa]")
def _count_docencia_aux(text: str) -> int:      return _count_docencia_por_rango(text, "ayudante|jtp")

def _count_docencia_posgrado(text: str) -> int:
    return _find_with_context(text, r"\b(curso|seminario)\b", must_in_window=["posgrado", "maestr", "doctorado"], window=80)

def _count_gestion(text: str, palabra: str) -> int:
    return _find_with_context(text, rf"\b{palabra}\b", must_in_window=["universidad", "facultad", "instituto", "secretaria", "resol"], window=80)

# --- CyT (resumen, conservador) --------------------------------------
def _count_eval_revistas(text: str) -> int:
    return _find_with_context(text, r"\b(reviewer|evaluador|arbitro|arbitra|peer review)\b", must_in_window=["revista", "journal", "congreso"], window=80)

def _count_eval_proyectos(text: str) -> int:
    return _find_with_context(text, r"\bevaluac", must_in_window=["proyecto", "i+d", "agencia", "conicet", "fondo"], window=80)

def _count_eval_institucional(text: str) -> int:
    return _find_with_context(text, r"\bevaluac", must_in_window=["institucion", "institucional", "acreditac"], window=80)

# --- Producciones -----------------------------------------------------
def _count_articulos_con_referato(text: str) -> int:
    core = r"\b(articulo|article|paper)\b"
    must = ["referat", "arbitra", "indexad", "scopus", "wos", "isi", "jcr", "sci", "journal", "revista", "issn", "doi"]
    forbid = ["proyecto", "programa"]  # para evitar referencias indirectas
    return _find_with_context(text, core, must_in_window=must, forbid_left=forbid, window=120)

def _count_articulos_sin_referato(text: str) -> int:
    core = r"\b(articulo|article|paper)\b"
    must = ["revista", "journal", "public", "issn"]
    return _find_with_context(text, core, must_in_window=must, window=120) - _count_articulos_con_referato(text)

def _count_libros(text: str) -> int:
    # Preferimos ISBN; si no hay, buscamos “libro” + editorial
    by_isbn = _count_distinct_isbn(text)
    if by_isbn > 0:
        return by_isbn
    return _find_with_context(text, r"\blibro\b", must_in_window=["editorial", "isbn", "capitulo", "autor"], window=80)

def _count_capitulos(text: str) -> int:
    raw = _find_with_context(text, r"\bcap[ií]tulo\b", must_in_window=["libro", "isbn", "editorial"], window=100)
    # si contamos libros por ISBN, evitamos inflar con capítulos del mismo libro
    # (heurística simple: como mínimo no superamos libros*10)
    return raw

def _count_documentos_tecnicos(text: str) -> int:
    return _find_with_context(text, r"\b(informe|documento|reporte|manual|gu[ií]a)\b", must_in_window=["tecnic", "tecnico", "tecnica", "institucional", "difusion"], window=100)

# --- Redes / Premios / Otros -----------------------------------------
def _count_redes(text: str) -> int:
    return _find_with_context(text, r"\bred(es)?\b", must_in_window=["academ", "cient", "profesional", "miembro", "particip"], window=80)

def _count_eventos(text: str) -> int:
    return _find_with_context(text, r"\b(organizador|comite|comite cientifico|coordinador)\b", must_in_window=["congreso", "jornada", "seminario"], window=80)

def _count_editorial(text: str) -> int:
    return _find_with_context(text, r"\b(editor|comite editorial)\b", must_in_window=["revista", "journal"], window=80)

def _count_premios_int(text: str) -> int:
    return _find_with_context(text, r"\bpremio\b", must_in_window=["internacional", "international"], window=80)

def _count_premios_nac(text: str) -> int:
    # restringimos para no contar cada mención de un programa
    return _find_with_context(text, r"\bpremio\b", must_in_window=["nacional", "argentina", "mendoza", "ministerio", "secretaria"], window=80)

def _count_premios_otros(text: str) -> int:
    return _find_with_context(text, r"\bdistinci[oó]n|menci[oó]n\b", must_in_window=["premio", "reconoc"], window=80)

# ---------------------------------------------------------------------
# Mapa de
