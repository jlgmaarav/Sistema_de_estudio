# -*- coding: utf-8 -*-
"""Gamificación estilo Math Academy: XP, niveles, objetivo diario, racha e insignias.

El estado vive dentro de perfil.json bajo la clave "gamificacion":
  { "xp_total": int, "diario": {"YYYY-MM-DD": xp}, "meta_diaria": int,
    "insignias": {"id": "YYYY-MM-DD"} }

Cada práctica otorga XP (más si estrena dominio o si fue fluida). El nivel, la
racha y las insignias se derivan del estado; no se guardan redundantes salvo la
fecha de desbloqueo de cada insignia.
"""
from datetime import date, datetime, timedelta

META_DIARIA_DEFECTO = 100

# XP por evento de práctica
XP_DIRECTO_EXITO = 10       # resolver bien un nodo
XP_RECIEN_DOMINADO = 20     # bonus al cruzar el umbral de dominio por primera vez
XP_FLUIDO = 5              # bonus por acierto rápido en quiz cronometrado
XP_FALLO = 2               # esfuerzo: intentarlo aunque falles


# ------------------------------------------------------------------ estado

def _bloque(perfil: dict) -> dict:
    g = perfil.setdefault("gamificacion", {})
    g.setdefault("xp_total", 0)
    g.setdefault("diario", {})
    g.setdefault("meta_diaria", META_DIARIA_DEFECTO)
    g.setdefault("insignias", {})
    return g


def umbral_nivel(n: int) -> int:
    """XP acumulado necesario para alcanzar el nivel n (1 = 0 XP).
    Incrementos crecientes: 100, 150, 200, ... (aritméticos)."""
    if n <= 1:
        return 0
    k = n - 1
    return 100 * k + 25 * k * (k - 1)  # suma de 100 + 50*(0..k-1)


def nivel_de(xp: int) -> int:
    n = 1
    while umbral_nivel(n + 1) <= xp:
        n += 1
    return n


def _racha(diario: dict, hoy: date) -> tuple[int, int]:
    """(racha actual, racha máxima) de días consecutivos con XP > 0."""
    dias = sorted(d for d, xp in diario.items() if xp > 0)
    if not dias:
        return 0, 0
    fechas = [datetime.strptime(d, "%Y-%m-%d").date() for d in dias]
    # racha máxima histórica
    maxima = actual_run = 1
    for i in range(1, len(fechas)):
        if (fechas[i] - fechas[i - 1]).days == 1:
            actual_run += 1
        else:
            actual_run = 1
        maxima = max(maxima, actual_run)
    # racha actual: cuenta hacia atrás desde hoy (o ayer, si hoy aún sin actividad)
    conjunto = set(fechas)
    ancla = hoy if hoy in conjunto else hoy - timedelta(days=1)
    if ancla not in conjunto:
        return 0, maxima
    actual = 0
    cursor = ancla
    while cursor in conjunto:
        actual += 1
        cursor -= timedelta(days=1)
    return actual, maxima


# ------------------------------------------------------------------ insignias

def _nodos_dominados(perfil: dict) -> int:
    return sum(1 for e in perfil.get("nodos", {}).values()
               if isinstance(e, dict) and e.get("dominio", 0) >= 0.7)


def _consolidados(perfil: dict) -> int:
    return sum(1 for e in perfil.get("nodos", {}).values()
               if isinstance(e, dict) and e.get("dominio", 0) >= 0.7 and e.get("fluidez", 0) >= 0.7)


