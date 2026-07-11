# -*- coding: utf-8 -*-
"""Tests del sistema de gamificación (knowledge_graph/gamificacion.py)."""
import os
import sys
from datetime import date, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(DIR), "knowledge_graph"))
import gamificacion as g  # noqa: E402
import perfil as motor  # noqa: E402

HOY = date(2026, 9, 1)


def _perfil():
    return {"actualizado": None, "nodos": {}}


# ------------------------------------------------------------ niveles

def test_umbral_nivel_creciente():
    umbrales = [g.umbral_nivel(n) for n in range(1, 6)]
    assert umbrales == [0, 100, 250, 450, 700]  # incrementos 100,150,200,250


def test_nivel_de_xp():
    assert g.nivel_de(0) == 1
    assert g.nivel_de(99) == 1
    assert g.nivel_de(100) == 2
    assert g.nivel_de(250) == 3


# ------------------------------------------------------------ otorgar XP

def test_exito_da_xp_base():
    p = _perfil()
    r = g.otorgar(p, "directo", exito=True, fluido=None, recien_dominado=False, hoy=HOY)
    assert r["xp"] == g.XP_DIRECTO_EXITO
    assert p["gamificacion"]["xp_total"] == g.XP_DIRECTO_EXITO


def test_recien_dominado_suma_bonus():
    p = _perfil()
    r = g.otorgar(p, "directo", True, None, recien_dominado=True, hoy=HOY)
    assert r["xp"] == g.XP_DIRECTO_EXITO + g.XP_RECIEN_DOMINADO


def test_fluido_suma_bonus():
    p = _perfil()
    r = g.otorgar(p, "directo", True, fluido=True, recien_dominado=False, hoy=HOY)
    assert r["xp"] == g.XP_DIRECTO_EXITO + g.XP_FLUIDO


def test_fallo_da_xp_de_esfuerzo():
    p = _perfil()
    r = g.otorgar(p, "directo", exito=False, fluido=False, recien_dominado=False, hoy=HOY)
    assert r["xp"] == g.XP_FALLO


def test_calidad_graduada_escala_el_xp():
    # resuelto = XP base; a-medias da menos pero más que un fallo; bloqueo = esfuerzo
    r_bien = g.otorgar(_perfil(), "directo", True, None, False, hoy=HOY, calidad=1.0)
    r_medias = g.otorgar(_perfil(), "directo", True, None, False, hoy=HOY, calidad=0.5)
    r_bloq = g.otorgar(_perfil(), "directo", False, None, False, hoy=HOY, calidad=0.25)
    assert r_bien["xp"] == g.XP_DIRECTO_EXITO
    assert g.XP_FALLO < r_medias["xp"] < r_bien["xp"]
    assert r_bloq["xp"] == g.XP_FALLO


def test_subida_de_nivel_se_detecta():
    p = _perfil()
    ult = None
    for _ in range(12):  # 12 * 10 = 120 XP > 100 (nivel 2)
        ult = g.otorgar(p, "directo", True, None, False, hoy=HOY)
    assert g.nivel_de(p["gamificacion"]["xp_total"]) >= 2
    assert any(g.otorgar(_perfil(), "directo", True, None, False, hoy=HOY) for _ in range(1))


# ------------------------------------------------------------ racha

def test_racha_dias_consecutivos():
    p = _perfil()
    for i in range(3):  # 3 días seguidos terminando en HOY
        g.otorgar(p, "directo", True, None, False, hoy=HOY - timedelta(days=2 - i))
    est = g.estado(p, HOY)
    assert est["racha"] == 3


def test_racha_se_rompe_con_hueco():
    p = _perfil()
    g.otorgar(p, "directo", True, None, False, hoy=HOY - timedelta(days=5))
    g.otorgar(p, "directo", True, None, False, hoy=HOY)
    est = g.estado(p, HOY)
    assert est["racha"] == 1
    assert est["racha_max"] == 1


# ------------------------------------------------------------ insignias

def test_insignia_primer_paso():
    p = _perfil()
    r = g.otorgar(p, "directo", True, None, False, hoy=HOY)
    assert "Primer paso" in r["nuevas_insignias"]
    assert "primer_paso" in p["gamificacion"]["insignias"]


def test_insignia_no_se_duplica():
    p = _perfil()
    g.otorgar(p, "directo", True, None, False, hoy=HOY)
    r2 = g.otorgar(p, "directo", True, None, False, hoy=HOY)
    assert "Primer paso" not in r2["nuevas_insignias"]


def test_meta_diaria_cumplida():
    p = _perfil()
    g._bloque(p)["meta_diaria"] = 20
    g.otorgar(p, "directo", True, fluido=True, recien_dominado=True, hoy=HOY)  # 35 XP
    est = g.estado(p, HOY)
    assert est["meta_cumplida"] is True


# ------------------------------------------------------------ integración con el motor

def test_aplicar_practica_otorga_xp():
    nodos = {"a": {"id": "a", "nombre": "A", "materia": "T", "tema": 1,
                   "curso": 1, "granularidad": "fina", "prerequisitos": []}}
    perfil = _perfil()
    motor.aplicar_practica(perfil, nodos, ["a"], True, fecha=HOY)
    assert perfil["gamificacion"]["xp_total"] >= g.XP_DIRECTO_EXITO
