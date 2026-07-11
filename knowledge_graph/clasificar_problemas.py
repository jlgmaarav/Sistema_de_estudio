# -*- coding: utf-8 -*-
"""Construye el banco de problemas etiquetado con nodos del knowledge graph.

Uso:
  python clasificar_problemas.py "../Problemas/Electromagnetismo/Ejercicios_Electromagnetismo_Completo.md" electromagnetismo.json
  python clasificar_problemas.py <md> <grafo.json> --sin-ia   (solo parseo, sin etiquetar)

Parsea el MD (# Tema / ## Hoja / ### N.- título), etiqueta cada problema con
los ids de nodos que ejercita (Gemini, en lotes) y guarda banco_problemas.json.
El tema del MD se usa como respaldo si la IA no está disponible.
"""
import argparse
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BANCO_PATH = os.path.join(DIR, "banco_problemas.json")
TAM_LOTE = 35


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


def etiquetar_con_ia(problemas: list[dict], catalogo: str, materia: str) -> int:
    sys.path.insert(0, os.path.dirname(DIR))
    import config
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    esquema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "id": types.Schema(type=types.Type.STRING, description="Id del problema tal cual se dio"),
                "nodos": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING),
                                      description="1 a 4 ids de nodos del catálogo que el problema ejercita directamente"),
            },
            required=["id", "nodos"],
        ),
    )

    etiquetados = 0
    for i in range(0, len(problemas), TAM_LOTE):
        lote = problemas[i:i + TAM_LOTE]
        listado = "\n\n".join(
            f"[{p['id']}] ({p['tema_md']} / {p['hoja']}) {p['titulo']}\n{p['enunciado'][:600]}"
            for p in lote
        )
        prompt = (
            f"Eres profesor experto en {materia}. Catálogo de nodos del grafo de conocimiento de {materia} "
            "(formato `id: nombre — descripción`):\n\n"
            f"{catalogo}\n\n"
            "Para CADA problema del siguiente listado, devuelve su id y los ids de los nodos "
            "(entre 1 y 4, EXACTOS del catálogo) que el problema ejercita DIRECTAMENTE — la técnica "
            "principal necesaria para resolverlo, no prerrequisitos lejanos.\n\n"
            f"Problemas:\n\n{listado}"
        )
        print(f"  Lote {i // TAM_LOTE + 1}: {len(lote)} problemas...", end=" ", flush=True)
        try:
            r = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=esquema,
                    temperature=0.1,
                ),
            )
            datos = json.loads(r.text)
            por_id = {p["id"]: p for p in lote}
            ok = 0
            for item in datos:
                p = por_id.get(item.get("id", ""))
                if p and item.get("nodos"):
                    p["nodos"] = item["nodos"]
                    ok += 1
            etiquetados += ok
            print(f"{ok} etiquetados")
        except Exception as e:
            print(f"ERROR ({e}); este lote queda con respaldo por tema")
    return etiquetados


def respaldo_por_tema(problemas: list[dict], nodos_por_tema: dict) -> None:
    """Si un problema quedó sin nodos, asigna los nodos de su tema del grafo.
    El Tema 1 del MD cubre los temas 0 y 1 del grafo."""
    for p in problemas:
        if p["nodos"]:
            continue
        temas_grafo = [0, 1] if p["num_tema"] == 1 else [p["num_tema"]]
        p["nodos_tema"] = [nid for t in temas_grafo for nid in nodos_por_tema.get(t, [])]


def procesar(ruta_md: str, ruta_grafo: str, con_ia: bool = True) -> dict:
    """Parsea, etiqueta y guarda el banco. API usada por CLI y por la app web."""
    problemas = parsear_md(ruta_md)
    print(f"Parseados {len(problemas)} problemas de {os.path.basename(ruta_md)}")

    materia, catalogo, nodos_por_tema = catalogo_materia(ruta_grafo)
    etiquetados = 0
    if con_ia:
        etiquetados = etiquetar_con_ia(problemas, catalogo, materia)
        print(f"Etiquetados con IA: {etiquetados}/{len(problemas)}")
    respaldo_por_tema(problemas, nodos_por_tema)
    _guardar(problemas, ruta_md, materia, nodos_por_tema)
    con_nodo = sum(1 for p in problemas if p["nodos"])
    return {"materia": materia, "problemas": len(problemas),
            "etiquetados_ia": etiquetados, "con_nodos": con_nodo}


def _guardar(problemas, ruta_md, materia, nodos_por_tema):

    # Validar ids devueltos por la IA contra el grafo
    validos = {nid for nids in nodos_por_tema.values() for nid in nids}
    for p in problemas:
        p["nodos"] = [n for n in p["nodos"] if n in validos]

    banco = {"fuente": os.path.abspath(ruta_md), "materia": materia, "problemas": problemas}
    if os.path.exists(BANCO_PATH):
        with open(BANCO_PATH, "r", encoding="utf-8") as f:
            existente = json.load(f)
        # Varios bancos por materia: estructura {materia: {...}}
        if "problemas" in existente:
            existente = {existente["materia"]: existente}
        if materia in existente:
            # FUSIONAR con lo ya existente (mismo id = se actualiza)
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
    print(f"Banco guardado en {BANCO_PATH}: {len(problemas)} problemas, {con_nodo} con nodos específicos.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("md")
    parser.add_argument("grafo")
    parser.add_argument("--sin-ia", action="store_true")
    args = parser.parse_args()
    procesar(args.md, args.grafo, con_ia=not args.sin_ia)


if __name__ == "__main__":
    main()
