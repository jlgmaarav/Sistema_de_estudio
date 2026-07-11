# -*- coding: utf-8 -*-
"""Perfil de conocimiento persistente sobre los knowledge graphs.

Estado por nodo (perfil.json): dominio (0-1), repeticiones, intervalo de
repaso, última práctica y próxima revisión. Cada intento corregido por el
pipeline actualiza los nodos practicados y propaga crédito implícito a sus
prerrequisitos (peso 1.0 = subskill ejercitada; 0.5 = crédito parcial).

Uso CLI:
  python perfil.py estado                      Resumen del perfil y frontera
  python perfil.py registrar em.1.07 --fallo   Registrar práctica directa
  python perfil.py registrar-conceptos --asignatura "Electromagnetismo" --conceptos "Ley de Gauss;Potencial"
  python perfil.py marcar-cursadas             Inicializa las asignaturas ya cursadas
  python perfil.py frontera [--materia X]      Nodos listos para aprender
  python perfil.py vencidos                    Repasos pendientes
"""
import argparse
import difflib
import glob
import json
import math
import os
import sys
import unicodedata
from datetime import date, datetime, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))
PERFIL_PATH = os.path.join(DIR, "perfil.json")

sys.path.insert(0, DIR)
import gamificacion  # noqa: E402  (mismo directorio)

INTERVALOS = [1, 3, 7, 14, 30, 60, 120, 240]
UMBRAL_FRONTERA = 0.7      # dominio efectivo mínimo de un prerrequisito duro
GANANCIA_DIRECTA = 0.35    # avance de dominio por práctica directa con éxito
GANANCIA_IMPLICITA = 0.18  # avance máximo por crédito implícito
DECAIMIENTO_FALLO = 0.55   # factor sobre el dominio al fallar (calidad 0)
ATENUACION_PROFUNDIDAD = 0.6
CREDITO_MINIMO = 0.1

# Escala de calidad graduada (0–1). Sustituye al éxito binario ✓/✗: distingue
# entre resuelto / desliz / a-medias / bloqueado / en-blanco, y modula cuánto
# sube o baja el dominio, si expande el intervalo de repaso, cuánto crédito
# propaga a los prerrequisitos y —si el intento fue un bloqueo— si empuja esos
# prerrequisitos a repaso (el hueco suele estar en la base).
CALIDAD = {
    "resuelto": 1.0,    # bien, camino correcto y terminado
    "desliz":   0.75,   # terminado pero mal por un desliz (concepto entendido)
    "a_medias": 0.5,    # iba bien pero no llegó al final
    "bloqueado": 0.25,  # bloqueado o a medias equivocado
    "en_blanco": 0.0,   # en blanco
}
UMBRAL_EXITO_CALIDAD = 0.5    # calidad >= => cuenta como avance (gana dominio, propaga crédito)
UMBRAL_SOLIDO_CALIDAD = 0.75  # calidad >= => además expande el intervalo de repaso (reps++)
UMBRAL_REPASO_PREREQ = 0.25   # calidad <= => empuja los prerrequisitos duros a repaso


def calidad_desde(exito: bool | None = None, calidad: float | None = None) -> float:
    """Normaliza una calidad 0–1 a partir de `calidad` explícita (número o clave
    de CALIDAD) o, si no se da, del `exito` binario (1.0 / 0.0)."""
    if calidad is None:
        return 1.0 if exito else 0.0
    if isinstance(calidad, str):
        return CALIDAD.get(calidad, 1.0 if exito else 0.0)
    return max(0.0, min(1.0, float(calidad)))

# Fluidez: segunda dimensión del dominio (¿lo haces con soltura/rápido?).
# Modelo de LÍNEA BASE PERSONAL por nodo: los primeros aciertos cronometrados fijan
# tu tiempo de referencia para ESE nodo (los tiempos varían muchísimo entre temas:
# un problema de operadores escalera puede llevar 1 h y una cuestión 5 min, así que
# no se comparan nodos entre sí). A partir de ahí, resolver un problema del mismo
# nodo por debajo de tu referencia sube la fluidez; más lento la baja. Un fallo la
# baja. Solo la mueve la práctica CRONOMETRADA (quiz/simulacro). Decae más rápido
# que el dominio (la automaticidad se pierde antes). No bloquea la frontera.
UMBRAL_FLUIDEZ = 0.7          # fluidez efectiva para considerar un nodo "consolidado"
BASELINE_MUESTRAS = 3         # primeros tiempos exitosos que fijan la referencia del nodo
MAX_TIEMPOS = 12              # tiempos guardados por nodo (los más recientes)
EMA_FLUIDEZ = 0.4             # cuánto se mueve la fluidez hacia su objetivo por intento
SENSIBILIDAD_FLUIDEZ = 1.67   # pendiente: resolver un 30% más rápido/lento = ±0.5 de fluidez
DECAIMIENTO_FLUIDEZ_FALLO = 0.7   # factor sobre la fluidez al fallar
ESTABILIDAD_FLUIDEZ = 1.0     # olvido de fluidez más rápido que el de dominio (2.0)


