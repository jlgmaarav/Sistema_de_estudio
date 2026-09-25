# -*- coding: utf-8 -*-
"""Apuntes personales vivos por asignatura.

La conversación no se copia literalmente a un documento. Este módulo conserva
una capa estructurada y privada de evidencias: qué se ha trabajado, qué parece
estable, qué cuesta, qué errores se repiten y qué procedimiento conviene usar
en un examen. A partir de esa capa genera un ``main.tex`` por asignatura.

El estado y los .tex son datos personales. El código del generador sí puede
versionarse, pero los resultados se mantienen fuera del repositorio público.
"""
from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "knowledge_graph", "apuntes_personales.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "apuntes_generados")
_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "asignatura"


def _default_state() -> dict:
    return {"version": 1, "updated_at": None, "subjects": {}}


def load_state() -> dict:
    with _LOCK:
        if not os.path.exists(STATE_PATH):
            return _default_state()
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError):
            return _default_state()
        base = _default_state()
        if isinstance(state, dict):
            base.update({k: v for k, v in state.items() if k in base})
        if not isinstance(base.get("subjects"), dict):
            base["subjects"] = {}
        return base


def save_state(state: dict) -> None:
    with _LOCK:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        state["updated_at"] = _now()
        temp = STATE_PATH + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(temp, STATE_PATH)


def _empty_node(node_id: str, title: str, node: dict | None = None) -> dict:
    node = node or {}
    return {
        "id": node_id,
        "title": title or node_id,
        "description": str(node.get("descripcion", ""))[:1200],
        "source_nodes": [str(node.get("id"))] if node.get("id") else [],
        "teoria": [],
        "aclaraciones": [],
        "explanations": [],
        "personal_explanations": [],
        "strengths": [],
        "difficulties": [],
        "recurrent_errors": [],
        "procedures": [],
        "examples": [],
        "evidence": [],
        "quality_samples": [],
        "last_result": None,
        "prerequisites": [
            {"id": str(item.get("id")), "weight": item.get("peso", 1.0)}
            for item in (node.get("prerequisitos", []) if node else [])
            if item.get("id")
        ],
        "updated_at": None,
    }


def _empty_subject(name: str) -> dict:
    return {
        "materia": name,
        "nodes": {},
        "recurrent_errors": [],
        "evidence": [],
        "updated_at": None,
    }


def _clean(value, limit: int = 1200) -> str:
    return str(value or "").strip()[:limit]


def _clean_list(values, limit: int = 12, item_limit: int = 900) -> list[str]:
    result = []
    for value in values or []:
        text = _clean(value, item_limit)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _add_unique(values: list, new_values, limit: int = 40) -> None:
    for value in new_values or []:
        if isinstance(value, dict):
            key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            key = str(value)
        existing = [json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, dict) else str(x) for x in values]
        if key not in existing:
            values.append(value)
        if len(values) > limit:
            del values[:-limit]


def _node_for(subject: dict, node_id: str, node: dict | None, title: str = "") -> dict:
    node_id = str(node_id or "")
    node_id = node_id or f"sin-nodo-{slugify(title)}"
    node_key = slugify(node_id)
    node_map = subject.setdefault("nodes", {})
    if node_key not in node_map:
        node_title = (node or {}).get("nombre", "") or title or node_id or "Tema sin clasificar"
        node_map[node_key] = _empty_node(node_id, node_title, node)
    chapter = node_map[node_key]
    if node_id and node_id not in chapter.setdefault("source_nodes", []):
        chapter["source_nodes"].append(node_id)
    return chapter


def _apply_update(chapter: dict, update: dict, evidence: dict) -> None:
    """Fusiona una observación sin borrar evidencias anteriores."""
    for t in update.get("teoria", []):
        t_clean = str(t).strip()[:50000]
        if t_clean and t_clean not in chapter.setdefault("teoria", []):
            chapter["teoria"].append(t_clean)

    for ac in update.get("aclaraciones", []):
        if isinstance(ac, dict):
            duda = str(ac.get("duda", ac.get("pregunta", ""))).strip()[:1000]
            resp = str(ac.get("aclaracion", ac.get("respuesta", ""))).strip()[:4000]
            if duda or resp:
                entry = {"duda": duda, "aclaracion": resp}
                if entry not in chapter.setdefault("aclaraciones", []):
                    chapter["aclaraciones"].append(entry)
        elif isinstance(ac, str) and ac.strip():
            entry = ac.strip()[:4000]
            if entry not in chapter.setdefault("aclaraciones", []):
                chapter["aclaraciones"].append(entry)

    _add_unique(chapter.setdefault("explanations", []), _clean_list(update.get("explanations", [])))
    _add_unique(chapter.setdefault("personal_explanations", []), _clean_list(update.get("personal_explanations", [])))
    _add_unique(chapter.setdefault("strengths", []), _clean_list(update.get("strengths", [])))
    _add_unique(chapter.setdefault("difficulties", []), _clean_list(update.get("difficulties", [])))
    _add_unique(chapter.setdefault("recurrent_errors", []), _clean_list(update.get("recurrent_errors", [])))
    _add_unique(chapter.setdefault("procedures", []), _clean_list(update.get("procedures", [])))
    _add_unique(chapter.setdefault("examples", []), _clean_list(update.get("examples", [])))
    if update.get("result"):
        chapter["last_result"] = _clean(update["result"], 80)
    quality = update.get("quality")
    if quality is not None:
        try:
            chapter.setdefault("quality_samples", []).append(round(max(0.0, min(1.0, float(quality))), 2))
            chapter["quality_samples"] = chapter["quality_samples"][-20:]
        except (TypeError, ValueError):
            pass
    if evidence:
        _add_unique(chapter.setdefault("evidence", []), [evidence], limit=30)
    chapter["updated_at"] = _now()


def _subject_update(subject_name: str, chapter_updates: list[dict], evidence: dict,
                    nodes: dict | None = None) -> None:
    state = load_state()
    subjects = state.setdefault("subjects", {})
    subject = subjects.setdefault(subject_name, _empty_subject(subject_name))
    nodes = nodes or {}
    for update in chapter_updates:
        node_id = update.get("node_id", "")
        chapter = _node_for(subject, node_id, nodes.get(node_id), update.get("chapter_title", ""))
        _apply_update(chapter, update, evidence)
    if evidence:
        _add_unique(subject.setdefault("evidence", []), [evidence], limit=60)
    _add_unique(subject.setdefault("recurrent_errors", []), _clean_list(evidence.get("recurrent_errors", []) if evidence else []))
    subject["updated_at"] = _now()
    save_state(state)


def apply_walk_report(session: dict, report: dict, nodes: dict | None = None) -> dict:
    """Incorpora el cierre de un paseo y genera apuntes para sus nodos."""
    nodes = nodes or {}
    report = report or {}
    by_id = {str(item.get("id")): item for item in report.get("nodos", []) if item.get("id")}
    custom = {str(item.get("node_id") or item.get("id")): item for item in report.get("apuntes", []) if item.get("node_id") or item.get("id")}
    grouped: dict[str, list[dict]] = {}
    errors = _clean_list(report.get("errores_recurrentes", []), 20, 500)
    target_node_ids = []
    seen = set()
    for nid in list(session.get("plan_ids", [])) + list(by_id.keys()) + list(custom.keys()):
        nid = str(nid)
        if nid and nid not in seen:
            seen.add(nid)
            target_node_ids.append(nid)

    for node_id in target_node_ids:
        item = by_id.get(node_id)
        note = custom.get(node_id, {})
        if not item and not note:
            continue
        node = nodes.get(node_id, {})
        subject_name = node.get("materia", "Sin asignatura")
        result = item.get("resultado", note.get("resultado", "parcial")) if item else note.get("resultado", "parcial")
        quality = item.get("calidad", note.get("calidad", 0.0)) if item else note.get("calidad", 0.0)
        strengths = list(item.get("dominado", [])) if item else []
        difficulties = list(item.get("dudas", [])) if item else []
        if result in {"debil", "no_trabajado"} and not difficulties:
            difficulties.append("Requiere una explicación y práctica adicional antes de considerarlo estable.")
        if result == "parcial" and not difficulties:
            difficulties.append("Comprensión parcial: comprobar hipótesis, límites y aplicación en problemas.")

        raw_teoria = note.get("teoria", [])
        if isinstance(raw_teoria, str):
            teoria = [raw_teoria[:50000]] if raw_teoria.strip() else []
        elif isinstance(raw_teoria, list):
            teoria = [str(x)[:25000] for x in raw_teoria if str(x).strip()][:8]
        else:
            teoria = []

        raw_aclaraciones = note.get("aclaraciones", note.get("dudas_resueltas", []))
        aclaraciones = []
        if isinstance(raw_aclaraciones, list):
            for entry in raw_aclaraciones[:15]:
                if isinstance(entry, dict):
                    aclaraciones.append({
                        "duda": str(entry.get("duda", entry.get("pregunta", "")))[:1000],
                        "aclaracion": str(entry.get("aclaracion", entry.get("respuesta", "")))[:4000],
                    })
                elif isinstance(entry, str) and entry.strip():
                    aclaraciones.append(entry.strip()[:4000])
        elif isinstance(raw_aclaraciones, dict):
            aclaraciones.append({
                "duda": str(raw_aclaraciones.get("duda", raw_aclaraciones.get("pregunta", "")))[:1000],
                "aclaracion": str(raw_aclaraciones.get("aclaracion", raw_aclaraciones.get("respuesta", "")))[:4000],
            })
        elif isinstance(raw_aclaraciones, str) and raw_aclaraciones.strip():
            aclaraciones.append(raw_aclaraciones.strip()[:4000])

        update = {
            "node_id": node_id,
            "chapter_title": node.get("nombre", node_id),
            "result": result,
            "quality": quality,
            "teoria": teoria,
            "aclaraciones": aclaraciones,
            "strengths": strengths + note.get("bien_entendido", note.get("fortalezas", [])),
            "difficulties": difficulties + note.get("dificultades", []),
            "recurrent_errors": errors + note.get("errores", []),
            "explanations": note.get("explicacion_validada", note.get("explicaciones", [])),
            "personal_explanations": note.get("explicacion_para_mi", note.get("personales", [])),
            "procedures": note.get("procedimiento_examen", note.get("procedimientos", [])),
            "examples": note.get("ejemplos", []),
        }
        grouped.setdefault(subject_name, []).append(update)
    evidence_base = {
        "kind": "walk",
        "session_id": _clean(session.get("id", ""), 80),
        "date": _now(),
        "summary": _clean(report.get("resumen", ""), 1000),
        "recommendation": _clean(report.get("recomendacion", ""), 700),
        "recurrent_errors": errors,
    }
    for subject_name, updates in grouped.items():
        evidence = {**evidence_base, "node_ids": [u["node_id"] for u in updates]}
        _subject_update(subject_name, updates, evidence, nodes)
    return {"subjects": sorted(grouped), "nodos": sum(len(x) for x in grouped.values()), "evidence": evidence_base}


