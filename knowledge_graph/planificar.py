# -*- coding: utf-8 -*-
"""Motor prescriptivo: plan de estudio diario orientado a exámenes.

Planificación hacia atrás desde las fechas de examen (examenes.json):
1. Viabilidad: nodos pendientes por examen × coste por nodo vs días restantes
   → ritmo requerido en min/día por asignatura y semáforo global.
2. Plan de hoy: repasos vencidos + nodos nuevos de la frontera, priorizando
   la asignatura más urgente y los nodos nuevos que repasan implícitamente
   prerrequisitos vencidos. Cada nodo lleva sus problemas del banco y sus
   fuentes de teoría.

Uso:
  python planificar.py                    Plan para hoy
  python planificar.py --minutos 90       Con otro presupuesto de tiempo
  python planificar.py --fecha 2026-10-01 Simular el plan de otro día
"""
import argparse
import hashlib
import json
import math
import os
import sys
from datetime import date, datetime, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import perfil as motor

EXAMENES_PATH = os.path.join(DIR, "examenes.json")
BANCO_PATH = os.path.join(DIR, "banco_problemas.json")
FRACCION_REPASOS = 0.4   # techo del presupuesto diario dedicado a repasos
REPASOS_POR_NODO = 1.5   # repasos medios estimados por nodo hasta el examen
BUFFER_DIAS = 3          # días antes del examen reservados a repaso global


def cargar_json(ruta, defecto=None):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return defecto


def problemas_de(banco: dict, nid: str, cuantos: int, semilla: str,
                 hechos: dict | None = None) -> list[dict]:
    """Problemas del banco para un nodo: primero los nunca hechos, luego los
    más antiguos; entre iguales rota con la semilla del día."""
    hechos = hechos or {}
    encontrados = []
    for materia_banco in (banco or {}).values():
        for p in materia_banco.get("problemas", []):
            if nid in p.get("nodos", []):
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


def viabilidad(nodos, perfil_d, examenes, cfg, hoy):
    """Ritmo requerido por examen y semáforo."""
    filas = []
    for ex in examenes:
        fecha = datetime.strptime(ex["fecha"], "%Y-%m-%d").date()
        if fecha <= hoy:
            continue
        objetivo = [n for n in nodos.values() if n["materia"] == ex["materia"]
                    and (ex.get("temas") is None or n["tema"] in ex["temas"])]
        pendientes = [n for n in objetivo
                      if motor.dominio_efectivo(perfil_d["nodos"].get(n["id"]), hoy) < motor.UMBRAL_FRONTERA]
        carga = len(pendientes) * cfg["min_nodo_nuevo"] + len(pendientes) * REPASOS_POR_NODO * cfg["min_repaso"]
        dias = max(1, (fecha - hoy).days - BUFFER_DIAS)
        ritmo = carga / dias

        # Ritmo real (últimas 2 semanas) y proyección de fin de temario
        rr = ritmo_real(perfil_d, nodos, ex["materia"], hoy)
        necesarios_sem = round(len(pendientes) / dias * 7, 1)
        reales_sem = round(rr * 7, 1)
        proyeccion, retraso_dias = None, None
        if rr > 0 and pendientes:
            fin = hoy + timedelta(days=int(len(pendientes) / rr))
            proyeccion = fin.isoformat()
            retraso_dias = (fin - fecha).days

        filas.append({
            "materia": ex["materia"], "fecha": ex["fecha"], "desc": ex.get("descripcion", ""),
            "pendientes": len(pendientes), "total": len(objetivo),
            "carga_h": carga / 60, "dias": dias, "ritmo": ritmo,
            "reales_sem": reales_sem, "necesarios_sem": necesarios_sem,
            "proyeccion": proyeccion, "retraso_dias": retraso_dias,
        })
    return filas


def plan_diario(nodos, perfil_d, banco, filas_viab, cfg, hoy):
    presupuesto = cfg["minutos_dia"]
    urgencia = {}
    for f in filas_viab:
        urgencia[f["materia"]] = max(urgencia.get(f["materia"], 0), f["ritmo"])

    plan = {"repasos": [], "nuevos": [], "implicitos": []}
    hechos = motor.problemas_hechos(perfil_d)

    # 1. Repasos vencidos (hasta FRACCION_REPASOS del presupuesto)
    vencidos = motor.vencidos(perfil_d, nodos, hoy)
    tope_repaso = presupuesto * FRACCION_REPASOS
    ids_vencidos = {v["id"] for v in vencidos}
    gastado_repaso = 0.0
    pendiente_repaso = []
    for v in vencidos:
        if gastado_repaso + cfg["min_repaso"] <= tope_repaso:
            probs = problemas_de(banco, v["id"], 1, hoy.isoformat(), hechos)
            plan["repasos"].append({**v, "problemas": probs, "min": cfg["min_repaso"]})
            gastado_repaso += cfg["min_repaso"]
        else:
            pendiente_repaso.append(v)
    presupuesto -= gastado_repaso

    # 2. Nodos nuevos de la frontera, priorizados por urgencia de examen
    #    y por cuántos vencidos repasan implícitamente
    frontera = motor.frontera(perfil_d, nodos, hoy=hoy)
    candidatos = []
    for c in frontera:
        if c["materia"] not in urgencia:
            continue
        ancestros = motor._creditos_ancestros([c["id"]], nodos)
        cubiertos = [a for a in ancestros if a in ids_vencidos]
        puntuacion = urgencia[c["materia"]] * (1 + 0.3 * len(cubiertos))
        candidatos.append((puntuacion, c, cubiertos))
    candidatos.sort(key=lambda x: -x[0])

    ya_cubiertos = set()
    for _, c, cubiertos in candidatos:
        if presupuesto < cfg["min_nodo_nuevo"]:
            break
        nodo = nodos[c["id"]]
        probs = problemas_de(banco, c["id"], 3, hoy.isoformat(), hechos)
        plan["nuevos"].append({**c, "fuentes": fuentes_txt(nodo), "problemas": probs,
                               "min": cfg["min_nodo_nuevo"], "cubre": cubiertos})
        ya_cubiertos.update(cubiertos)
        presupuesto -= cfg["min_nodo_nuevo"]

    # Vencidos que quedarán repasados implícitamente por los nodos nuevos de hoy
    plan["implicitos"] = sorted(ya_cubiertos)
    plan["sobrante"] = presupuesto
    return plan