# ---------------------------------------------------------------- grafos

def cargar_grafos() -> dict:
    """Devuelve {id: nodo} con materia/granularidad/curso anexados."""
    nodos = {}
    for ruta in sorted(glob.glob(os.path.join(DIR, "*.json"))):
        if os.path.basename(ruta) in ("perfil.json", "banco_problemas.json", "examenes.json"):
            continue
        with open(ruta, "r", encoding="utf-8") as f:
            g = json.load(f)
        if "materia" not in g or "nodos" not in g:
            continue
        for n in g.get("nodos", []):
            nodos[n["id"]] = dict(
                n,
                materia=g["materia"],
                granularidad=g.get("granularidad", "fina"),
                curso=g.get("curso", 0),
            )
    return nodos


# ---------------------------------------------------------------- perfil

def cargar_perfil() -> dict:
    if os.path.exists(PERFIL_PATH):
        with open(PERFIL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"actualizado": None, "nodos": {}}


def guardar_perfil(perfil: dict) -> None:
    perfil["actualizado"] = datetime.now().isoformat(timespec="seconds")
    with open(PERFIL_PATH, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=1)
    _backup_perfil(perfil)


def _backup_perfil(perfil: dict, conservar: int = 14) -> None:
    """Una copia por día en backups/; conserva las últimas `conservar`."""
    try:
        carpeta = os.path.join(DIR, "backups")
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, f"perfil_{_hoy().isoformat()}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(perfil, f, ensure_ascii=False, indent=1)
        copias = sorted(glob.glob(os.path.join(carpeta, "perfil_*.json")))
        for vieja in copias[:-conservar]:
            os.remove(vieja)
    except Exception:
        pass  # el backup nunca debe romper un registro


def _entrada_nueva() -> dict:
    return {"dominio": 0.0, "fluidez": 0.0, "tiempos": [], "reps": 0, "intervalo": 0,
            "ultima": None, "proxima": None, "historial": []}


def _hoy() -> date:
    return date.today()