def apply_problem_response(response, exerc_id: str = "", attempt_id: str = "", nodes: dict | None = None) -> dict:
    """Convierte una corrección de ejercicio en observaciones para los apuntes."""
    nodes = nodes or {}
    subject_name = _clean(getattr(response, "asignatura_detectada", "Sin asignatura"), 160) or "Sin asignatura"
    ids = [str(x) for x in (getattr(response, "nodos_detectados", []) or [])]
    if not ids:
        ids = [""]
    errors = []
    for error in getattr(response, "errores", []) or []:
        errors.append(_clean(getattr(error, "titulo", ""), 300))
        if getattr(error, "como_evitarlo", ""):
            errors.append(_clean(getattr(error, "como_evitarlo", ""), 600))
    checkpoints = getattr(response, "checkpoints", []) or []
    procedures = [_clean(getattr(cp, "descripcion", ""), 500) for cp in checkpoints if getattr(cp, "correcto", False)]
    summary = _clean(getattr(response, "resumen_correccion", ""), 1000)
    analysis = _clean(getattr(response, "analisis_detallado", ""), 1400)
    result = _clean(getattr(response, "resultado", ""), 80)
    quality = 1.0 if result == "correcto" and not getattr(response, "tiene_error", False) else 0.5 if result == "incompleto" else 0.25
    updates = []
    for node_id in ids:
        node = nodes.get(node_id, {})
        updates.append({
            "node_id": node_id,
            "chapter_title": node.get("nombre") or getattr(response, "tema_detectado", "Ejercicios"),
            "result": result,
            "quality": quality,
            "strengths": [summary] if result == "correcto" and summary else [],
            "difficulties": [summary] if result != "correcto" and summary else [],
            "recurrent_errors": errors,
            "explanations": [analysis] if analysis else [],
            "procedures": procedures,
            "examples": [getattr(response, "transcripcion_enunciado", "")[:900]] if getattr(response, "transcripcion_enunciado", "") else [],
        })
    evidence = {
        "kind": "problem",
        "date": _now(),
        "exercise_id": _clean(exerc_id, 80),
        "attempt_id": _clean(attempt_id, 80),
        "title": _clean(getattr(response, "titulo_corto", ""), 200),
        "node_ids": ids,
        "recurrent_errors": errors,
    }
    _subject_update(subject_name, updates, evidence, nodes)
    return {"subjects": [subject_name], "nodos": len(updates), "evidence": evidence}


def _status(chapter: dict) -> str:
    samples = chapter.get("quality_samples", [])
    if len(samples) >= 2 and sum(samples[-3:]) / len(samples[-3:]) >= 0.8:
        return "estable"
    if samples and sum(samples[-3:]) / len(samples[-3:]) >= 0.5:
        return "en consolidación"
    return "prioridad de repaso"


def _latex_escape(text: str) -> str:
    """Escapa texto normal, conservando fórmulas LaTeX delimitadas."""
    text = str(text or "").replace("\r", "")
    pieces = re.split(r"(\\\(.+?\\\)|\\\[.*?\\\]|\$\$.*?\$\$|\$[^$\n]+\$)", text, flags=re.DOTALL)
    out = []
    for piece in pieces:
        if not piece:
            continue
        if re.fullmatch(r"\\\(.+?\\\)|\\\[.*?\\\]|\$\$.*?\$\$|\$[^$\n]+\$", piece, flags=re.DOTALL):
            if piece.startswith("$$") and piece.endswith("$$"):
                out.append("\\[" + piece[2:-2] + "\\]")
            else:
                out.append(piece)
            continue
        piece = re.sub(r"^\s*#{1,6}\s*", "", piece, flags=re.MULTILINE)
        unicode_map = {
            "ρ": r"$\rho$", "ε": r"$\varepsilon$", "σ": r"$\sigma$", "λ": r"$\lambda$",
            "θ": r"$\theta$", "φ": r"$\phi$", "π": r"$\pi$", "∇": r"$\nabla$",
            "×": r"$\times$", "·": r"$\cdot$", "±": r"$\pm$", "μ": r"$\mu$",
            "Ω": r"$\Omega$", "ħ": r"$\hbar$", "₀": r"$_0$", "₁": r"$_1$",
            "₂": r"$_2$", "₃": r"$_3$", "₄": r"$_4$", "₅": r"$_5$",
        }
        for uchar, repl in unicode_map.items():
            piece = piece.replace(uchar, repl)
        # Algunos registros antiguos guardan comandos matemáticos sin $...$.
        # Los envolvemos de forma conservadora para que sigan siendo legibles
        # al regenerar el documento.
        legacy_math: list[str] = []

        def protect_math(match):
            legacy_math.append(match.group(0))
            return f"@@LATEXMATH{len(legacy_math) - 1}@@"

        piece = re.sub(r"\\vec\s+[A-Za-z]", protect_math, piece)
        piece = re.sub(
            r"([A-Za-z])_\{\\(?:mathrm|mathbf|boldsymbol)\{[^{}]*\}\}",
            protect_math,
            piece,
        )
        piece = re.sub(
            r"([A-Za-z])_\\([A-Za-z]+)",
            protect_math,
            piece,
        )
        piece = re.sub(
            r"\\(?:hat|vec|mathbf|boldsymbol|mathrm|text)\{(?:\\(?:mathbf|boldsymbol)\{[^{}]*\}|[^{}]*)\}",
            protect_math,
            piece,
        )
        piece = re.sub(
            r"\\(?:rho_v|epsilon_0|varepsilon_0|epsilon|varepsilon|rho|theta|phi|lambda|sigma|pi|nabla|partial|oint|cdot|ge|le|to|sin|cos|tan|sqrt|infty|vec)(?:[_^](?:\{[^{}]*\}|[A-Za-z0-9]+))?(?![A-Za-z])",
            protect_math,
            piece,
        )
        piece = re.sub(r"(?<![A-Za-z\\])([A-Za-z]+(?:_[A-Za-z0-9]+|\^[+-]?[A-Za-z0-9]+)+)", protect_math, piece)
        piece = re.sub(r"\\[,;:!]", protect_math, piece)
        piece = piece.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
        piece = piece.replace("_", r"\_").replace("^", r"\textasciicircum{}").replace("{", r"\{").replace("}", r"\}")
        piece = piece.replace("**", "")
        for index, math in enumerate(legacy_math):
            piece = piece.replace(f"@@LATEXMATH{index}@@", f"${math}$")
        out.append(piece)
    return "".join(out)


def _latex_list(items: list[str]) -> str:
    items = [x for x in items if str(x).strip()]
    if not items:
        return ""
    return "\\begin{itemize}\n" + "\n".join(f"\\item {_latex_escape(x)}" for x in items) + "\n\\end{itemize}\n"


def _section(title: str, body: str) -> str:
    return f"\\subsection{{{_latex_escape(title)}}}\n{body}\n"


def _equations(items: list[str]) -> str:
    """Renderiza ecuaciones de confianza como bloques independientes."""
    return "\n".join(f"\\[{item}\\]\n" for item in items if str(item).strip())


def _warning_box(title: str, paragraphs: list[str]) -> str:
    """Una anotacion personal visible, pero subordinada a la teoria."""
    content = _paragraphs(paragraphs)
    return (
        "\\begin{center}\n"
        "\\fcolorbox{warningline}{warningbg}{%\n"
        "\\begin{minipage}{0.88\\linewidth}\n"
        f"\\textbf{{{_latex_escape(title)}}}\\par\n"
        "\\small\n"
        f"{content}\n"
        "\\end{minipage}}\n"
        "\\end{center}\n"
    )


