# -*- coding: utf-8 -*-
"""Lecciones mínimas eficaces por nodo, generadas por IA y cacheadas.

La 'dosis mínima de instrucción guiada' del método: explicación concisa
asumiendo los prerrequisitos dominados + un ejemplo resuelto + reglas de oro.
Se genera una vez por nodo y queda cacheada en lecciones/<id>.md.
"""
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(DIR, "lecciones")


def obtener_leccion(nid: str, regenerar: bool = False) -> str:
    os.makedirs(CACHE, exist_ok=True)
    ruta = os.path.join(CACHE, f"{nid.replace('.', '_')}.md")
    if os.path.exists(ruta) and not regenerar:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()

    sys.path.insert(0, DIR)
    import perfil as motor
    nodos = motor.cargar_grafos()
    if nid not in nodos:
        raise ValueError(f"Nodo desconocido: {nid}")
    n = nodos[nid]
    prereqs = [nodos[p["id"]]["nombre"] for p in n.get("prerequisitos", []) if p["id"] in nodos]
    fuentes = " · ".join(f"{k} {v}" for k, v in n.get("fuentes", {}).items())

    sys.path.insert(0, os.path.dirname(DIR))
    import config
    from google import genai
    from google.genai import types

    prompt = (
        f"Eres un profesor experto en {n['materia']}. Escribe la LECCIÓN MÍNIMA EFICAZ "
        "del siguiente tema para un estudiante que sigue un plan de mastery learning:\n\n"
        f"Tema: {n['nombre']}\n"
        f"Materia: {n['materia']}\n"
        f"Alcance exacto: {n.get('descripcion', '')}\n"
        f"Prerrequisitos que el estudiante YA DOMINA (no los reexpliques): {', '.join(prereqs) or 'ninguno'}\n"
        f"Referencias bibliográficas del curso: {fuentes or 'las estándar'}\n\n"
        "Estructura EXACTA de la lección (en Markdown, matemáticas en LaTeX con $$ para bloques y \\( \\) en línea):\n"
        "## Idea central\n(2-3 frases: qué es y para qué sirve)\n\n"
        "## Explicación\n(300-500 palabras, directa y rigurosa, apoyada en los prerrequisitos ya dominados; "
        "incluye las fórmulas clave)\n\n"
        "## Ejemplo resuelto\n(UN problema representativo del nivel del curso, resuelto paso a paso con "
        "todos los desarrollos intermedios)\n\n"
        "## Reglas de oro\n(3 puntos: errores típicos a evitar y comprobaciones sistemáticas propias "
        "de la disciplina — en física: dimensiones, casos límite, signos; en póker: odds, rangos, posición; etc.)\n\n"
        "No añadas nada fuera de esas cuatro secciones. Sé conciso: es la dosis mínima antes de que el "
        "estudiante pase a resolver problemas por sí mismo."
    )

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    r = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(temperature=0.3),
    )
    md = f"# {n['nombre']}\n\n*{n['materia']} · {fuentes}*\n\n" + r.text.strip()
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(md)
    return md


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("nodo")
    ap.add_argument("--regenerar", action="store_true")
    a = ap.parse_args()
    print(obtener_leccion(a.nodo, a.regenerar))