def _fecha(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def dominio_efectivo(entrada: dict, hoy: date | None = None) -> float:
    """Dominio con curva de olvido: decae al pasarse la fecha de revisión."""
    if not entrada or entrada["dominio"] <= 0:
        return 0.0
    hoy = hoy or _hoy()
    proxima = _fecha(entrada.get("proxima"))
    if proxima is None or hoy <= proxima:
        return entrada["dominio"]
    retraso = (hoy - proxima).days
    estabilidad = max(entrada.get("intervalo", 1), 1) * 2.0
    return entrada["dominio"] * math.exp(-retraso / estabilidad)


def fluidez_efectiva(entrada: dict, hoy: date | None = None) -> float:
    """Fluidez con curva de olvido propia (decae más rápido que el dominio)."""
    if not entrada or entrada.get("fluidez", 0.0) <= 0:
        return 0.0
    hoy = hoy or _hoy()
    proxima = _fecha(entrada.get("proxima"))
    if proxima is None or hoy <= proxima:
        return entrada["fluidez"]
    retraso = (hoy - proxima).days
    estabilidad = max(entrada.get("intervalo", 1), 1) * ESTABILIDAD_FLUIDEZ
    return entrada["fluidez"] * math.exp(-retraso / estabilidad)


def consolidado(entrada: dict, hoy: date | None = None) -> bool:
    """Nodo dominado Y fluido: sabes hacerlo y con soltura."""
    return (dominio_efectivo(entrada, hoy) >= UMBRAL_FRONTERA
            and fluidez_efectiva(entrada, hoy) >= UMBRAL_FLUIDEZ)


def _anotar(entrada: dict, tipo: str, exito: bool, credito: float, fecha: date, origen: str) -> None:
    entrada.setdefault("historial", []).append(
        {"fecha": fecha.isoformat(), "tipo": tipo, "exito": exito,
         "credito": round(credito, 2), "origen": origen}
    )
    entrada["historial"] = entrada["historial"][-20:]


def _practica_directa(entrada: dict, exito: bool, fecha: date, origen: str,
                      calidad: float | None = None) -> None:
    """Aplica una práctica directa modulada por la calidad (0–1).

    - calidad >= UMBRAL_EXITO (0.5): el dominio sube proporcionalmente a la calidad.
      Si además calidad >= UMBRAL_SOLIDO (0.75) el intervalo de repaso se expande;
      si no (a-medias), gana algo de dominio pero se repasa pronto.
    - calidad < UMBRAL_EXITO: el dominio decae; el factor es más suave cuanto más
      cerca del umbral (bloqueado decae menos que en-blanco) y el intervalo se reinicia.
    """
    calidad = calidad_desde(exito, calidad)
    avanza = calidad >= UMBRAL_EXITO_CALIDAD
    if avanza:
        entrada["dominio"] = min(0.98, entrada["dominio"] + (1 - entrada["dominio"]) * GANANCIA_DIRECTA * calidad)
        if calidad >= UMBRAL_SOLIDO_CALIDAD:
            entrada["reps"] += 1
            idx = min(entrada["reps"] - 1, len(INTERVALOS) - 1)
            entrada["intervalo"] = INTERVALOS[idx]
        else:
            entrada["intervalo"] = 1   # a medias: consolidar con un repaso próximo
    else:
        factor = DECAIMIENTO_FALLO + (1 - DECAIMIENTO_FALLO) * (calidad / UMBRAL_EXITO_CALIDAD)
        entrada["dominio"] = round(entrada["dominio"] * factor, 4)
        entrada["intervalo"] = 1
    entrada["dominio"] = round(entrada["dominio"], 4)
    entrada["ultima"] = fecha.isoformat()
    entrada["proxima"] = (fecha + timedelta(days=entrada["intervalo"])).isoformat()
    _anotar(entrada, "directo", avanza, round(calidad, 2), fecha, origen)


def _mediana(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def baseline_tiempo(entrada: dict) -> float | None:
    """Tiempo de referencia del nodo: mediana de los primeros tiempos exitosos.
    None si aún no hay suficientes muestras para juzgar la velocidad."""
    tiempos = entrada.get("tiempos", [])
    if len(tiempos) < BASELINE_MUESTRAS:
        return None
    return _mediana(tiempos[:BASELINE_MUESTRAS])


def _actualizar_fluidez(entrada: dict, exito: bool, segundos: float | None) -> bool:
    """Ajusta la fluidez tras una práctica CRONOMETRADA con tiempo real (segundos).
    Devuelve True si el intento batió la referencia del nodo (fue "fluido").

    - Fallo: la fluidez baja; no se registra el tiempo.
    - Acierto sin referencia todavía: se registra el tiempo, la fluidez tiende
      suavemente a 0.5 (aún no hay con qué comparar).
    - Acierto con referencia: objetivo de fluidez según cuánto batas tu tiempo
      base; la fluidez se acerca a ese objetivo (media móvil)."""
    f = entrada.get("fluidez", 0.0)
    if not exito:
        entrada["fluidez"] = round(f * DECAIMIENTO_FLUIDEZ_FALLO, 4)
        return False
    if segundos is None or segundos <= 0:
        return False

    tiempos = entrada.setdefault("tiempos", [])
    base = baseline_tiempo(entrada)   # referencia ANTES de añadir el tiempo de hoy
    tiempos.append(round(float(segundos), 1))
    del tiempos[:-MAX_TIEMPOS]

    if base is None:
        # Aún estableciendo la referencia: acercar la fluidez a 0.5 sin premiar velocidad
        entrada["fluidez"] = round(f + (0.5 - f) * 0.5, 4)
        return False

    ratio = base / segundos                      # >1 = más rápido que tu referencia
    objetivo = min(0.98, max(0.0, 0.5 + (ratio - 1.0) * SENSIBILIDAD_FLUIDEZ))
    entrada["fluidez"] = round(f + (objetivo - f) * EMA_FLUIDEZ, 4)
    return segundos < base


def _practica_implicita(entrada: dict, credito: float, fecha: date, origen: str) -> None:
    entrada["dominio"] = round(min(0.98, entrada["dominio"] + (1 - entrada["dominio"]) * GANANCIA_IMPLICITA * credito), 4)
    entrada["ultima"] = fecha.isoformat()
    # El repaso implícito empuja la próxima revisión hacia delante
    base = _fecha(entrada.get("proxima")) or fecha
    empuje = max(1, int(round(max(entrada.get("intervalo", 1), 1) * 0.4 * credito)))
    nueva = max(base, fecha) + timedelta(days=empuje)
    entrada["proxima"] = nueva.isoformat()
    _anotar(entrada, "implicito", True, credito, fecha, origen)


def _creditos_ancestros(ids: list[str], nodos: dict) -> dict[str, float]:
    """Crédito implícito hacia los prerrequisitos: producto de pesos × 0.6^profundidad."""
    creditos: dict[str, float] = {}

    def subir(nid: str, credito: float):
        for p in nodos.get(nid, {}).get("prerequisitos", []):
            c = credito * p["peso"] * ATENUACION_PROFUNDIDAD
            if c < CREDITO_MINIMO or p["id"] not in nodos:
                continue
            if c > creditos.get(p["id"], 0.0):
                creditos[p["id"]] = c
                subir(p["id"], c)

    for i in ids:
        subir(i, 1.0)
    for i in ids:
        creditos.pop(i, None)
    return creditos


def _empujar_prerrequisitos_repaso(perfil: dict, nodos: dict, ids: list[str],
                                   fecha: date) -> list[str]:
    """Cuando un intento se queda bloqueado/en blanco, el hueco suele estar en la
    base: adelanta a mañana el repaso de los prerrequisitos duros ya practicados."""
    empujados: list[str] = []
    manana = fecha + timedelta(days=1)
    for i in ids:
        for p in nodos.get(i, {}).get("prerequisitos", []):
            if p["peso"] < 1.0 or p["id"] not in nodos:
                continue
            e = perfil["nodos"].get(p["id"])
            if not e or e.get("dominio", 0) <= 0:
                continue
            prox = _fecha(e.get("proxima"))
            if prox is None or prox > manana:
                e["proxima"] = manana.isoformat()
                e["intervalo"] = 1
                if p["id"] not in empujados:
                    empujados.append(p["id"])
    return empujados


def aplicar_practica(perfil: dict, nodos: dict, ids: list[str], exito: bool,
                     fecha: date | None = None, origen: str = "",
                     segundos: float | None = None,
                     calidad: float | None = None) -> list[str]:
    """Aplica una práctica a los nodos dados. Devuelve mensajes descriptivos.

    `segundos`: None si la práctica no está cronometrada (manuscrito/plan; no toca
    la fluidez). Si viene de un quiz cronometrado, el tiempo real empleado en el
    problema — se compara con la referencia del nodo para mover la fluidez.

    `calidad`: escala graduada 0–1 (o clave de CALIDAD) que sustituye al éxito
    binario. Si se da, `exito` se deriva de ella (calidad >= UMBRAL_EXITO). Si no,
    se usa el `exito` binario como antes.
    """
    fecha = fecha or _hoy()
    calidad = calidad_desde(exito, calidad)
    exito = calidad >= UMBRAL_EXITO_CALIDAD
    cronometrado = segundos is not None
    mensajes = []
    validos = [i for i in ids if i in nodos]
    for i in ids:
        if i not in nodos:
            mensajes.append(f"AVISO: id desconocido '{i}' (ignorado)")

    xp_total, insignias_nuevas, subio_a = 0, [], None
    for i in validos:
        entrada = perfil["nodos"].setdefault(i, _entrada_nueva())
        dom_antes = dominio_efectivo(entrada, fecha)
        _practica_directa(entrada, exito, fecha, origen, calidad=calidad)
        fue_fluido = _actualizar_fluidez(entrada, exito, segundos) if cronometrado else None
        recien = dom_antes < UMBRAL_FRONTERA <= dominio_efectivo(entrada, fecha)
        premio = gamificacion.otorgar(perfil, "directo", exito, fue_fluido, recien, fecha, calidad=calidad)
        xp_total += premio["xp"]
        insignias_nuevas += premio["nuevas_insignias"]
        if premio["nivel_despues"] > premio["nivel_antes"]:
            subio_a = premio["nivel_despues"]
        extra = f", fluidez {entrada.get('fluidez', 0.0):.2f}" if cronometrado else ""
        mensajes.append(
            f"{i} [{nodos[i]['nombre']}]: dominio {entrada['dominio']:.2f}{extra}, "
            f"próxima revisión {entrada['proxima']}"
        )

    if exito and validos:
        creditos = _creditos_ancestros(validos, nodos)
        for nid, credito in sorted(creditos.items()):
            entrada = perfil["nodos"].setdefault(nid, _entrada_nueva())
            _practica_implicita(entrada, credito * calidad, fecha, origen)
        mensajes.append(f"Crédito implícito propagado a {len(creditos)} prerrequisitos.")

    if calidad <= UMBRAL_REPASO_PREREQ and validos:
        empujados = _empujar_prerrequisitos_repaso(perfil, nodos, validos, fecha)
        if empujados:
            mensajes.append(f"Bloqueo: {len(empujados)} prerrequisito(s) empujados a repaso ({', '.join(empujados)}).")

    if xp_total:
        msg = f"+{xp_total} XP"
        if subio_a:
            msg += f" · ¡subes al nivel {subio_a}!"
        if insignias_nuevas:
            msg += f" · insignia: {', '.join(insignias_nuevas)}"
        mensajes.append(msg)
    return mensajes


# ---------------------------------------------------------------- consultas

def frontera(perfil: dict, nodos: dict, materia: str | None = None,
             hoy: date | None = None) -> list[dict]:
    """Nodos aún no dominados cuyos prerrequisitos duros están dominados."""
    hoy = hoy or _hoy()
    resultado = []
    for nid, n in nodos.items():
        if materia and n["materia"] != materia:
            continue
        propio = dominio_efectivo(perfil["nodos"].get(nid), hoy)
        if propio >= UMBRAL_FRONTERA:
            continue
        listo = True
        for p in n.get("prerequisitos", []):
            if p["peso"] >= 1.0 and p["id"] in nodos:
                if dominio_efectivo(perfil["nodos"].get(p["id"]), hoy) < UMBRAL_FRONTERA:
                    listo = False
                    break
        if listo:
            resultado.append({"id": nid, "nombre": n["nombre"], "materia": n["materia"],
                              "curso": n["curso"], "dominio": round(propio, 2)})
    resultado.sort(key=lambda x: (x["curso"], x["materia"], x["id"]))
    return resultado


def vencidos(perfil: dict, nodos: dict, hoy: date | None = None) -> list[dict]:
    hoy = hoy or _hoy()
    out = []
    for nid, e in perfil["nodos"].items():
        proxima = _fecha(e.get("proxima"))
        if proxima and proxima < hoy and e["dominio"] > 0 and nid in nodos:
            out.append({"id": nid, "nombre": nodos[nid]["nombre"], "materia": nodos[nid]["materia"],
                        "retraso": (hoy - proxima).days,
                        "dominio_efectivo": round(dominio_efectivo(e, hoy), 2)})
    out.sort(key=lambda x: -x["retraso"])
    return out


def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def resolver_conceptos(materia: str, conceptos: list[str], nodos: dict | None = None) -> list[str]:
    """Mapea nombres de conceptos a ids de nodos de esa materia (difuso)."""
    nodos = nodos or cargar_grafos()
    candidatos = {nid: _normalizar(n["nombre"]) for nid, n in nodos.items()
                  if _normalizar(n["materia"]) == _normalizar(materia)}
    if not candidatos:
        candidatos = {nid: _normalizar(n["nombre"]) for nid, n in nodos.items()}
    ids = []
    nombres = list(candidatos.values())
    por_nombre = {v: k for k, v in candidatos.items()}
    for c in conceptos:
        cn = _normalizar(c)
        m = difflib.get_close_matches(cn, nombres, n=1, cutoff=0.5)
        if m:
            nid = por_nombre[m[0]]
            if nid not in ids:
                ids.append(nid)
    return ids


def _cargar_banco() -> dict:
    ruta = os.path.join(DIR, "banco_problemas.json")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# --------------------------------------------------- problemas del banco

def problemas_hechos(perfil: dict) -> dict:
    """Registro de problemas del banco ya resueltos: {problema_id: {exito, fecha}}."""
    return perfil.setdefault("problemas", {})


def marcar_problema(perfil: dict, problema_id: str, exito: bool, fecha: date | None = None) -> None:
    fecha = fecha or _hoy()
    problemas_hechos(perfil)[problema_id] = {"exito": bool(exito), "fecha": fecha.isoformat()}


def marcar_problema_y_guardar(problema_id: str, exito: bool) -> None:
    perfil = cargar_perfil()
    marcar_problema(perfil, problema_id, exito)
    guardar_perfil(perfil)


def emparejar_enunciado(texto: str, nodos_ids: list[str] | None = None, umbral: float = 0.5) -> str | None:
    """Identifica a qué problema del banco corresponde un enunciado transcrito
    (para marcarlo como hecho al corregir un manuscrito)."""
    if not texto:
        return None
    banco = _cargar_banco()
    texto_n = _normalizar(texto)[:400]
    mejor, mejor_r = None, umbral
    for mb in banco.values():
        for p in mb.get("problemas", []):
            if nodos_ids and not (set(p.get("nodos", [])) & set(nodos_ids)):
                continue
            r = difflib.SequenceMatcher(None, texto_n, _normalizar(p.get("enunciado", ""))[:400]).ratio()
            if r > mejor_r:
                mejor, mejor_r = p["id"], r
    return mejor


def _probs_por_nodo(banco: dict) -> dict[str, list]:
    salida: dict[str, list] = {}
    for mb in banco.values():
        for p in mb.get("problemas", []):
            for nid in p.get("nodos", []):
                salida.setdefault(nid, []).append(p)
    return salida


def _elegir_problema(pool: list, nid: str, semilla: str, hechos: dict) -> dict:
    """Prefiere problemas nunca hechos; entre iguales, rota por semilla."""
    import hashlib
    def clave(p):
        h = hechos.get(p["id"])
        hecho = 1 if h else 0
        fecha = h["fecha"] if h else ""
        rot = int(hashlib.md5(f"{p['id']}|{semilla}".encode()).hexdigest(), 16) % 1000
        return (hecho, fecha, rot)
    return sorted(pool, key=clave)[0]


def _formatear_eleccion(nid: str, info: dict, entrada: dict | None, p: dict) -> dict:
    return {
        "id": nid, "nombre": info["nombre"], "materia": info["materia"],
        "dominio": round((entrada or {}).get("dominio", 0.0), 2),
        "reps": (entrada or {}).get("reps", 0),
        "problema": {k: p.get(k, "") for k in ("id", "titulo", "enunciado", "hoja", "numero")},
    }


def seleccionar_quiz(n: int = 6, modo: str = "repaso", materia: str | None = None,
                     semilla: str | None = None) -> list[dict]:
    """Selección de problemas del banco para quiz cronometrado.

    - modo 'repaso': nodos ya practicados, priorizando los más 'fríos'
      (revisión cercana/pasada, pocas reps), interleaving máx. 2 por materia-tema.
    - modo 'diagnostico': nodos SIN evidencia (dominio 0), en orden del temario,
      repartidos entre temas — para calibrar el perfil al empezar una materia.
    """
    nodos = cargar_grafos()
    perfil = cargar_perfil()
    probs = _probs_por_nodo(_cargar_banco())
    hechos = problemas_hechos(perfil)
    hoy = _hoy()
    semilla = semilla or hoy.isoformat()

    if modo == "diagnostico":
        cands = [nid for nid in probs
                 if nid in nodos
                 and (materia is None or nodos[nid]["materia"] == materia)
                 and perfil["nodos"].get(nid, {}).get("dominio", 0) <= 0]
        # Repartir entre temas, en orden del temario
        por_tema: dict = {}
        for nid in sorted(cands):
            por_tema.setdefault(nodos[nid]["tema"], []).append(nid)
        orden = []
        while len(orden) < len(cands):
            for t in sorted(por_tema):
                if por_tema[t]:
                    orden.append(por_tema[t].pop(0))
        seleccion = orden[:n]
    else:
        puntuados = []
        for nid, e in perfil["nodos"].items():
            if nid == "problemas" or not isinstance(e, dict):
                continue
            if nid not in nodos or nid not in probs or e.get("dominio", 0) <= 0:
                continue
            if materia and nodos[nid]["materia"] != materia:
                continue
            proxima = _fecha(e.get("proxima")) or hoy
            frialdad = (hoy - proxima).days / max(e.get("intervalo", 1), 1)
            puntuados.append((frialdad + 1.0 / (e.get("reps", 0) + 1), nid))
        puntuados.sort(key=lambda x: -x[0])
        seleccion, cupo = [], {}
        for _, nid in puntuados:
            if len(seleccion) >= n:
                break
            clave = (nodos[nid]["materia"], nodos[nid]["tema"])
            if cupo.get(clave, 0) >= 2:
                continue
            seleccion.append(nid)
            cupo[clave] = cupo.get(clave, 0) + 1

    return [_formatear_eleccion(nid, nodos[nid], perfil["nodos"].get(nid),
                                _elegir_problema(probs[nid], nid, semilla, hechos))
            for nid in seleccion]


def seleccionar_simulacro(materia: str, temas: list[int] | None = None, n: int = 4,
                          semilla: str | None = None) -> list[dict]:
    """Simulacro de examen: problemas de la materia (acotados a los temas del
    examen si se indican), repartidos entre temas, prefiriendo problemas no vistos."""
    nodos = cargar_grafos()
    perfil = cargar_perfil()
    probs = _probs_por_nodo(_cargar_banco())
    hechos = problemas_hechos(perfil)
    semilla = semilla or f"simulacro|{_hoy().isoformat()}"

    cands = [nid for nid in probs if nid in nodos and nodos[nid]["materia"] == materia
             and (temas is None or nodos[nid]["tema"] in temas)]
    por_tema: dict = {}
    for nid in sorted(cands):
        por_tema.setdefault(nodos[nid]["tema"], []).append(nid)
    # Barajar dentro de cada tema con la semilla y repartir
    import hashlib
    for t in por_tema:
        por_tema[t].sort(key=lambda x: int(hashlib.md5(f"{x}|{semilla}".encode()).hexdigest(), 16))
    seleccion = []
    while len(seleccion) < n and any(por_tema.values()):
        for t in sorted(por_tema):
            if por_tema[t] and len(seleccion) < n:
                seleccion.append(por_tema[t].pop(0))

    return [_formatear_eleccion(nid, nodos[nid], perfil["nodos"].get(nid),
                                _elegir_problema(probs[nid], nid, semilla, hechos))
            for nid in seleccion]


# ---------------------------------------------------------------- acciones

def _regenerar_mapa():
    try:
        sys.path.insert(0, DIR)
        import generar_mapa
        generar_mapa.generar()
        print("Mapa regenerado con el perfil actualizado.")
    except Exception as e:
        print(f"Aviso: no se pudo regenerar el mapa: {e}")


def registrar_y_guardar(ids: list[str], exito: bool, origen: str = "",
                        segundos: float | None = None,
                        calidad: float | None = None) -> list[str]:
    """API para el pipeline: registra, guarda y regenera el mapa."""
    nodos = cargar_grafos()
    perfil = cargar_perfil()
    mensajes = aplicar_practica(perfil, nodos, ids, exito, origen=origen,
                                segundos=segundos, calidad=calidad)
    guardar_perfil(perfil)
    _regenerar_mapa()
    return mensajes


def _snapshot_reverso(antes: dict, despues: dict) -> dict:
    """Datos mínimos para deshacer un registro: por cada nodo/problema que haya
    cambiado, guarda su valor ANTES (None si no existía). Localizado, así deshacer
    una corrección no pisa las demás."""
    import copy
    rev = {"nodos": {}, "problemas": {}, "otros": {}}
    a_n, d_n = antes.get("nodos", {}), despues.get("nodos", {})
    for nid in set(a_n) | set(d_n):
        if a_n.get(nid) != d_n.get(nid):
            rev["nodos"][nid] = copy.deepcopy(a_n.get(nid))
    a_p, d_p = antes.get("problemas", {}), despues.get("problemas", {})
    for pid in set(a_p) | set(d_p):
        if a_p.get(pid) != d_p.get(pid):
            rev["problemas"][pid] = copy.deepcopy(a_p.get(pid))
    for k in set(antes) | set(despues):
        if k in ("nodos", "problemas", "actualizado"):
            continue
        if antes.get(k) != despues.get(k):
            rev["otros"][k] = copy.deepcopy(antes.get(k))
    return rev


def registrar_manuscrito(ids: list[str], exito: bool, origen: str = "",
                         calidad: float | None = None,
                         problema_id: str | None = None) -> tuple[list[str], dict]:
    """Registra la práctica de un problema resuelto a mano (dominio/XP + marca del
    banco) en UNA sola pasada y devuelve (mensajes, reverso). `reverso` permite
    deshacer exactamente este registro si la corrección resultó equivocada."""
    import copy
    nodos = cargar_grafos()
    perfil = cargar_perfil()
    antes = copy.deepcopy(perfil)
    mensajes = aplicar_practica(perfil, nodos, ids, exito, origen=origen, calidad=calidad)
    if problema_id:
        marcar_problema(perfil, problema_id, exito)
    guardar_perfil(perfil)
    _regenerar_mapa()
    return mensajes, _snapshot_reverso(antes, perfil)


def revertir_reverso(reverso: dict) -> bool:
    """Deshace un registro a partir de su `reverso` (ver registrar_manuscrito):
    restaura los nodos y marcas afectados a su estado anterior. Devuelve True si
    hizo algún cambio."""
    if not reverso:
        return False
    perfil = cargar_perfil()
    cambiado = False
    for nid, val in reverso.get("nodos", {}).items():
        if val is None:
            cambiado = perfil["nodos"].pop(nid, None) is not None or cambiado
        else:
            perfil["nodos"][nid] = val
            cambiado = True
    probs = perfil.setdefault("problemas", {})
    for pid, val in reverso.get("problemas", {}).items():
        if val is None:
            cambiado = probs.pop(pid, None) is not None or cambiado
        else:
            probs[pid] = val
            cambiado = True
    for k, val in reverso.get("otros", {}).items():
        if val is None:
            cambiado = perfil.pop(k, None) is not None or cambiado
        else:
            perfil[k] = val
            cambiado = True
    if cambiado:
        guardar_perfil(perfil)
        _regenerar_mapa()
    return cambiado


def marcar_cursadas(dominio: float = 0.75) -> None:
    """Inicializa como sabidas las asignaturas ya cursadas (granularidad no fina)."""
    nodos = cargar_grafos()
    perfil = cargar_perfil()
    hoy = _hoy()
    contador = 0
    for nid, n in nodos.items():
        if n["granularidad"] == "fina":
            continue
        if nid in perfil["nodos"] and perfil["nodos"][nid]["dominio"] > 0:
            continue
        e = _entrada_nueva()
        e.update(dominio=dominio, fluidez=round(dominio * 0.8, 4), reps=3, intervalo=180,
                 ultima=hoy.isoformat(), proxima=(hoy + timedelta(days=180)).isoformat())
        _anotar(e, "inicial", True, 1.0, hoy, "marcar-cursadas")
        perfil["nodos"][nid] = e
        contador += 1
    guardar_perfil(perfil)
    print(f"Marcados {contador} nodos de asignaturas cursadas con dominio inicial {dominio}.")
    _regenerar_mapa()


def estado() -> None:
    nodos = cargar_grafos()
    perfil = cargar_perfil()
    hoy = _hoy()
    practicados = {k: v for k, v in perfil["nodos"].items() if k in nodos and v["dominio"] > 0}
    print(f"Perfil: {len(practicados)}/{len(nodos)} nodos con dominio > 0")

    por_materia: dict[str, list[tuple[float, float]]] = {}
    for nid, n in nodos.items():
        e = perfil["nodos"].get(nid)
        por_materia.setdefault(n["materia"], []).append(
            (dominio_efectivo(e, hoy), fluidez_efectiva(e, hoy)))
    print("\nDominio / fluidez efectivos medios por asignatura:")
    for m, ds in sorted(por_materia.items(), key=lambda kv: -sum(d for d, _ in kv[1]) / len(kv[1])):
        media_d = sum(d for d, _ in ds) / len(ds)
        media_f = sum(f for _, f in ds) / len(ds)
        barra = "#" * int(media_d * 20)
        print(f"  {m:<45} dom {media_d:5.0%} / flu {media_f:4.0%} {barra}")

    consolidados = sum(1 for nid in nodos if consolidado(perfil["nodos"].get(nid), hoy))
    dominados = sum(1 for nid in nodos if dominio_efectivo(perfil["nodos"].get(nid), hoy) >= UMBRAL_FRONTERA)
    print(f"\nDominados: {dominados}  ·  Consolidados (dominio+fluidez): {consolidados}")

    g = gamificacion.estado(perfil, hoy)
    print(f"\nNivel {g['nivel']} · {g['xp_total']} XP ({g['xp_en_nivel']}/{g['xp_para_siguiente']} al siguiente) · "
          f"racha {g['racha']} días (máx {g['racha_max']}) · hoy {g['xp_hoy']}/{g['meta_diaria']} XP")
    logradas = [i['nombre'] for i in g['insignias'] if i['conseguida']]
    if logradas:
        print("Insignias: " + ", ".join(logradas))

    v = vencidos(perfil, nodos)
    print(f"\nRepasos vencidos: {len(v)}")
    for x in v[:10]:
        print(f"  {x['id']:<10} {x['nombre']} ({x['retraso']} días, dominio ef. {x['dominio_efectivo']})")

    f = frontera(perfil, nodos)
    print(f"\nFrontera de conocimiento ({len(f)} nodos listos para aprender), primeros 15:")
    for x in f[:15]:
        print(f"  {x['id']:<10} [{x['materia']}] {x['nombre']}")


def main():
    parser = argparse.ArgumentParser(description="Perfil de conocimiento del knowledge graph")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("estado")

    p_reg = sub.add_parser("registrar")
    p_reg.add_argument("ids", nargs="+")
    p_reg.add_argument("--fallo", action="store_true")
    p_reg.add_argument("--calidad", choices=list(CALIDAD),
                       help="Calidad graduada del intento (resuelto/desliz/a_medias/bloqueado/en_blanco)")
    p_reg.add_argument("--origen", default="cli")

    p_rc = sub.add_parser("registrar-conceptos")
    p_rc.add_argument("--asignatura", required=True)
    p_rc.add_argument("--conceptos", required=True, help="Separados por ';'")
    p_rc.add_argument("--fallo", action="store_true")
    p_rc.add_argument("--origen", default="cli")

    p_mc = sub.add_parser("marcar-cursadas")
    p_mc.add_argument("--dominio", type=float, default=0.75)

    p_fr = sub.add_parser("frontera")
    p_fr.add_argument("--materia")

    sub.add_parser("vencidos")

    args = parser.parse_args()

    if args.cmd == "estado":
        estado()
    elif args.cmd == "registrar":
        cal = CALIDAD[args.calidad] if args.calidad else None
        for m in registrar_y_guardar(args.ids, not args.fallo, args.origen, calidad=cal):
            print(m)
    elif args.cmd == "registrar-conceptos":
        nodos = cargar_grafos()
        ids = resolver_conceptos(args.asignatura, args.conceptos.split(";"), nodos)
        if not ids:
            print("No se pudo mapear ningún concepto a nodos del grafo.")
            sys.exit(1)
        print(f"Conceptos mapeados a: {', '.join(ids)}")
        for m in registrar_y_guardar(ids, not args.fallo, args.origen):
            print(m)
    elif args.cmd == "marcar-cursadas":
        marcar_cursadas(args.dominio)
    elif args.cmd == "frontera":
        nodos = cargar_grafos()
        perfil = cargar_perfil()
        for x in frontera(perfil, nodos, args.materia):
            print(f"{x['id']:<10} [{x['materia']}] {x['nombre']} (dominio {x['dominio']})")
    elif args.cmd == "vencidos":
        nodos = cargar_grafos()
        perfil = cargar_perfil()
        for x in vencidos(perfil, nodos):
            print(f"{x['id']:<10} {x['nombre']} — {x['retraso']} días de retraso (ef. {x['dominio_efectivo']})")


if __name__ == "__main__":
    main()