NODE_GUIDES = {
    # Este bloque convierte el cierre del paseo de el.1.01 en una ficha de
    # estudio real: la evidencia personal queda después de la teoría y no la
    # sustituye.
    "el.1.01": {
        "objectives": [
            "Relacionar la estructura de bandas con la diferencia entre conductor, semiconductor y aislante.",
            "Explicar qué significa que un semiconductor sea intrínseco o extrínseco y qué papel tienen donores y aceptores.",
            "Justificar por qué una banda llena no conduce y por qué una banda parcialmente llena sí puede responder a un campo.",
            "Distinguir excitación térmica, excitación fotónica y túnel Zener en un diagrama de bandas.",
        ],
        "concepts": [
            "Un sólido no ofrece cualquier energía a sus electrones: la periodicidad de la red genera estados permitidos que se organizan en bandas.",
            "La banda de valencia contiene los estados ligados relevantes y la banda de conducción los estados de mayor energía que pueden participar en el transporte. Entre ambas puede existir una banda prohibida de anchura $E_g=E_c-E_v$.",
            "La energía de Fermi $E_F$ sirve para describir la ocupación electrónica. No es la energía que tengan todos los electrones ni implica que los electrones por debajo de ella estén quietos.",
        ],
        "development": [
            "En un conductor existe una banda parcialmente ocupada o bandas solapadas: hay estados vacíos arbitrariamente próximos a los ocupados, de modo que un campo puede producir una redistribución asimétrica.",
            "En un semiconductor o aislante, la banda de valencia está llena y la de conducción vacía en el modelo ideal a 0 K. La diferencia entre ambos está principalmente en el tamaño del gap: un gap pequeño permite generar portadores con temperatura, luz o campo intenso con más facilidad.",
            "Un semiconductor intrínseco es idealmente puro y sus portadores aparecen por excitación térmica: cada electrón que pasa a la banda de conducción deja un hueco en la banda de valencia, por lo que $n=p=n_i$ en equilibrio.",
            "En un semiconductor extrínseco se introducen impurezas controladas. Un donor aporta niveles próximos a la banda de conducción y favorece material tipo n; un aceptor introduce niveles próximos a la banda de valencia y favorece material tipo p.",
            "Los semiconductores elementales, como silicio o germanio, y los compuestos, como arseniuro de galio, comparten la lógica de bandas, pero pueden diferir en gap, movilidad, estructura cristalina y tipo de transición óptica.",
        ],
        "transport": [
            "La velocidad de grupo de un paquete electrónico en una banda se escribe como $\\mathbf{v}(\\mathbf{k})=\\frac{1}{\\hbar}\\nabla_{\\mathbf{k}}E(\\mathbf{k})$. El campo no se interpreta como una simple aceleración de partículas libres: cambia la distribución de ocupación en el espacio de momentos.",
            "La densidad de corriente puede expresarse esquemáticamente como $\\mathbf{J}=-e\\sum_{\\mathbf{k}}f(\\mathbf{k})\\mathbf{v}(\\mathbf{k})$ (o como una integral sobre la Zona de Brillouin). La corriente neta depende de la distribución $f(\\mathbf{k})$, no de sumar magnitudes de velocidades sin signo.",
            "En una banda llena, a cada estado con $+\\mathbf{k}$ le corresponde otro con velocidad opuesta. La suma se cancela y queda $\\mathbf{J}=0$ aunque cada electrón tenga energía y movimiento microscópico.",
            "Cuando faltan electrones en una banda casi llena, los estados vacíos permiten que la distribución deje de ser simétrica. Es más cómodo describir esas ausencias como huecos con carga efectiva positiva.",
        ],
        "transitions": [
            "Excitación térmica: la energía procede de la temperatura y la ocupación cambia entre bandas cuando la energía térmica disponible es suficiente.",
            "Excitación fotónica: un fotón aporta energía $\\hbar\\omega$ y la transición se dibuja vertical en un diagrama energía--momento cuando se desprecia su momento frente al del electrón.",
            "Túnel Zener: un campo eléctrico intenso inclina las bandas y permite atravesar el gap mediante una transición esencialmente isoenergética en la representación espacial. No es un salto vertical de energía producido por un fotón.",
        ],
        "comparison": [
            "Conducción frente a movimiento microscópico: que haya electrones moviéndose no basta; debe existir una ocupación asimétrica y estados vacíos accesibles.",
            "Energía frente a ocupación: a 0 K se suprime la agitación térmica, pero permanecen la energía de Fermi, la estructura de bandas y el movimiento asociado a los estados ocupados.",
            "Absorción frente a Zener: la primera cambia la energía del portador mediante un cuanto de radiación o una excitación térmica; el segundo conecta estados a través del gap por el campo aplicado.",
        ],
        "worked_example": [
            "Semiconductor ideal a 0 K y en oscuridad: la banda de valencia está llena, la de conducción vacía y no hay portadores libres térmicos. No se concluye que los electrones carezcan de energía; se concluye que no hay una redistribución neta disponible para transportar corriente.",
            "Si un fotón promueve un electrón a la banda de conducción, aparecen simultáneamente un electrón y un hueco. Si el campo separa sus movimientos y existen estados accesibles, la respuesta puede ser una corriente medible.",
            "Si en lugar de luz se aplica un campo suficientemente intenso, el esquema correcto es dibujar la inclinación de las bandas y el túnel Zener; etiquetar el proceso como absorción fotónica sería confundir dos mecanismos distintos.",
        ],
        "summary": [
            "Las bandas y su ocupación determinan la posibilidad de conducción.",
            "Una banda llena no produce corriente neta por cancelación de estados opuestos.",
            "Intrínseco significa portadores generados en el material puro; extrínseco, controlados mediante dopado.",
            "Temperatura, fotones y campo intenso pueden generar portadores, pero mediante mecanismos diferentes.",
        ],
        "idea": (
            "La conducción no depende de que los electrones estén simplemente en movimiento, "
            "sino de que puedan cambiar su estado dentro de la estructura de bandas. "
            "Una banda completamente llena no admite una corriente neta aunque sus electrones "
            "tengan energía y movimiento microscópico."
        ),
        "mechanism": [
            "En un sólido los estados permitidos se agrupan en bandas separadas, en general, por un intervalo prohibido.",
            "Para producir corriente debe existir una redistribución asimétrica de ocupaciones y estados vacíos accesibles; en una banda llena las contribuciones de estados con +k y -k se compensan.",
            "A 0 K desaparece la excitación térmica, pero no la energía de Fermi ni el movimiento asociado a los estados ocupados.",
            "La absorción térmica o fotónica se representa como un salto vertical de energía; el efecto Zener bajo campo intenso es un túnel isoenergético asociado a la inclinación de las bandas.",
        ],
        "formalism": [
            "Justificar la corriente nula de una banda llena mediante la suma o integral de velocidades v(k) sobre toda la Zona de Brillouin.",
            "Distinguir explícitamente el eje de energía del eje espacial en un diagrama E-x antes de dibujar una transición.",
            "Conectar la descripción microscópica con la densidad de corriente J y explicar qué estados vacíos permiten una respuesta neta.",
        ],
        "limits": [
            "El argumento de banda llena a 0 K es un argumento de ocupación cuántica, no una afirmación de que los electrones estén quietos.",
            "El efecto Zener requiere un campo suficientemente intenso; no debe confundirse con una excitación por fotón o por temperatura.",
            "Hay que separar siempre energía de los electrones, ocupación de estados y velocidad de deriva macroscópica.",
        ],
        "self_check": [
            "¿Por qué una banda llena puede tener electrones con energía y, aun así, corriente neta nula?",
            "¿Qué diferencia hay entre una transición fotónica vertical y el túnel Zener horizontal en un diagrama E-x?",
            "¿Qué papel desempeñan la Zona de Brillouin y los estados vacíos en la conducción?",
        ],
    },

    "em.0.05": {
        "idea": (
            "Una integral espacial no empieza por los limites: empieza por decidir que objeto geometrico se recorre. "
            "El elemento escalar mide longitud, area o volumen; el elemento vectorial anade la orientacion necesaria "
            "para calcular una circulacion o un flujo."
        ),
        "objectives": [
            "Distinguir los elementos diferenciales de linea, superficie y volumen.",
            "Construir el vector normal y su signo en cada cara de una superficie cerrada.",
            "Interpretar un flujo como la componente normal del campo y usar el teorema de la divergencia cuando convenga.",
        ],
        "concepts": [
            "En una integral de linea se recorre una curva. El elemento vectorial d\\mathbf{l} es tangente a la curva y su orientacion depende del sentido elegido; por eso una circulacion puede cambiar de signo al invertir el recorrido.",
            "En una integral de superficie, dS es un area escalar. En cambio, d\\mathbf{S}=\\hat{\\mathbf{n}}\\,dS es un area orientada: su direccion es la normal a la superficie y su sentido debe fijarse, normalmente hacia fuera si la superficie es cerrada.",
            "El flujo de un campo vectorial mide cuanto campo atraviesa la superficie. Solo participa la componente normal: si el campo es tangente, el producto escalar \\mathbf{F}\\cdot d\\mathbf{S} es cero.",
            "Los elementos diferenciales no son adornos de la notacion. Contienen la geometria de la region y determinan tanto las dimensiones como los signos del resultado.",
        ],
        "development": [
            "En cartesianas, una cara x=constante tiene area dy\\,dz y su normal es paralela al eje x. La cara x=x_0+a tiene normal +\\hat{\\mathbf{i}}, mientras que la cara x=x_0 tiene normal -\\hat{\\mathbf{i}}.",
            "Las caras y=constante y z=constante se construyen de la misma forma. Si el campo es paralelo a una de esas caras, el flujo a traves de ella desaparece porque el campo no tiene componente normal.",
            "El teorema de la divergencia convierte el flujo total que sale de una superficie cerrada en una integral de volumen de la divergencia. Es una igualdad geometrica: el balance de lo que sale por la frontera coincide con la suma de las fuentes locales del interior.",
        ],
        "equations": [
            r"d\mathbf{l}=dx\,\hat{\mathbf{i}}+dy\,\hat{\mathbf{j}}+dz\,\hat{\mathbf{k}}",
            r"d\mathbf{S}=\hat{\mathbf{n}}\,dS",
            r"d\mathbf{S}_{x=\mathrm{cte}}=\pm\,dy\,dz\,\hat{\mathbf{i}},\qquad dV=dx\,dy\,dz",
            r"\oint_{\partial V}\mathbf{F}\cdot d\mathbf{S}=\int_V(\nabla\cdot\mathbf{F})\,dV",
        ],
        "formalism": [
            "Para un flujo, escribir primero el producto escalar \\mathbf{F}\\cdot\\hat{\\mathbf{n}} y despues el area diferencial. No se debe tratar dS como si ya incluyera la normal.",
            "En una superficie cerrada, orientar todas las normales hacia el exterior. En caras opuestas, los signos son contrarios aunque el area escalar tenga el mismo valor.",
            "Elegir entre integrar cara por cara o usar la divergencia. El segundo camino es especialmente util cuando la divergencia es sencilla y la superficie encierra un volumen regular.",
        ],
        "worked_example": [
            "Consideremos \\mathbf{F}=x\\,\\hat{\\mathbf{i}} en el cubo x_0\\le x\\le x_0+a, y_0\\le y\\le y_0+a, z_0\\le z\\le z_0+a. En las cuatro caras y=constante y z=constante el campo es tangente, de modo que su flujo es cero.",
            "En la cara x=x_0, la normal exterior es -\\hat{\\mathbf{i}} y el flujo vale -x_0a^2. En la cara x=x_0+a, la normal es +\\hat{\\mathbf{i}} y el flujo vale (x_0+a)a^2. El flujo total es, por tanto, $-x_0a^2+(x_0+a)a^2=a^3$.",
            "La misma respuesta sale con la divergencia: \\nabla\\cdot\\mathbf{F}=1 y el volumen del cubo es a^3, luego $\\int_V1\\,dV=a^3$. Que el resultado no dependa de x_0 no significa que el campo sea uniforme; significa que el incremento del campo entre las dos caras siempre es el mismo cuando la arista mide a.",
        ],
        "comparison": [
            "Flujo y circulacion no son la misma operacion: el flujo usa la componente normal sobre una superficie, mientras que la circulacion usa la componente tangente a lo largo de una curva.",
            "El teorema de la divergencia no sustituye a la ley de Gauss. Es una identidad matematica general; la ley de Gauss relaciona el flujo electrico cerrado con la carga encerrada.",
        ],
        "limits": [
            "El teorema de la divergencia exige una superficie cerrada y una orientacion coherente hacia el exterior.",
            "Si se escribe solo dS, se esta usando el elemento escalar. El signo y la direccion aparecen al multiplicar por la normal.",
            "Un campo puede tener modulo no nulo y producir flujo cero a traves de una superficie si es tangente a ella.",
        ],
        "practice_warnings": [
            "El error mas importante es mezclar dS con d\\mathbf{S}. En una cara plana, dy\\,dz mide el area; el signo y la direccion los aporta la normal.",
            "En el cubo de \\mathbf{F}=x\\,\\hat{\\mathbf{i}}, el campo no entra en diagonal: es perpendicular a las caras x=constante y tangente a las caras y=constante y z=constante.",
        ],
    },

    "em.0.08": {
        "idea": (
            "Los factores de escala traducen un pequeno cambio de coordenada en una longitud fisica. "
            "En coordenadas curvilineas los diferenciales angulares no son longitudes por si mismos: generan arcos "
            "cuya longitud depende de la distancia al eje o al origen."
        ),
        "objectives": [
            "Reconocer las convenciones y la geometria de las coordenadas cilindricas y esfericas.",
            "Calcular los factores de escala a partir del vector de posicion.",
            "Construir elementos de linea, superficie y volumen sin memorizar factores aislados.",
        ],
        "concepts": [
            "En cilindricas se usan (\\rho,\\phi,z): \\rho es la distancia al eje z, \\phi es el azimut en el plano xy y z conserva su significado cartesiano.",
            "En esfericas se usan aqui (r,\\theta,\\phi): r es la distancia al origen, \\theta es el angulo polar medido desde el eje z y \\phi es el azimut. Algunos libros intercambian los nombres de los angulos, por lo que siempre hay que mirar la definicion.",
            "Si u_i es una coordenada, su factor de escala es h_i=|\\partial\\mathbf{r}/\\partial u_i|. El elemento de longitud asociado es h_i\\,du_i: la derivada indica hacia donde se mueve el punto y el modulo indica cuanto mide ese desplazamiento.",
        ],
        "development": [
            "En cilindricas, variar \\rho recorre una distancia d\\rho, variar z recorre dz y variar \\phi recorre un arco de radio \\rho, cuya longitud es \\rho\\,d\\phi. Por eso aparece un unico factor \\rho en las superficies y el volumen.",
            "En esfericas, variar r recorre dr, variar \\theta recorre un arco de radio r y variar \\phi recorre un paralelo de radio r\\sin\\theta. Por eso los dos diferenciales angulares llevan factores geometricos distintos.",
            "El producto de los tres factores de escala da el volumen: h_1h_2h_3\\,du_1du_2du_3. Esta regla explica el origen geometrico de cada factor y permite reconstruirlo si se olvida.",
        ],
        "equations": [
            r"\mathbf{r}=\rho\cos\phi\,\hat{\mathbf{i}}+\rho\sin\phi\,\hat{\mathbf{j}}+z\,\hat{\mathbf{k}},\qquad (h_\rho,h_\phi,h_z)=(1,\rho,1)",
            r"\mathbf{r}=r\sin\theta\cos\phi\,\hat{\mathbf{i}}+r\sin\theta\sin\phi\,\hat{\mathbf{j}}+r\cos\theta\,\hat{\mathbf{k}},\qquad (h_r,h_\theta,h_\phi)=(1,r,r\sin\theta)",
            r"d\mathbf{l}=d\rho\,\hat{\boldsymbol{\rho}}+\rho\,d\phi\,\hat{\boldsymbol{\phi}}+dz\,\hat{\mathbf{z}},\qquad dV=\rho\,d\rho\,d\phi\,dz",
            r"d\mathbf{l}=dr\,\hat{\mathbf{r}}+r\,d\theta\,\hat{\boldsymbol{\theta}}+r\sin\theta\,d\phi\,\hat{\boldsymbol{\phi}},\qquad dV=r^2\sin\theta\,dr\,d\theta\,d\phi",
            r"d\mathbf{S}_\rho=\rho\,d\phi\,dz\,\hat{\boldsymbol{\rho}},\quad d\mathbf{S}_z=\rho\,d\rho\,d\phi\,\hat{\mathbf{z}}",
            r"d\mathbf{S}_r=r^2\sin\theta\,d\theta\,d\phi\,\hat{\mathbf{r}},\quad d\mathbf{S}_\theta=r\sin\theta\,dr\,d\phi\,\hat{\boldsymbol{\theta}},\quad d\mathbf{S}_\phi=r\,dr\,d\theta\,\hat{\boldsymbol{\phi}}",
        ],
        "formalism": [
            "Para reconstruir un diferencial, identificar que coordenada permanece constante en la superficie. Una superficie \\rho=constante tiene como normal \\hat{\\boldsymbol{\\rho}}; una superficie z=constante tiene como normal \\hat{\\mathbf{z}}.",
            "En una superficie, multiplicar los dos factores de escala de las coordenadas que varian. En un volumen, multiplicar los tres.",
            "En el eje de un sistema cilindrico o en el origen de uno esferico, ciertos factores tienden a cero porque el arco asociado al angulo se hace degenerado: no hay circunferencia o paralelo con longitud finita que recorrer.",
        ],
        "worked_example": [
            "Sea f=(x^2+y^2+z^2)/2. En cilindricas, x^2+y^2=\\rho^2 y queda $f=(\\rho^2+z^2)/2$. En esfericas, x^2+y^2+z^2=r^2 y queda $f=r^2/2$.",
            "En cartesianas, \\nabla f=x\\,\\hat{\\mathbf{i}}+y\\,\\hat{\\mathbf{j}}+z\\,\\hat{\\mathbf{k}}. En cilindricas, \\nabla f=\\rho\\,\\hat{\\boldsymbol{\\rho}}+z\\,\\hat{\\mathbf{z}}; en esfericas, \\nabla f=r\\,\\hat{\\mathbf{r}}. El resultado es el mismo campo escrito con bases diferentes.",
            "El ejemplo muestra por que una simetria radial simplifica la expresion, pero no elimina la geometria: el factor \\rho o r\\sin\\theta sigue siendo necesario al integrar.",
        ],
        "comparison": [
            "Un cambio lineal de coordenadas conserva factores constantes; un cambio curvilineo hace que los factores de escala dependan de la posicion.",
            "El factor \\rho en cilindricas procede del arco de una circunferencia. El factor r\\sin\\theta en esfericas procede del radio del paralelo, no del radio r completo.",
        ],
        "limits": [
            "No confundir el simbolo \\rho cilindrico con una densidad volumetrica, que suele escribirse \\rho_v.",
            "Las formulas de los factores de escala dependen de la convencion elegida para \\theta y \\phi.",
            "Los vectores unitarios curvilineos cambian con la posicion; no son los mismos vectores constantes que \\hat{\\mathbf{i}}, \\hat{\\mathbf{j}} y \\hat{\\mathbf{k}}.",
        ],
        "practice_warnings": [
            "El primer factor cilindrico es h_\\rho=1, no cos\\theta. Al derivar respecto de \\rho se obtiene un vector radial unitario de modulo uno.",
            "El factor \\rho en dV no es arbitrario: dos cambios angulares iguales recorren arcos mas largos cuanto mayor es la distancia al eje.",
            "En esfericas hay dos factores asociados a angulos porque hay dos arcos distintos: r\\,d\\theta y r\\sin\\theta\\,d\\phi.",
        ],
    },

    "em.1.03": {
        "idea": (
            "Una distribucion continua se trata como muchas cargas diferenciales. La eleccion entre densidad lineal, "
            "superficial o volumetrica no es una cuestion de notacion: determina el elemento geometrico que acompana a dq."
        ),
        "objectives": [
            "Elegir la densidad adecuada para una carga distribuida en una linea, una superficie o un volumen.",
            "Construir dq y Q encerrada usando el elemento diferencial correcto.",
            "Separar la integracion de la carga de la integracion del campo, teniendo presentes los limites y el soporte de la distribucion.",
        ],
        "concepts": [
            "La densidad lineal \\lambda mide carga por unidad de longitud; la densidad superficial \\sigma mide carga por unidad de area; la densidad volumetrica \\rho_v mide carga por unidad de volumen.",
            "La carga diferencial es dq=\\lambda\\,dl para una distribucion lineal, dq=\\sigma\\,dS para una lamina o cascaron y dq=\\rho_v\\,dV para una region tridimensional.",
            "El campo de una distribucion se obtiene sumando vectorialmente el campo de cada elemento. La direccion de cada contribucion depende de la posicion del elemento respecto al punto de observacion.",
            "Una densidad constante solo simplifica la integral; no elimina la necesidad de describir correctamente la region cargada.",
        ],
        "development": [
            "Para hallar la carga encerrada dentro de una superficie gaussiana, primero se intersecta esa superficie con el soporte real de la carga. Despues se integra la densidad sobre esa porcion, no sobre todo el espacio.",
            "En una esfera maciza uniforme, una capa de radio r tiene area 4\\pi r^2 y espesor dr, de modo que su volumen es 4\\pi r^2dr. Al acumular capas desde el centro aparece un factor r^3 en la carga total encerrada.",
            "En una cáscara esferica ideal la carga vive solo en una superficie de radio a. Su carga total es superficie por densidad, Q=4\\pi a^2\\sigma; no se integra una densidad volumetrica en el interior vacio.",
        ],
        "equations": [
            r"dq=\lambda\,dl,\qquad Q=\int \lambda\,dl",
            r"dq=\sigma\,dS,\qquad Q=\int \sigma\,dS",
            r"dq=\rho_v\,dV,\qquad Q=\int \rho_v\,dV",
            r"\mathbf{E}(\mathbf{r})=\frac{1}{4\pi\varepsilon_0}\int\frac{dq\,(\mathbf{r}-\mathbf{r}')}{|\mathbf{r}-\mathbf{r}'|^3}",
        ],
        "formalism": [
            "Escribir primero donde esta la carga y que densidad la describe. Solo despues sustituir el diferencial de longitud, superficie o volumen en las coordenadas elegidas.",
            "Para Q_enc(r), imponer por separado las regiones del problema. En una esfera de radio a, la expresion interior solo vale para r<a; para r>a ya se ha encerrado toda la carga.",
            "Comprobar unidades: \\lambda en C/m, \\sigma en C/m^2 y \\rho_v en C/m^3. El resultado de integrar debe quedar en culombios.",
        ],
        "worked_example": [
            "Esfera maciza de radio a con densidad volumetrica uniforme \\rho_v. Para r<a, el volumen encerrado es 4\\pi r^3/3 y $Q_{\\mathrm{enc}}(r)=4\\pi\\rho_vr^3/3$. Para r\\ge a, la carga encerrada deja de crecer y vale $Q_{\\mathrm{tot}}=4\\pi\\rho_va^3/3$.",
            "Cáscara esferica de radio a con densidad superficial uniforme \\sigma. Toda la carga esta en el area $4\\pi a^2$, por lo que $Q_{\\mathrm{tot}}=4\\pi a^2\\sigma$. Una superficie de radio menor que a no encierra carga.",
            "La diferencia entre ambos resultados no es una sutileza algebraica: en el primer caso se suman volumenes de capas con espesor; en el segundo se suma un area sin espesor volumetrico.",
        ],
        "comparison": [
            "Una superficie cargada puede tener espesor despreciable y densidad \\sigma; una esfera maciza ocupa volumen y se describe con \\rho_v.",
            "La carga encerrada puede depender de r dentro de la distribucion y ser constante fuera de ella. Esa distincion debe conservarse al aplicar Gauss.",
        ],
        "limits": [
            "Las densidades pueden depender de la posicion; si no son constantes, no se pueden sacar fuera de la integral.",
            "Una carga superficial ideal es un modelo limite. En una capa de espesor finito habria una densidad volumetrica y una region interior de transicion.",
            "La ley de Coulomb para una distribucion siempre es vectorial: no se deben sumar modulos ignorando direcciones y cancelaciones.",
        ],
        "practice_warnings": [
            "No confundir el crecimiento del area de una capa, 4\\pi r^2, con la carga acumulada en el volumen, que en una esfera maciza crece como r^3.",
            "La formula interior de Q_{\\mathrm{enc}} no se puede prolongar automaticamente a r>a: fuera de la esfera ya se ha recogido toda la carga.",
        ],
    },

    "em.1.06": {
        "idea": (
            "La ley de Gauss relaciona el flujo electrico neto que atraviesa una superficie cerrada con la carga encerrada. "
            "La ley siempre es cierta; lo que depende de la simetria es que permita despejar el modulo del campo de forma sencilla."
        ),
        "objectives": [
            "Definir el flujo electrico mediante el producto escalar entre campo y elemento de superficie orientado.",
            "Interpretar el signo del flujo neto de una superficie cerrada.",
            "Distinguir la validez general de la ley de Gauss de las condiciones especiales que permiten usarla para calcular E.",
        ],
        "concepts": [
            "El flujo a traves de una superficie mide la componente del campo normal a ella. Si el campo es perpendicular y paralelo a la normal, el producto escalar es maximo; si es tangente, es cero.",
            "En una superficie cerrada se toma por convenio la normal exterior. Un flujo positivo significa que sale mas campo del que entra; un flujo negativo significa que entra mas del que sale.",
            "La ley de Gauss dice que el flujo neto de \\mathbf{E} es $Q_{\\mathrm{enc}}/\\varepsilon_0$. Las cargas exteriores pueden modificar el campo local, pero su contribucion neta al flujo cerrado es cero.",
            "El angulo solido permite entender por que una carga puntual produce el mismo flujo total a traves de cualquier superficie cerrada que la encierre, aunque el campo no sea uniforme sobre una superficie arbitraria.",
        ],
        "development": [
            "Para extraer E de la integral hacen falta dos hechos: que el modulo del campo sea constante en la superficie elegida y que el angulo entre el campo y la normal sea constante. En los casos simetricos habituales, ademas, el campo es paralelo a la normal y el producto escalar se reduce a E dS.",
            "Una esfera centrada en una carga o en una distribucion esferica es una superficie gaussiana natural: todos sus puntos estan a la misma distancia y la simetria obliga al campo a ser radial y del mismo modulo.",
            "Si no existe una superficie con esas propiedades, la ley sigue proporcionando una relacion integral, pero normalmente no basta para encontrar el campo punto a punto.",
        ],
        "equations": [
            r"\Phi_E=\int_S\mathbf{E}\cdot d\mathbf{S}=\int_S E\cos\alpha\,dS",
            r"\oint_{\partial V}\mathbf{E}\cdot d\mathbf{S}=\frac{Q_{\mathrm{enc}}}{\varepsilon_0}",
            r"\mathbf{E}=E(r)\,\hat{\mathbf{r}}\quad\Longrightarrow\quad \oint_S\mathbf{E}\cdot d\mathbf{S}=E(r)\,4\pi r^2",
        ],
        "formalism": [
            "Dibujar o describir la simetria antes de escoger la superficie. Preguntar de que variables puede depender el modulo y que direccion puede tener el campo.",
            "Escribir el elemento vectorial orientado y el angulo con la normal. Solo despues sacar E fuera de la integral si realmente es constante sobre esa superficie.",
            "Calcular Q_enc usando la distribucion real y la region correspondiente. La integral de flujo y la carga encerrada deben referirse a la misma superficie gaussiana.",
        ],
        "worked_example": [
            "Para \\mathbf{F}=x\\,\\hat{\\mathbf{i}} en un cubo, el flujo neto es a^3 porque el campo tiene valores distintos en las dos caras x=constante. Por el teorema de la divergencia, \\nabla\\cdot\\mathbf{F}=1 y el mismo resultado es el volumen del cubo. Es una ilustracion de flujo neto sin carga electrica: aqui se esta usando una identidad matematica, no la ley de Gauss electrostatica.",
            "Para una carga o distribucion esferica, el campo puede depender de r y, sin embargo, ser constante sobre una esfera de radio fijo. Esta es la razon correcta para extraer E: no que sea constante en todo el espacio, sino que lo sea en la superficie de integracion.",
        ],
        "comparison": [
            "Campo constante en una superficie no significa campo uniforme en el espacio. Un campo radial E(r) cambia al pasar de una esfera a otra, pero tiene un unico valor en cada esfera centrada.",
            "La ley de Gauss siempre aplica; la simetria determina su utilidad practica. Sin simetria suficiente, no se puede convertir automaticamente la integral en E por area.",
        ],
        "limits": [
            "En el vacio aparece \\varepsilon_0. En un medio material, la formulacion mas general usa el desplazamiento electrico \\mathbf{D} para relacionar el flujo con la carga libre; solo en modelos lineales homogeneos se puede trabajar con una permitividad \\varepsilon de forma equivalente para E.",
            "El flujo neto puede ser cero aunque el campo no sea cero: basta con que entre tanto campo como sale o que el campo sea tangente a toda la superficie.",
            "La superficie gaussiana es una herramienta matematica; no es necesariamente una superficie fisica cargada o conductora.",
        ],
        "practice_warnings": [
            "La condicion util no es que E no dependa nunca del radio. Es que en una superficie de radio fijo todos sus puntos tengan el mismo modulo y la misma orientacion relativa a la normal.",
            "No confundir la ley de Gauss con el teorema de la divergencia: el primero introduce la carga electrica y el segundo convierte una integral de superficie en una de volumen.",
        ],
    },

    "em.1.07": {
        "idea": (
            "Las aplicaciones de Gauss son problemas por regiones. Primero se obtiene la carga encerrada en cada dominio; "
            "despues se aplica la simetria para despejar el campo y finalmente se comprueba que el resultado cambia de expresion "
            "cuando la superficie gaussiana deja de atravesar la distribucion."
        ),
        "objectives": [
            "Elegir superficies gaussianas esfericas, cilindricas o planas a partir de la simetria.",
            "Obtener campos por tramos dentro y fuera de distribuciones cargadas.",
            "Distinguir un campo continuo de un salto producido por una carga superficial ideal.",
        ],
        "concepts": [
            "Una distribucion esferica uniforme produce un campo radial. Una distribucion cilindrica infinita produce un campo radial cilindrico y una distribucion plana infinita produce un campo perpendicular al plano.",
            "La superficie gaussiana debe respetar la simetria: esfera concentrica, cilindro coaxial o pastilla atravesando un plano. La eleccion no se hace por comodidad algebraica solamente.",
            "En una esfera maciza, Q_enc crece mientras la superficie esta dentro de la carga y se satura fuera. El campo puede crecer dentro y decrecer fuera sin contradiccion.",
        ],
        "development": [
            "Para una esfera maciza de radio a y densidad \\rho_v, dentro se encierra el volumen de radio r; fuera se encierra la carga total de radio a. Las dos regiones deben escribirse por separado.",
            "Para una cáscara esferica ideal de radio a y densidad superficial \\sigma, una esfera gaussiana interior no encierra carga y una exterior encierra $4\\pi a^2\\sigma$. El campo salta en la superficie porque existe una carga superficial concentrada.",
            "El mismo razonamiento da E=\\lambda/(2\\pi\\varepsilon_0\\rho) para una linea infinita y E=\\sigma/(2\\varepsilon_0) a cada lado de una lamina infinita aislada. En cada caso, la forma del area gaussiana explica la dependencia con la distancia.",
        ],
        "equations": [
            r"\mathbf{E}(r)=\begin{cases}\dfrac{\rho_v r}{3\varepsilon_0}\,\hat{\mathbf{r}},&r<a,\\[.5em]\dfrac{\rho_v a^3}{3\varepsilon_0r^2}\,\hat{\mathbf{r}},&r\ge a,\end{cases}",
            r"\text{cáscara esférica:}\qquad \mathbf{E}(r)=\begin{cases}0,&r<a,\\[.3em]\dfrac{\sigma a^2}{\varepsilon_0r^2}\,\hat{\mathbf{r}},&r>a,\end{cases}",
            r"E_\text{fuera}-E_\text{dentro}=\frac{\sigma}{\varepsilon_0}\quad\text{en una superficie cargada ideal}",
        ],
        "formalism": [
            "Separar las regiones antes de integrar: interior de la distribucion, superficie y exterior. No reutilizar una expresion de Q_enc fuera del intervalo donde se obtuvo.",
            "En una esfera gaussiana, usar dS=r^2\\sin\\theta\\,d\\theta\\,d\\phi y area total 4\\pi r^2. En un cilindro coaxial, usar el area lateral 2\\pi\\rho L; las tapas no contribuyen si el campo es radial cilindrico.",
            "Comprobar el resultado con unidades, limite lejano y comportamiento en el centro. Para una carga total finita, el campo exterior debe decaer como 1/r^2.",
        ],
        "worked_example": [
            "Esfera maciza uniforme: para r<a, $E(r)4\\pi r^2=Q_{\\mathrm{enc}}(r)/\\varepsilon_0=(4\\pi\\rho_vr^3/3)/\\varepsilon_0$, de donde $E(r)=\\rho_vr/(3\\varepsilon_0)$. El campo crece linealmente porque la carga encerrada crece como r^3, mientras el area gaussiana crece como r^2.",
            "Para r>a, ya se encierra $Q_{\\mathrm{tot}}=4\\pi\\rho_va^3/3$. Por eso $E(r)=\\rho_va^3/(3\\varepsilon_0r^2)$: el maximo se alcanza al llegar a la superficie y despues el campo decrece.",
            "En una cáscara esferica, $E=0$ para r<a y $E=\\sigma a^2/(\\varepsilon_0r^2)$ para r>a. En el limite de la superficie ideal, el salto radial es \\sigma/\\varepsilon_0; en la esfera maciza uniforme, el campo es continuo en r=a porque no hay carga superficial concentrada.",
        ],
        "comparison": [
            "Esfera maciza y cáscara: ambas tienen simetria esferica, pero la primera usa una densidad volumetrica y la segunda una densidad superficial. Por eso sus expresiones interiores y su comportamiento en la frontera son distintos.",
            "Una carga puntual, una esfera cargada y cualquier distribucion esferica vista desde fuera producen el mismo campo que una carga total puntual en el centro, siempre que la simetria esferica se conserve.",
        ],
        "limits": [
            "Las expresiones dependen de que la distribucion sea uniforme y tenga la simetria indicada. Una deformacion o una densidad angularmente variable puede impedir extraer E.",
            "En una superficie de carga ideal se estudian los limites $a\\to A^-$ y $a\\to A^+$. No se debe sustituir sin mas un unico valor en el punto exacto si el campo presenta salto.",
            "Para distribuciones finitas, el resultado exterior se expresa con la carga total, no con una carga que siga creciendo con el radio de la superficie gaussiana.",
        ],
        "practice_warnings": [
            "La formula interior de la esfera maciza solo vale para r<a. Usarla para r>a haria crecer el campo sin limite y contradice que fuera ya esta encerrada toda la carga.",
            "La esfera maciza no tiene por que tener el mismo campo justo dentro y fuera por una formula identica, pero si es continuo en la frontera. La cáscara ideal, en cambio, produce un salto porque concentra carga en una superficie.",
        ],
    },
}


