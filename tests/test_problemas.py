import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_graph"))
import auditar_electronica
import perfil as motor
import problemas


HOY = date(2026, 9, 15)


def nodo(nid, dominio=0.0):
    return {
        "id": nid, "nombre": nid.upper(), "materia": "Test", "tema": 1,
        "curso": 1, "prerequisitos": [], "dominio": dominio,
    }


def perfil_con(*ids):
    perfil = {"actualizado": None, "nodos": {}, "problemas": {}}
    for nid in ids:
        perfil["nodos"][nid] = dict(
            motor._entrada_nueva(), dominio=0.8, intervalo=30,
            proxima=(HOY + timedelta(days=30)).isoformat(),
        )
    return perfil


def banco_un_problema():
    return {"Test": {"problemas": [{
        "id": "P-1", "materia": "Test", "num_tema": 1,
        "titulo": "Problema de prueba", "enunciado": "...",
        "nodos": ["a", "b"], "nodos_requeridos": ["a", "b"],
    }]}}


def test_problema_solo_esta_listo_si_supera_todos_los_nodos():
    nodos = {"a": nodo("a"), "b": nodo("b")}
    perfil = perfil_con("a")
    estado = problemas.estado_banco(perfil, nodos, banco_un_problema(), hoy=HOY)
    assert estado["listos"] == 0
    assert estado["problemas_bloqueados"][0]["faltantes"][0]["id"] == "b"

    perfil["nodos"]["b"] = dict(
        motor._entrada_nueva(), dominio=0.8, intervalo=30,
        proxima=(HOY + timedelta(days=30)).isoformat(),
    )
    estado = problemas.estado_banco(perfil, nodos, banco_un_problema(), hoy=HOY)
    assert estado["listos"] == 1
    assert estado["problemas_listos"][0]["criterio_preparacion"] == "todos_los_nodos_superados"


def test_hueco_teorico_conserva_el_avance_y_baja_el_nodo_focal():
    nodos = {"a": nodo("a"), "b": nodo("b")}
    perfil = perfil_con("a", "b")
    resultado = problemas.registrar_feedback(
        perfil, nodos, banco_un_problema(), "P-1",
        veredicto="hueco_teorico", nodos_hueco=["b"], fecha=HOY,
    )
    assert resultado["problema"]["ultimo_resultado"]["veredicto"] == "hueco_teorico"
    assert perfil["nodos"]["a"]["dominio"] > perfil["nodos"]["b"]["dominio"]
    assert perfil["nodos"]["b"]["proxima"] == (HOY + timedelta(days=1)).isoformat()
    assert perfil["retroalimentacion"][0]["nodos_hueco_teorico"] == ["b"]


def test_fallo_sin_localizar_se_reparte_en_todos_los_requisitos():
    nodos = {"a": nodo("a"), "b": nodo("b")}
    perfil = perfil_con("a", "b")
    problemas.registrar_feedback(
        perfil, nodos, banco_un_problema(), "P-1",
        veredicto="incorrecto", fecha=HOY,
    )
    debilidades = problemas.debilidades(perfil, nodos, materia="Test")
    assert {x["id"] for x in debilidades} == {"a", "b"}
    assert all(x["errores"] == 1 for x in debilidades)


def test_auditoria_de_electronica_cubre_todos_los_problemas_y_nodos():
    base = os.path.join(os.path.dirname(__file__), "..", "knowledge_graph")
    graph = json.load(open(os.path.join(base, "electronica.json"), encoding="utf-8"))
    bank = json.load(open(os.path.join(base, "banco_problemas.json"), encoding="utf-8"))
    ids = {n["id"] for n in graph["nodos"]}
    problemas_e = bank["Electrónica"]["problemas"]
    assert len(graph["nodos"]) == 46
    expected_ids = set(auditar_electronica.CLASIFICACION)
    expected_ids.update(item["id"] for item in auditar_electronica.EXAMENES_EXTRA)
    assert {p["id"] for p in problemas_e} == expected_ids
    assert len(problemas_e) == len(expected_ids) == 160
    assert all(p.get("nodos_requeridos") for p in problemas_e)
    assert all(set(p["nodos_requeridos"]) <= ids for p in problemas_e)
    assert bank["Electrónica"]["auditoria"]["estado"] == "completa"
