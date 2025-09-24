import re
from typing import Dict, Tuple

try:
    from docx import Document  # python-docx
except Exception:
    Document = None

try:
    import docx2txt  # fallback
except Exception:
    docx2txt = None

import pdfplumber
import zipfile

def extract_text_from_docx(path: str) -> str:
    if Document is not None:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    if docx2txt is not None:
        return docx2txt.process(path) or ""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        return text
    except Exception:
        return ""

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
    # busca el primer grupo que contenga dígitos
    for g in (m.groups() or (m.group(0),)):
        if g and re.search(r"\d+", g):
            try:
                return int(re.search(r"\d+", g).group())
            except Exception:
                pass
    return default

def detect_counts(text: str) -> Dict[str, int]:
    c: Dict[str, int] = {}
    # Formación
    c["formacion:doctorado"] = 1 if re.search(r"\bdoctorado\b", text, re.I) else 0
    c["formacion:maestria"] = len(re.findall(r"maestr[ií]a", text, re.I))
    c["formacion:especializacion"] = len(re.findall(r"especializaci[oó]n", text, re.I))
    c["formacion:diplomatura"] = len(re.findall(r"\bdiplomatura\b", text, re.I))
    c["formacion:segundo_grado"] = 1 if re.search(r"segundo t[ií]tulo de grado|doble t[ií]tulo de grado", text, re.I) else 0
    c["formacion:cursos_posgrado"] = find_int(text, r"cursos? de posgrado:\s*(\d+)", 0)
    c["formacion:posdoc"] = len(re.findall(r"posdoc|posdoctorad", text, re.I))
    c["formacion:idiomas"] = len(re.findall(r"idioma[s]?|ingl[eé]s certificado|TOEFL|IELTS", text, re.I))
    c["formacion:estancias"] = find_int(text, r"pasant[ií]as?\s*\((\d+)\)", 0) or len(re.findall(r"\bestancia|\bpasant[ií]a", text, re.I))

    # Docencia (años)
    c["docencia:titular"] = find_int(text, r"titular.*?\((\d+)\s*a[nñ]os?\)", 0)
    c["docencia:asociado"] = find_int(text, r"asociad[oa].*?\((\d+)\s*a[nñ]os?\)", 0)
    c["docencia:adjunto"] = find_int(text, r"adjunt[oa].*?\((\d+)\s*a[nñ]os?\)", 0)
    c["docencia:jtp"] = find_int(text, r"(?:trabajos pr[aá]cticos|ayudant[eé]).*?\((\d+)\s*a[nñ]os?\)", 0)
    c["docencia:posgrado"] = find_int(text, r"posgrado acreditados? \((\d+)\s*cursos?\)", 0)

    # Gestión
    c["gestion:rector"] = 1 if re.search(r"\brector[ao]\b", text, re.I) else 0
    c["gestion:vicerrector"] = 1 if re.search(r"vicerrector[ao]|directorio", text, re.I) else 0
    c["gestion:decano"] = 1 if re.search(r"\bdecano\b|director[ae] de facultad|director instituto", text, re.I) else 0
    c["gestion:secretario"] = 1 if re.search(r"secretari[oa] (acad[eé]mica|de investigaci[oó]n|de extensi[oó]n)", text, re.I) else 0
    c["gestion:coordinador"] = 1 if re.search(r"coordinador[ae] de carrera|responsable de programas", text, re.I) else 0
    c["gestion:consejero"] = 1 if re.search(r"consejer[oa] (superior|directivo|de facultad)", text, re.I) else 0

    # Otros cargos
    c["otroscargos:funciones"] = find_int(text, r"comisiones internas \((\d+)\s*funciones\)", 0) or len(re.findall(r"comisi[oó]n interna", text, re.I))

    # CyT formación RRHH
    c["ciencia:dir_doctorandos"] = find_int(text, r"direcci[oó]n de (\d+) doctorandos?", 0)
    c["ciencia:dir_maestria"] = find_int(text, r"direcci[oó]n de (\d+) maestrandos?", 0)
    c["ciencia:dir_grado"] = find_int(text, r"direcci[oó]n de (\d+) tesistas de grado", 0)
    c["ciencia:becarios"] = find_int(text, r"(\d+)\s*becarios? (conicet|agencia)", 0)

    # Proyectos I+D
    c["proyectos:direccion"] = find_int(text, r"direcci[oó]n de (\d+) proyectos", 0)
    c["proyectos:codireccion"] = find_int(text, r"co-?direcci[oó]n de (\d+) proyectos", 0)
    c["proyectos:participacion"] = find_int(text, r"participaci[oó]n en (\d+) proyectos", 0)
    c["proyectos:coordinacion"] = find_int(text, r"coordinaci[oó]n de (\d+) equipo", 0)

    # Extensión
    c["extension:tutorias"] = find_int(text, r"tutor[ií]as? de (\d+) pasant[ií]as?", 0)
    c["extension:transferencia"] = find_int(text, r"(\d+)\s*(actividades?|acciones?) de transferencia", 0)
    c["extension:eventos_cientificos"] = find_int(text, r"(\d+)\s*(conferencias?|panel(es)?|exposiciones?)", 0)

    # Evaluación
    c["eval:tribunal_grado"] = find_int(text, r"jurado de (\d+) tesis de grado", 0)
    c["eval:tribunal_posgrado"] = find_int(text, r"jurado de (\d+) tesis de posgrado", 0)
    c["eval:eval_proyectos"] = find_int(text, r"evaluadora? de (\d+) proyectos? I\+D", 0)
    c["eval:eval_revistas"] = find_int(text, r"revistas? cient[ií]ficas.*?(\d+)", 0)
    c["eval:eval_institucional"] = find_int(text, r"evaluadora? institucional.*?(\d+)", 0)

    # Otras actividades
    c["otras:comites_redes"] = find_int(text, r"participaci[oó]n en (\d+) redes", 0) or len(re.findall(r"red(es)? acad[eé]mica", text, re.I))
    c["otras:ejercicio_prof"] = find_int(text, r"extraacad[eé]mico.*?(\d+) a[nñ]os?", 0)

    # Publicaciones
    c["pubs:con_referato"] = find_int(text, r"(\d+) art[íi]culos? con referato|indexad", 0)
    c["pubs:sin_referato"] = find_int(text, r"(\d+) art[íi]culos? sin referato", 0)
    c["pubs:libros"] = find_int(text, r"(\d+) libros? con ISBN", 0) or len(re.findall(r"libro[s]? con ISBN", text, re.I))
    c["pubs:capitulos"] = find_int(text, r"(\d+) cap[ií]tulos? de libro", 0)
    c["pubs:documentos"] = find_int(text, r"(\d+) documentos? t[eé]cnicos?", 0)

    # Desarrollos
    c["desarrollos:software_patente"] = find_int(text, r"(\d+) softwares? registrados?|patentes?", 0)
    c["desarrollos:procesos"] = find_int(text, r"(\d+) procesos? de gesti[oó]n", 0)

    # Servicios
    c["servicios:tecnicos"] = find_int(text, r"(\d+) servicios? t[eé]cnicos?", 0)
    c["servicios:informes"] = find_int(text, r"(\d+) informes? t[eé]cnicos?", 0)

    # Redes / Editorial / Eventos
    c["redes:participacion"] = find_int(text, r"miembro de (\d+) redes?", 0)
    c["redes:organizacion_eventos"] = find_int(text, r"organizaci[oó]n de (\d+) congresos?", 0)
    ge = 0
    ge += find_int(text, r"editora? asociad[oa] en (\d+) revistas?", 0)
    ge += find_int(text, r"comit[eé] editorial de (\d+) revistas?", 0)
    c["redes:gestion_editorial"] = ge

    # Premios
    c["premios:internacional"] = find_int(text, r"(\d+) premio[s]? internacional(es)?", 0)
    c["premios:nacional"] = find_int(text, r"(\d+) premios? nacionales?", 0)
    c["premios:distinciones"] = find_int(text, r"(\d+) distinciones?", 0)

    return c