ERROR_GUIDANCE = {
    "Confundir el elemento escalar de superficie con el elemento vectorial orientado.": (
        "dS es un area positiva. El elemento vectorial es d\\mathbf{S}=\\hat{\\mathbf{n}}dS y contiene la normal y su orientacion. "
        "En un flujo, el signo procede del producto escalar con esa normal."
    ),
    "Olvidar factores de escala, especialmente \\rho y r\\sin\\theta.": (
        "Un diferencial angular representa un arco. En cilindricas el arco azimutal mide \\rho d\\phi; en esfericas los arcos miden r d\\theta y r\\sin\\theta d\\phi. "
        "Por eso dV=\\rho d\\rho d\\phi dz y dV=r^2\\sin\\theta dr d\\theta d\\phi."
    ),
    "Confundir densidad superficial con densidad volumétrica.": (
        "Usa \\sigma cuando la carga esta sobre una superficie y dq=\\sigma dS; usa \\rho_v cuando ocupa un volumen y dq=\\rho_v dV. "
        "Las unidades C/m^2 y C/m^3 permiten detectar rapidamente la mezcla."
    ),
    "Usar una expresión de carga encerrada fuera de la región donde es válida.": (
        "Q_{\\mathrm{enc}}(r) debe calcularse por tramos. Dentro de una esfera maciza crece con r^3; fuera se ha alcanzado la carga total y deja de depender de r."
    ),
    "Confundir gradiente con divergencia en la notación verbal.": (
        "El gradiente actua sobre un escalar y produce un vector: \\nabla f. La divergencia actua sobre un campo vectorial y produce un escalar: \\nabla\\cdot\\mathbf{F}. "
        "Conviene identificar el tipo de entrada y de salida antes de derivar."
    ),
}


