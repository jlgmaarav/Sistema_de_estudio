# -*- coding: utf-8 -*-
"""Construye el banco de problemas sin llamadas de red ni API de IA.

El etiquetado del banco usa el tema declarado en el material y el catálogo
local del grafo. La corrección pedagógica de una resolución se hace aparte,
mediante el flujo de voz y Gemini Web.
"""
import argparse
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
BANCO_PATH = os.path.join(DIR, "banco_problemas.json")


def parsear_md(ruta_md: str) -> list[dict]:
    with open(ruta_md, "r", encoding="utf-8") as f:
        texto = f.read()

    problemas = []
    tema_actual, hoja_actual = "", ""
    num_tema = 0
    actual = None

    for linea in texto.splitlines():
        m_tema = re.match(r"^# (Tema \d+.*)$", linea)
        m_hoja = re.match(r"^## (.*)$", linea)
        m_prob = re.match(r"^### (\d+)[\.\-]*\s*(.*)$", linea)
        if m_tema:
            tema_actual = m_tema.group(1).strip()
            num_tema = int(re.search(r"\d+", tema_actual).group())
            continue
        if m_hoja:
            hoja_actual = m_hoja.group(1).strip()
            continue
        if m_prob:
            if actual:
                problemas.append(actual)
            actual = {
                "id": f"EM-T{num_tema}-{len([p for p in problemas if p['num_tema'] == num_tema]) + 1:03d}",
                "materia": "Electromagnetismo",
                "num_tema": num_tema,
                "tema_md": tema_actual,
                "hoja": hoja_actual,
                "numero": m_prob.group(1),
                "titulo": m_prob.group(2).strip(" -"),
                "enunciado": "",
                "nodos": [],
            }
            continue
        if actual is not None and not linea.startswith("---"):
            actual["enunciado"] += linea + "\n"
    if actual:
        problemas.append(actual)

    for p in problemas:
        p["enunciado"] = p["enunciado"].strip()
    return problemas


def catalogo_materia(ruta_grafo: str) -> tuple[str, str, dict]:
    with open(ruta_grafo, "r", encoding="utf-8") as f:
        g = json.load(f)
    lineas = [f"{n['id']}: {n['nombre']} — {n.get('descripcion', '')}" for n in g["nodos"]]
    nodos_por_tema = {}
    for n in g["nodos"]:
        nodos_por_tema.setdefault(n["tema"], []).append(n["id"])
    return g["materia"], "\n".join(lineas), nodos_por_tema


def respaldo_por_tema(problemas: list[dict], nodos_por_tema: dict) -> None:
    """Asigna nodos locales coherentes con el tema del material.

    El Tema 1 del MD cubre los temas 0 y 1 del grafo. Se limita a los nodos
    del catálogo y no intenta inventar una clasificación semántica por IA.
    """
    for p in problemas:
        if p["nodos"]:
            continue
        temas_grafo = [0, 1] if p["num_tema"] == 1 else [p["num_tema"]]
        nodos = [nid for t in temas_grafo for nid in nodos_por_tema.get(t, [])]
        p["nodos"] = nodos
        p["nodos_tema"] = list(nodos)


def procesar(ruta_md: str, ruta_grafo: str, con_ia: bool = False) -> dict:
    """Parsea, etiqueta localmente y guarda el banco.

    ``con_ia`` se conserva como parámetro de compatibilidad para la app, pero
    se ignora deliberadamente: el clasificador por API está retirado.
    """
    problemas = parsear_md(ruta_md)
    print(f"Parseados {len(problemas)} problemas de {os.path.basename(ruta_md)}")

    materia, _catalogo, nodos_por_tema = catalogo_materia(ruta_grafo)
    respaldo_por_tema(problemas, nodos_por_tema)
    _guardar(problemas, ruta_md, materia, nodos_por_tema)
    con_nodo = sum(1 for p in problemas if p["nodos"])
    return {"materia": materia, "problemas": len(problemas),
            "etiquetados_ia": 0, "con_nodos": con_nodo}


def _guardar(problemas, ruta_md, materia, nodos_por_tema):
    validos = {nid for nids in nodos_por_tema.values() for nid in nids}
    for p in problemas:
        p["nodos"] = [n for n in p["nodos"] if n in validos]

    banco = {"fuente": os.path.abspath(ruta_md), "materia": materia, "problemas": problemas}
    if os.path.exists(BANCO_PATH):
        with open(BANCO_PATH, "r", encoding="utf-8") as f:
            existente = json.load(f)
        if "problemas" in existente:
            existente = {existente["materia"]: existente}
        if materia in existente:
            previos = {p["id"]: p for p in existente[materia].get("problemas", [])}
            for p in problemas:
                previos[p["id"]] = p
            banco["problemas"] = list(previos.values())
            fuente_previa = existente[materia].get("fuente", "")
            if fuente_previa and banco["fuente"] not in fuente_previa:
                banco["fuente"] = f"{fuente_previa} + {banco['fuente']}"
        existente[materia] = banco
        contenido = existente
    else:
        contenido = {materia: banco}
    with open(BANCO_PATH, "w", encoding="utf-8") as f:
        json.dump(contenido, f, ensure_ascii=False, indent=1)

    con_nodo = sum(1 for p in problemas if p["nodos"])
    print(f"Banco guardado en {BANCO_PATH}: {len(problemas)} problemas, {con_nodo} con nodos locales.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("md")
    parser.add_argument("grafo")
    parser.add_argument("--sin-ia", action="store_true", help="Compatibilidad; el modo local ya es el único disponible")
    args = parser.parse_args()
    procesar(args.md, args.grafo, con_ia=False)


if __name__ == "__main__":
    main()
