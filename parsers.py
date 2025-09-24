
import re, unicodedata, zipfile, io
from typing import Dict, Tuple

# --- Exceptions ---------------------------------------------------------------
class PDFSupportMissing(Exception):
    """Se lanza cuando se intenta leer PDF sin pdfplumber instalado."""
    pass

# --- Normalización ------------------------------------------------------------
def _normalize(s: str) -> str:
    # minúsculas, sin tildes, espacios/saltos normalizados
    s = s.replace("\xa0", " ")
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[ \t]+", " ", s.lower())
    s = re.sub(r"\r?\n\s*\r?\n+", "\n", s).strip()
    return s

# --- Lectores de archivo ------------------------------------------------------
def extract_text_from_docx(path: str) -> str:
    """Docx robusto: intenta docx2txt (mejor con tablas), luego python-docx (párrafos + tablas),
    y por último raw XML del .docx (por si faltaran dependencias)."""
    # 1) docx2txt
    try:
        import docx2txt
        txt = docx2txt.process(path)
        if txt and txt.strip():
            return txt
    except Exception:
        pass
    # 2) python-docx
    try:
        from docx import Document
        doc = Document(path)
        parts = []
        for p in doc.paragraphs:
            if p.text and p.text.strip():
                parts.append(p.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    t = (cell.text or "").strip()
                    if t:
                        parts.append(t)
        if parts:
            return "\n".join(parts)
    except Exception:
        pass
    # 3) Raw XML
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        return text
    except Exception:
        return ""

def extract_text_from_pdf(path: str) -> str:
    try:
        import pdfplumber  # lazy import; opcional
    except Exception as e:
        raise PDFSupportMissing("pdfplumber no esta instalado.") from e
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
    return "\n".join(texts)

def extract_text(file_path: str) -> Tuple[str, str]:
    """Devuelve (texto_normalizado, formato) para .docx/.pdf/.txt"""
    lower = (file_path or "").lower()
    if lower.endswith(".docx"):
        raw = extract_text_from_docx(file_path)
        return _normalize(raw), "docx"
    elif lower.endswith(".pdf"):
        raw = extract_text_from_pdf(file_path)
        return _normalize(raw), "pdf"
    elif lower.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return _normalize(f.read()), "txt"
    elif lower.endswith(".doc"):
        raise ValueError("Formato .DOC (Word 97-2003) no soportado. Convertir a .DOCX o PDF.")
    else:
        raise ValueError("Formato no soportado. Use .docx, .pdf o .txt")

# --- Detectores ---------------------------------------------------------------
def _count(rx: str, t: str) -> int:
    return len(re.findall(rx, t, flags=re.IGNORECASE))

def _has(rx: str, t: str) -> int:
    return 1 if re.search(rx, t, flags=re.IGNORECASE) else 0

def detect_counts(text: str) -> Dict[str, int]:
    t = _normalize(text)
    c: Dict[str, int] = {}

    # ---------- FORMACION ----------
    c["formacion:doctorado"] = _has(r"\bdoctorado\b", t)
    c["formacion:maestria"] = _count(r"\bmaestria\b", t)
    c["formacion:especializacion"] = _count(r"\bespecializacion\b", t)
    c["formacion:diplomatura"] = _count(r"\bdiplomatura\b", t)
    c["formacion:segundo_grado"] = _has(r"segundo titulo de grado|doble titulo de grado", t)
    m = re.search(r"(?:cursos? de posgrado|cursos? de postgrado|cursos? de especializacion).*?(\d+)", t)
    c["formacion:cursos_posgrado"] = int(m.group(1)) if m else 0
    c["formacion:posdoc"] = _count(r"\bposdoc(?:torado)?\b", t)
    c["formacion:idiomas"] = _count(r"\bidioma[s]?\b|ingles certificado|toefl|ielts|b2|c1|c2", t)
    m = re.search(r"(?:estancia|pasantia)[^0-9]{0,20}(\d+)", t)
    c["formacion:estancias"] = int(m.group(1)) if m else _count(r"\bestancia\b|\bpasantia\b", t)

    # ---------- DOCENCIA ----------
    def _get_years(rx):
        m = re.search(rx, t)
        return int(m.group(1)) if m else 0
    c["docencia:titular"] = _get_years(r"titular[^0-9]{0,20}(\d+)\s*a(?:n|ñ)os?")
    c["docencia:asociado"] = _get_years(r"asociad[oa][^0-9]{0,20}(\d+)\s*a(?:n|ñ)os?")
    c["docencia:adjunto"] = _get_years(r"adjunt[oa][^0-9]{0,20}(\d+)\s*a(?:n|ñ)os?")
    c["docencia:jtp"] = _get_years(r"(?:trabajos practicos|ayudante)[^0-9]{0,20}(\d+)\s*a(?:n|ñ)os?")
    c["docencia:posgrado"] = _get_years(r"posgrado[^0-9]{0,20}(\d+)\s*cursos?")

    # ---------- GESTION ----------
    c["gestion:rector"] = _has(r"\brector(?:a|ado)?\b", t)
    c["gestion:vicerrector"] = _has(r"\bvicerrector(?:a)?\b|directorio", t)
    c["gestion:decano"] = _has(r"\bdecano\b|director[ae] de facultad|director instituto", t)
    c["gestion:secretario"] = _has(r"secretari[oa] (academica|de investigacion|de extension)", t)
    c["gestion:coordinador"] = _has(r"coordinador[ae] de carrera|responsable de programas", t)
    c["gestion:consejero"] = _has(r"consejer[oa] (superior|directivo|de facultad)", t)

    # ---------- OTROS CARGOS ----------
    m = re.search(r"comisiones? internas?[^0-9]{0,20}(\d+)\s*funciones?", t)
    c["otroscargos:funciones"] = int(m.group(1)) if m else _count(r"comision interna", t)

    # ---------- FORMACION RRHH ----------
    def _num(rx):
        m = re.search(rx, t)
        return int(m.group(1)) if m else 0
    c["ciencia:dir_doctorandos"] = _num(r"direccion de (\d+) doctorand")
    c["ciencia:dir_maestria"] = _num(r"direccion de (\d+) maestrand")
    c["ciencia:dir_grado"] = _num(r"direccion de (\d+) tesis(?:tas)? de grado")
    c["ciencia:becarios"] = _num(r"(\d+)\s*becarios? (?:conicet|agencia)")

    # ---------- PROYECTOS ----------
    c["proyectos:direccion"] = _num(r"(?:direccion|dir\.) de (\d+) proyectos?")
    c["proyectos:codireccion"] = _num(r"co-?direccion de (\d+) proyectos?")
    c["proyectos:participacion"] = _num(r"participacion en (\d+) proyectos?")
    c["proyectos:coordinacion"] = _num(r"coordinacion de (\d+) equipo")

    # ---------- EXTENSION ----------
    c["extension:tutorias"] = _num(r"tutorias? de (\d+) pasant")
    c["extension:transferencia"] = _num(r"(\d+)\s*(?:actividades?|acciones?) de transferencia")
    c["extension:eventos_cientificos"] = _num(r"(\d+)\s*(?:conferencias?|panel(?:es)?|exposiciones?)")

    # ---------- EVALUACION ----------
    c["eval:tribunal_grado"] = _num(r"jurado de (\d+) tesis de grado")
    c["eval:tribunal_posgrado"] = _num(r"jurado de (\d+) tesis de posgrado")
    c["eval:eval_revistas"] = max(
        _num(r"evaluador(?:a)? de (\d+) (?:revistas?|congresos?|jornadas?)"),
        _count(r"\b(revisor|arbitro|reviewer)\b", t)
    )
    c["eval:eval_proyectos"] = max(
        _num(r"evaluador(?:a)? de (\d+) proyectos?\s*(?:i\+d|investigacion)?"),
        _count(r"\bevaluador(?:a)? de proyectos\b", t)
    )
    c["eval:eval_institucional"] = max(
        _num(r"evaluacion institucional.*?(\d+)"),
        _count(r"\bevaluacion institucional\b", t)
    )

    # ---------- OTRAS ACTIVIDADES ----------
    c["otras:comites_redes"] = max(
        _num(r"participacion en (\d+) redes"),
        _count(r"red(?:es)? academicas?|comite(s)?", t)
    )
    c["otras:ejercicio_prof"] = _num(r"extraacademico.*?(\d+)\s*a(?:n|ñ)os?")

    # ---------- PUBLICACIONES ----------
    c["pubs:con_referato"] = max(
        _num(r"(\d+) articulos? con referato"),
        _count(r"articulos? (?:indexad|con referato)", t)
    )
    c["pubs:sin_referato"] = _num(r"(\d+) articulos? sin referato")
    c["pubs:libros"] = max(
        _num(r"(\d+) libros? con isbn"),
        _count(r"\blibro[s]? con isbn\b", t)
    )
    c["pubs:capitulos"] = _num(r"(\d+) capitulos? de libro")
    c["pubs:documentos"] = _num(r"(\d+) documentos? tecnicos?")

    # ---------- DESARROLLOS ----------
    c["desarrollos:software_patente"] = max(
        _num(r"(\d+) softwares? registrados?"),
        _num(r"(\d+) patentes?")
    )
    c["desarrollos:procesos"] = _num(r"(\d+) procesos? de gestion")

    # ---------- SERVICIOS ----------
    c["servicios:tecnicos"] = _num(r"(\d+) servicios? tecnicos?")
    c["servicios:informes"] = _num(r"(\d+) informes? tecnicos?")

    # ---------- REDES / EDITORIAL / EVENTOS ----------
    c["redes:participacion"] = max(
        _num(r"miembro de (\d+) redes?"),
        _count(r"\b(membresia|miembro|socio|asociado|integrante)\b", t)
    )
    c["redes:organizacion_eventos"] = max(
        _num(r"organizacion de (\d+) (?:congresos?|jornadas?|seminarios?)"),
        _count(r"(comite (?:organizador|cientifico)|coordinacion) de (?:congreso|jornada|seminario|evento)", t)
    )
    c["redes:gestion_editorial"] = max(
        _num(r"comite editorial de (\d+) revistas?"),
        _count(r"\b(editor(?:a)?(?: asociado[a]?| en jefe)?|comite editorial)\b", t)
    )

    # ---------- PREMIOS ----------
    total_premios = _count(r"\bpremio[s]?\b|\bdistincion(?:es)?\b|\bmencion(?:es)?\b|\breconocimiento[s]?\b", t)
    premios_int = _count(r"\binternac", t)
    premios_nac = _count(r"\bnacional", t)
    c["premios:internacional"] = premios_int
    c["premios:nacional"] = max(premios_nac - premios_int, 0)
    resto = max(total_premios - c["premios:internacional"] - c["premios:nacional"], 0)
    c["premios:distinciones"] = resto

    return c