def _paragraphs(items: list[str]) -> str:
    return "\n\n".join(_latex_escape(x) + "\\par" for x in items if str(x).strip())


def _markdown_to_latex(text: str) -> str:
    text = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""

    math_blocks = []
    def save_math(match):
        raw = match.group(0)
        if raw.startswith("$$") and raw.endswith("$$"):
            clean_inner = raw[2:-2].strip()
            math_blocks.append(f"\\[{clean_inner}\\]")
        else:
            math_blocks.append(raw)
        return f"@@MATH_BLOCK_{len(math_blocks)-1}@@"

    text = re.sub(r"(\$\$.*?\$\$|\\\[.*?\\\]|\$[^$\n]+\$|\\\(.+?\\\))", save_math, text, flags=re.DOTALL)
    text = text.replace("%", r"\%").replace("&", r"\&")

    lines = text.split("\n")
    processed_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        list_match = re.match(r"^[*-]\s+(.*)$", stripped)
        if list_match:
            if not in_list:
                processed_lines.append(r"\begin{itemize}")
                in_list = True
            item_text = list_match.group(1)
            item_text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", item_text)
            item_text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\textit{\1}", item_text)
            processed_lines.append(f"  \\item {item_text}")
            continue
        else:
            if in_list:
                processed_lines.append(r"\end{itemize}")
                in_list = False

        h_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if h_match:
            level = len(h_match.group(1))
            h_text = h_match.group(2)
            h_text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", h_text)
            if level <= 3:
                processed_lines.append(f"\n\\subsubsection*{{{h_text}}}")
            else:
                processed_lines.append(f"\n\\paragraph{{{h_text}}}")
            continue

        if stripped:
            line_conv = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", line)
            line_conv = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\textit{\1}", line_conv)
            processed_lines.append(line_conv)
        else:
            processed_lines.append("")

    if in_list:
        processed_lines.append(r"\end{itemize}")

    result = "\n".join(processed_lines)

    parts = re.split(r"(@@MATH_BLOCK_\d+@@)", result)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("_", r"\_").replace("^", r"\textasciicircum{}")
    result = "".join(parts)

    for idx, math in enumerate(math_blocks):
        result = result.replace(f"@@MATH_BLOCK_{idx}@@", math)

    return result


