# -*- coding: utf-8 -*-
"""Genera el mapa global del knowledge graph (estilo Math Academy).

Uso: python generar_mapa.py electromagnetismo.json electronica.json electrodinamica.json
Produce: mapa_conocimiento.html — grafo de fuerzas en canvas, autocontenido.
"""
import json
import sys
import os
from collections import defaultdict, deque

def tono_materia(indice):
    """Tono estable por ángulo áureo: materias vecinas quedan bien separadas."""
    return (indice * 137.508) % 360


def color_nodo(indice_materia, tema):
    luz = 38 + ((tema * 7) % 20)
    return f"hsl({tono_materia(indice_materia):.0f}, 55%, {luz}%)"


def color_leyenda(indice_materia):
    return f"hsl({tono_materia(indice_materia):.0f}, 55%, 46%)"


def niveles_topologicos(nodos):
    """Nivel = camino más largo desde una raíz (0 = raíz)."""
    por_id = {n["id"]: n for n in nodos}
    nivel = {}

    def calc(i, visitando=()):
        if i in nivel:
            return nivel[i]
        if i in visitando:
            return 0
        prs = por_id[i].get("prerequisitos", [])
        n = 0 if not prs else 1 + max(calc(p["id"], visitando + (i,)) for p in prs if p["id"] in por_id)
        nivel[i] = n
        return n

    for n in nodos:
        calc(n["id"])
    return nivel


DIR = os.path.dirname(os.path.abspath(__file__))


NO_GRAFOS = {"perfil.json", "banco_problemas.json", "examenes.json", "correcciones.json"}


def archivos_por_defecto() -> list[str]:
    import glob as _glob
    return [r for r in sorted(_glob.glob(os.path.join(DIR, "*.json")))
            if os.path.basename(r) not in NO_GRAFOS]


def generar(rutas: list[str] | None = None) -> str:
    rutas = rutas or archivos_por_defecto()
    grafos = []
    for ruta in rutas:
        with open(ruta, "r", encoding="utf-8") as f:
            g = json.load(f)
        if "materia" in g and "nodos" in g:
            grafos.append(g)

    # Perfil de conocimiento (opcional): sombreado por dominio
    perfil_nodos = {}
    ruta_perfil = os.path.join(DIR, "perfil.json")
    if os.path.exists(ruta_perfil):
        with open(ruta_perfil, "r", encoding="utf-8") as f:
            perfil_nodos = json.load(f).get("nodos", {})

    # Orden estable: por curso y, dentro del curso, por orden de llegada
    grafos.sort(key=lambda g: g.get("curso", 0))
    indice_materia = {g["materia"]: i for i, g in enumerate(grafos)}
    n_mat = len(grafos)

    nodos_fusion = [dict(n, materia=g["materia"], temaNombre=g["temas"][str(n["tema"])])
                    for g in grafos for n in g["nodos"]]
    nivel = niveles_topologicos(nodos_fusion)

    datos_nodos = []
    for n in nodos_fusion:
        i = indice_materia[n["materia"]]
        entrada = perfil_nodos.get(n["id"])
        datos_nodos.append({
            "dominio": round(entrada["dominio"], 3) if entrada and entrada.get("dominio", 0) > 0 else None,
            "fluidez": round(entrada["fluidez"], 3) if entrada and entrada.get("fluidez", 0) > 0 else None,
            "proxima": entrada.get("proxima") if entrada else None,
            "id": n["id"],
            "nombre": n["nombre"],
            "materia": n["materia"],
            "temaNombre": n["temaNombre"],
            "descripcion": n.get("descripcion", ""),
            "fuentes": n.get("fuentes", {}),
            "color": color_nodo(i, n["tema"]),
            "nivel": nivel[n["id"]],
            "anclaX": (i - (n_mat - 1) / 2) * 250,
            "prereq": [{"id": p["id"], "peso": p["peso"]} for p in n.get("prerequisitos", [])],
        })

    datos = {
        "nodos": datos_nodos,
        "materias": [
            {"nombre": g["materia"], "curso": g.get("curso", 0),
             "color": color_leyenda(indice_materia[g["materia"]]),
             "n": len(g["nodos"])} for g in grafos
        ],
        "maxNivel": max(nivel.values()),
    }

    ruta_plantilla = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_plantilla_mapa.html")
    with open(ruta_plantilla, "r", encoding="utf-8") as f:
        plantilla = f.read()

    html = plantilla.replace("__DATA__", json.dumps(datos, ensure_ascii=False))
    salida = os.path.join(DIR, "mapa_conocimiento.html")
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Mapa generado: {salida} ({len(datos_nodos)} nodos)")
    return salida


def main():
    rutas = sys.argv[1:] or None
    generar(rutas)


if __name__ == "__main__":
    main()
