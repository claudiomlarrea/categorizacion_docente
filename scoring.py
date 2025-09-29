from dataclasses import dataclass
from typing import Dict

# ---------------------------------------------------------------------
# Modelo de regla
# ---------------------------------------------------------------------
@dataclass
class Rule:
    label: str
    points_per_unit: float
    max_points: float

# ---------------------------------------------------------------------
# Reglas por ítem (clave = "<seccion>:<item>")
# Ajustá puntos/tope si tu valorador oficial usa otros números.
# ---------------------------------------------------------------------
RULES: Dict[str, Rule] = {
    # ---------------- FORMACION ----------------
    "formacion:doctorado":       Rule("Doctorado acreditado",                     400, 400),
    "formacion:maestria":        Rule("Maestría acreditada",                      60, 120),
    "formacion:especializacion": Rule("Especialización",                          30,  60),
    "formacion:diplomatura":     Rule("Diplomatura >200 hs",                      50, 100),
    "formacion:segundo_grado":   Rule("Segundo título de grado",                  30,  30),
    "formacion:cursos_posgrado": Rule("Cursos de posgrado (>40 hs con evaluación)", 5, 75),
    "formacion:posdoc":          Rule("Posdoctorado acreditado",                 100, 100),
    "formacion:idiomas":         Rule("Idiomas certificados (intermedio/avanzado)",10,  50),
    "formacion:estancias":       Rule("Estancias y pasantías en I+D",             20,  60),

    # ---------------- DOCENCIA / CARGOS ----------------
    "docencia:titular":          Rule("Docencia universitaria - Titular (por año)",30, 150),
    "docencia:asociado":         Rule("Docencia universitaria - Asociado (por año)",20, 120),
    "docencia:adjunto":          Rule("Docencia universitaria - Adjunto (por año)",15,  90),
    "docencia:jtp":              Rule("Docencia universitaria - JTP/Ayudante (por año)",10, 60),
    "docencia:posgrado":         Rule("Docencia de posgrado (cursos/año)",         15,  90),

    "gestion:rector":            Rule("Rector/a o Rectorado",                     80,  80),
    "gestion:vicerrector":       Rule("Vicerrector/a / Directorio",               60,  60),
    "gestion:decano":            Rule("Decano/a / Dirección de Facultad",         50,  50),
    "gestion:secretario":        Rule("Secretarías (Acad./Inv./Extensión)",       40,  80),
    "gestion:coordinador":       Rule("Coordinación de carrera/programas",        20,  60),
    "gestion:consejero":         Rule("Consejos (superior/directivo)",            10,  40),

    "otroscargos:funciones":     Rule("Comisiones internas / funciones",           5,  30),

    # ---------------- CyT / RRHH / PROYECTOS / EXTENSIÓN / EVALUACIÓN / OTRAS ----------------
    "ciencia:dir_doctorandos":   Rule("Dirección de doctorandos",                 40, 120),
    "ciencia:dir_maestria":      Rule("Dirección de maestrandos",                 20,  80),
    "ciencia:dir_grado":         Rule("Dirección de tesis de grado",               8,  40),
    "ciencia:becarios":          Rule("Dirección de becarios (CONICET/Agencia)",  10,  50),

    "proyectos:direccion":       Rule("Dirección de proyectos",                   20,  80),
    "proyectos:codireccion":     Rule("Codirección de proyectos",                 10,  40),
    "proyectos:participacion":   Rule("Participación en proyectos",                5,  35),
    "proyectos:coordinacion":    Rule("Coordinación/equipos",                      6,  30),

    "extension:tutorias":        Rule("Tutorías/Pasantías (Extensión)",            4,  24),
    "extension:transferencia":   Rule("Actividades de transferencia",              6,  36),
    "extension:eventos_cientificos": Rule("Conferencias/charlas/paneles",         3,  30),

    "eval:tribunal_grado":       Rule("Jurado de tesis de grado",                  4,  20),
    "eval:tribunal_posgrado":    Rule("Jurado de tesis de posgrado",               6,  30),
    "eval:eval_revistas":        Rule("Evaluación de revistas/congresos",          3,  30),
    "eval:eval_proyectos":       Rule("Evaluación de proyectos I+D",               4,  24),
    "eval:eval_institucional":   Rule("Evaluación institucional",                  5,  25),

    "otras:comites_redes":       Rule("Comités / Redes académicas",                4,  24),
    "otras:ejercicio_prof":      Rule("Ejercicio profesional extraacadémico (años)",5, 25),

    # ---------------- PRODUCCIONES (Publicaciones) ----------------
    "pubs:con_referato":         Rule("Artículos con referato/indexados",         20, 200),
    "pubs:sin_referato":         Rule("Artículos sin referato/divulgación",        5,  50),
    "pubs:libros":               Rule("Libros con ISBN",                          30,  90),
    "pubs:capitulos":            Rule("Capítulos de libro",                       15,  60),
    "pubs:documentos":           Rule("Documentos/Informes técnicos",             10,  40),

    # ---------------- DESARROLLOS / SERVICIOS ----------------
    "desarrollos:software_patente": Rule("Software registrado / Patente",         25, 100),
    "desarrollos:procesos":      Rule("Procesos de gestión/tecnológicos",         10,  40),

    "servicios:tecnicos":        Rule("Servicios técnicos",                         6,  36),
    "servicios:informes":        Rule("Informes técnicos",                          5,  30),

    # ---------------- REDES / PREMIOS ----------------
    "redes:participacion":       Rule("Membresías/participación en redes",          4,  24),
    "redes:organizacion_eventos":Rule("Organización de eventos científicos",        6,  36),
    "redes:gestion_editorial":   Rule("Gestión editorial / editor/a",               8,  40),

    "premios:internacional":     Rule("Premios/Distinciones internacionales",      15,  60),
    "premios:nacional":          Rule("Premios/Distinciones nacionales",            8,  40),
    "premios:distinciones":      Rule("Otras distinciones/menciones",               5,  25),
}