def _render_markdown_theory(items: list[str] | str) -> str:
    if isinstance(items, list):
        text = "\n\n".join(str(x).strip() for x in items if str(x).strip())
    else:
        text = str(items or "").strip()
    if not text:
        return ""
    return _markdown_to_latex(text)


def _render_aclaraciones(items: list) -> str:
    blocks = []
    for item in items or []:
        if isinstance(item, dict):
            duda = item.get("duda") or item.get("pregunta") or ""
            aclaracion = item.get("aclaracion") or item.get("respuesta") or ""
            duda_tex = _markdown_to_latex(duda).strip()
            aclaracion_tex = _markdown_to_latex(aclaracion).strip()
            box = (
                "\\begin{center}\n"
                "\\fcolorbox{qaline}{qabg}{%\n"
                "\\begin{minipage}{0.92\\linewidth}\n"
                f"\\textbf{{Duda o cuestión clave:}} {duda_tex}\\par\\vspace{{0.4em}}\n"
                f"\\textbf{{Aclaración y resolución física:}}\\par\n"
                f"{aclaracion_tex}\n"
                "\\end{minipage}}\n"
                "\\end{center}"
            )
            blocks.append(box)
        elif isinstance(item, str) and item.strip():
            text = item.strip()
            parts = re.split(r"(?:^|\n)\s*(?:Aclaraci[oó]n|Respuesta)\s*:\s*", text, flags=re.IGNORECASE)
            if len(parts) == 2:
                duda_part = re.sub(r"^(?:Duda|Pregunta)\s*:\s*", "", parts[0], flags=re.IGNORECASE).strip()
                aclaracion_part = parts[1].strip()
                box = (
                    "\\begin{center}\n"
                    "\\fcolorbox{qaline}{qabg}{%\n"
                    "\\begin{minipage}{0.92\\linewidth}\n"
                    f"\\textbf{{Duda o cuestión clave:}} {_markdown_to_latex(duda_part)}\\par\\vspace{{0.4em}}\n"
                    f"\\textbf{{Aclaración y resolución física:}}\\par\n"
                    f"{_markdown_to_latex(aclaracion_part)}\n"
                    "\\end{minipage}}\n"
                    "\\end{center}"
                )
                blocks.append(box)
            else:
                box = (
                    "\\begin{center}\n"
                    "\\fcolorbox{qaline}{qabg}{%\n"
                    "\\begin{minipage}{0.92\\linewidth}\n"
                    f"\\textbf{{Aclaración conceptual clave:}}\\par\n"
                    f"{_markdown_to_latex(text)}\n"
                    "\\end{minipage}}\n"
                    "\\end{center}"
                )
                blocks.append(box)
    return "\n\n".join(blocks)