# id -> (nombre, descripción, predicado(contexto) -> bool)
INSIGNIAS = [
    ("primer_paso", "Primer paso", "Tu primera práctica registrada",
     lambda c: c["xp_total"] > 0),
    ("diez_dominados", "Base sólida", "10 nodos dominados",
     lambda c: c["dominados"] >= 10),
    ("cincuenta_dominados", "Cincuentena", "50 nodos dominados",
     lambda c: c["dominados"] >= 50),
    ("cien_dominados", "Centenar", "100 nodos dominados",
     lambda c: c["dominados"] >= 100),
    ("primer_consolidado", "Con soltura", "Tu primer nodo consolidado (dominio + fluidez)",
     lambda c: c["consolidados"] >= 1),
    ("racha_7", "Semana en racha", "7 días seguidos estudiando",
     lambda c: c["racha"] >= 7),
    ("racha_30", "Mes de fuego", "30 días seguidos estudiando",
     lambda c: c["racha"] >= 30),
    ("nivel_5", "Nivel 5", "Alcanza el nivel 5",
     lambda c: c["nivel"] >= 5),
    ("nivel_10", "Nivel 10", "Alcanza el nivel 10",
     lambda c: c["nivel"] >= 10),
    ("mil_xp", "Kilo-XP", "1000 XP acumulados",
     lambda c: c["xp_total"] >= 1000),
    ("meta_cumplida", "Objetivo del día", "Cumple tu meta diaria de XP",
     lambda c: c["xp_hoy"] >= c["meta_diaria"]),
]


def estado(perfil: dict, hoy: date | None = None) -> dict:
    hoy = hoy or date.today()
    g = _bloque(perfil)
    xp_total = g["xp_total"]
    nivel = nivel_de(xp_total)
    base, techo = umbral_nivel(nivel), umbral_nivel(nivel + 1)
    xp_hoy = g["diario"].get(hoy.isoformat(), 0)
    racha, racha_max = _racha(g["diario"], hoy)
    return {
        "xp_total": xp_total,
        "nivel": nivel,
        "xp_en_nivel": xp_total - base,
        "xp_para_siguiente": techo - base,
        "meta_diaria": g["meta_diaria"],
        "xp_hoy": xp_hoy,
        "meta_cumplida": xp_hoy >= g["meta_diaria"],
        "racha": racha,
        "racha_max": racha_max,
        "dominados": _nodos_dominados(perfil),
        "consolidados": _consolidados(perfil),
        "insignias": [
            {"id": iid, "nombre": nom, "desc": desc,
             "conseguida": iid in g["insignias"], "fecha": g["insignias"].get(iid)}
            for iid, nom, desc, _ in INSIGNIAS
        ],
    }


def _revisar_insignias(perfil: dict, hoy: date) -> list[str]:
    """Desbloquea insignias cuyo predicado ya se cumple. Devuelve las nuevas."""
    g = _bloque(perfil)
    ctx = estado(perfil, hoy)
    nuevas = []
    for iid, nom, _desc, pred in INSIGNIAS:
        if iid not in g["insignias"] and pred(ctx):
            g["insignias"][iid] = hoy.isoformat()
            nuevas.append(nom)
    return nuevas


# ------------------------------------------------------------------ otorgar

def otorgar(perfil: dict, tipo: str, exito: bool, fluido: bool | None,
            recien_dominado: bool, hoy: date | None = None,
            calidad: float | None = None) -> dict:
    """Otorga XP por un evento de práctica directa y actualiza racha/insignias.

    tipo: 'directo' (los eventos implícitos no dan XP).
    `calidad`: escala graduada 0–1. Si se da, el XP base se escala con ella
    (resuelto=10, desliz≈8, a-medias=5); un bloqueo/blanco da el XP de esfuerzo.
    Si no se da, se usa el `exito` binario (compatibilidad).
    Devuelve {xp, nivel_antes, nivel_despues, nuevas_insignias}.
    """
    hoy = hoy or date.today()
    g = _bloque(perfil)
    nivel_antes = nivel_de(g["xp_total"])

    if calidad is None:
        calidad = 1.0 if exito else 0.0
    avanza = calidad >= 0.5

    if avanza:
        xp = round(XP_DIRECTO_EXITO * calidad)
        if recien_dominado:
            xp += XP_RECIEN_DOMINADO
        if fluido:
            xp += XP_FLUIDO
    else:
        xp = XP_FALLO

    g["xp_total"] += xp
    clave = hoy.isoformat()
    g["diario"][clave] = g["diario"].get(clave, 0) + xp
    nuevas = _revisar_insignias(perfil, hoy)
    return {
        "xp": xp,
        "nivel_antes": nivel_antes,
        "nivel_despues": nivel_de(g["xp_total"]),
        "nuevas_insignias": nuevas,
    }
