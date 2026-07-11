# -*- coding: utf-8 -*-
"""Tests del motor de dominio (knowledge_graph/perfil.py).

Usan grafos y perfiles sintéticos en memoria: NO leen ni escriben perfil.json
ni el disco, así que son seguros de ejecutar en cualquier momento.

Ejecutar:  python -m pytest tests/ -q
"""
import math
import os
import sys
from datetime import date, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(DIR), "knowledge_graph"))
import perfil as motor  # noqa: E402


# --------------------------------------------------------------- utilidades

def _nodo(nid, prereqs=None, materia="Test", tema=1, curso=1, granularidad="fina"):
    return {
        "id": nid, "nombre": nid.upper(), "materia": materia, "tema": tema,
        "curso": curso, "granularidad": granularidad,
        "prerequisitos": prereqs or [],
    }


def _grafo_cadena():
    """a -> b -> c  (c también tiene arista blanda directa a a)."""
    return {
        "a": _nodo("a"),
        "b": _nodo("b", [{"id": "a", "peso": 1.0}]),
        "c": _nodo("c", [{"id": "b", "peso": 1.0}, {"id": "a", "peso": 0.5}]),
    }


def _perfil_vacio():
    return {"actualizado": None, "nodos": {}}


HOY = date(2026, 9, 1)


# --------------------------------------------------------------- olvido

def test_dominio_efectivo_sin_revision_pendiente():
    e = {"dominio": 0.8, "intervalo": 7, "proxima": (HOY + timedelta(days=3)).isoformat()}
    assert motor.dominio_efectivo(e, HOY) == 0.8


def test_dominio_efectivo_decae_al_vencer():
    proxima = HOY - timedelta(days=14)
    e = {"dominio": 0.8, "intervalo": 7, "proxima": proxima.isoformat()}
    esperado = 0.8 * math.exp(-14 / (7 * 2.0))
    assert motor.dominio_efectivo(e, HOY) == esperado
    assert motor.dominio_efectivo(e, HOY) < 0.8  # ha decaído


def test_dominio_efectivo_nodo_sin_practica():
    assert motor.dominio_efectivo(None, HOY) == 0.0
    assert motor.dominio_efectivo({"dominio": 0.0}, HOY) == 0.0


# --------------------------------------------------------------- práctica directa

def test_practica_directa_necesita_varios_exitos_para_dominar():
    e = motor._entrada_nueva()
    for _ in range(2):
        motor._practica_directa(e, True, HOY, "test")
    assert e["dominio"] < motor.UMBRAL_FRONTERA  # 2 éxitos aún no bastan
    motor._practica_directa(e, True, HOY, "test")
    assert e["dominio"] >= motor.UMBRAL_FRONTERA  # ~3 sí


def test_practica_directa_intervalos_expansivos():
    e = motor._entrada_nueva()
    motor._practica_directa(e, True, HOY, "test")
    assert e["intervalo"] == motor.INTERVALOS[0]
    motor._practica_directa(e, True, HOY, "test")
    assert e["intervalo"] == motor.INTERVALOS[1]


def test_fallo_reduce_dominio_y_reinicia_intervalo():
    e = motor._entrada_nueva()
    for _ in range(3):
        motor._practica_directa(e, True, HOY, "test")
    dominio_antes = e["dominio"]
    motor._practica_directa(e, False, HOY, "test")
    assert e["dominio"] == round(dominio_antes * motor.DECAIMIENTO_FALLO, 4)
    assert e["intervalo"] == 1
    assert e["proxima"] == (HOY + timedelta(days=1)).isoformat()


def test_dominio_nunca_supera_098():
    e = motor._entrada_nueva()
    for _ in range(50):
        motor._practica_directa(e, True, HOY, "test")
    assert e["dominio"] <= 0.98


# --------------------------------------------------------------- crédito implícito