def _node_tex(chapter: dict, graph_node: dict | None = None) -> str:
    graph_node = graph_node or {}
    node_id = str(chapter.get("id", graph_node.get("id", "")))
    guide = NODE_GUIDES.get(node_id, {})
    body = []
    body.append(f"\\section{{{_latex_escape(chapter.get('title', 'Nodo'))}}}")
    description = chapter.get("description") or graph_node.get("descripcion", "")
    idea = guide.get("idea") or description
    if idea:
        body.append(_section("Idea física y principios fundamentales", "\\begin{quote}\n" + _latex_escape(idea) + "\n\\end{quote}"))

    if guide.get("objectives"):
        body.append(_section("Qué se aprende en este bloque", _latex_list(guide["objectives"])))

    # 1. Fundamentos teóricos: prioriza la teoría viva registrada del tutor
    if chapter.get("teoria"):
        body.append(_section("Fundamentos teóricos y estructura matemática", _render_markdown_theory(chapter["teoria"])))
    else:
        if guide.get("concepts"):
            body.append(_section("Conceptos fundamentales", _paragraphs(guide["concepts"])))
        if guide.get("development"):
            body.append(_section("Desarrollo conceptual", _paragraphs(guide["development"])))

    # 2. Aclaraciones y dudas surgidas durante el estudio
    if chapter.get("aclaraciones"):
        body.append(_section("Aclaraciones y preguntas clave resueltas", _render_aclaraciones(chapter["aclaraciones"])))

    # 3. Mecanismo físico / ampliaciones
    if guide.get("mechanism"):
        body.append(_section("Mecanismo físico", _paragraphs(guide["mechanism"])))
    elif chapter.get("explanations") and not chapter.get("teoria"):
        body.append(_section("Explicación del mecanismo", _paragraphs(chapter["explanations"])))
    if chapter.get("explanations") and (guide.get("mechanism") or chapter.get("teoria")):
        body.append(_section("Ampliaciones surgidas del estudio", _paragraphs(chapter["explanations"])))

    if guide.get("transport"):
        body.append(_section("Aplicación física", _paragraphs(guide["transport"])))
    if guide.get("transitions"):
        body.append(_section("Mecanismos de excitación", _latex_list(guide["transitions"])))

    if guide.get("equations") and not chapter.get("teoria"):
        body.append(_section("Ecuaciones y elementos que hay que reconocer", _equations(guide["equations"])))

    # 4. Formalismo y procedimientos de examen
    if chapter.get("procedures"):
        body.append(_section("Caja de herramientas y procedimiento operativo", _paragraphs(chapter["procedures"])))
    elif guide.get("formalism"):
        body.append(_section("Cómo se aplica el formalismo", _paragraphs(guide["formalism"])))

    if guide.get("comparison"):
        body.append(_section("Distinciones importantes", _paragraphs(guide["comparison"])))

    if guide.get("limits"):
        body.append(_section("Hipótesis y límites de validez", _paragraphs(guide["limits"])))
    if guide.get("worked_example"):
        body.append(_section("Ejemplo razonado", _paragraphs(guide["worked_example"])))
    if guide.get("summary"):
        body.append(_section("Resumen", _paragraphs(guide["summary"])))

    # 5. Anotaciones de práctica y advertencias
    personal_notes = list(guide.get("practice_warnings", []))
    personal_notes.extend(
        f"Durante el estudio: {item}" for item in chapter.get("personal_explanations", [])
    )
    personal_notes.extend(
        f"Queda por consolidar: {item}" for item in chapter.get("difficulties", [])
    )
    if personal_notes:
        body.append(_warning_box("Anotaciones personales nacidas de la práctica", personal_notes))
    if chapter.get("procedures") and guide.get("formalism") and not chapter.get("teoria"):
        body.append(_section("Procedimiento personal añadido", _paragraphs(chapter["procedures"])))
    if chapter.get("examples"):
        body.append(_section("Ejercicios o comprobaciones registrados", _paragraphs(chapter["examples"])))
    return "\n".join(body)


def _error_register(subject: dict, observed: dict) -> str:
    """Cierra el documento con errores explicados, no con una lista de estados."""
    errors = []
    origins: dict[str, list[str]] = {}

    def add(error, origin=""):
        error = str(error or "").strip()
        if not error:
            return
        if error not in errors:
            errors.append(error)
        if origin and origin not in origins.setdefault(error, []):
            origins[error].append(origin)

    for error in subject.get("recurrent_errors", []):
        add(error)
    for chapter in observed.values():
        origin = chapter.get("title", "")
        for error in chapter.get("recurrent_errors", []):
            add(error, origin)

    if not errors:
        return ""

    parts = [
        r"\section{Registro de errores personales}",
        r"Esta sección conserva los tropiezos que aparecieron al estudiar. No sustituye a la teoría anterior: sirve para volver sobre los puntos que pueden hacer fallar un ejercicio, entender por qué fallan y reconocerlos a tiempo.",
    ]
    for index, error in enumerate(errors, start=1):
        explanation = ERROR_GUIDANCE.get(
            error,
            "Volver a la definición, escribir las hipótesis y comprobar el resultado con unidades, signos y un caso límite.",
        )
        body = "\\textbf{Error observado:} " + _latex_escape(error) + "\\par\n"
        body += _paragraphs([explanation])
        if 0 < len(origins.get(error, [])) <= 2:
            body += "\\textit{Apareció al trabajar: " + _latex_escape("; ".join(origins[error])) + ".}\\par\n"
        parts.append(_section(f"Error personal {index}", body))
    return "\n".join(parts)


