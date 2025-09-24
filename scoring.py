
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ItemRule:
    key: str
    label: str
    points_per_unit: float
    max_points: float

RULES = {
    "formacion:doctorado": ItemRule("formacion:doctorado", "Doctorado acreditado", 250, 375),
    "formacion:maestria": ItemRule("formacion:maestria", "Maestría acreditada", 150, 225),
    "formacion:especializacion": ItemRule("formacion:especializacion", "Especialización", 70, 105),
    "formacion:diplomatura": ItemRule("formacion:diplomatura", "Diplomatura >200 hs", 50, 100),
    "formacion:segundo_grado": ItemRule("formacion:segundo_grado", "Segundo título de grado", 30, 30),
    "formacion:cursos_posgrado": ItemRule("formacion:cursos_posgrado", "Cursos de posgrado (>40 hs con evaluación)", 5, 75),
    "formacion:posdoc": ItemRule("formacion:posdoc", "Posdoctorado acreditado", 100, 100),
    "formacion:idiomas": ItemRule("formacion:idiomas", "Idiomas certificados (intermedio/avanzado)", 10, 50),
    "formacion:estancias": ItemRule("formacion:estancias", "Estancias y pasantías en I+D", 20, 60),

    "docencia:titular": ItemRule("docencia:titular", "Docencia universitaria - Titular (por año)", 30, 150),
    "docencia:asociado": ItemRule("docencia:asociado", "Docencia universitaria - Asociado (por año)", 25, 125),
    "docencia:adjunto": ItemRule("docencia:adjunto", "Docencia universitaria - Adjunto (por año)", 20, 100),
    "docencia:jtp": ItemRule("docencia:jtp", "JTP o Ayudante (por año)", 10, 50),
    "docencia:posgrado": ItemRule("docencia:posgrado", "Docencia en posgrado (por curso)", 20, 100),

    "gestion:rector": ItemRule("gestion:rector", "Rector", 100, 100),
    "gestion:vicerrector": ItemRule("gestion:vicerrector", "Vicerrector/Directorio", 80, 80),
    "gestion:decano": ItemRule("gestion:decano", "Decano / Director Instituto", 60, 60),
    "gestion:secretario": ItemRule("gestion:secretario", "Secretario Acad., Inv. o Ext.", 60, 60),
    "gestion:coordinador": ItemRule("gestion:coordinador", "Coordinador de carrera/programas", 40, 40),
    "gestion:consejero": ItemRule("gestion:consejero", "Consejero institucional", 20, 20),

    "otroscargos:funciones": ItemRule("otroscargos:funciones", "Funciones especiales (por función)", 10, 50),

    "ciencia:dir_doctorandos": ItemRule("ciencia:dir_doctorandos", "Dirección de doctorandos/posdocs", 30, 90),
    "ciencia:dir_maestria": ItemRule("ciencia:dir_maestria", "Dirección de maestrandos", 20, 50),
    "ciencia:dir_grado": ItemRule("ciencia:dir_grado", "Dirección de tesistas de grado", 10, 50),
    "ciencia:becarios": ItemRule("ciencia:becarios", "Formación de becarios (CONICET/Agencia)", 20, 40),

    "proyectos:direccion": ItemRule("proyectos:direccion", "Dirección de proyectos (eval+financ)", 50, 150),
    "proyectos:codireccion": ItemRule("proyectos:codireccion", "Co-dirección de proyectos", 30, 90),
    "proyectos:participacion": ItemRule("proyectos:participacion", "Participación en proyectos", 20, 60),
    "proyectos:coordinacion": ItemRule("proyectos:coordinacion", "Coordinación de equipos", 20, 20),

    "extension:tutorias": ItemRule("extension:tutorias", "Tutorías de pasantías/prácticas", 10, 20),
    "extension:transferencia": ItemRule("extension:transferencia", "Vinculación/transferencia (acciones)", 15, 45),
    "extension:eventos_cientificos": ItemRule("extension:eventos_cientificos", "Eventos científicos (expositor/conferencista/panelista)", 20, 100),

    "eval:tribunal_grado": ItemRule("eval:tribunal_grado", "Tribunal de tesis de grado", 5, 20),
    "eval:tribunal_posgrado": ItemRule("eval:tribunal_posgrado", "Tribunal de tesis de posgrado", 10, 30),
    "eval:eval_proyectos": ItemRule("eval:eval_proyectos", "Evaluación de proyectos/programas I+D/ext.", 10, 30),
    "eval:eval_revistas": ItemRule("eval:eval_revistas", "Evaluación en revistas/congresos/jornadas", 10, 30),
    "eval:eval_institucional": ItemRule("eval:eval_institucional", "Evaluación institucional/organismos I+D", 10, 30),

    "otras:comites_redes": ItemRule("otras:comites_redes", "Participación en redes/comités/eventos", 20, 60),
    "otras:ejercicio_prof": ItemRule("otras:ejercicio_prof", "Ejercicio profesional extraacadémico (años)", 5, 20),

    "pubs:con_referato": ItemRule("pubs:con_referato", "Artículos con referato (indexados)", 20, 140),
    "pubs:sin_referato": ItemRule("pubs:sin_referato", "Artículos sin referato", 10, 80),
    "pubs:libros": ItemRule("pubs:libros", "Libros (ISBN)", 40, 80),
    "pubs:capitulos": ItemRule("pubs:capitulos", "Capítulos de libro (ISBN)", 20, 60),
    "pubs:documentos": ItemRule("pubs:documentos", "Documentos técnicos/comunicaciones", 10, 30),

    "desarrollos:software_patente": ItemRule("desarrollos:software_patente", "Patentes/soft. registrado", 30, 60),
    "desarrollos:procesos": ItemRule("desarrollos:procesos", "Procesos de gestión/innovación", 20, 60),

    "servicios:tecnicos": ItemRule("servicios:tecnicos", "Servicios técnicos/profesionales", 20, 40),
    "servicios:informes": ItemRule("servicios:informes", "Informes técnicos/diagnósticos", 10, 20),

    "redes:participacion": ItemRule("redes:participacion", "Participación en redes", 10, 30),
    "redes:organizacion_eventos": ItemRule("redes:organizacion_eventos", "Organización de eventos", 20, 60),
    "redes:gestion_editorial": ItemRule("redes:gestion_editorial", "Gestión editorial (revistas)", 20, 60),

    "premios:internacional": ItemRule("premios:internacional", "Premios internacionales", 50, 100),
    "premios:nacional": ItemRule("premios:nacional", "Premios nacionales", 20, 100),
    "premios:distinciones": ItemRule("premios:distinciones", "Menciones/distinciones", 20, 100),
}

