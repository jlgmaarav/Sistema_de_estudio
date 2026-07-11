# -*- coding: utf-8 -*-
"""Extrae 'errores típicos' de un documento (PDF/TXT de listas de errores,
propias o de compañeros) y los clasifica por nodo del knowledge graph.

Uso:
  python extraer_errores_tipicos.py "<documento.pdf>" <grafo.json> --fuente "compañero 2025"

Guarda/fusiona en errores_tipicos.json: {nodo_id: [{titulo, como_evitarlo, fuente}]}.
Estos avisos aparecen en el plan junto a tus propios errores.
"""
import argparse
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(DIR, "errores_tipicos.json")


def leer_documento(ruta: str) -> str:
    if ruta.lower().endswith(".pdf"):
        import fitz
        doc = fitz.open(ruta)
        texto = "\n".join(p.get_text() for p in doc)
        doc.close()
        return texto
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("documento")
    ap.add_argument("grafo")
    ap.add_argument("--fuente", default="documento externo")
    args = ap.parse_args()

    texto = leer_documento(args.documento)
    with open(args.grafo, "r", encoding="utf-8") as f:
        g = json.load(f)
    catalogo = "\n".join(f"{n['id']}: {n['nombre']}" for n in g["nodos"])

    sys.path.insert(0, os.path.dirname(DIR))
    import config
    from google import genai
    from google.genai import types

    esquema = types.Schema(type=types.Type.ARRAY, items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "titulo": types.Schema(type=types.Type.STRING, description="Título corto del error (máx 10 palabras)"),
            "como_evitarlo": types.Schema(type=types.Type.STRING, description="Regla de oro concreta para no cometerlo"),
            "nodos": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING),
                                  description="1-3 ids EXACTOS del catálogo donde aplica este error"),
        },
        required=["titulo", "como_evitarlo", "nodos"],
    ))
    prompt = (
        f"Eres profesor experto en {g['materia']}. El siguiente documento contiene errores reales "
        "cometidos por estudiantes al resolver problemas (con sus enunciados). "
        "Extrae CADA error como una lección accionable: título corto, regla de oro para evitarlo, "
        "y los nodos del catálogo donde aplica.\n\n"
        f"Catálogo de nodos (id: nombre):\n{catalogo}\n\n"
        f"Documento:\n{texto[:20000]}"
    )
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    r = client.models.generate_content(
        model=config.GEMINI_MODEL, contents=[prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json",
                                           response_schema=esquema, temperature=0.1),
    )
    errores = json.loads(r.text)
    validos = {n["id"] for n in g["nodos"]}

    existente = {}
    if os.path.exists(SALIDA):
        with open(SALIDA, "r", encoding="utf-8") as f:
            existente = json.load(f)
    anadidos = 0
    for e in errores:
        for nid in e.get("nodos", []):
            if nid not in validos:
                continue
            lista = existente.setdefault(nid, [])
            if any(x["titulo"] == e["titulo"] for x in lista):
                continue
            lista.append({"titulo": e["titulo"], "como_evitarlo": e["como_evitarlo"],
                          "fuente": args.fuente})
            anadidos += 1
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(existente, f, ensure_ascii=False, indent=1)
    print(f"{len(errores)} errores extraídos; {anadidos} entradas añadidas en {len(existente)} nodos -> {SALIDA}")


if __name__ == "__main__":
    main()