# ---------------------------------------------------------------------
# Límites por sección (aplican ANTES de armar los bloques 2..6)
# Ajustalos si tu reglamento usa otros topes.
# ---------------------------------------------------------------------
SECTION_LIMITS: Dict[str, float] = {
    "formacion":     400,
    "docencia":      160,
    "gestion":       160,
    "otroscargos":    40,

    "ciencia":       120,
    "proyectos":     120,
    "extension":      60,
    "eval":           60,
    "otras":          60,

    "pubs":          200,  # <-- importante: que no sea 0
    "desarrollos":    80,
    "servicios":      80,

    "redes":          60,
    "premios":        60,
}

# ---------------------------------------------------------------------
# Bloques del reporte (2..6) -> qué secciones suma cada uno
# ---------------------------------------------------------------------
SECTION_GROUPS = {
    "2:Formacion_total":   ["formacion"],
    "3:Cargos_total":      ["docencia", "gestion", "otroscargos"],
    "4:CyT_total":         ["ciencia", "proyectos", "extension", "eval", "otras"],
    "5:Producciones_total":["pubs", "desarrollos", "servicios"],   # <-- aquí entra PUBS
    "6:Otros_total":       ["redes", "premios"],
}

# ---------------------------------------------------------------------
# Suma con topes por sección y por bloque
# ---------------------------------------------------------------------
def sum_with_section_caps(section_totals: Dict[str, float]) -> Dict[str, float]:
    # Aseguro topes por sección
    capped = {}
    for sec, val in section_totals.items():
        lim = SECTION_LIMITS.get(sec, float("inf"))
        capped[sec] = min(val, lim)

    # Armo subtotales por bloque 2..6
    out = {}
    for block, secs in SECTION_GROUPS.items():
        out[block] = sum(capped.get(s, 0.0) for s in secs)

    # Total general
    out["TOTAL_GENERAL"] = sum(out.get(k, 0.0) for k in [
        "2:Formacion_total", "3:Cargos_total", "4:CyT_total",
        "5:Producciones_total", "6:Otros_total"
    ])
    return out
