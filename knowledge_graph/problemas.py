# -*- coding: utf-8 -*-
"""Preparación y retroalimentación de problemas del banco.

Un problema no se considera preparado por pertenecer a un tema: se considera
preparado cuando todos sus nodos requeridos tienen dominio efectivo suficiente.
El módulo mantiene esa regla separada del motor de dominio para que el banco
pueda crecer sin duplicar lógica en la interfaz.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date

import perfil as motor

DIR = os.path.dirname(os.path.abspath(__file__))
BANCO_PATH = os.path.join(DIR, "banco_problemas.json")
UMBRAL_PROBLEMA = motor.UMBRAL_FRONTERA
MAX_RETROALIMENTACION = 500

VEREDICTOS = {
    "resuelto": {"calidad": 1.0, "etiqueta": "Perfecto"},
    "hueco_teorico": {"calidad": 0.75, "etiqueta": "Bien, pero con hueco teórico"},
    "incorrecto": {"calidad": 0.25, "etiqueta": "Mal: revisar el error"},
}


def cargar_banco(ruta: str = BANCO_PATH) -> dict:
    if not os.path.exists(ruta):
        return {}
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def iterar_problemas(banco: dict):
    for materia, bloque in (banco or {}).items():
        for problema in bloque.get("problemas", []):
            yield materia, problema


def buscar_problema(banco: dict, problema_id: str) -> tuple[str | None, dict | None]:
    for materia, problema in iterar_problemas(banco):
        if problema.get("id") == problema_id:
            return materia, problema
    return None, None


def nodos_requeridos(problema: dict) -> list[str]:
    """Lee el nombre nuevo y conserva compatibilidad con el banco anterior."""
    ids = problema.get("nodos_requeridos") or problema.get("nodos") or []
    salida = []
    for nid in ids:
        if nid and nid not in salida:
            salida.append(nid)
    return salida


def evaluar_problema(problema: dict, perfil: dict, nodos: dict,
                     hoy: date | None = None, umbral: float = UMBRAL_PROBLEMA) -> dict:
    """Devuelve el semáforo explicable de un problema."""
    hoy = hoy or date.today()
    ids = nodos_requeridos(problema)
    evidencias = []
    for nid in ids:
        entrada = perfil.get("nodos", {}).get(nid)
        dominio = motor.dominio_efectivo(entrada, hoy)
        evidencias.append({
            "id": nid,
            "nombre": nodos.get(nid, {}).get("nombre", nid),
            "dominio": round(dominio, 3),
            "superado": dominio >= umbral,
            "conocido": nid in nodos,
        })
    faltantes = [e for e in evidencias if not e["superado"] or not e["conocido"]]
    hechos = motor.problemas_hechos(perfil)
    ultimo = hechos.get(problema.get("id"))
    listo = bool(ids) and not faltantes
    return {
        **problema,
        "nodos_requeridos": ids,
        "criterio_preparacion": "todos_los_nodos_superados",
        "umbral_dominio": umbral,
        "listo": listo,
        "estado_preparacion": "listo" if listo else "bloqueado",
        "porcentaje_nodos_superados": round(
            sum(e["superado"] and e["conocido"] for e in evidencias) / len(evidencias), 3
        ) if evidencias else 0.0,
        "nodos_estado": evidencias,
        "faltantes": faltantes,
        "ultimo_resultado": ultimo,
        "hecho": bool(ultimo),
    }


def problemas_de_materia(banco: dict, materia: str | None = None) -> list[dict]:
    return [p for m, p in iterar_problemas(banco) if materia is None or m == materia]


def estado_banco(perfil: dict, nodos: dict, banco: dict,
                 materia: str | None = None, hoy: date | None = None,
                 limite: int | None = None) -> dict:
    """Resumen completo para la API y el planificador."""
    hoy = hoy or date.today()
    evaluados = [evaluar_problema(p, perfil, nodos, hoy)
                 for p in problemas_de_materia(banco, materia)]

    def orden(p):
        r = p.get("ultimo_resultado") or {}
        # Primero los que se pueden hacer y aún no tienen un intento sólido.
        resuelto = r.get("veredicto") == "resuelto"
        return (0 if p["listo"] else 1, 1 if resuelto else 0,
                r.get("fecha", ""), p.get("id", ""))

    listos = sorted((p for p in evaluados if p["listo"]), key=orden)
    bloqueados = sorted((p for p in evaluados if not p["listo"]),
                        key=lambda p: (-len(p["faltantes"]), p.get("id", "")))
    salida = {
        "materia": materia,
        "total": len(evaluados),
        "listos": len(listos),
        "bloqueados": len(bloqueados),
        "problemas_listos": listos[:limite] if limite else listos,
        "problemas_bloqueados": bloqueados[:limite] if limite else bloqueados,
        "criterio": f"Todos los nodos requeridos con dominio efectivo >= {UMBRAL_PROBLEMA:.1f}",
    }
    return salida


def resumen_para_plan(perfil: dict, nodos: dict, banco: dict,
                      materias: set[str] | None = None,
                      hoy: date | None = None, limite: int = 6) -> dict:
    """Devuelve problemas listos y un pequeño mapa de bloqueos por asignatura."""
    hoy = hoy or date.today()
    materias_banco = {m for m, _ in iterar_problemas(banco)}
    if materias:
        materias_banco &= set(materias)
    listos = []
    resumenes = []
    for materia in sorted(materias_banco):
        estado = estado_banco(perfil, nodos, banco, materia, hoy)
        resumenes.append({
            "materia": materia,
            "total": estado["total"],
            "listos": estado["listos"],
            "bloqueados": estado["bloqueados"],
        })
        listos.extend(estado["problemas_listos"])
    return {
        "problemas_listos": listos[:limite],
        "por_materia": resumenes,
        "total_listos": len(listos),
    }


def _normalizar_veredicto(veredicto: str | None, calidad: float | None = None) -> str:
    if veredicto in VEREDICTOS:
        return veredicto
    if calidad is not None:
        if calidad >= 0.9:
            return "resuelto"
        if calidad >= 0.5:
            return "hueco_teorico"
        return "incorrecto"
    return "resuelto"


def registrar_evento_retroalimentacion(perfil: dict, *, problema_id: str | None,
                                       materia: str, veredicto: str,
                                       calidad: float, nodos_requeridos: list[str],
                                       nodos_hueco: list[str] | None = None,
                                       nodos_error: list[str] | None = None,
                                       comentarios: str = "",
                                       fecha: date | None = None,
                                       origen: str = "") -> dict:
    """Guarda el diagnóstico histórico sin sustituir el historial del dominio."""
    fecha = fecha or date.today()
    evento = {
        "id": hashlib.sha1(
            f"{problema_id}|{materia}|{fecha.isoformat()}|{len(perfil.get('retroalimentacion', []))}".encode()
        ).hexdigest()[:12],
        "fecha": fecha.isoformat(),
        "problema_id": problema_id,
        "materia": materia,
        "veredicto": veredicto,
        "calidad": round(calidad, 2),
        "nodos_requeridos": list(nodos_requeridos),
        "nodos_hueco_teorico": list(nodos_hueco or []),
        "nodos_error": list(nodos_error or []),
        "comentarios": comentarios or "",
        "origen": origen or "",
    }
    historial = perfil.setdefault("retroalimentacion", [])
    historial.insert(0, evento)
    del historial[MAX_RETROALIMENTACION:]
    return evento


def registrar_feedback(perfil: dict, nodos: dict, banco: dict, problema_id: str,
                       *, veredicto: str | None = None, calidad: float | None = None,
                       nodos_hueco: list[str] | None = None,
                       nodos_error: list[str] | None = None,
                       comentarios: str = "", segundos: float | None = None,
                       fecha: date | None = None, origen: str = "web") -> dict:
    """Aplica un resultado global y devuelve el estado actualizado del problema.

    Un hueco teórico es un intento esencialmente resuelto (0.75) pero los nodos
    marcados como hueco/error reciben además una práctica fallida conservadora,
    que los devuelve a repaso. Así se conserva lo aprendido y se aísla la base
    que necesita trabajo.
    """
    fecha = fecha or date.today()
    materia, problema = buscar_problema(banco, problema_id)
    if problema is None:
        raise KeyError(f"No existe el problema {problema_id!r} en el banco")
    ids = nodos_requeridos(problema)
    veredicto = _normalizar_veredicto(veredicto, calidad)
    calidad_real = VEREDICTOS[veredicto]["calidad"]
    validos = [nid for nid in ids if nid in nodos]
    mensajes = motor.aplicar_practica(
        perfil, nodos, validos, calidad_real >= motor.UMBRAL_EXITO_CALIDAD,
        fecha=fecha, origen=f"problema:{problema_id}", segundos=segundos,
        calidad=calidad_real,
    )
    huecos = [nid for nid in (nodos_hueco or []) if nid in validos]
    errores = [nid for nid in (nodos_error or []) if nid in validos]
    if veredicto == "hueco_teorico":
        # Un fallo focalizado no borra el avance del resto del problema.
        focales = list(dict.fromkeys(huecos + errores))
        if focales:
            motor.aplicar_practica(
                perfil, nodos, focales, False,
                fecha=fecha, origen=f"hueco:{problema_id}", calidad=motor.CALIDAD["bloqueado"],
            )
    elif veredicto == "incorrecto" and errores and set(errores) != set(validos):
        # El intento global ya baja todos los requisitos; esto deja constancia
        # de los nodos donde el error fue realmente localizado.
        pass

    exito = calidad_real >= motor.UMBRAL_EXITO_CALIDAD
    motor.marcar_problema(
        perfil, problema_id, exito, fecha=fecha, calidad=calidad_real,
        veredicto=veredicto, nodos_requeridos=validos,
        nodos_hueco=huecos, nodos_error=errores, comentarios=comentarios,
    )
    evento = registrar_evento_retroalimentacion(
        perfil, problema_id=problema_id, materia=materia or problema.get("materia", ""),
        veredicto=veredicto, calidad=calidad_real, nodos_requeridos=validos,
        nodos_hueco=huecos, nodos_error=errores, comentarios=comentarios,
        fecha=fecha, origen=origen,
    )
    estado = evaluar_problema(problema, perfil, nodos, fecha)
    return {"problema": estado, "mensajes": mensajes, "evento": evento}


def debilidades(perfil: dict, nodos: dict, materia: str | None = None,
                limite: int = 12) -> list[dict]:
    """Cuenta errores y huecos por nodo para que el plan sea retroalimentativo."""
    cuenta: dict[str, dict] = {}
    for evento in perfil.get("retroalimentacion", []):
        if materia and evento.get("materia") != materia:
            continue
        for nid in evento.get("nodos_hueco_teorico", []):
            x = cuenta.setdefault(nid, {"id": nid, "huecos": 0, "errores": 0, "intentos": 0})
            x["huecos"] += 1
            x["intentos"] += 1
        for nid in evento.get("nodos_error", []):
            x = cuenta.setdefault(nid, {"id": nid, "huecos": 0, "errores": 0, "intentos": 0})
            x["errores"] += 1
            x["intentos"] += 1
        event_nodes = (set(evento.get("nodos_hueco_teorico", []))
                       | set(evento.get("nodos_error", [])))
        if evento.get("veredicto") == "incorrecto" and not event_nodes:
            for nid in evento.get("nodos_requeridos", []):
                x = cuenta.setdefault(nid, {"id": nid, "huecos": 0, "errores": 0, "intentos": 0})
                x["errores"] += 1
                x["intentos"] += 1
    salida = []
    for nid, x in cuenta.items():
        x["nombre"] = nodos.get(nid, {}).get("nombre", nid)
        x["materia"] = nodos.get(nid, {}).get("materia", materia or "")
        x["prioridad"] = x["errores"] * 2 + x["huecos"]
        salida.append(x)
    salida.sort(key=lambda x: (-x["prioridad"], -x["intentos"], x["id"]))
    return salida[:limite]
