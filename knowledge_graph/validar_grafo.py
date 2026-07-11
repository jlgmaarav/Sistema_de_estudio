# -*- coding: utf-8 -*-
"""Valida uno o varios knowledge graphs y genera sus documentos de revisión.

Uso: python validar_grafo.py electromagnetismo.json [electronica.json ...]
Los archivos se validan como un grafo fusionado: los prerrequisitos pueden
apuntar a nodos de otro archivo (aristas entre asignaturas).
Comprueba: ids duplicados, prerrequisitos inexistentes, ciclos, pesos válidos.
Genera: REVISION_<materia>.md por archivo.
"""
import json
import sys
import os
from collections import defaultdict, deque


def validar_archivo(grafo: dict) -> list[str]:
    """Comprobaciones locales a un archivo (temas y pesos)."""
    errores = []
    for n in grafo["nodos"]:
        if str(n["tema"]) not in grafo["temas"]:
            errores.append(f"{n['id']}: tema {n['tema']} no está en 'temas'")
        for p in n.get("prerequisitos", []):
            if p["id"] == n["id"]:
                errores.append(f"{n['id']}: se tiene a sí mismo como prerrequisito")
            if not (0 < p.get("peso", 0) <= 1.0):
                errores.append(f"{n['id']}: peso inválido {p.get('peso')} para {p['id']}")
    return errores


def validar_fusion(nodos: list[dict]) -> list[str]:
    """Comprobaciones sobre el grafo fusionado: duplicados, refs y ciclos."""
    errores = []
    ids = [n["id"] for n in nodos]

    vistos = set()
    for i in ids:
        if i in vistos:
            errores.append(f"Id duplicado: {i}")
        vistos.add(i)

    for n in nodos:
        for p in n.get("prerequisitos", []):
            if p["id"] not in vistos:
                errores.append(f"{n['id']}: prerrequisito inexistente {p['id']}")

    # Detección de ciclos (Kahn)
    entrantes = defaultdict(int)
    salientes = defaultdict(list)
    for n in nodos:
        for p in n.get("prerequisitos", []):
            if p["id"] in vistos:
                entrantes[n["id"]] += 1
                salientes[p["id"]].append(n["id"])
    cola = deque(i for i in ids if entrantes[i] == 0)
    procesados = 0
    while cola:
        actual = cola.popleft()
        procesados += 1
        for hijo in salientes[actual]:
            entrantes[hijo] -= 1
            if entrantes[hijo] == 0:
                cola.append(hijo)
    if procesados != len(ids):
        en_ciclo = [i for i in ids if entrantes[i] > 0]
        errores.append(f"Ciclo detectado; nodos implicados: {', '.join(en_ciclo)}")

    return errores


def generar_revision(grafo: dict, por_id_global: dict, dependientes: dict, ruta_salida: str) -> None:
    por_tema = defaultdict(list)
    for n in grafo["nodos"]:
        por_tema[str(n["tema"])].append(n)

    lineas = [
        f"# Revisión del grafo — {grafo['materia']}",
        "",
        f"Total: **{len(grafo['nodos'])} nodos**. Para cada nodo revisa: ¿se dio en clase?, "
        "¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?",
        "",
        "Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.",
        "Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).",
        "",
    ]
    for tema_id in sorted(por_tema, key=lambda t: int(t)):
        lineas.append(f"## {grafo['temas'][tema_id]}")
        lineas.append("")
        lineas.append("| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |")
        lineas.append("|---|---|---|---|---|")
        for n in por_tema[tema_id]:
            prs = ", ".join(
                f"{p['id']}" + ("" if p["peso"] == 1.0 else f" ({p['peso']})")
                for p in n.get("prerequisitos", [])
            ) or "—"
            fts = "; ".join(f"{k.capitalize()} {v}" for k, v in n.get("fuentes", {}).items())
            lineas.append(f"| {n['id']} | **{n['nombre']}** — {n['descripcion']} | {prs} | {fts} | |")
        lineas.append("")

    ids_materia = {n["id"] for n in grafo["nodos"]}
    hojas = [i for i in ids_materia if not dependientes.get(i)]
    raices = [n["id"] for n in grafo["nodos"] if not n.get("prerequisitos")]
    n_aristas = sum(len(n.get("prerequisitos", [])) for n in grafo["nodos"])
    externas = sum(
        1 for n in grafo["nodos"] for p in n.get("prerequisitos", [])
        if p["id"] not in ids_materia
    )
    lineas.append("## Estadísticas")
    lineas.append("")
    lineas.append(f"- Nodos raíz (sin prerrequisitos): {', '.join(raices) or '—'}")
    lineas.append(f"- Nodos sin dependientes en todo el sistema: {', '.join(sorted(hojas)) or '—'}")
    lineas.append(f"- Aristas: {n_aristas} ({externas} hacia otras asignaturas)")
    lineas.append("")

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


def main():
    if len(sys.argv) < 2:
        print("Uso: python validar_grafo.py <grafo.json> [<grafo2.json> ...]")
        sys.exit(1)

    grafos = []
    for ruta in sys.argv[1:]:
        with open(ruta, "r", encoding="utf-8") as f:
            grafos.append((ruta, json.load(f)))

    errores = []
    for _, g in grafos:
        errores.extend(validar_archivo(g))

    nodos_fusion = [n for _, g in grafos for n in g["nodos"]]
    errores.extend(validar_fusion(nodos_fusion))

    if errores:
        print(f"ERRORES ({len(errores)}):")
        for e in errores:
            print(f"  - {e}")
        sys.exit(1)

    por_id = {n["id"]: n for n in nodos_fusion}
    dependientes = defaultdict(list)
    for n in nodos_fusion:
        for p in n.get("prerequisitos", []):
            dependientes[p["id"]].append(n["id"])

    n_aristas = sum(len(n.get("prerequisitos", [])) for n in nodos_fusion)
    print(f"Grafo fusionado válido: {len(nodos_fusion)} nodos, {n_aristas} aristas, sin ciclos.")

    for ruta, g in grafos:
        salida = os.path.join(
            os.path.dirname(os.path.abspath(ruta)),
            f"REVISION_{g['materia'].replace(' ', '_')}.md",
        )
        generar_revision(g, por_id, dependientes, salida)
        print(f"  {g['materia']}: {len(g['nodos'])} nodos -> {os.path.basename(salida)}")


if __name__ == "__main__":
    main()