def render_md(filas_viab, plan, cfg, hoy, minutos):
    lineas = [f"# Plan de estudio — {hoy.strftime('%d/%m/%Y')}", ""]
    lineas.append(f"Presupuesto: **{minutos} min** · lección nueva ≈ {cfg['min_nodo_nuevo']} min · repaso ≈ {cfg['min_repaso']} min")
    lineas.append("")

    lineas.append("## ¿Llego a los exámenes?")
    lineas.append("")
    lineas.append("| Examen | Fecha | Nodos pendientes | Carga restante | Ritmo necesario | Real vs necesario |")
    lineas.append("|---|---|---|---|---|---|")
    total_ritmo = 0.0
    for f in sorted(filas_viab, key=lambda x: x["fecha"]):
        total_ritmo += f["ritmo"]
        if f.get("proyeccion") and f.get("retraso_dias", 0) > 0:
            real = f"⚠ {f['reales_sem']} vs {f['necesarios_sem']} nodos/sem → acabarías el {f['proyeccion']} ({f['retraso_dias']} días tarde)"
        elif f.get("reales_sem", 0) > 0:
            real = f"✓ {f['reales_sem']} vs {f['necesarios_sem']} nodos/sem"
        else:
            real = f"— sin actividad aún (necesitas {f['necesarios_sem']} nodos/sem)"
        lineas.append(f"| {f['materia']} — {f['desc']} | {f['fecha']} | {f['pendientes']}/{f['total']} "
                      f"| {f['carga_h']:.0f} h | {f['ritmo']:.0f} min/día | {real} |")
    estado = "✅ HOLGADO" if total_ritmo <= minutos * 0.7 else ("🟡 AJUSTADO" if total_ritmo <= minutos else "🔴 INSUFICIENTE")
    lineas.append("")
    lineas.append(f"**Ritmo total requerido: {total_ritmo:.0f} min/día frente a {minutos} disponibles → {estado}**")
    if total_ritmo > minutos:
        lineas.append(f"*(faltan {total_ritmo - minutos:.0f} min/día: sube el presupuesto, adelanta el inicio o recorta temario en examenes.json)*")
    lineas.append("")

    if plan["repasos"]:
        lineas.append(f"## Repasos de hoy ({len(plan['repasos'])})")
        lineas.append("")
        for r in plan["repasos"]:
            lineas.append(f"- [ ] **{r['id']}** {r['nombre']} — {r['retraso']} días de retraso")
            for p in r["problemas"]:
                lineas.append(f"    - Problema {p['id']}: {p['titulo']} ({p['hoja']})")
        lineas.append("")

    lineas.append(f"## Lecciones nuevas de hoy ({len(plan['nuevos'])})")
    lineas.append("")
    for n in plan["nuevos"]:
        lineas.append(f"- [ ] **{n['id']}** [{n['materia']}] {n['nombre']}")
        if n["fuentes"]:
            lineas.append(f"    - Teoría: {n['fuentes']}")
        for p in n["problemas"]:
            lineas.append(f"    - Problema {p['id']}: {p['titulo']} ({p['hoja']})")
        if not n["problemas"]:
            lineas.append("    - (Sin problemas en el banco: estudia la teoría y usa un problema del tema)")
        if n["cubre"]:
            lineas.append(f"    - Repasa implícitamente: {', '.join(n['cubre'])}")
    lineas.append("")
    if plan["implicitos"]:
        lineas.append(f"*Repasados implícitamente al hacer las lecciones de hoy: {', '.join(plan['implicitos'])}*")
        lineas.append("")
    lineas.append("---")
    lineas.append("Al terminar cada nodo: sube tu intento al Inbox (se registra solo) o `python knowledge_graph/perfil.py registrar <id>`.")
    return "\n".join(lineas)


def calcular(hoy: date | None = None, minutos: int | None = None) -> dict:
    """Calcula viabilidad y plan del día. API usada por CLI y por la app web."""
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

    filas = viabilidad(nodos, perfil_d, cfg["examenes"], cfg, hoy)
    plan = plan_diario(nodos, perfil_d, banco, filas, cfg, hoy)
    md = render_md(filas, plan, cfg, hoy, minutos)
    ritmo_total = sum(f["ritmo"] for f in filas)
    estado = "HOLGADO" if ritmo_total <= minutos * 0.7 else ("AJUSTADO" if ritmo_total <= minutos else "INSUFICIENTE")
    return {"hoy": hoy.isoformat(), "minutos": minutos, "cfg": cfg,
            "viabilidad": filas, "plan": plan, "md": md,
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


if __name__ == "__main__":
    main()
