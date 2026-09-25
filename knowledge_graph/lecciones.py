# -*- coding: utf-8 -*-
"""Lecciones cacheadas y preparación manual de lecciones en Gemini Web.

No se llama a ninguna API. Las lecciones ya cacheadas se sirven localmente;
una regeneración prepara un encargo para la web y deja al estudiante decidir
qué respuesta guardar.
"""
import os
import subprocess
import webbrowser

DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(DIR, "lecciones")
BASE = os.path.dirname(DIR)


def _copiar(texto: str) -> bool:
    try:
        subprocess.run(
            ["clip.exe"], input=texto, text=True, check=True,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _prompt_leccion(n: dict, prereqs: list[str], fuentes: str) -> str:
    import config
    return (
        f"MODELO OBLIGATORIO: {config.GEMINI_REQUIRED_MODEL}. "
        "Comprueba visualmente el selector de Gemini Web antes de responder; "
        "si no aparece exactamente ese modelo, detente.\n\n"
        f"Eres un catedrático y examinador de máxima exigencia en {n['materia']} (4º de Física UVa).\n"
        "OBJETIVO OBLIGATORIO DEL ESTUDIANTE: MATRÍCULA DE HONOR (10.0).\n"
        "Escribe la LECCIÓN RIGUROSA Y EXIGENTE para dominar este concepto al nivel de un 10 en examen oficial, "
        "sin saltos lógicos, explicando la física microscópica, las hipótesis de validez exactas, las condiciones de contorno y las trampas típicas.\n\n"
        f"Tema: {n['nombre']}\nMateria: {n['materia']}\n"
        f"Alcance: {n.get('descripcion', '')}\n"
        f"Prerrequisitos dominados: {', '.join(prereqs) or 'ninguno'}\n"
        f"Referencias: {fuentes or 'las estándar'}\n\n"
        "Devuelve Markdown con estas secciones: ## Mecanismo físico e idea central, "
        "## Deducción matemática e hipótesis de validez, ## Trampas típicas y errores en exámenes UVa, y ## Ejemplo de examen resuelto paso a paso (nivel 10)."
    )


def obtener_leccion(nid: str, regenerar: bool = False) -> str:
    os.makedirs(CACHE, exist_ok=True)
    ruta = os.path.join(CACHE, f"{nid.replace('.', '_')}.md")
    if os.path.exists(ruta) and not regenerar:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()

    import sys
    sys.path.insert(0, DIR)
    import perfil as motor
    nodos = motor.cargar_grafos()
    if nid not in nodos:
        raise ValueError(f"Nodo desconocido: {nid}")
    n = nodos[nid]
    prereqs = [nodos[p["id"]]["nombre"] for p in n.get("prerequisitos", []) if p["id"] in nodos]
    fuentes = " · ".join(f"{k} {v}" for k, v in n.get("fuentes", {}).items())
    prompt = _prompt_leccion(n, prereqs, fuentes)

    encargos = os.path.join(DIR, "encargos_gemini")
    os.makedirs(encargos, exist_ok=True)
    encargo = os.path.join(encargos, f"leccion_{nid.replace('.', '_')}.md")
    with open(encargo, "w", encoding="utf-8") as f:
        f.write(prompt)
    copiado = _copiar(prompt)
    try:
        import config
        webbrowser.open(config.GEMINI_WEB_URL)
    except Exception:
        pass
    estado = "Prompt copiado al portapapeles." if copiado else "Abre el encargo guardado en disco."
    return (
        f"# Regeneración preparada para {n['nombre']}\n\n"
        f"{estado} Gemini Web debe mostrar exactamente el modelo requerido.\n\n"
        f"Encargo: `{encargo}`\n\n"
        "La respuesta no se guarda automáticamente: copia el Markdown revisado en "
        f"`{ruta}` cuando quieras conservarlo."
    )


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("nodo")
    ap.add_argument("--regenerar", action="store_true")
    a = ap.parse_args()
    print(obtener_leccion(a.nodo, a.regenerar))
