# -*- coding: utf-8 -*-
"""Construcción del contexto vivo del sistema de estudio.

El dashboard no es la fuente de verdad. La información canónica sigue estando
en los grafos, el perfil, el banco de problemas, el vault y los registros de
sesiones. Este módulo reúne esas capas en un contrato estable que puede
consumir cualquier IA, y ofrece una exportación JSON/Markdown portable.

La lectura es deliberadamente tolerante: un archivo personal que todavía no
exista, o una nota con formato antiguo, no debe impedir que el resto del
contexto esté disponible.
"""
from __future__ import annotations

import copy
import glob
import hashlib
import json
import os
import re
import sys
import threading
from datetime import date, datetime
from typing import Any

import apuntes
import config
import generar_dashboard
import study_sessions


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KG_DIR = os.path.join(BASE_DIR, "knowledge_graph")
CONTEXT_JSON_PATH = os.path.join(KG_DIR, "contexto_ia.json")
CONTEXT_MD_PATH = os.path.join(KG_DIR, "contexto_ia.md")
ACTIVE_STUDY_CONTEXT_PATH = os.path.join(KG_DIR, "active_study_context.json")
ACTIVE_STUDY_REPORT_PATH = os.path.join(KG_DIR, "active_study_report.json")
_WORK_REPORT_IMPORT_LOCK = threading.RLock()

if KG_DIR not in sys.path:
    sys.path.insert(0, KG_DIR)

import perfil as kg_perfil  # noqa: E402  (la ruta se prepara arriba)
import problemas as kg_problemas  # noqa: E402
import planificar as kg_planificar  # noqa: E402


CONTEXT_SCHEMA_VERSION = 1
WORK_SESSION_SCHEMA_VERSION = 2
GRAPH_EXCLUDED = {
    "perfil.json",
    "banco_problemas.json",
    "examenes.json",
    "correcciones.json",
    "study_sessions.json",
    "apuntes_personales.json",
    "contexto_ia.json",
}
MAX_DOCUMENT_CHARS = 500_000
MAX_TOTAL_DOCUMENT_CHARS = 12_000_000


def _practice_first_subject(materia: str) -> bool:
    """Indica las asignaturas que empiezan por diagnóstico práctico."""
    key = re.sub(r"\s+", " ", str(materia or "").strip().casefold())
    return key == "electromagnetismo"