def test_creditos_ancestros_propaga_a_prerrequisitos():
    nodos = _grafo_cadena()
    creditos = motor._creditos_ancestros(["c"], nodos)
    # b: 1.0 * 0.6 = 0.6
    assert creditos["b"] == 0.6
    # a: por la cadena c->b->a = 0.6*1.0*0.6 = 0.36, gana al directo c->a (0.5*0.6=0.3)
    assert creditos["a"] == 0.36
    assert "c" not in creditos  # el propio nodo no recibe crédito


def test_creditos_ancestros_respeta_minimo():
    nodos = _grafo_cadena()
    creditos = motor._creditos_ancestros(["c"], nodos)
    assert all(v >= motor.CREDITO_MINIMO for v in creditos.values())


def test_aplicar_practica_sube_dominio_de_ancestros():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    motor.aplicar_practica(perfil, nodos, ["c"], True, fecha=HOY, origen="test")
    assert perfil["nodos"]["c"]["dominio"] > 0        # directo
    assert perfil["nodos"]["b"]["dominio"] > 0        # implícito
    assert perfil["nodos"]["a"]["dominio"] > 0        # implícito por cadena
    assert perfil["nodos"]["b"]["dominio"] > perfil["nodos"]["a"]["dominio"]


def test_aplicar_practica_ignora_ids_desconocidos():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    mensajes = motor.aplicar_practica(perfil, nodos, ["zzz"], True, fecha=HOY)
    assert any("desconocido" in m for m in mensajes)
    assert "zzz" not in perfil["nodos"]


def test_fallo_no_propaga_credito():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    motor.aplicar_practica(perfil, nodos, ["c"], False, fecha=HOY)
    assert perfil["nodos"].get("b", {"dominio": 0})["dominio"] == 0


# --------------------------------------------------------------- frontera

def test_frontera_bloquea_sin_prerrequisito_duro():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    ids = {n["id"] for n in motor.frontera(perfil, nodos)}
    assert "a" in ids           # sin prerrequisitos → listo
    assert "b" not in ids       # su prerrequisito duro 'a' no está dominado


def test_frontera_se_abre_al_dominar_prerrequisito():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    perfil["nodos"]["a"] = motor._entrada_nueva()
    perfil["nodos"]["a"].update(dominio=0.8,
                                proxima=(HOY + timedelta(days=30)).isoformat())
    ids = {n["id"] for n in motor.frontera(perfil, nodos)}
    assert "b" in ids           # ahora 'a' está dominado
    assert "a" not in ids       # 'a' ya dominado, sale de la frontera


def test_frontera_prerrequisito_blando_no_bloquea():
    # c depende de b (duro) y a (blando). Con solo b dominado, c entra.
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    for n in ("a", "b"):
        perfil["nodos"][n] = dict(motor._entrada_nueva(),
                                  dominio=0.8,
                                  proxima=(HOY + timedelta(days=30)).isoformat())
    ids = {n["id"] for n in motor.frontera(perfil, nodos)}
    assert "c" in ids


# --------------------------------------------------------------- vencidos

def test_vencidos_detecta_revision_pasada():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    perfil["nodos"]["a"] = dict(motor._entrada_nueva(), dominio=0.8, intervalo=7,
                                proxima=(HOY - timedelta(days=5)).isoformat())
    v = motor.vencidos(perfil, nodos, HOY)
    assert len(v) == 1 and v[0]["id"] == "a" and v[0]["retraso"] == 5


def test_vencidos_ignora_futuros_y_sin_dominio():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    perfil["nodos"]["a"] = dict(motor._entrada_nueva(), dominio=0.8,
                                proxima=(HOY + timedelta(days=5)).isoformat())
    perfil["nodos"]["b"] = dict(motor._entrada_nueva(), dominio=0.0,
                                proxima=(HOY - timedelta(days=5)).isoformat())
    assert motor.vencidos(perfil, nodos, HOY) == []


