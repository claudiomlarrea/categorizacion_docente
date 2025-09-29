# parsers.py
import io, re, unicodedata
from typing import Dict, Tuple, List, Set

# --- Excepción para soporte PDF opcional ---
class PDFSupportMissing(Exception):
    pass

# --- Normalización básica ---
def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def _normalize(s: str) -> str:
    s = _strip_accents(s).lower()
    s = s.replace('\r', '\n')
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n+', '\n', s)
    return s

def _find_section(text_norm: str, start_key: str, stop_keys: List[str]) -> str:
    """Devuelve el bloque desde start_key hasta el próximo encabezado (stop_keys) o fin."""
    i = text_norm.find(start_key)
    if i < 0:
        return ""
    j_candidates = [text_norm.find(k, i + len(start_key)) for k in stop_keys]
    j_candidates = [j for j in j_candidates if j != -1]
    j = min(j_candidates) if j_candidates else len(text_norm)
    return text_norm[i:j]

def _unique_titles(matches: List[str]) -> Set[str]:
    cleaned = []
    for m in matches:
        m = re.sub(r'\s+', ' ', m).strip()
        # acorta títulos larguísimos
        cleaned.append(m[:120])
    return set(cleaned)

# --- Extracción de texto ---
def extract_text(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        try:
            import pdfplumber  # lazy import
        except Exception:
            raise PDFSupportMissing("pdfplumber no está instalado")
        text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for p in pdf.pages:
                txt = p.extract_text() or ""
                text.append(txt)
        return "\n".join(text)

    elif name.endswith(".docx"):
        # 1) rápido
        try:
            import docx2txt
            return docx2txt.process(io.BytesIO(file_bytes)) or ""
        except Exception:
            pass
        # 2) fallback
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        # .txt u otros
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore")

# --- Reglas de conteo ---
def detect_counts(raw_text: str) -> Dict[str, int]:
    t = _normalize(raw_text)

    # Delimitadores de secciones frecuentes en CVar / CVs
    sec_acad = "formacion academica"
    sec_comp = "formacion complementaria"
    stop = [
        "formacion complementaria", "actividades", "antecedentes", "publicaciones",
        "libros", "experiencia", "cargos", "docencia", "ciencia y tecnologia",
        "otros antecedentes", "premios", "participacion", "membresias", "resumen"
    ]

    bloque_acad = _find_section(t, sec_acad, stop) or t  # si no encuentra, usamos todo
    bloque_comp = _find_section(t, sec_comp, stop)

    # Filtros de falsos positivos
    NEG_AROUND_DEGREE = r"(jurad|direccion|dir\.|dirig|codirig|comision|comite|evaluac|tesis|tesista)"
    NEG_COURSE_TOKENS = r"(curso|taller|seminar|diplomatura|otro:|horas|hs|de 0 hasta|entre \d+ y \d+ horas)"

    # --- Doctorados (solo en Formación Académica) ---
    doc_titles = re.findall(
        rf"(?:doctor(?:ado)?\s+en\s+([a-z0-9 áéíóú\-]+))", bloque_acad, flags=re.I)
    # limpia frases cortando en fin de línea o punto
    doc_titles = [re.split(r"[.,;\n]", x)[0] for x in doc_titles]
    # descarta falsos positivos por seguridad
    safe_docs = [d for d in doc_titles if not re.search(NEG_AROUND_DEGREE, d)]
    n_doctorado = len(_unique_titles(safe_docs))

    # --- Maestrías/Magíster (solo en Formación Académica) ---
    m_titles = re.findall(
        rf"(?:maestr[ií]a|magister)\s+en\s+([a-z0-9 áéíóú\-]+)", bloque_acad, flags=re.I)
    m_titles = [re.split(r"[.,;\n]", x)[0] for x in m_titles]
    m_titles = [m for m in m_titles if not re.search(NEG_COURSE_TOKENS, m)]
    n_maestria = len(_unique_titles(m_titles))

    # --- Especializaciones (solo en Formación Académica) ---
    e_titles = re.findall(
        rf"(?:especialista?|especializacion)\s+en\s+([a-z0-9 áéíóú\-]+)", bloque_acad, flags=re.I)
    e_titles = [re.split(r"[.,;\n]", x)[0] for x in e_titles]
    e_titles = [e for e in e_titles if not re.search(NEG_COURSE_TOKENS, e)]
    n_espec = len(_unique_titles(e_titles))

    # --- Segundo título de grado (si hay >=2 carreras de grado explícitas) ---
    # señales típicas: Licenciado/a en ..., Profesor en ..., Bioquímico, Ingeniero ...
    grado_matches = re.findall(
        r"(?:licenciad[oa]\s+en\s+[a-z0-9 áéíóú\-]+|profesor\s+en\s+[a-z0-9 áéíóú\-]+|ingenier[oa]\s+en\s+[a-z0-9 áéíóú\-]+)",
        bloque_acad, flags=re.I)
    n_seg_grado = 1 if len(_unique_titles(grado_matches)) >= 2 else 0

    # --- Cursos de posgrado (>40h) (van en Formación complementaria) ---
    cursos_pos = 0
    if bloque_comp:
        # Busca cursos en comp con indicios de carga horaria
        for line in bloque_comp.split("\n"):
            if re.search(r"(curso|taller|seminar|diplomatura|actualizacion)", line):
                if re.search(r"(?:\b>\s*40\s*hs\b|\b40\s*horas|\b51\s*y\s*100\s*horas|\b101\s*y\s*200\s*horas|\b201\s*y\s*359\s*horas)",
                             line):
                    cursos_pos += 1

    # --- Libros con ISBN (únicos) ---
    # busca ISBN10/13; evita confundir ISSN
    isbn_set = set(re.findall(r"\b97[89][- ]?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?\d\b|\b\d{9}[0-9xX]\b", t))
    # limpia posibles capturas de ISSN
    isbn_set = {i for i in isbn_set if "issn" not in t[max(0, t.find(i)-10): t.find(i)+10]}
    n_libros = len(isbn_set)

    # --- Artículos con referato (muy conservador) ---
    # Busca “artículo/article/paper” + pista de revista (journal/revista/ISSN/JCR/Scopus/WoS)
    art_refs = re.findall(
        r"(?:art[ií]culo|article|paper).{0,120}?(?:revista|journal|issn|jcr|scopus|wos|indexed)",
        t, flags=re.I | re.S)
    n_art_ref = len(art_refs)

    # --- Capítulos (capítulo de libro cerca de ISBN o editorial) ---
    cap_refs = re.findall(
        r"cap[ií]tulo.{0,80}?(?:isbn|editorial|en:)", t, flags=re.I | re.S)
    n_capitulos = len(cap_refs)

    # --- Documentos/Informes técnicos ---
    doc_tecnicos = re.findall(r"(?:informe|documento)s?\s+t[eé]cnic", t, flags=re.I)
    n_doc_tecnicos = len(doc_tecnicos)

    # --- Premios/Distinciones (nacionales/internacionales) ---
    premios = re.findall(r"(?:premio|distinci[oó]n|accesit|menci[oó]n)", t, flags=re.I)
    n_premios = len(premios)

    # --- Redes/Membresías ---
    redes = re.findall(r"(?:red|membres[ií]a|membership|agency|agencia)\b", t, flags=re.I)
    n_redes = len(redes)

    # --- Resultado con claves esperadas por la app ---
    return {
        # Formación
        "formacion:doctorado": n_doctorado,
        "formacion:maestria": n_maestria,
        "formacion:especializacion": n_espec,
        "formacion:diplomatura": 1 if re.search(r"diplomatura", t) else 0,
        "formacion:segundo_grado": n_seg_grado,
        "formacion:cursos_posgrado": cursos_pos,

        # Cargos y CyT (estos son ejemplos mínimos; tu scoring topa luego)
        "gestion:rector": len(re.findall(r"\brector", t)),
        "gestion:decano": len(re.findall(r"\bdecano", t)),
        "eval:institucional": len(re.findall(r"evaluaci[oó]n institucional", t)),

        # Producciones
        "pubs:con_referato": n_art_ref,
        "pubs:sin_referato": 0,  # si querés diferenciar, agregamos otra heurística
        "pubs:libros": n_libros,
        "pubs:capitulos": n_capitulos,
        "pubs:documentos": n_doc_tecnicos,

        # Redes / premios (como “otros”)
        "redes:membresias": n_redes,
        "premios:total": n_premios,
    }

# --- API “extract_text” + “detect_counts” ya es lo que usa streamlit_app.py ---
