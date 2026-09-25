# -*- coding: utf-8 -*-
"""Motor de recomendaciones de estudio orientado a exámenes.

Contexto académico a partir de las fechas de examen (examenes.json):
1. Riesgo: combina nodos pendientes, dominio, prerrequisitos, importancia y
   proximidad del examen para ordenar las opciones.
2. Recomendaciones: repasos vencidos + nodos nuevos de la frontera, priorizando
   la asignatura más urgente y los nodos nuevos que repasan implícitamente
   prerrequisitos vencidos. Cada nodo lleva sus problemas del banco y sus
   fuentes de teoría.

Uso:
  python planificar.py                    Recomendaciones para hoy
  python planificar.py --fecha 2026-10-01 Simular otro día
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import perfil as motor
import problemas as kg_problemas

EXAMENES_PATH = os.path.join(DIR, "examenes.json")
BANCO_PATH = os.path.join(DIR, "banco_problemas.json")
REPASOS_POR_NODO = 1.5   # repasos medios estimados por nodo hasta el examen
BUFFER_DIAS = 3          # días antes del examen reservados a repaso global
MAX_REPASOS_RECOMENDADOS = 8
MAX_NUEVOS_RECOMENDADOS = 8


def cargar_json(ruta, defecto=None):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return defecto


def problemas_de(banco: dict, nid: str, cuantos: int, semilla: str,
                 hechos: dict | None = None, perfil_d: dict | None = None,
                 nodos: dict | None = None, hoy: date | None = None) -> list[dict]:
    """Problemas del banco para un nodo: primero los nunca hechos, luego los
    más antiguos; entre iguales rota con la semilla del día."""
    hechos = hechos or {}
    encontrados = []
    for materia_banco in (banco or {}).values():
        for p in materia_banco.get("problemas", []):
            if nid in p.get("nodos", []):
                if perfil_d is not None and nodos is not None:
                    estado = kg_problemas.evaluar_problema(p, perfil_d, nodos, hoy)
                    if not estado["listo"]:
                        continue
                    p = {**p, "preparacion": estado}
                encontrados.append(p)
    if not encontrados:
        return []

    def clave(p):
        h = hechos.get(p["id"])
        rot = int(hashlib.md5(f"{p['id']}|{semilla}".encode()).hexdigest(), 16) % 1000
        return (1 if h else 0, h["fecha"] if h else "", rot)

    return [{**p, "hecho": p["id"] in hechos} for p in sorted(encontrados, key=clave)[:cuantos]]


def ritmo_real(perfil_d: dict, nodos: dict, materia: str, hoy, ventana: int = 14) -> float:
    """Nodos-día con práctica directa exitosa en la ventana (nodos/día).
    Excluye la inicialización de cursadas."""
    eventos = set()
    for nid, e in perfil_d["nodos"].items():
        if nid not in nodos or nodos[nid]["materia"] != materia:
            continue
        for h in e.get("historial", []):
            if h.get("tipo") == "directo" and h.get("exito") and h.get("origen") != "marcar-cursadas":
                try:
                    f = datetime.strptime(h["fecha"], "%Y-%m-%d").date()
                except ValueError:
                    continue
                if 0 <= (hoy - f).days < ventana:
                    eventos.add((nid, h["fecha"]))
    return len(eventos) / ventana


def fuentes_txt(nodo: dict) -> str:
    f = nodo.get("fuentes", {})
    nombres = {"wangsness": "Wangsness", "griffiths": "Griffiths", "jackson": "Jackson",
               "problemas": "Probl.", "apuntes": "Apuntes", "guia": "Guía",
               "feynman": "Feynman", "panofsky": "Panofsky", "thide": "Thidé",
               "libro": "Libro", "libro_metodos": "Métodos"}
    return " · ".join(f"{nombres.get(k, k)} {v}" for k, v in f.items())


def plan_diario(nodos, perfil_d, banco, filas_viab, cfg, hoy, materia_forzada=None):
    """Genera opciones priorizadas, no una lista de tareas que haya que cumplir.

    El tiempo disponible se conserva como contexto de la sesión, pero no decide
    cuántos conceptos aparecen ni crea una deuda de minutos. Los topes solo
    evitan saturar la interfaz; no limitan lo que el estudiante puede hacer.
    """
    urgencia = {}
    for f in filas_viab:
        # La recomendación se ordena por riesgo y contexto académico, no por
        # una cuota temporal calculada.
        urgencia[f["materia"]] = max(
            urgencia.get(f["materia"], 0), f.get("prioridad_score", f.get("riesgo", 0))
        )

    plan = {
        "modo": "recomendaciones",
        "repasos": [],
        "nuevos": [],
        "implicitos": [],
        "repasos_omitidos": 0,
        "nuevos_omitidos": 0,
        "problemas_listos": [],
        "problemas_por_materia": [],
        "problemas_bloqueados": 0,
        "practica": {"activa": False, "mensaje": ""},
        "debilidades": [],
    }
    hechos = motor.problemas_hechos(perfil_d)

    # 1. Repasos vencidos, ordenados por retraso. No se impone un cupo temporal.
    vencidos = motor.vencidos(perfil_d, nodos, hoy)
    if materia_forzada:
        vencidos = [v for v in vencidos if v.get("materia") == materia_forzada]
    ids_vencidos = {v["id"] for v in vencidos}
    plan["repasos_omitidos"] = max(0, len(vencidos) - MAX_REPASOS_RECOMENDADOS)
    for v in vencidos[:MAX_REPASOS_RECOMENDADOS]:
        probs = problemas_de(banco, v["id"], 1, hoy.isoformat(), hechos,
                             perfil_d=perfil_d, nodos=nodos, hoy=hoy)
        plan["repasos"].append({**v, "problemas": probs})

    # 2. Nodos nuevos de la frontera, priorizados por contexto de examen y por
    #    cuántos vencidos repasan implícitamente. El tope es visual, no temporal.
    frontera = motor.frontera(perfil_d, nodos, hoy=hoy)
    if materia_forzada:
        frontera = [c for c in frontera if c.get("materia") == materia_forzada]
    candidatos = []
    for c in frontera:
        if c["materia"] not in urgencia:
            continue
        # Un nodo vencido ya tiene una recomendación de repaso; no debe
        # aparecer además como contenido nuevo en la misma lista.
        if c["id"] in ids_vencidos:
            continue
        ancestros = motor._creditos_ancestros([c["id"]], nodos)
        cubiertos = [a for a in ancestros if a in ids_vencidos]
        puntuacion = urgencia[c["materia"]] * (1 + 0.3 * len(cubiertos))
        candidatos.append((puntuacion, c, cubiertos))
    candidatos.sort(key=lambda x: -x[0])

    ya_cubiertos = set()
    plan["nuevos_omitidos"] = max(0, len(candidatos) - MAX_NUEVOS_RECOMENDADOS)
    for _, c, cubiertos in candidatos[:MAX_NUEVOS_RECOMENDADOS]:
        nodo = nodos[c["id"]]
        probs = problemas_de(banco, c["id"], 3, hoy.isoformat(), hechos,
                             perfil_d=perfil_d, nodos=nodos, hoy=hoy)
        plan["nuevos"].append({**c, "fuentes": fuentes_txt(nodo), "problemas": probs,
                               "cubre": cubiertos})
        ya_cubiertos.update(cubiertos)

    # Vencidos que quedarán repasados implícitamente por las opciones nuevas
    plan["implicitos"] = sorted(ya_cubiertos)

    materias_plan = {materia_forzada} if materia_forzada else set(urgencia)
    practica = kg_problemas.resumen_para_plan(
        perfil_d, nodos, banco, materias=materias_plan or None, hoy=hoy, limite=6
    )
    plan["problemas_listos"] = practica["problemas_listos"]
    plan["problemas_por_materia"] = practica["por_materia"]
    plan["problemas_bloqueados"] = sum(x["bloqueados"] for x in practica["por_materia"])
    plan["debilidades"] = kg_problemas.debilidades(
        perfil_d, nodos, materia=materia_forzada, limite=8
    )
    if plan["problemas_listos"]:
        materias = sorted({p.get("materia", "") for p in plan["problemas_listos"] if p.get("materia")})
        nombres = ", ".join(materias)
        plan["practica"] = {
            "activa": True,
            "mensaje": (
                f"Ya has superado los nodos necesarios de {len(plan['problemas_listos'])} problema(s) "
                f"de {nombres}: toca practicar antes de seguir abriendo teoría nueva."
            ),
            "criterio": "Todos los nodos requeridos tienen dominio efectivo ≥ 0.7.",
        }
    return plan


def render_md(filas_viab, plan, cfg, hoy, minutos):
    """Renderiza directamente el plan actual como nota de Obsidian.

    La información de los exámenes sirve para ordenar prioridades y detectar
    riesgo. El tiempo disponible no limita ni convierte las opciones en tareas.
    """
    cfg = cfg or {}
    repasos = plan.get("repasos", [])
    nuevos = plan.get("nuevos", [])
    implicitos = plan.get("implicitos", [])

    lineas = [
        f"# Recomendaciones de estudio — {hoy.strftime('%d/%m/%Y')}",
        "",
        "## Orientación para hoy",
        "Estas son opciones ordenadas por utilidad probable. Puedes elegir una, varias, cambiar de idea o no hacer ninguna; no hay una cuota que completar.",
        "",
        "## Contexto de exámenes",
        "",
        "| Examen | Fecha | Fase | Riesgo | Pendientes | Estado |",
        "|---|---:|---|---:|---:|---|",
    ]

    if filas_viab:
        for fila in sorted(filas_viab, key=lambda x: x.get("fecha", "")):
            lineas.append(
                f"| {fila.get('materia', '—')} — {fila.get('desc', '')} "
                f"| {fila.get('fecha', '—')} | {fila.get('fase', '—')} "
                f"| {fila.get('riesgo', 0):.0%} | {fila.get('pendientes', 0)}/{fila.get('total', 0)} "
                f"| {'preparado' if fila.get('preparado') else 'en progreso'} |"
            )
    else:
        lineas.append("| No hay exámenes futuros configurados | — | — | — | — | — |")

    listos = plan.get("problemas_listos", [])
    lineas.extend(["", "## Problemas desbloqueados", ""])
    if listos:
        lineas.append(
            f"**{len(listos)} problema(s) ya están preparados:** todos sus nodos requeridos superan el umbral de dominio efectivo."
        )
        for problema in listos:
            req = ", ".join(problema.get("nodos_requeridos", []))
            lineas.append(
                f"- `{problema.get('id', '—')}` — {problema.get('titulo', 'sin título')} "
                f"[{problema.get('materia', '—')}] · nodos: {req}"
            )
    else:
        lineas.append("- Todavía no hay problemas cuyos nodos requeridos estén todos superados.")

    if plan.get("debilidades"):
        lineas.extend(["", "## Retroalimentación acumulada", ""])
        for debilidad in plan["debilidades"][:5]:
            lineas.append(
                f"- **{debilidad['id']} — {debilidad['nombre']}**: "
                f"{debilidad['errores']} error(es), {debilidad['huecos']} hueco(s) teórico(s)."
            )

    lineas.extend(["", "## Opciones de repaso", ""])
    if repasos:
        for repaso in repasos:
            retraso = repaso.get("retraso", 0)
            cuando = "hoy" if retraso == 0 else f"{retraso} días de retraso"
            lineas.append(f"- **{repaso['id']}** — {repaso['nombre']} [{repaso['materia']}] — {cuando}")
            for problema in repaso.get("problemas", []):
                lineas.append(
                    f"    - Problema `{problema.get('id', '—')}`: "
                    f"{problema.get('titulo', 'sin título')} ({problema.get('hoja', 'sin hoja')})"
                )
    else:
        lineas.append("- No hay repasos conceptuales vencidos entre las recomendaciones actuales.")

    lineas.extend(["", "## Opciones de exploración", ""])
    if nuevos:
        for nuevo in nuevos:
            lineas.append(f"- **{nuevo['id']}** — {nuevo['nombre']} [{nuevo['materia']}]")
            if nuevo.get("fuentes"):
                lineas.append(f"    - Fuentes: {nuevo['fuentes']}")
            for problema in nuevo.get("problemas", []):
                lineas.append(
                    f"    - Problema `{problema.get('id', '—')}`: "
                    f"{problema.get('titulo', 'sin título')} ({problema.get('hoja', 'sin hoja')})"
                )
            if not nuevo.get("problemas"):
                lineas.append("    - Sin problema asociado en el banco; estudia la lección y practica un problema del tema.")
    else:
        lineas.append("- No hay conceptos nuevos recomendados ahora.")

    if implicitos:
        lineas.extend([
            "",
            "## Nodos cubiertos implícitamente",
            "",
            f"Al explorar las opciones nuevas también se repasan: {', '.join(implicitos)}.",
        ])

    lineas.extend([
        "",
        "## Cómo usar estas recomendaciones",
        "",
        "Empieza por la opción que mejor encaje con tu estado y con lo que quieras trabajar. Puedes profundizar en un único problema o concepto todo lo que necesites. Cuando termines, registra la calidad real si quieres que el sistema aprenda de la sesión; también puedes narrar la resolución para analizarla con Whisper y Gemini Web.",
        "",
        "---",
        "Este documento contiene recomendaciones, no obligaciones. El estado real vive en el perfil de conocimiento y en los grafos.",
    ])
    return "\n".join(lineas)


def calcular(hoy: date | None = None, minutos: int | None = None, energia: int | None = None, foco: int | None = None, materia_forzada: str | None = None) -> dict:
    """Calcula contexto académico y recomendaciones. API de la CLI y la app web."""
    hoy = hoy or date.today()
    cfg = cargar_json(EXAMENES_PATH, {}) or {}
    if not cfg.get("examenes"):
        raise RuntimeError("No hay exámenes configurados en examenes.json")
    minutos = minutos or cfg.get("minutos_dia", 120)
    cfg["minutos_dia"] = minutos
    cfg.setdefault("min_nodo_nuevo", 40)
    cfg.setdefault("min_repaso", 15)

    nodos = motor.cargar_grafos()
    perfil_d = motor.cargar_perfil()
    banco = cargar_json(BANCO_PATH, {})

    cfg["examenes"] = [normalizar_examen(ex) for ex in cfg["examenes"]]
    filas = viabilidad_academica(nodos, perfil_d, banco, cfg["examenes"], cfg, hoy)
    plan = plan_diario(nodos, perfil_d, banco, filas, cfg, hoy, materia_forzada)
    materias_aprendizaje = {f["materia"] for f in filas if f["fase"] == "aprendizaje"}
    if materias_aprendizaje:
        plan["nuevos"] = [n for n in plan["nuevos"] if n["materia"] in materias_aprendizaje]
    else:
        plan["nuevos"] = []
    plan["fase"] = "aprendizaje" if materias_aprendizaje else (filas[0]["fase"] if filas else "sin_examen")
    plan["recomendacion"] = recomendacion_diaria(filas, hoy, minutos, energia, foco, materia_forzada)
    if plan.get("practica", {}).get("activa"):
        plan["recomendacion"]["accion"] = plan["practica"]["mensaje"]
        plan["recomendacion"]["practica_prioritaria"] = True
        plan["recomendacion"]["problemas_listos"] = len(plan["problemas_listos"])
        plan["recomendacion"]["justificacion"] = (
            "El sistema detecta problemas cuyos requisitos ya están superados. "
            "Haz uno ahora y usa el resultado para decidir qué teoría necesita refuerzo."
        )
    if plan["recomendacion"].get("principal"):
        plan["fase"] = plan["recomendacion"]["principal"]["fase"]
    md = render_md(filas, plan, cfg, hoy, minutos)
    ritmo_total = sum(f["ritmo"] for f in filas)
    # El plan diario se ajusta al tiempo de la sesion, pero la carga agregada
    # de todos los examenes no es un objetivo diario. Se conserva como dato
    # orientativo para estudiar prioridades, nunca como semaforo de fracaso.
    estado = "INFORMATIVO"
    return {"hoy": hoy.isoformat(), "minutos": minutos, "cfg": cfg,
            "viabilidad": filas, "plan": plan, "md": md,
            "recomendacion": plan["recomendacion"],
            "ritmo_total": round(ritmo_total), "estado": estado}


def guardar_plan(md: str) -> str:
    """Escribe el plan como nota en el vault de Obsidian."""
    try:
        sys.path.insert(0, os.path.dirname(DIR))
        import config
        destino = os.path.join(config.VAULT_PATH, "Plan de Estudio.md")
    except Exception:
        destino = os.path.join(DIR, "Plan de Estudio.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(md)
    return destino


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutos", type=int)
    parser.add_argument("--fecha", help="Simular el plan de otro día (YYYY-MM-DD)")
    args = parser.parse_args()

    hoy = datetime.strptime(args.fecha, "%Y-%m-%d").date() if args.fecha else None
    try:
        r = calcular(hoy=hoy, minutos=args.minutos)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print(r["md"])
    if not args.fecha:
        destino = guardar_plan(r["md"])
        print(f"\n[Plan guardado en {destino}]")


PREPARACION_DIAS_DEFAULT = 7
MARGEN_SIMULACRO_DIAS = 3
UMBRAL_PREPARADO = motor.UMBRAL_FRONTERA


def fecha_preparacion(examen: dict) -> date:
    """Fecha desde la que no se prescribe contenido nuevo importante."""
    oficial = datetime.strptime(examen["fecha"], "%Y-%m-%d").date()
    preparada = examen.get("fecha_preparacion")
    if preparada:
        try:
            return datetime.strptime(preparada, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            pass
    return oficial - timedelta(days=PREPARACION_DIAS_DEFAULT)


def fase_examen(examen: dict, hoy: date) -> str:
    oficial = datetime.strptime(examen["fecha"], "%Y-%m-%d").date()
    preparacion = fecha_preparacion(examen)
    if hoy < preparacion:
        return "aprendizaje"
    if hoy < oficial - timedelta(days=MARGEN_SIMULACRO_DIAS):
        return "consolidacion"
    if hoy < oficial:
        return "margen_simulacro"
    return "examen_pasado"


def normalizar_examen(examen: dict) -> dict:
    """Devuelve una copia compatible con configuraciones antiguas."""
    out = dict(examen)
    out["fecha_preparacion"] = fecha_preparacion(out).isoformat()
    out.setdefault("importancia", 1.0)
    try:
        out["importancia"] = max(0.1, min(3.0, float(out["importancia"])))
    except (TypeError, ValueError):
        out["importancia"] = 1.0
    return out


def _objetivo_examen(nodos: dict, examen: dict) -> list[dict]:
    return [n for n in nodos.values()
            if n["materia"] == examen["materia"]
            and (examen.get("temas") is None or n["tema"] in examen["temas"])]


def _importancia_nodo(nodo: dict, examen: dict) -> float:
    """La importancia expl?cita del nodo gana; si no existe, la del examen."""
    valor = nodo.get("importancia", examen.get("importancia", 1.0))
    try:
        return max(0.1, min(3.0, float(valor)))
    except (TypeError, ValueError):
        return 1.0


def _prerrequisitos_duros(ids: set[str], nodos: dict) -> set[str]:
    encontrados = set()
    pendientes = list(ids)
    while pendientes:
        nid = pendientes.pop()
        for prereq in nodos.get(nid, {}).get("prerequisitos", []):
            pid = prereq.get("id")
            if prereq.get("peso", 1.0) < 1.0 or pid not in nodos or pid in encontrados:
                continue
            encontrados.add(pid)
            pendientes.append(pid)
    return encontrados


def _problemas_por_nodo(banco: dict) -> dict[str, list[dict]]:
    salida: dict[str, list[dict]] = {}
    for materia_banco in (banco or {}).values():
        for problema in materia_banco.get("problemas", []):
            for nid in problema.get("nodos", []):
                salida.setdefault(nid, []).append(problema)
    return salida


def estado_preparacion(nodos: dict, perfil_d: dict, banco: dict,
                       examen: dict, hoy: date) -> dict:
    """Criterio operativo explicable; se?ales ausentes no penalizan."""
    objetivos = _objetivo_examen(nodos, examen)
    objetivo_ids = {n["id"] for n in objetivos}
    prereq_ids = _prerrequisitos_duros(objetivo_ids, nodos)
    importantes = [n for n in objetivos if _importancia_nodo(n, examen) >= 1.0]
    if not importantes:
        importantes = objetivos
    imp_ids = {n["id"] for n in importantes}
    conceptos_ok = sum(motor.dominio_efectivo(perfil_d["nodos"].get(nid), hoy) >= UMBRAL_PREPARADO
                       for nid in imp_ids)
    prereq_ok = sum(motor.dominio_efectivo(perfil_d["nodos"].get(nid), hoy) >= UMBRAL_PREPARADO
                    for nid in prereq_ids)
    problemas = _problemas_por_nodo(banco)
    hechos = motor.problemas_hechos(perfil_d)
    con_senal_problema = [nid for nid in imp_ids if problemas.get(nid)]
    problemas_ok = sum(any(hechos.get(p["id"], {}).get("exito") for p in problemas[nid])
                       for nid in con_senal_problema)
    concept_ratio = conceptos_ok / len(imp_ids) if imp_ids else 1.0
    prereq_ratio = prereq_ok / len(prereq_ids) if prereq_ids else 1.0
    problem_ratio = (problemas_ok / len(con_senal_problema)
                     if con_senal_problema else None)
    partes = [(concept_ratio, 0.60), (prereq_ratio, 0.25)]
    if problem_ratio is not None:
        partes.append((problem_ratio, 0.15))
    peso = sum(p for _, p in partes)
    score = sum(valor * p for valor, p in partes) / peso if peso else 0.0
    return {
        "preparado": score >= 0.8 and concept_ratio >= 0.8 and prereq_ratio >= 0.8,
        "score": round(score, 3),
        "conceptos_importantes": len(imp_ids), "conceptos_ok": conceptos_ok,
        "prerequisitos_duros": len(prereq_ids), "prerequisitos_ok": prereq_ok,
        "problemas_con_senal": len(con_senal_problema), "problemas_ok": problemas_ok,
        "problemas_disponibles": bool(con_senal_problema),
        "criterio": ">=80% de conceptos importantes y prerrequisitos dominados; problemas solo cuentan si hay banco y registro.",
    }
def viabilidad_academica(nodos, perfil_d, banco, examenes, cfg, hoy):
    """Evalúa todos los exámenes con señales disponibles y riesgo explicable."""
    filas = []
    for original in examenes:
        # Los hitos provisionales sirven como referencia visual hasta conocer
        # su alcance; no deben meter presión ni tratarse como un examen oficial.
        if original.get("planificar", True) is False:
            continue
        ex = normalizar_examen(original)
        oficial = datetime.strptime(ex["fecha"], "%Y-%m-%d").date()
        if oficial <= hoy:
            continue
        objetivos = _objetivo_examen(nodos, ex)
        estado = estado_preparacion(nodos, perfil_d, banco, ex, hoy)
        pendientes = [n for n in objetivos
                      if motor.dominio_efectivo(perfil_d["nodos"].get(n["id"]), hoy) < motor.UMBRAL_FRONTERA]
        atrasados = [v for v in motor.vencidos(perfil_d, nodos, hoy)
                     if v["materia"] == ex["materia"]
                     and (ex.get("temas") is None or nodos[v["id"]]["tema"] in ex["temas"])]
        prep = datetime.strptime(ex["fecha_preparacion"], "%Y-%m-%d").date()
        dias_preparacion = max(1, (prep - hoy).days)
        dias_oficial = max(1, (oficial - hoy).days)
        carga_nueva = len(pendientes) * cfg["min_nodo_nuevo"] if hoy < prep else 0
        carga_repaso = (len(pendientes) * REPASOS_POR_NODO + len(atrasados)) * cfg["min_repaso"]
        carga = carga_nueva + carga_repaso
        ritmo = carga / dias_preparacion if hoy < prep else carga / dias_oficial
        # La disponibilidad diaria no es una meta ni debe alterar el riesgo
        # academico. El usuario decide el tiempo de cada sesion; la presion
        # aqui se estima por carga pendiente y urgencia del examen.
        presion = min(1.0, len(pendientes) / max(1, len(objetivos)))
        urgencia = min(1.0, 14 / dias_oficial)
        riesgo = min(1.0, 0.30 * presion + 0.50 * (1 - estado["score"]) + 0.20 * urgencia)
        if fase_examen(ex, hoy) in {"consolidacion", "margen_simulacro"}:
            riesgo = min(1.0, riesgo + 0.15 * (1 - estado["score"]))
        fila = {
            "materia": ex["materia"], "fecha": ex["fecha"],
            "fecha_preparacion": ex["fecha_preparacion"],
            "desc": ex.get("descripcion", ""), "temas": ex.get("temas"), "importancia": ex["importancia"],
            "fase": fase_examen(ex, hoy), "preparado": estado["preparado"],
            "preparacion": estado, "pendientes": len(pendientes),
            "total": len(objetivos), "repasos_pendientes": len(atrasados),
            "carga_h": carga / 60, "dias": dias_preparacion if hoy < prep else dias_oficial,
            "ritmo": ritmo, "riesgo": round(riesgo, 3),
            "prioridad_score": round(riesgo * ex["importancia"], 3),
            "reales_sem": round(ritmo_real(perfil_d, nodos, ex["materia"], hoy) * 7, 1),
            "necesarios_sem": round(len(pendientes) / dias_preparacion * 7, 1) if hoy < prep else 0,
            "proyeccion": None, "retraso_dias": None,
        }
        rr = ritmo_real(perfil_d, nodos, ex["materia"], hoy)
        if rr > 0 and pendientes and hoy < prep:
            fin = hoy + timedelta(days=int(len(pendientes) / rr))
            fila["proyeccion"] = fin.isoformat()
            fila["retraso_dias"] = (fin - prep).days
        filas.append(fila)
    return filas


def recomendacion_diaria(filas, hoy: date, minutos: int | None = None,
                         energia: int | None = None, foco: int | None = None,
                         materia_forzada: str | None = None) -> dict:
    """Devuelve sugerencias ordenadas sin convertirlas en obligaciones.

    El parámetro minutos se conserva por compatibilidad con las sesiones
    antiguas, pero no decide qué aparece ni cuánto debe durar una actividad.
    """
    activas = [f for f in filas if f.get("fase") != "examen_pasado"]
    if not activas:
        return {
            "principal": None,
            "mantenimiento": [],
            "accion": "Puedes elegir libremente otra forma de estudiar o cerrar por hoy.",
            "justificacion": "No hay exámenes futuros configurados que generen recomendaciones.",
            "por_que": "",
            "energia": energia,
            "foco": foco,
            "simulacro": None,
            "aceptada": materia_forzada is None,
        }

    puntuadas = []
    for fila in activas:
        orden = fila.get("prioridad_score", 0) + min(
            0.2, fila.get("repasos_pendientes", 0) / 100
        )
        puntuadas.append((orden, fila))

    principal = next(
        (fila for _, fila in puntuadas if fila.get("materia") == materia_forzada),
        None,
    ) if materia_forzada else None
    if principal is None:
        principal = max(puntuadas, key=lambda pareja: pareja[0])[1]

    mantenimiento = [
        fila for _, fila in sorted(puntuadas, key=lambda pareja: -pareja[0])
        if fila.get("materia") != principal.get("materia")
    ][:1]

    energia_baja = energia is not None and energia <= 2
    foco_bajo = foco is not None and foco <= 2
    fase = principal.get("fase")
    if fase == "aprendizaje" and not (energia_baja or foco_bajo):
        accion = f"Podrías explorar contenido de {principal['materia']}."
    elif fase == "aprendizaje":
        accion = f"Podrías quedarte en repaso o prerrequisitos de {principal['materia']} si hoy te resulta más llevadero."
    elif fase == "consolidacion":
        accion = f"Podrías consolidar {principal['materia']} con problemas, explicaciones o revisión de errores."
    else:
        accion = f"Podrías probar un simulacro o un repaso mezclado de {principal['materia']}."

    por_que = (
        f"Esta opción aparece destacada por el riesgo registrado "
        f"({principal.get('riesgo', 0):.0%}), la fecha del examen y los nodos pendientes; "
        "puedes escogerla, combinarla con otra o ignorarla."
    )
    simulacro = None
    if fase in {"consolidacion", "margen_simulacro"}:
        simulacro = {
            "materia": principal["materia"],
            "temas": principal.get("temas"),
            "problemas": 6 if fase == "margen_simulacro" else 4,
        }
    return {
        "principal": {
            k: principal.get(k)
            for k in (
                "materia", "fecha", "fase", "riesgo", "pendientes",
                "repasos_pendientes", "preparado", "temas",
            )
        },
        "mantenimiento": [
            {
                k: fila.get(k)
                for k in ("materia", "fecha", "fase", "riesgo", "pendientes")
            }
            for fila in mantenimiento
        ],
        "accion": accion,
        "justificacion": por_que,
        "por_que": "No hay penalización por elegir otra cosa.",
        "energia": energia,
        "foco": foco,
        "simulacro": simulacro,
        "aceptada": materia_forzada is None,
    }

if __name__ == "__main__":
    main()