SECTION_LIMITS = {
    "formacion": 400,
    "docencia": 300,
    "gestion": 200,
    "otroscargos": 75,
    "ciencia": 150,
    "proyectos": 150,
    "extension": 60,
    "eval": 100,
    "otras": 60,
    "pubs": 300,
    "desarrollos": 100,
    "servicios": 40,
    "redes": 150,
    "premios": 100,
}

GLOBAL_LIMITS = {
    "3:Cargos_total": 500,
    "4:CyT_total": 500,
    "5:Producciones_total": 350,
    "6:Otros_total": 200,
}

def clamp(value, max_value):
    return min(value, max_value)

def sum_with_section_caps(section_scores: Dict[str, float]) -> Dict[str, Any]:
    out = dict(section_scores)
    cargos_total = out.get("docencia",0)+out.get("gestion",0)+out.get("otroscargos",0)
    out["3:Cargos_total"] = clamp(cargos_total, GLOBAL_LIMITS["3:Cargos_total"])
    cyt_total = out.get("ciencia",0)+out.get("proyectos",0)+out.get("extension",0)+out.get("eval",0)+out.get("otras",0)
    out["4:CyT_total"] = clamp(cyt_total, GLOBAL_LIMITS["4:CyT_total"])
    prod_total = out.get("pubs",0)+out.get("desarrollos",0)+out.get("servicios",0)
    out["5:Producciones_total"] = clamp(prod_total, GLOBAL_LIMITS["5:Producciones_total"])
    otros_total = out.get("redes",0)+out.get("premios",0)
    out["6:Otros_total"] = clamp(otros_total, GLOBAL_LIMITS["6:Otros_total"])
    out["2:Formacion_total"] = clamp(out.get("formacion",0), SECTION_LIMITS["formacion"])
    out["TOTAL_GENERAL"] = out["2:Formacion_total"] + out["3:Cargos_total"] + out["4:CyT_total"] + out["5:Producciones_total"] + out["6:Otros_total"]
    return out