def test_vencidos_y_frontera_respetan_fecha_simulada():
    """Regresión: --fecha debe simular repasos/frontera en esa fecha, no en hoy."""
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    # 'a' dominado con revisión el 2026-09-10
    perfil["nodos"]["a"] = dict(motor._entrada_nueva(), dominio=0.8, intervalo=7,
                                proxima="2026-09-10")
    futuro = date(2026, 12, 1)     # muy posterior a la revisión de 'a'
    assert any(v["id"] == "a" for v in motor.vencidos(perfil, nodos, futuro))
    # y en esa fecha 'a' ha decaído lo bastante para sacar a 'b' de la frontera
    ids = {n["id"] for n in motor.frontera(perfil, nodos, hoy=futuro)}
    assert "b" not in ids


# --------------------------------------------------------------- conceptos

# --------------------------------------------------------------- fluidez

def test_entrada_nueva_incluye_fluidez():
    assert motor._entrada_nueva()["fluidez"] == 0.0


def test_practica_no_cronometrada_no_toca_fluidez():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    motor.aplicar_practica(perfil, nodos, ["a"], True, fecha=HOY)  # fluido=None
    assert perfil["nodos"]["a"]["fluidez"] == 0.0
    assert perfil["nodos"]["a"]["dominio"] > 0  # el dominio sí sube


def test_baseline_tiempo_none_hasta_k_muestras():
    e = motor._entrada_nueva()
    for _ in range(motor.BASELINE_MUESTRAS - 1):
        motor._actualizar_fluidez(e, True, 100)
    assert motor.baseline_tiempo(e) is None      # aún sin referencia
    motor._actualizar_fluidez(e, True, 100)
    assert motor.baseline_tiempo(e) == 100        # ya hay referencia (mediana de los primeros)


def test_acierto_mas_rapido_que_referencia_sube_fluidez():
    e = motor._entrada_nueva()
    for _ in range(motor.BASELINE_MUESTRAS):
        motor._actualizar_fluidez(e, True, 100)   # referencia = 100 s
    f0 = e["fluidez"]
    fue = motor._actualizar_fluidez(e, True, 50)  # mitad de tiempo
    assert fue is True
    assert e["fluidez"] > f0


def test_acierto_mas_lento_que_referencia_baja_fluidez():
    e = motor._entrada_nueva()
    for _ in range(motor.BASELINE_MUESTRAS):
        motor._actualizar_fluidez(e, True, 100)
    motor._actualizar_fluidez(e, True, 50)        # sube la fluidez
    f0 = e["fluidez"]
    fue = motor._actualizar_fluidez(e, True, 200)  # más lento que la referencia
    assert fue is False
    assert e["fluidez"] < f0


def test_fallo_baja_fluidez_y_no_registra_tiempo():
    e = motor._entrada_nueva()
    e["fluidez"] = 0.5
    fue = motor._actualizar_fluidez(e, exito=False, segundos=100)
    assert fue is False
    assert e["fluidez"] == round(0.5 * motor.DECAIMIENTO_FLUIDEZ_FALLO, 4)
    assert e["tiempos"] == []                      # un fallo no fija referencia


def test_aplicar_practica_cronometrada_registra_tiempo():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    motor.aplicar_practica(perfil, nodos, ["a"], True, fecha=HOY, segundos=120)
    assert perfil["nodos"]["a"]["tiempos"] == [120.0]


def test_fluidez_efectiva_decae_mas_rapido_que_dominio():
    proxima = HOY - timedelta(days=7)
    e = {"dominio": 0.8, "fluidez": 0.8, "intervalo": 7, "proxima": proxima.isoformat()}
    d = motor.dominio_efectivo(e, HOY)
    f = motor.fluidez_efectiva(e, HOY)
    assert f < d < 0.8  # ambos decaen, la fluidez más


def test_consolidado_exige_dominio_y_fluidez():
    futuro = (HOY + timedelta(days=30)).isoformat()
    solo_dominio = {"dominio": 0.8, "fluidez": 0.3, "intervalo": 30, "proxima": futuro}
    ambos = {"dominio": 0.8, "fluidez": 0.8, "intervalo": 30, "proxima": futuro}
    assert not motor.consolidado(solo_dominio, HOY)
    assert motor.consolidado(ambos, HOY)


