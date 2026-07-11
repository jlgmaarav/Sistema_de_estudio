# -*- coding: utf-8 -*-
"""Regenera taxonomy_uva.json a partir de los knowledge graphs.

Uso: python actualizar_taxonomia.py <grafo1.json> [<grafo2.json> ...]
Para cada materia usa sus temas como taxonomía; si el grafo es de granularidad
gruesa (un único tema genérico), usa los nombres de los nodos como temas.
Conserva las entradas de la taxonomía que no tienen grafo (p. ej. TFG).
"""
import json
import sys
import os

RUTA_TAXONOMIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "taxonomy_uva.json")


def temas_de(grafo: dict) -> list[str]:
    temas = [v for _, v in sorted(grafo["temas"].items(), key=lambda kv: int(kv[0]))]
    if len(temas) == 1:
        # Grafo grueso: los nodos son la mejor taxonomía disponible
        return [n["nombre"] for n in grafo["nodos"]]
    return temas


def main():
    if len(sys.argv) < 2:
        print("Uso: python actualizar_taxonomia.py <grafo.json> ...")
        sys.exit(1)

    with open(RUTA_TAXONOMIA, "r", encoding="utf-8") as f:
        taxonomia = json.load(f)

    for ruta in sys.argv[1:]:
        with open(ruta, "r", encoding="utf-8") as f:
            grafo = json.load(f)
        materia = grafo["materia"]
        # Eliminar duplicados con distinta capitalización
        for clave in list(taxonomia):
            if clave.lower() == materia.lower() and clave != materia:
                del taxonomia[clave]
        taxonomia[materia] = temas_de(grafo)

    with open(RUTA_TAXONOMIA, "w", encoding="utf-8") as f:
        json.dump(taxonomia, f, ensure_ascii=False, indent=2)
    print(f"Taxonomía actualizada: {len(taxonomia)} asignaturas -> {os.path.abspath(RUTA_TAXONOMIA)}")


if __name__ == "__main__":
    main()
