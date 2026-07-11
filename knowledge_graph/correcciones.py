# -*- coding: utf-8 -*-
"""Almacén de correcciones para verlas en la app web (no en Obsidian).

Cada vez que Gemini corrige un ejercicio (vía watcher o CLI), se guarda aquí una
entrada estructurada: qué problema es, el veredicto, un resumen directo de qué
está bien y qué está mal, y los errores con su corrección en LaTeX. La app web
las muestra en la vista "Correcciones"; Obsidian queda solo como registro.
"""
import json
import os
import uuid
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(DIR, "correcciones.json")
MAX_ENTRADAS = 200


def cargar() -> list:
    if os.path.exists(RUTA):
        try:
            with open(RUTA, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def guardar(entradas: list) -> None:
    """Persiste la lista (más reciente primero), recortada a MAX_ENTRADAS."""
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(entradas[:MAX_ENTRADAS], f, ensure_ascii=False, indent=1)


def registrar(entrada: dict) -> None:
    """Añade una corrección al principio (más reciente primero) y persiste."""
    entrada.setdefault("id", uuid.uuid4().hex[:12])
    entrada.setdefault("fecha", datetime.now().isoformat(timespec="seconds"))
    entradas = cargar()
    entradas.insert(0, entrada)
    guardar(entradas)


def registrar_desde_respuesta(response, *, exerc_id="", asignatura="", tema="",
                              calidad=None, asset="", reverso=None,
                              modelo="", es_fallback=False) -> dict:
    """Construye y guarda una entrada de corrección a partir de la respuesta de
    Gemini (schemas.AnalysisResponse). `reverso` (opcional) permite deshacer el
    efecto en el perfil si la corrección fue equivocada. Devuelve la entrada."""
    errores = []
    for e in getattr(response, "errores", []) or []:
        errores.append({
            "titulo": getattr(e, "titulo", ""),
            "tipo": getattr(e, "tipo_error", []) or [],
            "descripcion": getattr(e, "descripcion", ""),
            "incorrecto": getattr(e, "ejemplo_incorrecto", ""),
            "correcto": getattr(e, "ejemplo_correcto", ""),
            "como_evitarlo": getattr(e, "como_evitarlo", ""),
        })
    entrada = {
        "id": uuid.uuid4().hex[:12],
        "exerc_id": exerc_id,
        "asignatura": asignatura or getattr(response, "asignatura_detectada", ""),
        "tema": tema or getattr(response, "tema_detectado", ""),
        "codigo": getattr(response, "codigo_problema", "") or "",
        "titulo": getattr(response, "titulo_corto", ""),
        "enunciado": getattr(response, "transcripcion_enunciado", ""),
        "manuscrito": getattr(response, "transcripcion_manuscrito", "") or "",
        "resultado": getattr(response, "resultado", ""),
        "tiene_error": bool(getattr(response, "tiene_error", False)),
        "resumen": getattr(response, "resumen_correccion", "") or "",
        "analisis": getattr(response, "analisis_detallado", ""),
        "errores": errores,
        "calidad": calidad,
        "asset": asset,
        "confianza": getattr(response, "confianza_analisis", None),
        "modelo": modelo or "",
        "es_fallback": bool(es_fallback),
        "motivo_baja_confianza": getattr(response, "motivo_baja_confianza", "") or "",
        "dudas": bool(getattr(response, "dudas_transcripcion", False)),
        "mensaje_duda": getattr(response, "mensaje_duda", "") or "",
        "reverso": reverso,
    }
    registrar(entrada)
    return entrada


def revertir(corr_id: str) -> dict:
    """Marca una corrección como "mal corregida": deshace su efecto en el perfil
    del knowledge graph (si tiene `reverso`) y la elimina de la lista.
    Devuelve {'revertido': bool, 'encontrado': bool}."""
    entradas = cargar()
    idx = next((i for i, e in enumerate(entradas) if e.get("id") == corr_id), None)
    if idx is None:
        return {"encontrado": False, "revertido": False}
    entrada = entradas[idx]
    revertido = False
    reverso = entrada.get("reverso")
    if reverso:
        try:
            import perfil as kg_perfil
        except Exception:
            import sys
            sys.path.insert(0, DIR)
            import perfil as kg_perfil
        revertido = bool(kg_perfil.revertir_reverso(reverso))
    del entradas[idx]
    guardar(entradas)
    return {"encontrado": True, "revertido": revertido}
