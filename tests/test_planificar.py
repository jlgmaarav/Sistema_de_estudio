import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_graph"))
import planificar


def nodo(nid, materia="A", tema=1, prerequisitos=None):
    return {
        "id": nid, "nombre": nid, "materia": materia, "tema": tema,
        "prerequisitos": prerequisitos or [],
    }


def perfil_vacio():
    return {"actualizado": None, "nodos": {}}


def test_fecha_preparacion_default_and_override():
    assert planificar.normalizar_examen({"fecha": "2027-01-11"})["fecha_preparacion"] == "2027-01-04"
    assert planificar.normalizar_examen({
        "fecha": "2027-01-11", "fecha_preparacion": "2026-12-20"
    })["fecha_preparacion"] == "2026-12-20"


def test_fases_aprendizaje_consolidacion_y_margen():
    examen = {"fecha": "2027-01-11", "fecha_preparacion": "2027-01-04"}
    assert planificar.fase_examen(examen, date(2027, 1, 3)) == "aprendizaje"
    assert planificar.fase_examen(examen, date(2027, 1, 5)) == "consolidacion"
    assert planificar.fase_examen(examen, date(2027, 1, 9)) == "margen_simulacro"


def test_preparacion_no_penaliza_si_no_hay_banco_de_problemas():
    nodos = {
        "a": nodo("a"),
        "b": nodo("b", prerequisitos=[{"id": "a", "peso": 1.0}]),
    }
    perfil = perfil_vacio()
    perfil["nodos"]["a"] = {"dominio": 0.8, "intervalo": 30, "proxima": "2027-01-30"}
    perfil["nodos"]["b"] = {"dominio": 0.8, "intervalo": 30, "proxima": "2027-01-30"}
    estado = planificar.estado_preparacion(
        nodos, perfil, {}, {"materia": "A", "fecha": "2027-02-01"}, date(2027, 1, 20)
    )
    assert estado["preparado"] is True
    assert estado["problemas_disponibles"] is False


def test_recomendacion_prioriza_riesgo_y_permita_cambio():
    filas = [
        {"materia": "A", "fecha": "2027-01-10", "fase": "aprendizaje",
         "riesgo": 0.8, "prioridad_score": 0.8, "pendientes": 4,
         "repasos_pendientes": 2, "preparado": False, "importancia": 1.0},
        {"materia": "B", "fecha": "2027-02-10", "fase": "aprendizaje",
         "riesgo": 0.2, "prioridad_score": 0.2, "pendientes": 8,
         "repasos_pendientes": 0, "preparado": False, "importancia": 1.0},
    ]
    rec = planificar.recomendacion_diaria(filas, date(2026, 12, 1), 120)
    assert rec["principal"]["materia"] == "A"
    forced = planificar.recomendacion_diaria(filas, date(2026, 12, 1), 120, materia_forzada="B")
    assert forced["principal"]["materia"] == "B"
    assert forced["aceptada"] is False


def test_viabilidad_academica_expone_riesgo_y_preparacion():
    nodos = {"a": nodo("a", materia="A")}
    cfg = {"minutos_dia": 120, "min_nodo_nuevo": 40, "min_repaso": 15}
    filas = planificar.viabilidad_academica(
        nodos, perfil_vacio(), {}, [{"materia": "A", "fecha": "2027-02-01"}],
        cfg, date(2027, 1, 1)
    )
    assert filas[0]["fecha_preparacion"] == "2027-01-25"
    assert filas[0]["fase"] == "aprendizaje"
    assert 0 <= filas[0]["riesgo"] <= 1
    assert filas[0]["preparado"] is False


def test_recomendacion_prepara_simulacro_en_margen():
    filas = [{"materia": "A", "fecha": "2027-01-10", "fase": "margen_simulacro",
              "riesgo": 0.6, "prioridad_score": 0.6, "pendientes": 1,
              "repasos_pendientes": 0, "preparado": False, "importancia": 1.0,
              "temas": [1, 2]}]
    rec = planificar.recomendacion_diaria(filas, date(2027, 1, 8), 150)
    assert rec["simulacro"] == {"materia": "A", "temas": [1, 2], "problemas": 6}
    assert "obligación" not in rec["justificacion"].lower()
    assert "por_que" in rec


