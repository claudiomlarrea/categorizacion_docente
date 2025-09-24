import re
from typing import Dict, Tuple
from docx import Document
import pdfplumber

def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    texts = []
    for p in doc.paragraphs:
        texts.append(p.text)
    return "\n".join(texts)

def extract_text_from_pdf(path: str) -> str:
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
    return "\n".join(texts)

def extract_text(file_path: str) -> Tuple[str, str]:
    lower = file_path.lower()
    if lower.endswith(".docx"):
        return extract_text_from_docx(file_path), "docx"
    elif lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path), "pdf"
    elif lower.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(), "txt"
    else:
        raise ValueError("Formato no soportado. Use .docx, .pdf o .txt")

def find_int(text: str, pattern: str, default: int = 0) -> int:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return default
    try:
        return int(m.group(1))
    except:
        return default

def count_matches(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))

def detect_counts(text: str) -> Dict[str, int]:
    # Heurísticas por regex para el CV de ejemplo y textos similares
    counts = {}
    # Formación
    counts["formacion:doctorado"] = max(1 if re.search(r"doctorado", text, re.I) else 0, 0)
    counts["formacion:maestria"] = len(re.findall(r"maestr[ií]a", text, re.I))
    counts["formacion:especializacion"] = len(re.findall(r"especializaci[oó]n", text, re.I))
    counts["formacion:diplomatura"] = len(re.findall(r"diplomatura", text, re.I))
    counts["formacion:segundo_grado"] = 1 if re.search(r"segundo t[ií]tulo de grado|doble t[ií]tulo de grado", text, re.I) else 0
    counts["formacion:cursos_posgrado"] = find_int(text, r"cursos? de posgrado:\s*(\d+)", 0)
    counts["formacion:posdoc"] = len(re.findall(r"posdoc|posdoctorad", text, re.I))
    counts["formacion:idiomas"] = len(re.findall(r"idioma[s]?|ingl[eé]s certificado|TOEFL|IELTS", text, re.I))
    counts["formacion:estancias"] = find_int(text, r"pasant[ií]as?\s*\((\d+)\)", 0) or len(re.findall(r"estancia|pasant[ií]a", text, re.I))

    # Docencia (años)
    counts["docencia:titular"] = find_int(text, r"titular.*?\((\d+)\s*a[nñ]os?\)", 0)
    counts["docencia:asociado"] = find_int(text, r"asociad[oa].*?\((\d+)\s*a[nñ]os?\)", 0)
    counts["docencia:adjunto"] = find_int(text, r"adjunt[oa].*?\((\d+)\s*a[nñ]os?\)", 0)
    counts["docencia:jtp"] = find_int(text, r"trabajos pr[aá]cticos.*?\((\d+)\s*a[nñ]os?\)|ayudant[eé].*?\((\d+)\s*a[nñ]os?\)", 0)
    counts["docencia:posgrado"] = find_int(text, r"posgrado acreditados? \((\d+)\s*cursos?\)", 0)

    # Gestión (presencia)
    counts["gestion:rector"] = 1 if re.search(r"rector[ao]", text, re.I) else 0
    counts["gestion:vicerrector"] = 1 if re.search(r"vicerrector[ao]|directorio", text, re.I) else 0
    counts["gestion:decano"] = 1 if re.search(r"decano|director[ae] de facultad|director instituto", text, re.I) else 0
    counts["gestion:secretario"] = 1 if re.search(r"secretari[oa] (acad[eé]mica|de investigaci[oó]n|de extensi[oó]n)", text, re.I) else 0
    counts["gestion:coordinador"] = 1 if re.search(r"coordinador[ae] de carrera|responsable de programas", text, re.I) else 0
    counts["gestion:consejero"] = 1 if re.search(r"consejer[oa] (superior|directivo|de facultad)", text, re.I) else 0

    # Otros cargos
    counts["otroscargos:funciones"] = find_int(text, r"comisiones internas \((\d+)\s*funciones\)", 0) or len(re.findall(r"comisi[oó]n interna", text, re.I))

    # CyT formación RRHH
    counts["ciencia:dir_doctorandos"] = find_int(text, r"direcci[oó]n de (\d+) doctorandos?", 0)
    counts["ciencia:dir_maestria"] = find_int(text, r"direcci[oó]n de (\d+) maestrandos?", 0)
    counts["ciencia:dir_grado"] = find_int(text, r"direcci[oó]n de (\d+) tesistas de grado", 0)
    counts["ciencia:becarios"] = find_int(text, r"(\d+)\s*becarios? (conicet|agencia)", 0)

    # Proyectos I+D
    counts["proyectos:direccion"] = find_int(text, r"direcci[oó]n de (\d+) proyectos", 0)
    counts["proyectos:codireccion"] = find_int(text, r"co-?direcci[oó]n de (\d+) proyectos", 0)
    counts["proyectos:participacion"] = find_int(text, r"participaci[oó]n en (\d+) proyectos", 0)
    counts["proyectos:coordinacion"] = find_int(text, r"coordinaci[oó]n de (\d+) equipo", 0)

    # Extensión
    counts["extension:tutorias"] = find_int(text, r"tutor[ií]as? de (\d+) pasant[ií]as?", 0)
    counts["extension:transferencia"] = find_int(text, r"(\d+)\s*actividades? de transferencia|(\d+)\s*acciones? de transferencia", 0)
    counts["extension:eventos_cientificos"] = find_int(text, r"(\d+)\s*conferencias?|panelista.*?(\d+)", 0)

    # Evaluación
    counts["eval:tribunal_grado"] = find_int(text, r"jurado de (\d+) tesis de grado", 0)
    counts["eval:tribunal_posgrado"] = find_int(text, r"jurado de (\d+) tesis de posgrado", 0)
    counts["eval:eval_proyectos"] = find_int(text, r"evaluadora? de (\d+) proyectos? I\+D", 0)
    counts["eval:eval_revistas"] = find_int(text, r"revistas? cient[ií]ficas.*?(\d+)", 0)
    counts["eval:eval_institucional"] = find_int(text, r"evaluadora? institucional.*?(\d+)", 0)

    # Otras actividades
    counts["otras:comites_redes"] = find_int(text, r"participaci[oó]n en (\d+) redes", 0) or len(re.findall(r"red(es)? acad[eé]mica", text, re.I))
    counts["otras:ejercicio_prof"] = find_int(text, r"extraacad[eé]mico\s*\((\d+) a[nñ]os?\)", 0) or find_int(text, r"extraacad[eé]mico.*?(\d+) a[nñ]os?", 0)

    # Publicaciones
    counts["pubs:con_referato"] = find_int(text, r"(\d+) art[íi]culos? con referato|indexad", 0)
    counts["pubs:sin_referato"] = find_int(text, r"(\d+) art[íi]culos? sin referato", 0)
    counts["pubs:libros"] = find_int(text, r"(\d+) libros? con ISBN", 0) or len(re.findall(r"libro[s]? con ISBN", text, re.I))
    counts["pubs:capitulos"] = find_int(text, r"(\d+) cap[ií]tulos? de libro", 0)
    counts["pubs:documentos"] = find_int(text, r"(\d+) documentos? t[eé]cnicos?", 0)

    # Desarrollos
    counts["desarrollos:software_patente"] = find_int(text, r"(\d+) softwares? registrados?|patentes?", 0)
    counts["desarrollos:procesos"] = find_int(text, r"(\d+) procesos? de gesti[oó]n", 0)

    # Servicios
    counts["servicios:tecnicos"] = find_int(text, r"(\d+) servicios? t[eé]cnicos?", 0)
    counts["servicios:informes"] = find_int(text, r"(\d+) informes? t[eé]cnicos?", 0)

    # Redes / Editorial / Eventos
    counts["redes:participacion"] = find_int(text, r"miembro de (\d+) redes?", 0)
    counts["redes:organizacion_eventos"] = find_int(text, r"organizaci[oó]n de (\d+) congresos?", 0)
    # Para gestión editorial usamos la suma de puestos (editora asociada + comité)
    ge = 0
    ge += find_int(text, r"editora? asociad[oa] en (\d+) revistas?", 0)
    ge += find_int(text, r"comit[eé] editorial de (\d+) revistas?", 0)
    counts["redes:gestion_editorial"] = ge

    # Premios
    counts["premios:internacional"] = find_int(text, r"(\d+) premio[s]? internacional(es)?", 0)
    counts["premios:nacional"] = find_int(text, r"(\d+) premios? nacionales?", 0)
    counts["premios:distinciones"] = find_int(text, r"(\d+) distinciones?", 0)

    return counts
