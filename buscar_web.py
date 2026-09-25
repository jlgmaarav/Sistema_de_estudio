# -*- coding: utf-8 -*-
"""Buscador local con entrega manual a Gemini Web.

Este módulo no importa el SDK de Gemini ni realiza llamadas de red a una API.
Construye localmente un catálogo compacto de la bóveda, prepara un prompt,
lo copia al portapapeles y abre Gemini Web. La respuesta se pega de vuelta
en el Centro de Estudio y se renderiza localmente.
"""

from __future__ import annotations

import html
import re
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

import config


BASE = Path(__file__).resolve().parent
HANDOFF_DIR = BASE / "knowledge_graph" / "encargos_gemini"


def parse_yaml_field(content: str, field_name: str) -> str:
    match = re.search(rf'^{field_name}:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_yaml_list(content: str, field_name: str) -> list[str]:
    pattern = rf'^{field_name}:\s*\n((?:\s*-\s*.*?\n)+)'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        inline_match = re.search(rf'^{field_name}:\s*\[(.*?)\]', content, re.MULTILINE)
        if inline_match:
            items = [item.strip().strip('"').strip("'") for item in inline_match.group(1).split(",")]
            return [item for item in items if item]
        return []
    return [
        re.sub(r"^\s*-\s*", "", line).strip().strip('"').strip("'")
        for line in match.group(1).strip().split("\n")
        if line.strip()
    ]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def build_lightweight_catalog() -> str:
    """Devuelve un catálogo local, compacto y suficiente para buscar."""
    catalog: list[str] = []
    subjects_dir = Path(config.ASIGNATURAS_DIR)
    catalog.append("=== EJERCICIOS REGISTRADOS ===")
    if subjects_dir.exists():
        for path in sorted(subjects_dir.rglob("ejercicio_*.md")):
            content = _read(path)
            if not content:
                continue
            ex_id = parse_yaml_field(content, "id") or path.stem
            subj = parse_yaml_field(content, "asignatura")
            topic = parse_yaml_field(content, "tema")
            state = parse_yaml_field(content, "estado")
            has_err = parse_yaml_field(content, "tiene_error")
            concepts = parse_yaml_list(content, "conceptos")
            body = content.split("---")[-1].replace("\n", " ").strip()[:250]
            catalog.append(
                f"- Ejercicio: [[{ex_id}]] | Asignatura: {subj} | Tema: {topic} | "
                f"Estado: {state} | Tiene error: {has_err} | "
                f"Conceptos: {', '.join(concepts)} | Enunciado: {body}..."
            )

    catalog.append("\n=== HISTORIAL DE INTENTOS ===")
    attempts_dir = Path(config.INTENTOS_DIR)
    if attempts_dir.exists():
        for path in sorted(attempts_dir.glob("intento_*.md")):
            content = _read(path)
            att_id = parse_yaml_field(content, "id") or path.stem
            origin = parse_yaml_field(content, "ejercicio_origen").replace("[[", "").replace("]]", "")
            result = parse_yaml_field(content, "resultado")
            attempted_at = parse_yaml_field(content, "fecha_intento")
            catalog.append(
                f"- Intento: [[{att_id}]] del ejercicio [[{origin}]] | "
                f"Resultado: {result} | Fecha: {attempted_at}"
            )

    catalog.append("\n=== ERRORES HISTÓRICOS ===")
    errors_dir = Path(config.ERRORES_DIR)
    if errors_dir.exists():
        for path in sorted(errors_dir.glob("error_*.md")):
            content = _read(path)
            err_id = parse_yaml_field(content, "id") or path.stem
            subj = parse_yaml_field(content, "asignatura")
            topic = parse_yaml_field(content, "tema")
            error_types = parse_yaml_list(content, "tipo_error")
            origin = parse_yaml_field(content, "ejercicio_origen").replace("[[", "").replace("]]", "")
            details = content.split("---")[-1].replace("\n", " ").strip()[:200]
            catalog.append(
                f"- Error: [[{err_id}]] del ejercicio [[{origin}]] | Asignatura: {subj} | "
                f"Tema: {topic} | Tipos: {', '.join(error_types)} | Detalles: {details}..."
            )

    catalog.append("\n=== CONCEPTOS FÍSICOS ===")
    concepts_dir = Path(config.CONCEPTOS_DIR)
    if concepts_dir.exists():
        for path in sorted(concepts_dir.glob("*.md")):
            content = _read(path)
            concept_id = parse_yaml_field(content, "id") or path.stem
            domain = parse_yaml_field(content, "dominio_actual")
            catalog.append(f"- Concepto: [[{concept_id}]] | Dominio actual: {domain}")
    return "\n".join(catalog)


def build_search_prompt(query: str) -> str:
    catalog = build_lightweight_catalog()
    return (
        "Eres el buscador personal de un estudiante de Física de la UVa. "
        "Trabajas únicamente con el catálogo local que aparece abajo.\n\n"
        f"CONSULTA DEL ESTUDIANTE:\n{query.strip()}\n\n"
        "TAREA:\n"
        "- Busca ejercicios, intentos, errores y conceptos relevantes.\n"
        "- No inventes resultados ni enlaces que no aparezcan en el catálogo.\n"
        "- Devuelve únicamente Markdown.\n"
        f"- Empieza con '# Resultados de búsqueda: {query.strip()}'.\n"
        "- Agrupa por ejercicios recomendados, errores relacionados y conceptos clave.\n"
        "- Para cada resultado usa los enlaces [[id]] existentes y explica en una o dos líneas "
        "por qué es relevante.\n"
        "- Si no hay coincidencias, dilo claramente y sugiere términos cercanos del catálogo.\n\n"
        "CATÁLOGO LOCAL:\n"
        f"{catalog}\n"
    )


def _copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(
            ["clip.exe"],
            input=text,
            text=True,
            check=True,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def prepare_search_handoff(query: str) -> dict:
    """Guarda el prompt, lo copia y abre Gemini Web; nunca usa una API."""
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    prompt_path = HANDOFF_DIR / f"busqueda_{stamp}_encargo.md"
    prompt_path.write_text(build_search_prompt(query), encoding="utf-8")
    copied = _copy_to_clipboard(prompt_path.read_text(encoding="utf-8"))
    try:
        opened = bool(webbrowser.open(config.GEMINI_WEB_URL))
    except Exception:
        opened = False
    return {
        "query": query.strip(),
        "prompt_path": str(prompt_path),
        "copied": copied,
        "opened": opened,
        "model": config.GEMINI_REQUIRED_MODEL,
    }


def _strip_fences(markdown: str) -> str:
    text = (markdown or "").strip()
    text = re.sub(r"^\x60\x60\x60(?:markdown|md)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\x60\x60\x60$", "", text)
    return text.strip()


def _inline_html(text: str) -> str:
    def link_repl(match: re.Match) -> str:
        name = match.group(1).strip()
        shown = html.escape(name)
        if name.startswith("ejercicio_") and re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            safe = html.escape(name, quote=True)
            return (
                f'<a href="#" class="obsidian-link" data-exercise-id="{safe}" '
                f'onclick="viewExercise(this.dataset.exerciseId); return false;">{shown}</a>'
            )
        kind = "error" if name.startswith("error_") else "attempt" if name.startswith("intento_") else "concept"
        return f'<span class="obsidian-badge {kind}">{shown}</span>'

    text = html.escape(text, quote=False)
    text = re.sub(r"\[\[(.*?)\]\]", link_repl, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\x60([^\x60]+)\x60", r"<code>\1</code>", text)
    return text


def markdown_to_html(markdown: str) -> str:
    """Renderiza una salida Markdown de Gemini sin permitir HTML arbitrario."""
    lines = _strip_fences(markdown).splitlines()
    output: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            close_list()
            continue
        if line.startswith("### "):
            close_list()
            output.append(f"<h3>{_inline_html(line[4:])}</h3>")
        elif line.startswith("## "):
            close_list()
            output.append(f"<h2>{_inline_html(line[3:])}</h2>")
        elif line.startswith("# "):
            close_list()
            output.append(f"<h1>{_inline_html(line[2:])}</h1>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{_inline_html(line[2:])}</li>")
        else:
            close_list()
            output.append(f"<p>{_inline_html(line)}</p>")
    close_list()
    return "\n".join(output)