DOCUMENT_EXTENSIONS = {".md", ".txt"}
SKIP_DIRECTORY_NAMES = {
    ".git",
    "__pycache__",
    "backups",
    "_subidas",
    "apuntes_generados",
    "tmp",
    "venv",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return copy.deepcopy(default)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return copy.deepcopy(default)


def _slug(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9áéíóúüñ]+", "-", value, flags=re.IGNORECASE)
    value = value.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def _redact_paths(value: Any) -> Any:
    """Hace portable el contexto sin exponer rutas locales ni el usuario."""
    if isinstance(value, dict):
        return {key: _redact_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_paths(item) for item in value]
    if not isinstance(value, str):
        return value

    replacements = {
        os.path.abspath(BASE_DIR).replace("\\", "/"): "[SISTEMA_ESTUDIO]",
        os.path.abspath(config.VAULT_PATH).replace("\\", "/"): "[OBSIDIAN_VAULT]",
    }
    result = value
    for source, replacement in replacements.items():
        result = result.replace(source, replacement)
        result = result.replace(source.replace("/", "\\"), replacement)
    return result


def _active_subjects() -> set[str] | None:
    taxonomy = _read_json(os.path.join(BASE_DIR, "taxonomy_uva.json"), {})
    return set(taxonomy) if isinstance(taxonomy, dict) and taxonomy else None


def _load_graphs() -> list[dict]:
    active_subjects = _active_subjects()
    graphs = []
    for path in sorted(glob.glob(os.path.join(KG_DIR, "*.json"))):
        filename = os.path.basename(path)
        if filename in GRAPH_EXCLUDED:
            continue
        data = _read_json(path, None)
        if not isinstance(data, dict) or not isinstance(data.get("nodos"), list):
            continue
        # La taxonomía delimita qué asignaturas forman parte del sistema. Esto
        # evita incorporar por accidente grafos auxiliares o archivados que
        # puedan quedar físicamente en knowledge_graph.
        if active_subjects is not None and data.get("materia") not in active_subjects:
            continue
        graph = _redact_paths(data)
        graph["archivo"] = filename
        graphs.append(graph)
    return graphs


def _node_index(graphs: list[dict]) -> dict[str, dict]:
    nodes = {}
    for graph in graphs:
        for raw in graph.get("nodos", []):
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            node = dict(raw)
            node.setdefault("materia", graph.get("materia", ""))
            node.setdefault("curso", graph.get("curso", 0))
            node.setdefault("archivo_grafo", graph.get("archivo", ""))
            nodes[str(node["id"])] = _redact_paths(node)
    return nodes


def _scope_graphs(graphs: list[dict], materia: str | None,
                  node_ids: set[str] | None) -> list[dict]:
    selected = []
    for graph in graphs:
        if materia and graph.get("materia") != materia:
            continue
        if node_ids:
            graph = dict(graph)
            graph["nodos"] = [
                node for node in graph.get("nodos", [])
                if str(node.get("id")) in node_ids
            ]
            if not graph["nodos"]:
                continue
        selected.append(graph)
    return selected


def _scope_profile(profile: dict, nodes: dict[str, dict], materia: str | None,
                   node_ids: set[str] | None) -> dict:
    raw = _redact_paths(profile if isinstance(profile, dict) else {})
    selected_ids = {
        nid for nid, node in nodes.items()
        if (not materia or node.get("materia") == materia)
        and (not node_ids or nid in node_ids)
    }
    profile_nodes = raw.get("nodos", {}) if isinstance(raw, dict) else {}
    raw["nodos"] = {
        nid: entry for nid, entry in profile_nodes.items()
        if nid in selected_ids
    }

    enriched = {}
    for nid in sorted(selected_ids):
        node = nodes[nid]
        entry = copy.deepcopy(profile.get("nodos", {}).get(nid, {}))
        try:
            domain = kg_perfil.dominio_efectivo(entry, date.today())
        except (KeyError, TypeError, ValueError):
            domain = float(entry.get("dominio", 0) or 0)
        try:
            fluency = kg_perfil.fluidez_efectiva(entry, date.today())
        except (AttributeError, KeyError, TypeError, ValueError):
            fluency = float(entry.get("fluidez", 0) or 0)
        enriched[nid] = {
            **_redact_paths(entry),
            "id": nid,
            "nombre": node.get("nombre", nid),
            "materia": node.get("materia", ""),
            "tema": node.get("tema"),
            "dominio_efectivo": round(float(domain), 4),
            "fluidez_efectiva": round(float(fluency), 4),
        }
    raw["estado_efectivo"] = enriched
    return raw


def _scope_problem_bank(bank: dict, materia: str | None,
                        node_ids: set[str] | None) -> dict:
    result = {}
    for subject, block in (bank or {}).items():
        if materia and subject != materia:
            continue
        if not isinstance(block, dict):
            continue
        selected_block = dict(block)
        problems = []
        for problem in block.get("problemas", []) or []:
            required = set(kg_problemas.nodos_requeridos(problem))
            if node_ids and not required.intersection(node_ids):
                continue
            problems.append(_redact_paths(problem))
        selected_block["problemas"] = problems
        result[subject] = _redact_paths(selected_block)
    return result


def _document_kind(label: str, relative_path: str) -> str:
    path = relative_path.lower().replace("\\", "/")
    if "intento" in path:
        return "intento"
    if "error" in path:
        return "error"
    if "ejercicio" in path or "/asignaturas/" in path:
        return "ejercicio_o_apunte"
    if "knowledge_graph" in path or label == "sistema":
        return "documentacion_sistema"
    return "nota"


def _iter_document_roots() -> list[tuple[str, str, str]]:
    """Devuelve (etiqueta, raíz, prefijo) sin incluir PDFs ni material bruto."""
    roots = [
        ("sistema", KG_DIR, "knowledge_graph"),
        ("sistema", os.path.join(BASE_DIR, "docs"), "docs"),
        ("sistema", BASE_DIR, "raiz"),
        ("obsidian", config.CONCEPTOS_DIR, "obsidian/Conceptos"),
        ("obsidian", config.ASIGNATURAS_DIR, "obsidian/Estudios/Asignaturas"),
        ("obsidian", config.INTENTOS_DIR, "obsidian/Intentos"),
        ("obsidian", config.ERRORES_DIR, "obsidian/Errores"),
        ("obsidian", config.ESTUDIOS_DIR, "obsidian/Estudios"),
        ("obsidian", config.INBOX_DIR, "obsidian/Inbox"),
    ]
    # El vault puede tener rutas coincidentes (por ejemplo, Estudios dentro de
    # Asignaturas). Se conservan aquí y se deduplican por ruta después.
    return [(label, os.path.abspath(root), prefix)
            for label, root, prefix in roots if os.path.isdir(root)]


def _load_documents(materia: str | None = None,
                    include_documents: bool = True) -> list[dict]:
    if not include_documents:
        return []
    active_subjects = _active_subjects()
    subject_slug = _slug(materia) if materia else ""
    documents = []
    seen = set()
    total_chars = 0
    for label, root, prefix in _iter_document_roots():
        for current, dirs, files in os.walk(root):
            dirs[:] = [name for name in dirs if name not in SKIP_DIRECTORY_NAMES]
            for filename in sorted(files):
                extension = os.path.splitext(filename)[1].lower()
                if extension not in DOCUMENT_EXTENSIONS:
                    continue
                path = os.path.abspath(os.path.join(current, filename))
                # Las exportaciones son salidas derivadas y no deben
                # reintroducirse a sí mismas como documentos fuente.
                if path in {os.path.abspath(CONTEXT_MD_PATH), os.path.abspath(CONTEXT_JSON_PATH)}:
                    continue
                if path in seen:
                    continue
                relative = os.path.relpath(path, root).replace("\\", "/")
                portable_path = f"{prefix}/{relative}" if relative != "." else prefix
                if label == "sistema" and active_subjects is not None:
                    base_name = os.path.splitext(filename)[0]
                    if base_name.lower().startswith("revision_"):
                        revision_subject = _slug(base_name[len("revision_"):].replace("_", " "))
                        if not any(_slug(subject) == revision_subject for subject in active_subjects):
                            continue
                # En una exportación acotada solo se conservan documentos que
                # parecen pertenecer a la asignatura elegida. La documentación
                # general del sistema sí se mantiene.
                if subject_slug and label != "sistema":
                    hay_subject = subject_slug in _slug(portable_path)
                    if not hay_subject:
                        continue
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read(MAX_DOCUMENT_CHARS + 1)
                except OSError:
                    continue
                if total_chars >= MAX_TOTAL_DOCUMENT_CHARS:
                    break
                truncated = len(content) > MAX_DOCUMENT_CHARS
                content = content[:MAX_DOCUMENT_CHARS]
                remaining = MAX_TOTAL_DOCUMENT_CHARS - total_chars
                if len(content) > remaining:
                    content = content[:remaining]
                    truncated = True
                seen.add(path)
                content = _redact_paths(content)
                total_chars += len(content)
                documents.append({
                    "id": hashlib.sha1(portable_path.encode("utf-8")).hexdigest()[:12],
                    "kind": _document_kind(label, portable_path),
                    "path": portable_path,
                    "filename": filename,
                    "content": content,
                    "truncated": truncated,
                })
            if total_chars >= MAX_TOTAL_DOCUMENT_CHARS:
                break
        if total_chars >= MAX_TOTAL_DOCUMENT_CHARS:
            break
    return documents


def _derived_state(profile: dict, nodes: dict[str, dict], bank: dict,
                   materia: str | None, node_ids: set[str] | None) -> dict:
    today = date.today()
    selected = {
        nid: node for nid, node in nodes.items()
        if (not materia or node.get("materia") == materia)
        and (not node_ids or nid in node_ids)
    }
    effective = {}
    for nid in selected:
        entry = profile.get("nodos", {}).get(nid, {})
        try:
            effective[nid] = kg_perfil.dominio_efectivo(entry, today)
        except (KeyError, TypeError, ValueError):
            effective[nid] = 0.0
    weak = sorted(effective.items(), key=lambda item: item[1])
    try:
        due = kg_perfil.pendientes_repaso(profile, selected, today)
    except (KeyError, TypeError, ValueError):
        due = []
    try:
        frontier = kg_perfil.frontera(profile, selected)
    except (KeyError, TypeError, ValueError):
        frontier = []
    try:
        problem_state = kg_problemas.resumen_para_plan(
            profile, selected, bank,
            materias={materia} if materia else None,
            hoy=today,
            limite=12,
        )
    except (KeyError, TypeError, ValueError):
        problem_state = {"problemas_listos": [], "por_materia": [], "total_listos": 0}

    return {
        "hoy": today.isoformat(),
        "resumen_dominio": {
            "nodos": len(selected),
            "con_evidencia": sum(value > 0 for value in effective.values()),
            "dominados": sum(value >= kg_perfil.UMBRAL_FRONTERA for value in effective.values()),
            "debiles": sum(value < 0.6 for value in effective.values()),
            "media": round(sum(effective.values()) / len(effective), 4) if effective else 0.0,
        },
        "nodos_debiles": [
            {
                "id": nid,
                "nombre": selected[nid].get("nombre", nid),
                "materia": selected[nid].get("materia", ""),
                "dominio_efectivo": round(value, 4),
            }
            for nid, value in weak[:30]
        ],
        "repasos_pendientes": _redact_paths(due[:100]),
        "frontera_aprendizaje": _redact_paths(frontier[:100]),
        "problemas": _redact_paths(problem_state),
    }


def _stats(context: dict) -> dict:
    graphs = context.get("knowledge_graph", {}).get("grafos", [])
    nodes = sum(len(graph.get("nodos", [])) for graph in graphs)
    bank = context.get("problem_bank", {})
    problems = sum(len(block.get("problemas", [])) for block in bank.values())
    profile_nodes = context.get("student", {}).get("profile", {}).get("nodos", {})
    sessions = context.get("learning_history", {}).get("sessions", {}).get("sessions", [])
    documents = context.get("documents", [])
    return {
        "asignaturas": len(graphs),
        "nodos_grafo": nodes,
        "problemas_banco": problems,
        "nodos_con_perfil": len(profile_nodes),
        "sesiones": len(sessions) if isinstance(sessions, list) else 0,
        "documentos": len(documents),
        "caracteres_documentos": sum(len(d.get("content", "")) for d in documents),
    }


def build_context(materia: str | None = None,
                  node_ids: list[str] | set[str] | None = None,
                  include_documents: bool = True) -> dict:
    """Construye una instantánea consistente del sistema completo.

    ``materia`` y ``node_ids`` permiten crear un contexto de sesión más
    pequeño. Sin filtros, la salida contiene el sistema entero.
    """
    materia = str(materia).strip() if materia else None
    selected_ids = {str(item).strip() for item in (node_ids or []) if str(item).strip()}
    selected_ids = selected_ids or None

    all_graphs = _load_graphs()
    graphs = _scope_graphs(all_graphs, materia, selected_ids)
    all_nodes = _node_index(all_graphs)
    scoped_nodes = _node_index(graphs)
    profile = kg_perfil.cargar_perfil()
    bank_all = kg_problemas.cargar_banco()
    bank = _scope_problem_bank(bank_all, materia, selected_ids)
    exams = _read_json(os.path.join(KG_DIR, "examenes.json"), {})
    notebooks = _read_json(os.path.join(KG_DIR, "cuadernos_gemini.json"), {})
    typical_errors = _read_json(os.path.join(KG_DIR, "errores_tipicos.json"), {})
    corrections = _read_json(os.path.join(KG_DIR, "correcciones.json"), [])
    sessions = study_sessions.load_state()
    notes = apuntes.load_state()
    try:
        dashboard = generar_dashboard.scan_vault()
    except Exception as exc:
        dashboard = {"error": str(exc)}

    if materia:
        exams = dict(exams) if isinstance(exams, dict) else {}
        exams["examenes"] = [
            exam for exam in exams.get("examenes", [])
            if exam.get("materia") == materia
        ]
        notebooks = {key: value for key, value in (notebooks or {}).items()
                     if key == materia}
        typical_errors = {
            nid: values for nid, values in (typical_errors or {}).items()
            if nid in scoped_nodes
        }

    context = {
        "context_schema_version": CONTEXT_SCHEMA_VERSION,
        "generated_at": _now(),
        "purpose": "Contexto vivo para tutoría y seguimiento del estudio de Física.",
        "scope": {
            "materia": materia,
            "node_ids": sorted(selected_ids) if selected_ids else None,
            "complete_system": not materia and not selected_ids,
        },
        "assistant_contract": {
            "role": "Tutor de Física personalizado, exigente y basado en evidencias.",
            "source_priority": [
                "instrucciones explícitas del estudiante",
                "evidencias del perfil y del historial",
                "grafos y materiales del sistema",
            ],
            "rules": [
                "No inventes dominio: distingue evidencia demostrada de hipótesis inicial.",
                "Usa los ids exactos de nodos y problemas cuando registres algo.",
                "Si falta información o hay conflicto, dilo antes de asumir.",
                "Las señales derivadas del perfil son descriptivas; no elijas por ellas el contenido de una sesión.",
                "La sesión sigue el último punto trabajado o la elección explícita del estudiante.",
                "Da solo la teoría mínima necesaria para abordar un problema real del banco vinculado al nodo.",
                "No inventes problemas, variantes ni ejercicios fuera del banco salvo que el estudiante lo pida.",
                "Propón cambios estructurados para el perfil; no sobrescribas datos sin confirmación.",
            ],
        "write_protocol": {
            "event_types": [
                "concept_review",
                "problem_attempt",
                "error_detected",
                "session_completed",
                "note_validated",
            ],
            "minimum_evidence": ["fecha", "origen", "ids_afectados", "resultado_o_calidad"],
            "routes": {
                "concept_review": "POST /api/context/events",
                "problem_attempt": "POST /api/context/events",
                "session_completed": "POST /api/study/sessions/{id}/finish",
                "voice_report": "POST /api/study/walks/{id}/close",
            },
            },
        },
        "student": {
            "profile": _scope_profile(profile, scoped_nodes, materia, selected_ids),
            "personal_notes": _redact_paths(notes),
            "objective": _redact_paths(profile.get("objetivo_academico", {})),
        },
        "academic": {
            "exams": _redact_paths(exams),
            "notebooks": _redact_paths(notebooks),
            "taxonomy": _redact_paths(_read_json(os.path.join(BASE_DIR, "taxonomy_uva.json"), {})),
        },
        "knowledge_graph": {
            "grafos": graphs,
            "node_count_total": len(all_nodes),
            "node_count_scope": len(scoped_nodes),
        },
        "problem_bank": bank,
        "learning_history": {
            "dashboard_scan": _redact_paths(dashboard),
            "sessions": _redact_paths(sessions),
            "typical_errors": _redact_paths(typical_errors),
            "corrections": _redact_paths(corrections),
        },
        "derived": _derived_state(profile, scoped_nodes, bank, materia, selected_ids),
        "documents": _load_documents(materia, include_documents),
    }
    context["stats"] = _stats(context)
    context["sources"] = {
        "graphs": "knowledge_graph/*.json",
        "profile": "knowledge_graph/perfil.json",
        "problem_bank": "knowledge_graph/banco_problemas.json",
        "sessions": "knowledge_graph/study_sessions.json",
        "notes": "knowledge_graph/apuntes_personales.json",
        "vault": "[OBSIDIAN_VAULT]",
        "documents_are_markdown_only": True,
    }
    return context


def subject_summaries() -> dict:
    """Resumen de navegación del dashboard, una tarjeta por asignatura."""
    graphs = _load_graphs()
    profile = kg_perfil.cargar_perfil()
    bank = kg_problemas.cargar_banco()
    sessions = study_sessions.load_state().get("sessions", [])
    exams_data = _read_json(os.path.join(KG_DIR, "examenes.json"), {})
    notebooks = _read_json(os.path.join(KG_DIR, "cuadernos_gemini.json"), {})
    today = date.today()
    summaries = []

    for graph in graphs:
        materia = str(graph.get("materia", "")).strip()
        if not materia:
            continue
        nodes = _node_index([graph])
        effective = {}
        for node_id in nodes:
            entry = profile.get("nodos", {}).get(node_id, {})
            try:
                effective[node_id] = float(kg_perfil.dominio_efectivo(entry, today))
            except (KeyError, TypeError, ValueError):
                effective[node_id] = float(entry.get("dominio", 0) or 0)
        try:
            due = kg_perfil.pendientes_repaso(profile, nodes, today)
        except (KeyError, TypeError, ValueError):
            due = []
        try:
            frontier = kg_perfil.frontera(profile, nodes)
        except (KeyError, TypeError, ValueError):
            frontier = []
        weak = sorted(effective.items(), key=lambda item: item[1])
        values = list(effective.values())
        average = sum(values) / len(values) if values else 0.0
        subject_problems = bank.get(materia, {}).get("problemas", []) if isinstance(bank.get(materia, {}), dict) else []
        node_ids = set(nodes)
        subject_sessions = [
            session for session in sessions
            if session.get("materia") == materia
            or bool(node_ids.intersection(set(session.get("plan_ids", []))))
        ]
        last_session = max(
            subject_sessions,
            key=lambda item: item.get("ended_at") or item.get("started_at") or "",
            default=None,
        )
        exams = exams_data.get("examenes", []) if isinstance(exams_data, dict) else []
        exam = next((item for item in exams if item.get("materia") == materia), None)
        notebook = notebooks.get(materia, {}) if isinstance(notebooks, dict) else {}
        if due:
            status = "Repasos pendientes"
        elif not values or average < 0.6:
            status = "En aprendizaje"
        elif average < 0.85:
            status = "En consolidación"
        else:
            status = "Estable"
        summaries.append({
            "materia": materia,
            "nodos": len(nodes),
            "nodos_con_evidencia": sum(value > 0 for value in values),
            "dominio_medio": round(average, 3),
            "dominio_porcentaje": round(average * 100),
            "nodos_debiles": sum(value < 0.6 for value in values),
            "repasos_pendientes": len(due),
            "frontera": len(frontier),
            "problemas": len(subject_problems),
            "sesiones": len(subject_sessions),
            "ultima_sesion": last_session.get("ended_at") if last_session else None,
            "estado": status,
            "examen": exam,
            "cuaderno": {
                "nombre": notebook.get("nombre", f"{materia} — Física"),
                "url": notebook.get("url", ""),
            },
        })
    return {"generated_at": _now(), "subjects": summaries}


def apply_event(event: dict) -> dict:
    """Aplica una actualización pequeña y explícita enviada por una IA.

    Solo se permiten dos mutaciones directas: revisión de conceptos y resultado
    de un problema. Las sesiones y los informes de voz conservan sus endpoints
    específicos porque necesitan más contexto y validación.
    """
    if not isinstance(event, dict):
        raise ValueError("El evento debe ser un objeto JSON")
    event_type = str(event.get("type", "")).strip()
    origin = str(event.get("origin", "ia"))[:120]
    if event_type not in {"concept_review", "problem_attempt"}:
        raise ValueError("Tipo de evento no admitido para esta ruta")

    try:
        quality = event.get("quality")
        quality = float(quality) if quality is not None else None
    except (TypeError, ValueError):
        quality = None
    if quality is not None:
        quality = max(0.0, min(1.0, quality))

    try:
        seconds = event.get("seconds")
        seconds = float(seconds) if seconds is not None else None
    except (TypeError, ValueError):
        seconds = None

    if event_type == "concept_review":
        raw_ids = event.get("node_ids", event.get("ids", []))
        if isinstance(raw_ids, str):
            raw_ids = [raw_ids]
        ids = list(dict.fromkeys(str(item).strip() for item in (raw_ids or []) if str(item).strip()))
        if not ids:
            raise ValueError("Una revisión de conceptos necesita node_ids")
        nodes = kg_perfil.cargar_grafos()
        invalid = [nid for nid in ids if nid not in nodes]
        if invalid:
            raise ValueError(f"Nodos no encontrados: {', '.join(invalid[:8])}")
        success = bool(event.get("success", quality is None or quality >= 0.5))
        messages = kg_perfil.registrar_y_guardar(
            ids, success, origen=origin, segundos=seconds, calidad=quality
        )
        return {
            "type": event_type,
            "node_ids": ids,
            "success": success,
            "quality": quality,
            "origin": origin,
            "messages": messages,
        }

    problem_id = str(event.get("problem_id", "")).strip()
    if not problem_id:
        raise ValueError("Un intento de problema necesita problem_id")
    bank = kg_problemas.cargar_banco()
    if kg_problemas.buscar_problema(bank, problem_id)[1] is None:
        raise KeyError(f"No existe el problema {problem_id!r}")
    profile = kg_perfil.cargar_perfil()
    nodes = kg_perfil.cargar_grafos()
    result = kg_problemas.registrar_feedback(
        profile,
        nodes,
        bank,
        problem_id,
        veredicto=event.get("verdict", event.get("veredicto")),
        calidad=quality,
        nodos_hueco=event.get("theory_gap_nodes", event.get("nodos_hueco_teorico", [])) or [],
        nodos_error=event.get("error_nodes", event.get("nodos_error", [])) or [],
        comentarios=str(event.get("comments", event.get("comentarios", "")) or "")[:2000],
        segundos=seconds,
        origen=origin,
    )
    kg_perfil.guardar_perfil(profile)
    return {
        "type": event_type,
        "problem_id": problem_id,
        "quality": quality,
        "origin": origin,
        "result": _redact_paths(result),
    }


def context_summary() -> dict:
    """Resumen ligero para la interfaz, sin cargar el contenido de documentos."""
    context = build_context(include_documents=False)
    return {
        "context_schema_version": context["context_schema_version"],
        "generated_at": context["generated_at"],
        "scope": context["scope"],
        "stats": context["stats"],
        "derived": context["derived"],
        "exports": {
            "json": "knowledge_graph/contexto_ia.json",
            "markdown": "knowledge_graph/contexto_ia.md",
        },
    }


def context_to_markdown(context: dict) -> str:
    """Renderiza el contexto completo en un único archivo que puede adjuntarse."""
    stats = context.get("stats", {})
    lines = [
        "# Contexto vivo — Sistema de Estudio de Física",
        "",
        f"> Generado: {context.get('generated_at', '—')} · Esquema: {context.get('context_schema_version', '—')}",
        "> Este documento es una instantánea del sistema. El JSON equivalente conserva la misma información de forma estructurada.",
        "",
        "## Cómo debe usarlo la IA",
        "",
        "Actúa como tutor de Física personalizado. Utiliza primero las instrucciones del estudiante y las evidencias del perfil e historial; después el grafo y los materiales. No inventes dominio ni problemas: cita los ids exactos y usa únicamente ejercicios del banco vinculados a los nodos trabajados. Si propones actualizar el sistema, devuelve un evento estructurado con fecha, origen, ids y resultado.",
        "",
        "## Resumen",
        "",
        f"- Asignaturas: {stats.get('asignaturas', 0)}",
        f"- Nodos del grafo: {stats.get('nodos_grafo', 0)}",
        f"- Problemas del banco: {stats.get('problemas_banco', 0)}",
        f"- Nodos con perfil: {stats.get('nodos_con_perfil', 0)}",
        f"- Sesiones registradas: {stats.get('sesiones', 0)}",
        f"- Documentos Markdown/TXT incluidos: {stats.get('documentos', 0)}",
        "",
        "## Estado actual e historial",
        "",
        "```json",
        json.dumps(context.get("derived", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Datos estructurados completos",
        "",
        "La siguiente sección contiene el mismo contexto completo que el archivo JSON, para que esta versión Markdown sea autónoma.",
        "",
        "```json",
        json.dumps(context, ensure_ascii=False, indent=2),
        "```",
        "",
        "---",
        "Generado automáticamente por el Sistema de Estudio. Los archivos fuente locales siguen siendo la fuente de verdad; este documento es su representación portable para la IA.",
        "",
    ]
    return "\n".join(lines)


def _atomic_write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(temporary, path)


def export_context(materia: str | None = None,
                   node_ids: list[str] | set[str] | None = None,
                   include_documents: bool = True) -> dict:
    """Genera los dos artefactos portables y devuelve metadatos de la exportación."""
    context = build_context(materia, node_ids, include_documents)
    json_content = json.dumps(context, ensure_ascii=False, indent=2) + "\n"
    markdown_content = context_to_markdown(context)
    _atomic_write(CONTEXT_JSON_PATH, json_content)
    _atomic_write(CONTEXT_MD_PATH, markdown_content)
    return {
        "success": True,
        "generated_at": context["generated_at"],
        "scope": context["scope"],
        "stats": context["stats"],
        "files": {
            "json": "knowledge_graph/contexto_ia.json",
            "markdown": "knowledge_graph/contexto_ia.md",
        },
    }


def _clamp_number(value: Any, minimum: float, maximum: float, default: float) -> float:
    try:
        return max(minimum, min(maximum, float(value)))
    except (TypeError, ValueError):
        return default


def _work_problem(problem: dict) -> dict:
    """Reduce un problema a lo que necesita el tutor, sin incluir soluciones."""
    return {
        "id": str(problem.get("id", ""))[:120],
        "titulo": str(problem.get("titulo", "Problema"))[:300],
        "materia": str(problem.get("materia", ""))[:160],
        "tipo_problema": str(problem.get("tipo_problema", ""))[:80],
        "numero": problem.get("numero"),
        "hoja": str(problem.get("hoja", ""))[:120],
        "nodos_requeridos": [str(item)[:80] for item in kg_problemas.nodos_requeridos(problem)[:20]],
        "enunciado": str(problem.get("enunciado", ""))[:1800],
    }


def _outline_topics(description: str, fallback: str) -> list[str]:
    """Divide la descripción canónica de un nodo en subpuntos breves.

    Los grafos usan descripciones compactas separadas normalmente por punto y
    coma y comas. Esta función las convierte en un índice legible sin inventar
    contenido ni depender de una asignatura concreta.
    """
    text = str(description or "").strip()
    if not text:
        return [str(fallback or "Contenido del nodo").strip()]

    clauses = re.split(r"[;\n]+|(?<=[.!?])\s+", text)
    topics: list[str] = []
    seen: set[str] = set()
    for clause in clauses:
        clause = re.sub(r"^\s*(incluye(?:\s+(?:la|el|los|las))?|incluyendo)\s+",
                        "", clause.strip(), flags=re.IGNORECASE)
        if not clause:
            continue
        # Las descripciones del grafo separan normalmente subskills con
        # comas y conjunciones. Se conserva el texto original para no inventar
        # un temario nuevo.
        parts = re.split(r",|\s+y\s+", clause)
        for part in parts:
            item = re.sub(r"\s+", " ", part).strip(" .:–—")
            key = item.casefold()
            if item and key not in seen:
                topics.append(item)
                seen.add(key)

    return topics[:10] or [str(fallback or "Contenido del nodo").strip()]


def build_session_outline(nodes: list[dict] | None = None,
                          problems: list[dict] | None = None,
                          session: dict | None = None,
                          profile: dict | None = None) -> dict:
    """Construye el índice de trabajo de una sesión, sin planificador.

    El índice se limita a los nodos y problemas que ya forman parte del paquete
    o que el estudiante ha elegido. No decide qué estudiar: solo ordena el ciclo
    didáctico de microteoría, ejercicio real, corrección y siguiente ejercicio.
    """
    nodes = list(nodes or [])
    problems = list(problems or [])
    session = session or {}
    profile_nodes = (profile or {}).get("nodos", {})
    practice_first = _practice_first_subject(session.get("materia", ""))
    orientation_items = (
        [
            "Empezar directamente con una cuestión o ejercicio real del banco para diagnosticar huecos.",
            "No dar teoría inicial de bloque: explicar solo lo que el intento revele que falta.",
            "Después de cada corrección, comprobar el hueco con otra cuestión o ejercicio real.",
        ]
        if practice_first else [
            "Confirmar el último punto trabajado o la elección explícita del estudiante.",
            "Dar solo la teoría mínima necesaria para el primer ejercicio del banco.",
            "Mantener el trabajo acotado a los nodos y problemas incluidos en el paquete.",
        ]
    )
    blocks: list[dict] = [{
        "order": 1,
        "type": "orientation",
        "title": "Orientación inicial",
        "items": orientation_items,
    }]

    for index, node in enumerate(nodes, start=2):
        node_id = str(node.get("id", "")).strip()
        prerequisite_items = []
        for item in node.get("prerequisitos", []) or []:
            if not isinstance(item, dict):
                continue
            prerequisite_items.append({
                "id": str(item.get("id", "")),
                "title": str(item.get("nombre", item.get("id", ""))),
            })

        node_problems = []
        for problem in problems:
            problem_nodes = {str(item) for item in problem.get("nodos_requeridos", [])}
            if node_id and node_id in problem_nodes:
                node_problems.append({
                    "id": str(problem.get("id", "")),
                    "title": str(problem.get("titulo", "Problema")),
                })

        tipo = node.get("tipo")
        mode = {
            "repaso": "Repaso",
            "continuacion": "Continuación",
            "inicio": "Inicio",
            "eleccion": "Elección",
            "nuevo": "Nuevo",
        }.get(tipo, "Nuevo")
        profile_entry = profile_nodes.get(node_id, {})
        theory_seen = bool(
            node.get("teoria_vista", False)
            or node.get("theory_status") == "vista"
            or profile_entry.get("teoria_vista", False)
        )
        blocks.append({
            "order": index,
            "type": "node",
            "node_id": node_id,
            "title": str(node.get("nombre", node_id)),
            "mode": mode,
            "theory_status": "vista" if theory_seen else "pendiente",
            "practice_first": practice_first,
            "items": _outline_topics(node.get("descripcion", ""), node.get("nombre", node_id)),
            "prerequisites": prerequisite_items,
            "practice": node_problems[:6],
        })

    blocks.append({
        "order": len(blocks) + 1,
        "type": "integration",
        "title": "Integración y transferencia",
        "items": (
            [
                "Aislar el hueco que aparezca en cada intento y explicar solo ese microbloque.",
                "Revisar hipótesis, unidades, límites de validez y casos límite dentro del ejercicio.",
                "Pasar a la siguiente cuestión o problema real del banco vinculado a los nodos trabajados.",
            ]
            if practice_first else [
                "Después de cada corrección, aislar el hueco concreto y dar solo el microbloque necesario.",
                "Revisar hipótesis, unidades, límites de validez y casos límite dentro del ejercicio.",
                "Pasar al siguiente problema real del banco vinculado a los nodos trabajados.",
            ]
        ),
    })
    blocks.append({
        "order": len(blocks) + 1,
        "type": "closure",
        "title": "Cierre",
        "items": [
            "Recuperación final sin mirar los apuntes.",
            "Dudas, errores y conexiones que aún necesiten refuerzo.",
            "Siguiente acción y criterio para el próximo repaso.",
        ],
    })

    return {
        "title": "Índice granular de la sesión",
        "objective": str(session.get("goal", "aprender")),
        "available_minutes": session.get("available_minutes"),
        "teaching_mode": "practica_primero" if practice_first else "microteoria_justo_a_tiempo",
        "blocks": blocks,
    }


def render_session_outline(outline: dict) -> str:
    """Renderiza el índice estructurado en texto breve para el tutor."""
    lines = [str(outline.get("title", "Índice de la sesión"))]
    objective = str(outline.get("objective", "")).strip()
    minutes = outline.get("available_minutes")
    if objective:
        lines.append(f"Objetivo: {objective}")
    if minutes:
        lines.append(f"Duración orientativa: {minutes} minutos")
    if outline.get("teaching_mode") == "practica_primero":
        lines.append("Método: práctica primero; teoría solo para explicar los huecos que aparezcan")
    lines.append("")

    for block in outline.get("blocks", []) or []:
        order = block.get("order", "")
        title = str(block.get("title", "Bloque")).strip()
        if block.get("type") == "node":
            mode = str(block.get("mode", "")).strip()
            label = f"{mode} · " if mode else ""
            node_id = str(block.get("node_id", "")).strip()
            suffix = f" [{node_id}]" if node_id else ""
            lines.append(f"{order}. {label}{title}{suffix}")
            if block.get("practice_first"):
                lines.append(f"   {order}.T Cuestiones y ejercicios primero → teoría solo si el intento descubre un hueco")
            elif block.get("theory_status") == "vista":
                lines.append(f"   {order}.T Teoría ya impartida → solo microteoría necesaria y práctica directa")
            else:
                lines.append(f"   {order}.T Teoría pendiente → microteoría necesaria y después práctica")
            for suborder, item in enumerate(block.get("items", []) or [], start=1):
                lines.append(f"   {order}.{suborder} {item}")
            prerequisites = block.get("prerequisites", []) or []
            if prerequisites:
                names = ", ".join(item.get("title", item.get("id", ""))
                                 for item in prerequisites)
                lines.append(f"   {order}.P Puente previo: {names}")
            practice = block.get("practice", []) or []
            if practice:
                names = "; ".join(item.get("title", item.get("id", ""))
                                 for item in practice)
                lines.append(f"   {order}.E Práctica disponible: {names}")
        else:
            lines.append(f"{order}. {title}")
            for suborder, item in enumerate(block.get("items", []) or [], start=1):
                lines.append(f"   {order}.{suborder} {item}")
        lines.append("")
    return "\n".join(lines).strip()


def _work_prompt(pack: dict) -> str:
    session = pack["session"]
    state = pack["state"]
    outline = pack.get("outline") or build_session_outline(
        pack.get("nodes", []), pack.get("problems", []), session,
        pack.get("profile")
    )
    outline_text = render_session_outline(outline)
    practice_first = _practice_first_subject(session.get("materia", ""))
    if practice_first:
        session_method = """Esta es mi segunda cursada de Electromagnetismo. No empieces impartiendo teoría ni siguiendo una secuencia teoría → ejercicios. Empieza directamente con una cuestión o ejercicio real del banco para detectar los huecos que arrastro. Usa mis respuestas para diagnosticar qué falló; explica únicamente el concepto, definición, hipótesis o paso que falte y vuelve a comprobarlo con otra cuestión o ejercicio real."""
        first_cycle = "- Primera respuesta obligatoria: muestra el índice brevemente antes de explicar teoría o lanzar una pregunta y, en Electromagnetismo, empieza directamente con una cuestión o ejercicio real del banco. No des una introducción teórica previa salvo un recordatorio de una línea que sea imprescindible para poder intentarlo."
        theory_rule = "- En Electromagnetismo, la teoría es reactiva: solo aparece después de detectar un hueco en mi intento y debe ser la mínima necesaria para corregirlo o volver a comprobarlo."
        cycle_rule = "- En Electromagnetismo, la unidad normal es: cuestión o problema real → intento → diagnóstico del hueco → microexplicación si hace falta → nueva cuestión o problema real."
    else:
        session_method = "La asignatura sigue el método general: microteoría imprescindible para el ejercicio actual y práctica inmediata con problemas reales del banco."
        first_cycle = "- Primera respuesta obligatoria: muestra el índice brevemente antes de explicar teoría o lanzar una pregunta; indica la continuidad o elección y empieza el primer ciclo."
        theory_rule = "- Da únicamente la microteoría mínima indispensable para poder abordar el siguiente ejercicio real (máx. 2-3 minutos): solo definiciones, hipótesis, ecuaciones y método inmediato. No des clases teóricas largas."
        cycle_rule = "- La unidad normal de trabajo es: microteoría mínima imprescindible → ejercicio real del banco/libro/apuntes → intento del estudiante → corrección → aislar el fallo y profundizar ÚNICAMENTE en el hueco teórico descubierto → siguiente ejercicio."
    partial_notice_block = ""
    if pack.get("partial_notice"):
        partial_notice_block = f"\nALERTA DE EXAMEN PARCIAL (LÍMITE ESTRICTO DE TEMARIO)\n{pack['partial_notice']}\n"
    template = {
        "session_id": session.get("id"),
        "nodos": [
            {
                "id": "id-del-nodo-trabajado",
                "resultado": "solido|parcial|debil|no_trabajado",
                "calidad": 0.0,
                "dominado": [],
                "dudas": [],
                "evidencias": [],
                "siguiente_accion": "",
                "teoria_vista": False,
            }
        ],
        "problem_attempts": [
            {
                "problem_id": "id-del-problema",
                "verdict": "resuelto|hueco_teorico|incorrecto",
                "quality": 0.0,
                "theory_gap_nodes": [],
                "error_nodes": [],
                "comments": "",
                "seconds": 0,
            }
        ],
        "resumen": "",
        "errores_recurrentes": [],
        "siguiente_accion": "",
        "apuntes": [],
        "reflection": {
            "worked": "",
            "friction": "",
            "next_change": "",
            "energy_after": session.get("energy", 3),
        },
        "rail": {"stage": "relevance", "action": "", "experiment": ""},
    }
    state_json = json.dumps(state, ensure_ascii=False, indent=2)
    template_json = json.dumps(template, ensure_ascii=False, indent=2)
    return f"""ENCARGO DE SESIÓN DE ESTUDIO INTEGRADA

Actúa como mi tutor personalizado para la asignatura «{session['materia']}».
Esta sesión parte de un sistema local de seguimiento. Si tienes abierta la carpeta del
proyecto, lee primero este archivo, que contiene el contexto vivo de esta sesión:
  knowledge_graph/active_study_context.json
Lee también TUTOR_WORK.md si está disponible: contiene las reglas persistentes del
tutor y del intercambio con el dashboard.

OBJETIVO DE LA SESIÓN
{session['goal']} durante aproximadamente {session['available_minutes']} minutos. El índice
solo organiza los nodos y problemas ya seleccionados; no es una recomendación automática
ni una lista de tareas obligatoria.{partial_notice_block}

MÉTODO ESPECÍFICO DE ESTA ASIGNATURA
{session_method}

ÍNDICE GRANULAR DE LA SESIÓN
Este es el mapa de los nodos y problemas reales disponibles hoy. Preséntalo al estudiante
al comienzo. Usa su numeración para anunciar las transiciones, pero sigue la elección
explícita del estudiante y la continuidad de la última sesión, no una prioridad calculada.
```text
{outline_text}
```

ESTADO RESUMIDO QUE DEBES TENER EN CUENTA
```json
{state_json}
```

PROTOCOLO DIDÁCTICO
{first_cycle}
{theory_rule}
- Presenta después el enunciado exacto de un problema incluido en el contexto, con su id
  y sus nodos. Espera el intento del estudiante antes de corregir.
- Tras la corrección, identifica el hueco concreto, explica solo el microbloque que falte
  y pasa al siguiente problema real vinculado al nodo.
- Nunca inventes problemas, variantes ni datos. Si un nodo no tiene problemas en el banco,
  dilo y trabaja la teoría mínima o espera a que el estudiante elija otro nodo.
- «Teoría ya impartida» solo evita repetir explicaciones innecesarias; no obliga a hacer
  una clase completa antes de practicar. «Teoría pendiente» tampoco implica impartirla
  entera: se cubre solo lo necesario para el problema actual.
- La cercanía de un examen, un repaso pendiente, el dominio o la frontera pueden describir
  el estado, pero no eligen el contenido de la sesión.
- Justifica las propiedades no inmediatas desde las definiciones y muestra los pasos
  intermedios necesarios. No presentes identidades o criterios importantes como hechos
  aislados: distingue siempre definición, demostración y consecuencia.
- Traduce cada ecuación no trivial antes de usarla: identifica los objetos, la operación,
  el significado de la igualdad y su interpretación física. Para una ecuación de
  operadores, aclara qué afirma al actuar sobre un ket arbitrario; reconocer los símbolos
  no equivale a comprender la afirmación.
- Separa la manipulación algebraica de la conclusión física y explica el puente entre ambas.
- Distingue siempre hipótesis, cálculo y conclusión. No supongas como premisa lo que se
  pretende demostrar: una implicación condicional no demuestra su antecedente.
- Haz una sola pregunta o petición de resolución cada vez y espera mi respuesta.
{cycle_rule}
- Exige intuición física, hipótesis, límites de validez, condiciones de contorno,
  unidades, casos límite y conexión con otros conceptos.
- No me des la solución de un problema antes de que haya intentado plantearlo.
- Para el seguimiento de procedencia, considera que los ejercicios de clase ya trabajados
  por el estudiante son únicamente los de Electromagnetismo; en las demás asignaturas no
  marques ejercicios de clase como hechos sin evidencia explícita.
- No inventes dominio ni marques un concepto como sólido sin evidencia de mi respuesta.
- El índice es la referencia inicial. Si el estudiante decide avanzar o profundizar en otros conceptos del temario o repasar prerrequisitos, acopla la explicación y regístralos con sus IDs oficiales en el cierre.

PROTOCOLO DE ESCRITURA
No modifiques directamente los grafos ni el perfil. Al cerrar, escribe únicamente el
informe JSON en:
  knowledge_graph/active_study_report.json
No pongas Markdown ni comentarios fuera del JSON. Incluye en el informe todos los nodos y
problemas que se hayan trabajado durante la sesión (tanto del índice como cualquier otro concepto
del temario o prerrequisito abordado con sus IDs oficiales del grafo). Si no puedes escribir el archivo,
devuelve exactamente el mismo JSON para que pueda copiarlo al dashboard.

Cuando diga «CIERRE DE SESIÓN» o «CERRAMOS LA CONVERSACIÓN» (también si lo expresa
con una variación inequívoca como «cerramos»), deja de enseñar y genera el informe con
esta estructura. No me pidas que pulse ningún botón: cuando el JSON esté guardado en
la ruta indicada, el Centro de Estudio lo detectará e importará automáticamente.
```json
{template_json}
```

No cierres por tu cuenta antes de que yo lo pida. Durante la sesión, conserva el rigor y
la continuidad con el historial, pero permite que yo decida el ritmo y la profundidad.
"""


def _latest_completed_subject_session(materia: str) -> dict | None:
    """Devuelve la última sesión terminada de una asignatura, si existe."""
    sessions = study_sessions.load_state().get("sessions", [])
    candidates = [
        item for item in sessions
        if item.get("materia") == materia and item.get("status") == "completed"
    ]
    return max(
        candidates,
        key=lambda item: item.get("ended_at") or item.get("started_at") or "",
        default=None,
    )


def build_study_pack(materia: str, minutos: int = 60,
                     objetivo: str = "aprender", session: dict | None = None,
                     node_ids: list[str] | None = None) -> dict:
    """Crea un paquete de tutoría basado en historial y ejercicios reales.

    La selección no consulta el planificador. Si no se especifican nodos, se
    continúa desde los nodos de la última sesión de la asignatura; si no existe
    historial, se empieza por el orden del grafo. Los problemas siempre salen
    del banco y deben estar vinculados a uno de esos nodos.
    """
    try:
        auto_import_ready_work_report()
    except Exception:
        pass

    materia = str(materia or "").strip()
    if not materia:
        raise ValueError("La sesión necesita una asignatura")
    minutos = int(_clamp_number(minutos, 5, 600, 60))
    objetivo = str(objetivo or "aprender").strip()[:160] or "aprender"

    context = build_context(materia=materia, include_documents=False)
    graphs = context.get("knowledge_graph", {}).get("grafos", [])
    if not graphs:
        raise ValueError(f"No existe una asignatura activa llamada {materia!r}")

    all_nodes = kg_perfil.cargar_grafos()
    profile = kg_perfil.cargar_perfil()
    session_state = study_sessions.load_state()
    overrides = session_state.get("pacer_overrides", {})
    previous = _latest_completed_subject_session(materia)

    # Comprueba si hay un examen parcial próximo confirmado con temas acotados
    examenes_path = os.path.join(KG_DIR, "examenes.json")
    allowed_temas = None
    partial_notice = ""
    if os.path.exists(examenes_path):
        try:
            ex_data = _read_json(examenes_path, {})
            upcoming_partials = [
                e for e in ex_data.get("examenes", [])
                if str(e.get("materia", "")).strip().casefold() == materia.casefold()
                and e.get("tipo") == "parcial"
                and e.get("confirmado", False)
                and e.get("temas")
            ]
            if upcoming_partials:
                upcoming_partials.sort(key=lambda x: x.get("fecha", "9999"))
                target_exam = upcoming_partials[0]
                allowed_temas = set(int(t) for t in target_exam["temas"])
                temas_str = ", ".join(map(str, sorted(allowed_temas)))
                partial_notice = (
                    f"LÍMITE ESTRICTO DE EXAMEN PARCIAL ({target_exam.get('descripcion', '')}): "
                    f"El estudio queda limitado exclusivamente a los Temas {temas_str}. "
                    f"Está terminantemente prohibido avanzar o introducir temas posteriores hasta superar este parcial."
                )
        except Exception:
            pass

    if allowed_temas:
        canonical_subject_nodes = [
            str(node.get("id")) for graph in graphs
            for node in graph.get("nodos", [])
            if node.get("id") and node.get("tema") in allowed_temas
        ]
    else:
        canonical_subject_nodes = [
            str(node.get("id")) for graph in graphs
            for node in graph.get("nodos", [])
            if node.get("id")
        ]

    requested_ids = [str(item).strip() for item in (node_ids or []) if str(item).strip()]
    if not requested_ids and session:
        requested_ids = [str(item).strip() for item in session.get("plan_ids", []) if str(item).strip()]
    if not requested_ids and previous:
        prev_plans = [str(x).strip() for x in previous.get("plan_ids", []) if str(x).strip()]
        last_node = prev_plans[-1] if prev_plans else None
        if last_node and last_node in canonical_subject_nodes:
            idx = canonical_subject_nodes.index(last_node)
            last_entry = profile.get("nodos", {}).get(last_node, {})
            start_idx = idx + 1 if (last_entry.get("teoria_vista") or last_entry.get("dominio", 0) >= 0.7) else idx
            if start_idx >= len(canonical_subject_nodes):
                start_idx = idx
            requested_ids = canonical_subject_nodes[start_idx : start_idx + 4]
        if not requested_ids:
            requested_ids = prev_plans
    if not requested_ids:
        # Es el orden canónico del grafo, no una recomendación calculada.
        requested_ids = canonical_subject_nodes[:4]

    source_kind = "continuacion" if previous and not node_ids and not session else "eleccion"
    preview = []
    for node_id in requested_ids:
        node = all_nodes.get(node_id)
        if not node or node.get("materia") != materia:
            continue
        preview.append(study_sessions._node_preview(
            {"id": node_id, "tipo": source_kind},
            all_nodes, profile, overrides,
        ))
    preview = preview[:12]
    node_ids = [str(item.get("id")) for item in preview if item.get("id")]

    all_problems = [
        problem
        for block in context.get("problem_bank", {}).values()
        for problem in block.get("problemas", []) or []
    ]
    problem_items = []
    seen_problem_ids: set[str] = set()
    if session and session.get("problem_ids"):
        wanted = [str(item).strip() for item in session.get("problem_ids", []) if str(item).strip()]
        all_problems = [
            problem for problem in all_problems
            if str(problem.get("id", "")).strip() in wanted
        ]
    else:
        previous_problem_ids = set(previous.get("problem_ids", []) if previous else [])
        successful_problem_ids = {
            str(problem_id) for problem_id, result in (profile.get("problemas", {}) or {}).items()
            if isinstance(result, dict) and result.get("exito") is True
        }
        node_set = set(node_ids)
        linked = [
            problem for problem in all_problems
            if node_set.intersection(set(kg_problemas.nodos_requeridos(problem)))
        ]
        def problem_order(problem: dict) -> tuple[int, int, int]:
            source = str(problem.get("tipo_problema", "")).strip().lower()
            source_rank = 0 if source == "clase" else 1
            seen_rank = 1 if str(problem.get("id", "")).strip() in (previous_problem_ids | successful_problem_ids) else 0
            return source_rank, seen_rank, all_problems.index(problem)
        all_problems = sorted(linked, key=problem_order)

    for problem in all_problems:
        problem_id = str(problem.get("id", "")).strip()
        if not problem_id or problem_id in seen_problem_ids:
            continue
        problem_items.append(_work_problem(problem))
        seen_problem_ids.add(problem_id)
        if len(problem_items) >= 6:
            break

    for node in preview:
        node_id = str(node.get("id", ""))
        node["problemas"] = [
            problem for problem in problem_items
            if node_id in problem.get("nodos_requeridos", [])
        ]

    effective = context.get("student", {}).get("profile", {}).get("estado_efectivo", {})
    previous_reflection = (previous or {}).get("reflection") or {}
    state = {
        "resumen_dominio": context.get("derived", {}).get("resumen_dominio", {}),
        "continuidad": {
            "previous_session_id": (previous or {}).get("id"),
            "previous_ended_at": (previous or {}).get("ended_at"),
            "previous_next_change": previous_reflection.get("next_change", ""),
        },
        "practice_policy": {
            "source": "knowledge_graph/banco_problemas.json",
            "require_node_link": True,
            "invent_problems": False,
            "class_exercises_attempted_subjects": ["Electromagnetismo"],
            "teaching_mode": (
                "practica_primero_segunda_cursada"
                if _practice_first_subject(materia)
                else "microteoria_justo_a_tiempo"
            ),
        },
        "estado_de_los_nodos": {
            node_id: effective[node_id] for node_id in node_ids if node_id in effective
        },
    }
    session_info = {
        "id": session.get("id") if session else None,
        "materia": materia,
        "status": session.get("status", "active") if session else "prepared",
        "available_minutes": minutos,
        "goal": objetivo,
        "session_type": session.get("session_type", "work_guided") if session else "work_guided",
        "energy": session.get("context", {}).get("energy", 3) if session else 3,
    }
    outline = build_session_outline(preview, problem_items, session_info, profile)
    pack = {
        "study_pack_schema_version": WORK_SESSION_SCHEMA_VERSION,
        "generated_at": context.get("generated_at", _now()),
        "session": session_info,
        "assignment": {"materia": materia},
        "state": state,
        "profile": {"nodos": {
            node_id: {
                "teoria_vista": bool(profile.get("nodos", {}).get(node_id, {}).get("teoria_vista", False))
            }
            for node_id in node_ids
        }},
        "nodes": preview,
        "problems": problem_items,
        "outline": outline,
        "personal_notes": apuntes.context_for_nodes(node_ids)[:12000] if node_ids else "",
        "selection": {
            "basis": "historial" if previous and source_kind == "continuacion" else source_kind,
            "previous_session_id": (previous or {}).get("id"),
        },
        "files": {
            "context": "knowledge_graph/active_study_context.json",
            "report": "knowledge_graph/active_study_report.json",
        },
        "plan_ids": node_ids,
        "problem_ids": [item["id"] for item in problem_items],
        "partial_notice": partial_notice,
    }
    pack["prompt"] = _work_prompt(pack)
    return pack


def save_active_study_context(pack: dict) -> dict:
    """Guarda el paquete actual para que Work pueda leerlo desde la carpeta local."""
    _atomic_write(
        ACTIVE_STUDY_CONTEXT_PATH,
        json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
    )
    return {
        "path": "knowledge_graph/active_study_context.json",
        "session_id": pack.get("session", {}).get("id"),
        "generated_at": pack.get("generated_at"),
    }


def reset_active_study_report() -> None:
    """Vacía el buzón derivado antes de iniciar una nueva sesión."""
    _atomic_write(ACTIVE_STUDY_REPORT_PATH, "{}\n")


def load_active_study_context() -> dict:
    return _read_json(ACTIVE_STUDY_CONTEXT_PATH, {})


def load_active_study_report() -> dict:
    return _read_json(ACTIVE_STUDY_REPORT_PATH, {})


def active_study_status() -> dict:
    """Estado pequeño para que el dashboard detecte el cierre escrito por Work."""
    context = load_active_study_context()
    session = None
    session_id = context.get("session", {}).get("id") if isinstance(context, dict) else None
    if session_id:
        try:
            session = study_sessions.get_session(session_id)
        except KeyError:
            session = None
    report = load_active_study_report()
    report_ready = (
        isinstance(report, dict)
        and bool(report)
        and report.get("status") != "imported"
        and report.get("session_id", session_id) == session_id
    )
    return {
        "active": bool(session and session.get("status") == "active"),
        "report_ready": report_ready,
        "session": session,
        "materia": context.get("session", {}).get("materia") if isinstance(context, dict) else None,
        "generated_at": context.get("generated_at") if isinstance(context, dict) else None,
        "files": {
            "context": "knowledge_graph/active_study_context.json",
            "report": "knowledge_graph/active_study_report.json",
        },
    }


def _normalize_work_report(report: dict, session: dict) -> dict:
    """Valida el cierre de Work garantizando que los nodos y problemas pertenezcan al grafo y banco."""
    if not isinstance(report, dict):
        raise ValueError("El cierre de Work debe ser un objeto JSON")
    all_nodes = kg_perfil.cargar_grafos()
    materia = str(session.get("materia", "")).strip()
    allowed_nodes = set(session.get("plan_ids", []))
    if materia:
        subject_nodes = {
            nid for nid, n in all_nodes.items()
            if str(n.get("materia", "")).strip().casefold() == materia.casefold()
        }
        allowed_nodes |= subject_nodes
    if not allowed_nodes:
        allowed_nodes = set(all_nodes.keys())
    normalized = study_sessions.normalize_walk_report(report, list(allowed_nodes))
    problems = []
    raw_problems = report.get("problem_attempts", report.get("problemas", [])) or []
    bank = kg_problemas.cargar_banco()
    for raw in raw_problems:
        if not isinstance(raw, dict):
            continue
        problem_id = str(raw.get("problem_id", raw.get("id", ""))).strip()
        if not problem_id:
            continue
        if kg_problemas.buscar_problema(bank, problem_id)[1] is None:
            continue
        verdict = str(raw.get("verdict", raw.get("veredicto", ""))).strip()
        verdict = {
            "correcto": "resuelto",
            "solido": "resuelto",
            "parcial": "hueco_teorico",
            "debil": "incorrecto",
            "mal": "incorrecto",
        }.get(verdict, verdict)
        if verdict not in {"resuelto", "hueco_teorico", "incorrecto"}:
            verdict = "hueco_teorico"
        quality = _clamp_number(raw.get("quality", raw.get("calidad", 0)), 0.0, 1.0, 0.0)
        gaps = [str(item) for item in (raw.get("theory_gap_nodes", raw.get("nodos_hueco_teorico", [])) or [])
                if str(item) in all_nodes]
        errors = [str(item) for item in (raw.get("error_nodes", raw.get("nodos_error", [])) or [])
                  if str(item) in all_nodes]
        problems.append({
            "problem_id": problem_id[:120],
            "verdict": verdict,
            "quality": round(quality, 2),
            "theory_gap_nodes": gaps[:20],
            "error_nodes": errors[:20],
            "comments": str(raw.get("comments", raw.get("comentarios", "")) or "")[:2000],
            "seconds": _clamp_number(raw.get("seconds", raw.get("segundos", 0)), 0, 86400, 0),
        })
    normalized["problem_attempts"] = problems
    reflection = report.get("reflection", {}) or {}
    normalized["reflection"] = {
        "worked": str(reflection.get("worked", ""))[:2000],
        "friction": str(reflection.get("friction", ""))[:1000],
        "next_change": str(reflection.get("next_change", ""))[:1000],
        "energy_after": int(_clamp_number(reflection.get("energy_after", 3), 1, 5, 3)),
    }
    rail = report.get("rail", {}) or {}
    normalized["rail"] = {
        "stage": rail.get("stage", "relevance"),
        "action": str(rail.get("action", ""))[:40],
        "experiment": str(rail.get("experiment", ""))[:1200],
    }
    return normalized


def apply_work_report(session_id: str, report: dict) -> dict:
    """Integra el informe de Work en perfil, problemas, apuntes y sesiones."""
    session = study_sessions.get_session(session_id)
    if session.get("status") == "completed":
        return {"already_completed": True, "session": session, "applied": {}}
    normalized = _normalize_work_report(report, session)
    origin = "chatgpt_work"
    applied_nodes = []
    applied_problems = []
    for item in normalized.get("nodos", []):
        quality = float(item.get("calidad", 0))
        result = apply_event({
            "type": "concept_review",
            "node_ids": [item["id"]],
            "success": item.get("resultado") == "solido" or quality >= 0.5,
            "quality": quality,
            "origin": origin,
        })
        study_sessions.record_event(session_id, {
            "type": "concept_review",
            "node_id": item["id"],
            "quality": quality,
            "encoding_response": "; ".join(item.get("evidencias", [])[:4]),
        })
        applied_nodes.append(result)

    worked_node_ids = [item["id"] for item in normalized.get("nodos", [])]
    if worked_node_ids:
        current_plans = set(session.get("plan_ids", []))
        for nid in worked_node_ids:
            if nid not in current_plans:
                session.setdefault("plan_ids", []).append(nid)
                current_plans.add(nid)

    worked_prob_ids = [item["problem_id"] for item in normalized.get("problem_attempts", [])]
    if worked_prob_ids:
        current_probs = set(session.get("problem_ids", []))
        for pid in worked_prob_ids:
            if pid not in current_probs:
                session.setdefault("problem_ids", []).append(pid)
                current_probs.add(pid)

    theory_ids = [
        item["id"] for item in normalized.get("nodos", [])
        if item.get("teoria_vista") is True or (item.get("teoria_vista") is not False and float(item.get("calidad", 0)) >= 0.5)
    ]
    if theory_ids:
        profile = kg_perfil.cargar_perfil()
        kg_perfil.marcar_teoria_vista(profile, theory_ids, origen=origin)
        kg_perfil.guardar_perfil(profile)

    for item in normalized.get("problem_attempts", []):
        result = apply_event({
            "type": "problem_attempt",
            "problem_id": item["problem_id"],
            "verdict": item["verdict"],
            "quality": item["quality"],
            "theory_gap_nodes": item["theory_gap_nodes"],
            "error_nodes": item["error_nodes"],
            "comments": item["comments"],
            "seconds": item["seconds"],
            "origin": origin,
        })
        study_sessions.record_event(session_id, {
            "type": "problem_attempt",
            "quality": item["quality"],
            "problem_results": {"problem_id": item["problem_id"], "verdict": item["verdict"]},
        })
        applied_problems.append(result)

    nodes = kg_perfil.cargar_grafos()
    note_result = apuntes.apply_walk_report(session, normalized, nodes)
    latex_files = []
    pdf_files = []
    for subject_name in note_result.get("subjects", []):
        generated = apuntes.generate(subject_name, nodes)
        latex_files.extend(generated.get("files", []))
        pdf_files.extend(generated.get("pdf_files", []))

    rail = normalized.get("rail", {})
    reflection = normalized.get("reflection", {})
    finished = study_sessions.finish_session(session_id, {
        "worked": normalized.get("resumen", "") or reflection.get("worked", ""),
        "friction": "; ".join(normalized.get("errores_recurrentes", [])) or reflection.get("friction", ""),
        "next_change": normalized.get("siguiente_accion", "") or normalized.get("recomendacion", "") or reflection.get("next_change", ""),
        "energy_after": reflection.get("energy_after", 3),
        "rail_stage": rail.get("stage", "relevance"),
        "rail_action": rail.get("action", ""),
        "rail_experiment": rail.get("experiment", ""),
        "map_note": normalized.get("resumen", ""),
    })
    finished["apuntes"] = {**note_result, "latex_files": latex_files, "pdf_files": pdf_files}
    _atomic_write(
        ACTIVE_STUDY_REPORT_PATH,
        json.dumps({
            "status": "imported",
            "session_id": session_id,
            "imported_at": _now(),
        }, ensure_ascii=False, indent=2) + "\n",
    )
    active = load_active_study_context()
    if isinstance(active, dict):
        active.setdefault("session", {})["status"] = "completed"
        active["closed_at"] = _now()
        save_active_study_context(active)
    return {
        "already_completed": False,
        "session": finished,
        "applied": {"nodes": applied_nodes, "problems": applied_problems},
        "notes": note_result,
        "latex_files": latex_files,
        "pdf_files": pdf_files,
        "context_summary": context_summary(),
    }


def finish_work_report(session_id: str, report: dict) -> dict:
    """Aplica un cierre de Work de forma serializada.

    El dashboard puede consultar el estado mientras el usuario conserva abierta
    la ventana de cierre. El bloqueo evita que una detección automática y un
    envío manual eventual procesen el mismo informe a la vez.
    """
    with _WORK_REPORT_IMPORT_LOCK:
        return apply_work_report(session_id, report)


def auto_import_ready_work_report() -> dict:
    """Importa el informe listo de Work sin intervención en la interfaz.

    Devuelve ``imported=True`` solo cuando una sesión activa ha sido cerrada y
    sus datos se han aplicado correctamente. Los cierres inválidos permanecen
    disponibles para revisión manual y no rompen el sondeo del dashboard.
    """
    with _WORK_REPORT_IMPORT_LOCK:
        status = active_study_status()
        if not status.get("active") or not status.get("report_ready"):
            return {"imported": False}

        session = status.get("session") or {}
        session_id = str(session.get("id", "")).strip()
        report = load_active_study_report()
        if not session_id or not isinstance(report, dict) or not report:
            return {"imported": False, "error": "El cierre detectado no tiene una sesión válida."}

        try:
            result = finish_work_report(session_id, report)
        except Exception as exc:
            return {"imported": False, "error": str(exc)}
        return {"imported": True, "session_id": session_id, "result": result}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "import-report":
        res = auto_import_ready_work_report()
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif cmd == "status":
        st = active_study_status()
        print(json.dumps(st, ensure_ascii=False, indent=2))
    else:
        print("Uso: python study_context.py [status | import-report]")
