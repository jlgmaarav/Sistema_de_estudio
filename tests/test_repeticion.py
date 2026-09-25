"""Pruebas del contrato único entre ejercicios y repasos académicos."""

import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "knowledge_graph"))

import repeticion  # noqa: E402
import perfil as motor  # noqa: E402


def _nodo(nid, materia="Test"):
    return {
        "id": nid,
        "nombre": f"Concepto {nid}",
        "materia": materia,
        "curso": 4,
        "prerequisitos": [],
    }


def test_rating_y_reintento_no_crean_calendario_academico():
    assert repeticion.calidad_de_rating("facil") == 1.0
    assert repeticion.calidad_de_rating("duda") == 0.5
    assert repeticion.calidad_de_rating("fallo") == 0.0
    assert repeticion.fecha_reintento(1.0, date(2026, 9, 13)) == ""
    assert repeticion.fecha_reintento(0.5, date(2026, 9, 13)) == "15/09/2026"
    assert repeticion.fecha_reintento(0.0, date(2026, 9, 13)) == "14/09/2026"


def test_fecha_antigua_no_se_convierte_en_reintento_local():
    ejercicio = {"proxima_revision_legacy": "13/09/2026"}
    assert not repeticion.reintento_pendiente(ejercicio, date(2026, 9, 13))
    assert not repeticion.reintento_pendiente(
        {"proxima_reintento": "14/09/2026"}, date(2026, 9, 13)
    )


def test_pendientes_repaso_incluye_hoy_y_no_ejercicios_sin_dominio():
    hoy = date(2026, 9, 13)
    nodos = {"a": _nodo("a"), "b": _nodo("b")}
    perfil = {"actualizado": None, "nodos": {
        "a": dict(motor._entrada_nueva(), dominio=0.8,
                   proxima=hoy.isoformat(), intervalo=7),
        "b": dict(motor._entrada_nueva(), dominio=0.0,
                   proxima=(hoy - timedelta(days=2)).isoformat(), intervalo=7),
    }}
    pendientes = motor.pendientes_repaso(perfil, nodos, hoy)
    assert [x["id"] for x in pendientes] == ["a"]
    assert pendientes[0]["retraso"] == 0