def test_recomendaciones_no_dependen_del_tiempo_ni_crean_sobrante(monkeypatch):
    nodos = {"a": nodo("a")}
    perfil = perfil_vacio()
    frontera = [{"id": "a", "nombre": "a", "materia": "A", "tema": 1}]
    monkeypatch.setattr(planificar.motor, "problemas_hechos", lambda _: {})
    monkeypatch.setattr(planificar.motor, "vencidos", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(planificar.motor, "frontera", lambda *_args, **_kwargs: frontera)
    monkeypatch.setattr(planificar.motor, "_creditos_ancestros", lambda *_args, **_kwargs: set())
    filas = [{"materia": "A", "riesgo": 0.8, "prioridad_score": 0.8}]

    corto = planificar.plan_diario(
        nodos, perfil, {}, filas, {"minutos_dia": 5, "min_nodo_nuevo": 40, "min_repaso": 15}, date(2027, 1, 1)
    )
    largo = planificar.plan_diario(
        nodos, perfil, {}, filas, {"minutos_dia": 600, "min_nodo_nuevo": 40, "min_repaso": 15}, date(2027, 1, 1)
    )

    assert [x["id"] for x in corto["nuevos"]] == ["a"]
    assert [x["id"] for x in corto["nuevos"]] == [x["id"] for x in largo["nuevos"]]
    assert corto["modo"] == "recomendaciones"
    assert "sobrante" not in corto
    assert "min" not in corto["nuevos"][0]


def test_plan_forzado_filtra_repasos_y_nuevos_por_asignatura(monkeypatch):
    nodos = {"a": nodo("a", materia="A"), "b": nodo("b", materia="B")}
    frontera = [
        {"id": "a", "nombre": "a", "materia": "A", "tema": 1},
        {"id": "b", "nombre": "b", "materia": "B", "tema": 1},
    ]
    vencidos = [
        {"id": "a", "nombre": "a", "materia": "A", "retraso": 2},
        {"id": "b", "nombre": "b", "materia": "B", "retraso": 1},
    ]
    monkeypatch.setattr(planificar.motor, "problemas_hechos", lambda _: {})
    monkeypatch.setattr(planificar.motor, "vencidos", lambda *_args, **_kwargs: vencidos)
    monkeypatch.setattr(planificar.motor, "frontera", lambda *_args, **_kwargs: frontera)
    monkeypatch.setattr(planificar.motor, "_creditos_ancestros", lambda *_args, **_kwargs: set())

    plan = planificar.plan_diario(
        nodos, perfil_vacio(), {},
        [{"materia": "A", "prioridad_score": 0.8}, {"materia": "B", "prioridad_score": 0.7}],
        {"minutos_dia": 120, "min_nodo_nuevo": 40, "min_repaso": 15},
        date(2027, 1, 1),
        materia_forzada="B",
    )

    assert [x["materia"] for x in plan["repasos"]] == ["B"]
    assert plan["nuevos"] == []


def test_render_del_plan_no_convierte_la_carga_en_una_meta_diaria():
    filas = [{
        "materia": "A", "fecha": "2027-01-10", "desc": "Ordinaria",
        "fecha_preparacion": "2027-01-03", "fase": "aprendizaje",
        "riesgo": 0.5, "pendientes": 4, "total": 4, "carga_h": 5,
        "ritmo": 227, "reales_sem": 0, "necesarios_sem": 2,
        "proyeccion": None, "retraso_dias": None,
    }]
    texto = planificar.render_md(
        filas,
        {"repasos": [], "nuevos": [], "implicitos": []},
        {"min_nodo_nuevo": 40, "min_repaso": 15},
        date(2026, 9, 13),
        150,
    )

    assert "no hay una cuota" in texto
    assert "Tiempo disponible" not in texto
    assert "Ritmo orientativo" not in texto
    assert "INSUFICIENTE" not in texto
    assert "AJUSTADO" not in texto


def test_fuentes_del_planificador_conservan_el_texto_unicode():
    texto = planificar.fuentes_txt({
        "fuentes": {"guia": "Tema 1", "thide": "1.1", "libro_metodos": "cap. 1"}
    })

    assert texto == "Guía Tema 1 · Thidé 1.1 · Métodos cap. 1"
    assert not any(marca in texto for marca in ("Ã", "Â", "�", "Eval?", "â€"))