# --------------------------------------------------------------- calidad graduada

def test_calidad_bien_equivale_al_exito_binario():
    e1, e2 = motor._entrada_nueva(), motor._entrada_nueva()
    motor._practica_directa(e1, True, HOY, "t")                       # binario
    motor._practica_directa(e2, True, HOY, "t", calidad=motor.CALIDAD["resuelto"])
    assert e1["dominio"] == e2["dominio"]


def test_calidad_desliz_gana_menos_que_resuelto_pero_avanza():
    bien, desliz = motor._entrada_nueva(), motor._entrada_nueva()
    motor._practica_directa(bien, True, HOY, "t", calidad=1.0)
    motor._practica_directa(desliz, True, HOY, "t", calidad=motor.CALIDAD["desliz"])
    assert 0 < desliz["dominio"] < bien["dominio"]
    assert desliz["reps"] == 1          # desliz consolida (expande intervalo)


def test_calidad_a_medias_gana_algo_pero_repasa_pronto():
    e = motor._entrada_nueva()
    motor._practica_directa(e, None, HOY, "t", calidad=motor.CALIDAD["a_medias"])
    assert e["dominio"] > 0              # gana algo de dominio
    assert e["reps"] == 0               # pero no consolida
    assert e["intervalo"] == 1          # se repasa pronto


def test_calidad_bloqueado_decae_menos_que_en_blanco():
    base = 0.6
    bloq = dict(motor._entrada_nueva(), dominio=base)
    blanco = dict(motor._entrada_nueva(), dominio=base)
    motor._practica_directa(bloq, None, HOY, "t", calidad=motor.CALIDAD["bloqueado"])
    motor._practica_directa(blanco, None, HOY, "t", calidad=motor.CALIDAD["en_blanco"])
    assert blanco["dominio"] < bloq["dominio"] < base


def test_calidad_baja_empuja_prerrequisitos_a_repaso():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    # 'a' (prerrequisito duro de 'b') dominado con revisión lejana
    perfil["nodos"]["a"] = dict(motor._entrada_nueva(), dominio=0.8, intervalo=30,
                                proxima=(HOY + timedelta(days=30)).isoformat())
    # 'b' bloqueado: su prerrequisito 'a' debe adelantarse a repaso
    motor.aplicar_practica(perfil, nodos, ["b"], False, fecha=HOY,
                           calidad=motor.CALIDAD["bloqueado"])
    assert perfil["nodos"]["a"]["proxima"] == (HOY + timedelta(days=1)).isoformat()


def test_calidad_a_medias_no_empuja_prerrequisitos():
    nodos = _grafo_cadena()
    perfil = _perfil_vacio()
    perfil["nodos"]["a"] = dict(motor._entrada_nueva(), dominio=0.8, intervalo=30,
                                proxima=(HOY + timedelta(days=30)).isoformat())
    motor.aplicar_practica(perfil, nodos, ["b"], True, fecha=HOY,
                           calidad=motor.CALIDAD["a_medias"])
    # a-medias es un acierto (propaga crédito, que empuja 'a' hacia ADELANTE),
    # pero NO es un bloqueo: no debe adelantar 'a' a repaso inmediato (mañana).
    assert motor._fecha(perfil["nodos"]["a"]["proxima"]) > HOY + timedelta(days=1)


def test_resolver_conceptos_mapea_por_nombre_difuso():
    nodos = {
        "em.1": _nodo("em.1", materia="Electromagnetismo"),
        "em.2": _nodo("em.2", materia="Electromagnetismo"),
    }
    nodos["em.1"]["nombre"] = "Ley de Gauss"
    nodos["em.2"]["nombre"] = "Potencial eléctrico"
    ids = motor.resolver_conceptos("Electromagnetismo", ["ley de gauss"], nodos)
    assert ids == ["em.1"]
