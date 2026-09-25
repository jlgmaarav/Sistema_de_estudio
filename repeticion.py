# -*- coding: utf-8 -*-
"""Contrato común para la repetición de ejercicios.

El calendario académico vive en ``knowledge_graph/perfil.json`` y se calcula
por nodo conceptual. Este módulo solo conserva la parte local del ejercicio:
su estado visible y, cuando procede, un reintento inmediato tras un fallo o
una duda. No genera un segundo calendario académico.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


# La misma escala se usa para actualizar el perfil del grafo y para decidir si
# un ejercicio necesita reintento local.
CALIDAD_POR_RATING = {
    "facil": 1.0,
    "duda": 0.5,
    "fallo": 0.0,
}


def calidad_de_rating(rating: str) -> float:
    """Convierte una valoración de interfaz en calidad 0–1.

    ``ValueError`` evita que una entrada desconocida se convierta
    silenciosamente en un fallo.
    """
    try:
        return CALIDAD_POR_RATING[rating]
    except KeyError as exc:
        raise ValueError("Valoración no válida: usa 'facil', 'duda' o 'fallo'.") from exc


def calidad_de_correccion(resultado: str, tiene_error: bool) -> float:
    """Normaliza el resultado de una corrección automática o narrada."""
    if resultado == "correcto":
        return 0.75 if tiene_error else 1.0
    if resultado == "incompleto":
        return 0.5
    return 0.25


def estado_ejercicio(current_state: str, calidad: float) -> str:
    """Calcula el estado local visible del ejercicio.

    Este estado no sustituye al dominio del nodo: resume la historia del
    ejercicio concreto y sirve para distinguir un reintento de una revisión
    conceptual.
    """
    if calidad < 0.5:
        return "nuevo"
    if calidad < 0.75:
        return "revisado"
    if current_state == "nuevo":
        return "revisado"
    if current_state == "revisado":
        return "dominado"
    return "dominado"


def fecha_reintento(calidad: float, hoy: date | None = None) -> str:
    """Devuelve una fecha DD/MM/YYYY solo para reintentos locales.

    Un ejercicio resuelto con solidez no necesita crear una fecha paralela.
    Las respuestas parciales esperan dos días y los fallos un día.
    """
    hoy = hoy or date.today()
    if calidad >= 0.75:
        return ""
    dias = 2 if calidad >= 0.5 else 1
    return (hoy + timedelta(days=dias)).strftime("%d/%m/%Y")


def parsear_fecha_dmy(valor: str | None) -> date | None:
    """Parsea una fecha visible de ejercicio sin lanzar errores."""
    if not valor:
        return None
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return None


def fecha_reintento_de_ejercicio(ejercicio: dict) -> date | None:
    """Lee la fecha de reintento nueva y, por compatibilidad, la antigua.

    Las fechas antiguas de ``proxima_revision`` no se convierten
    automáticamente en reintentos: pertenecían al calendario antiguo y no
    hay evidencia de que representen un fallo pendiente. Se conservan como
    histórico y solo ``proxima_reintento`` alimenta esta cola.
    """
    return parsear_fecha_dmy(ejercicio.get("proxima_reintento"))


def reintento_pendiente(ejercicio: dict, hoy: date | None = None) -> bool:
    """Indica si hay un reintento local vencido o para hoy."""
    fecha = fecha_reintento_de_ejercicio(ejercicio)
    return fecha is not None and fecha <= (hoy or date.today())