def render_subject(subject: dict, graph_nodes: list[dict] | None = None) -> str:
    """Devuelve apuntes de estudio estructurados, no un registro cronológico."""
    parts = [
        r"\documentclass[11pt,a4paper]{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[spanish,es-nodecimaldot]{babel}",
        r"\usepackage[a4paper,margin=2.35cm,headheight=22pt]{geometry}",
        r"\usepackage{amsmath,amssymb,mathtools,enumitem,xcolor,hyperref,fancyhdr}",
        r"\definecolor{ink}{HTML}{1F2937}",
        r"\definecolor{accent}{HTML}{1F4E79}",
        r"\definecolor{warningbg}{HTML}{FFF7ED}",
        r"\definecolor{warningline}{HTML}{C2410C}",
        r"\definecolor{qabg}{HTML}{F0F9FF}",
        r"\definecolor{qaline}{HTML}{0284C7}",
        r"\hypersetup{colorlinks=true,linkcolor=accent,urlcolor=accent}",
        r"\setlist[itemize]{itemsep=.25em,topsep=.35em,leftmargin=1.6em}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{0.65em}",
        r"\color{ink}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        f"\\lhead{{\\small\\textit{{{_latex_escape(subject.get('materia', 'Apuntes'))}}}}}",
        r"\rhead{\small Apuntes de estudio}",
        r"\cfoot{\thepage}",
        r"\renewcommand{\headrulewidth}{0.3pt}",
        r"\renewcommand{\headrule}{\hbox to\headwidth{\color{accent}\leaders\hrule height \headrulewidth\hfill}}",
        r"\begin{document}",
        r"\pagenumbering{roman}",
        r"\begin{titlepage}",
        r"\centering\vspace*{2cm}",
        f"{{\\Huge\\color{{accent}}\\textbf{{{_latex_escape(subject.get('materia', 'Apuntes'))}}}\\par}}",
        r"\vspace{1cm}{\Large Apuntes de estudio\par}",
        r"\vfill",
        r"\begin{minipage}{0.78\linewidth}\centering\small Documento construido para estudiar la asignatura con explicaciones, formalismo, ejemplos y un registro final de las dificultades que han aparecido en la práctica.\end{minipage}",
        r"\vfill\today",
        r"\end{titlepage}",
        r"\pagenumbering{arabic}",
        r"\section*{Cómo usar estos apuntes}",
        r"El cuerpo principal está escrito como apuntes de la asignatura: presenta las ideas, justifica las fórmulas y muestra cómo se usan. Las anotaciones con fondo cálido son observaciones personales surgidas durante el estudio. El registro final reúne esos errores con una explicación para que puedan corregirse y no solo marcarse.",
        r"\tableofcontents\clearpage",
    ]
    observed = subject.get("nodes", {})
    rendered = set()
    rendered_graph_nodes = []
    # Solo se renderizan nodos con evidencia. El resto del grafo no se convierte
    # en un manual vacío: aparecerá cuando se estudie de verdad.
    for graph_node in graph_nodes or []:
        node_id = str(graph_node.get("id", ""))
        node_key = slugify(node_id)
        node_data = observed.get(node_key)
        if not node_data:
            continue
        parts.append(_node_tex(node_data, graph_node))
        rendered.add(node_key)
        rendered_graph_nodes.append(graph_node)
    for node_key, node_data in observed.items():
        if node_key not in rendered:
            parts.append(_node_tex(node_data))
    if not observed:
        parts.append(r"Todavía no hay nodos estudiados. Este documento se irá construyendo a medida que trabajes la asignatura.")

    error_section = _error_register(subject, observed)
    if error_section:
        parts.append(error_section)

    sources = []
    for graph_node in rendered_graph_nodes:
        fuentes = graph_node.get("fuentes", {}) or {}
        if not fuentes:
            continue
        details = "; ".join(f"{key}: {value}" for key, value in fuentes.items())
        sources.append(f"{graph_node.get('nombre', graph_node.get('id', 'Bloque'))}: {details}")
    if sources:
        parts.append(r"\section{Fuentes de referencia}")
        parts.append(r"Los bloques se han organizado a partir de las referencias indicadas en el grafo de la asignatura. La notación concreta puede variar entre libros, especialmente en los nombres de los ángulos esféricos.")
        parts.append(_latex_list(sources))

    parts.append(r"\end{document}")
    return "\n".join(parts) + "\n"


def _graph_nodes_by_subject(nodes: dict | None = None) -> dict[str, list[dict]]:
    if nodes is None:
        try:
            import sys
            graph_dir = os.path.join(BASE_DIR, "knowledge_graph")
            if graph_dir not in sys.path:
                sys.path.insert(0, graph_dir)
            import perfil
            nodes = perfil.cargar_grafos()
        except Exception:
            nodes = {}
    grouped: dict[str, list[dict]] = {}
    for node in (nodes or {}).values():
        grouped.setdefault(node.get("materia", "Sin asignatura"), []).append(node)
    return grouped


def compile_pdf(tex_path: str, runs: int = 2, clean_aux: bool = True) -> dict:
    """Compila un archivo .tex a .pdf usando pdflatex si está disponible en el sistema."""
    import shutil
    import subprocess

    if not os.path.exists(tex_path):
        return {"success": False, "error": f"Archivo no encontrado: {tex_path}"}

    pdflatex_bin = shutil.which("pdflatex")
    if not pdflatex_bin:
        return {"success": False, "error": "pdflatex no está disponible en PATH"}

    folder = os.path.dirname(os.path.abspath(tex_path))
    filename = os.path.basename(tex_path)
    base_name = os.path.splitext(filename)[0]
    pdf_path = os.path.join(folder, f"{base_name}.pdf")

    last_error = ""
    for _ in range(max(1, runs)):
        try:
            res = subprocess.run(
                [pdflatex_bin, "-interaction=nonstopmode", "-halt-on-error", filename],
                cwd=folder,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=40,
            )
            if res.returncode != 0:
                last_error = (res.stdout[-800:] if res.stdout else "") or (res.stderr[-800:] if res.stderr else "")
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    success = os.path.exists(pdf_path)

    if clean_aux:
        for ext in [".aux", ".log", ".out", ".toc"]:
            aux_file = os.path.join(folder, f"{base_name}{ext}")
            if os.path.exists(aux_file):
                try:
                    os.remove(aux_file)
                except OSError:
                    pass

    return {
        "success": success,
        "pdf_file": pdf_path if success else None,
        "error": None if success else (last_error or "Fallo de compilación de LaTeX"),
    }


def generate(subject_name: str | None = None, nodes: dict | None = None, compile_to_pdf: bool = True) -> dict:
    """Genera los .tex de todas las asignaturas o de una concreta y compila a .pdf si pdflatex está disponible."""
    state = load_state()
    subjects = state.setdefault("subjects", {})
    graph_by_subject = _graph_nodes_by_subject(nodes)
    selected_names = [subject_name] if subject_name and subject_name in subjects else sorted(subjects)
    files = []
    pdf_files = []
    compile_errors = {}
    for name in selected_names:
        subject = subjects.setdefault(name, _empty_subject(name))
        folder = os.path.join(OUTPUT_DIR, slugify(name))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "main.tex")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_subject(subject, graph_by_subject.get(name, [])))
        files.append(path)

        if compile_to_pdf:
            res = compile_pdf(path)
            if res.get("success") and res.get("pdf_file"):
                pdf_files.append(res["pdf_file"])
            elif res.get("error") and res["error"] != "pdflatex no está disponible en PATH":
                compile_errors[name] = res["error"]

    return {
        "files": files,
        "pdf_files": pdf_files,
        "compile_errors": compile_errors,
        "subjects": sorted(selected_names),
        "output_dir": OUTPUT_DIR,
    }


def summary() -> dict:
    state = load_state()
    rows = []
    for name, subject in state.get("subjects", {}).items():
        tex_path = os.path.join(OUTPUT_DIR, slugify(name), "main.tex")
        pdf_path = os.path.join(OUTPUT_DIR, slugify(name), "main.pdf")
        rows.append({
            "materia": name,
            "nodos": len(subject.get("nodes", {})),
            "evidencias": len(subject.get("evidence", [])),
            "actualizado": subject.get("updated_at"),
            "tex": tex_path,
            "pdf": pdf_path if os.path.exists(pdf_path) else None,
        })
    return {"subjects": sorted(rows, key=lambda x: x["materia"]), "output_dir": OUTPUT_DIR}


def context_for_nodes(node_ids: list[str]) -> str:
    """Resumen breve de lo ya construido para llevarlo al siguiente paseo."""
    state = load_state()
    wanted = {slugify(x) for x in node_ids}
    lines = []
    for subject in state.get("subjects", {}).values():
        for node in subject.get("nodes", {}).values():
            if slugify(node.get("id", "")) not in wanted:
                continue
            lines.append(f"- {node.get('id')}: {node.get('title', '')} — estado: {_status(node)}")
            if node.get("personal_explanations"):
                lines.append(f"  Explicación personal previa: {node['personal_explanations'][-1]}")
            if node.get("difficulties"):
                lines.append(f"  Dificultades previas: {'; '.join(node['difficulties'][-3:])}")
            if node.get("recurrent_errors"):
                lines.append(f"  Errores previos: {'; '.join(node['recurrent_errors'][-3:])}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generador y compilador de apuntes vivos en LaTeX/PDF")
    parser.add_argument("--materia", type=str, default=None, help="Materia específica a generar (ej. 'Mecánica Cuántica')")
    parser.add_argument("--no-pdf", action="store_true", help="Desactivar la compilación automática a PDF")
    args = parser.parse_args()
    res = generate(args.materia, compile_to_pdf=not args.no_pdf)
    print("--- Apuntes generados ---")
    for f in res.get("files", []):
        print(f"  [TEX] {f}")
    for p in res.get("pdf_files", []):
        print(f"  [PDF] {p}")
    if res.get("compile_errors"):
        print("--- Errores de compilación ---")
        for mat, err in res["compile_errors"].items():
            print(f"  [{mat}] {err[:200]}...")
