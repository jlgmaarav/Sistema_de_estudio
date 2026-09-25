# -*- coding: utf-8 -*-
"""Persistencia y reglas de la experiencia de estudio centralizada.

Este módulo no sustituye al perfil del knowledge graph: guarda la capa que antes
faltaba alrededor del dominio físico —cómo se estudió, qué se intentó antes de
pedir ayuda, qué tipo de información se trabajó y qué se va a cambiar después.
"""
from __future__ import annotations

import copy
import json
import os
import threading
import uuid
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "knowledge_graph", "study_sessions.json")
WALK_REPORTS_DIR = os.path.join(BASE_DIR, "knowledge_graph", "informes_paseos")
ACTIVE_WALK_PATH = os.path.join(BASE_DIR, "knowledge_graph", "paseo_actual.json")
_LOCK = threading.RLock()

PACER = {
    "P": {
        "nombre": "Procedimental",
        "color": "#60a5fa",
        "accion": "Intenta ejecutar el proceso: escribe los primeros pasos antes de mirar la lección.",
    },
    "A": {
        "nombre": "Análoga",
        "color": "#c084fc",
        "accion": "Busca una analogía: ¿a qué problema o idea conocida se parece y dónde deja de funcionar?",
    },
    "C": {
        "nombre": "Conceptual",
        "color": "#34d399",
        "accion": "Explícalo con tus palabras y relaciona causa, mecanismo, condiciones y consecuencias.",
    },
    "E": {
        "nombre": "Evidencia",
        "color": "#fb923c",
        "accion": "Concreta la idea: busca un ejemplo físico, un caso límite o una predicción observable.",
    },
    "R": {
        "nombre": "Referencia",
        "color": "#fbbf24",
        "accion": "Recupera los detalles exactos que necesitas: definición, símbolo, unidad o identidad.",
    },
}

RAIL = {
    "relevance": {
        "nombre": "Relevancia",
        "descripcion": "Estás descubriendo qué técnicas y decisiones importan para aprender mejor.",
        "siguiente": "Elige una técnica y observa qué cambia.",
        "acciones": ["explorar", "cuestionar"],
    },
    "awareness": {
        "nombre": "Conciencia",
        "descripcion": "Estás identificando dónde te bloqueas y qué error de proceso se repite.",
        "siguiente": "Experimenta y escribe qué ocurrió.",
        "acciones": ["experimentar", "reflexionar"],
    },
    "iteration": {
        "nombre": "Iteración",
        "descripcion": "Ya tienes una técnica útil; ahora toca variarla y ajustarla al contexto.",
        "siguiente": "Cambia una variable y comprueba si mantienes el rendimiento.",
        "acciones": ["variar", "ajustar"],
    },
    "lifelong": {
        "nombre": "Mantenimiento",
        "descripcion": "La forma de estudiar ya es estable y toca mantenerla, revisarla y evitar que decaiga.",
        "siguiente": "Mantén una revisión breve y periódica.",
        "acciones": ["mantener", "refinar"],
    },
}

WALK_MODES = {
    "walk_introduction": {
        "nombre": "Microteoría y ejercicios (paseo o bus)",
        "descripcion": "La IA da la teoría mínima para abordar un ejercicio real del banco y comprueba la resolución; puedes responder hablando o escribiendo.",
        "reparto": "La IA explica lo imprescindible y después plantea un ejercicio del banco por vez; si vas en bus, responde por texto y no uses el micrófono.",
        "instrucciones": "Primero explica solo las definiciones, hipótesis y ecuaciones necesarias para un problema incluido en el encargo. No plantees problemas inventados: después presenta el enunciado exacto, espera el intento y corrige antes de pasar al siguiente.",
    },
    "walk_rescue": {
        "nombre": "Paseo de rescate conceptual",
        "descripcion": "La IA localiza una confusión concreta mediante preguntas y pistas.",
        "reparto": "El estudiante habla más; la IA diagnostica y da pistas breves.",
        "instrucciones": "No des una clase larga de entrada. Pregunta qué creo que significa el concepto y localiza exactamente la confusión antes de explicar.",
    },
    "walk_review": {
        "nombre": "Paseo de repaso general",
        "descripcion": "La IA examina la asignatura y registra qué recuperas, dudas y fallos.",
        "reparto": "El estudiante habla la mayor parte del tiempo; la IA pregunta y corrige al final de cada respuesta.",
        "instrucciones": "Alterna microteoría y ejercicios reales del banco vinculados a los nodos. Haz preguntas de conceptos, hipótesis, relaciones, unidades y casos límite dentro de cada ejercicio. Da pistas solo si me bloqueo.",
    },
    "walk_oral_exam": {
        "nombre": "Paseo de examen oral",
        "descripcion": "La IA plantea una situación y evalúa tu enfoque físico y tu razonamiento.",
        "reparto": "El estudiante dirige la resolución; la IA actúa como examinador.",
        "instrucciones": "Plantea un problema del banco cada vez. No corrijas hasta que termine mi razonamiento y pregunta por hipótesis, signos y significado físico.",
    },
}


def _default_state() -> dict:
    return {
        "version": 1,
        "sessions": [],
        "skills": {
            "study_method": {
                "stage": "relevance",
                "logs": [],
            }
        },
        "pacer_overrides": {},
    }


def walk_mode_info(mode: str) -> dict:
    return copy.deepcopy(WALK_MODES.get(mode, WALK_MODES["walk_review"]))


def walk_report_path(session_id: str) -> str:
    """Ruta local, predecible y acotada para el cierre de un paseo remoto."""
    safe_id = "".join(c for c in str(session_id) if c.isalnum())[:32]
    if not safe_id:
        raise ValueError("Identificador de sesión no válido")
    return os.path.join(WALK_REPORTS_DIR, f"{safe_id}.json")


def save_active_walk_context(session: dict, prompt: str, report_path: str) -> dict:
    """Contexto que consulta el chat persistente de Paseos de Física."""
    payload = {
        "session_id": session["id"],
        "mode": session["session_type"],
        "status": session.get("status"),
        "report_path": report_path,
        "prompt": prompt,
        "updated_at": _now(),
    }
    os.makedirs(os.path.dirname(ACTIVE_WALK_PATH), exist_ok=True)
    with open(ACTIVE_WALK_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def build_walk_prompt(mode: str, context: dict, preview: list[dict],
                      report_path: str | None = None,
                      note_context: str = "") -> str:
    info = walk_mode_info(mode)
    materia = str(context.get("materia", "")).strip()
    practice_first = materia.casefold() == "electromagnetismo"
    if practice_first:
        method = """Esta es mi segunda cursada de Electromagnetismo. Empieza directamente con cuestiones y ejercicios reales del banco para descubrir mis huecos. No impartas teoría de entrada ni sigas una secuencia teoría → ejercicios. Explica teoría únicamente cuando mi intento revele un hueco y vuelve a comprobarlo con otra cuestión o ejercicio real."""
        first_rule = "- En Electromagnetismo, empieza con una cuestión o ejercicio real del banco, sin exposición teórica previa salvo el recordatorio imprescindible de una línea."
        theory_rule = "- En Electromagnetismo, la teoría es reactiva: solo explica el hueco que aparezca en mi intento y vuelve después a la práctica."
        cycle_rule = "- En Electromagnetismo, sigue: cuestión o problema real → intento → diagnóstico → microexplicación si hace falta → nueva cuestión o problema real."
    else:
        method = "La asignatura sigue el método general: microteoría imprescindible para el ejercicio actual y práctica inmediata con problemas reales del banco."
        first_rule = "- Empieza mostrando brevemente el alcance y plantea el primer ciclo de trabajo."
        theory_rule = "- Da solo la teoría mínima necesaria para resolver el siguiente problema del banco."
        cycle_rule = "- Sigue el ciclo: microteoría → enunciado exacto → intento del estudiante → corrección → siguiente ejercicio."
    conceptos = "\n".join(
        f"- {item.get('id')}: {item.get('nombre')} ({item.get('materia', '')}) — {item.get('descripcion', '')}"
        for item in preview
    ) or "- No hay nodos concretos; haz un repaso general de la asignatura indicada."
    problemas = "\n".join(
        f"- {problem.get('id')}: {problem.get('titulo', 'Problema')} "
        f"({problem.get('tipo_problema', 'procedencia no indicada')}) — "
        f"nodos: {', '.join(problem.get('nodos_requeridos', []))} — {problem.get('enunciado', '')}"
        for item in preview
        for problem in item.get('problemas', []) or []
    ) or "- No hay problemas empaquetados; no inventes ninguno."
    return f"""ENCARGO DE PASEO DE ESTUDIO INTEGRADO
Este texto es el encargo completo de una sesión de estudio. Pégalo entero en NotebookLM o en el chat remoto que vayas a utilizar. No conviertas la sesión en una conversación genérica: trabaja sobre los conceptos indicados y respeta el cierre estructurado.

MODO: {info['nombre']}

PROPÓSITO DEL PASEO:
Usa los nodos y problemas reales incluidos en el encargo para trabajar en ciclos de microteoría, intento y corrección. El estudiante decide qué profundidad darle a cada concepto, cuándo cambiar de tema y cuándo cerrar; no hay una lista obligatoria que completar.
Tu función es actuar como tutor y examinador exigente cuando resulte útil: señala lagunas, dudas de planteamiento y falta de rigor en hipótesis o condiciones de contorno, pero no conviertas la conversación en una cuota de rendimiento.

MÉTODO ESPECÍFICO:
{method}

La duración del paseo es flexible; el valor de disponibilidad, si existe, solo se conserva como contexto y no limita la conversación.
{info['instrucciones']}
{info['reparto']}

CONCEPTOS SUGERIDOS PARA EXPLORAR:
{conceptos}

PROBLEMAS REALES DEL BANCO DISPONIBLES:
{problemas}

APUNTES PERSONALES PREVIOS DE ESOS NODOS:
{note_context or '- No hay apuntes previos: este será el primer registro personal de estos nodos.'}
Usa esta información solo para comprobar continuidad. No la des por cierta si el estudiante la corrige durante la conversación.

REGLAS DIDÁCTICAS OBLIGATORIAS (MÁXIMA EXIGENCIA - NIVEL 10):
- Haz una sola pregunta cada vez y espera la respuesta del estudiante.
{first_rule}
{theory_rule}
- Presenta únicamente problemas incluidos arriba y no inventes problemas ni variantes.
{cycle_rule}
- CERO COMPLACENCIA: No aceptes respuestas aproximadas, intuiciones vagas ni fórmulas sueltas sin derivación física. Si una respuesta sacaría un 7 en un examen, repregunta hasta elevarla al nivel del 10.
- Para cada concepto, exige implacablemente estos 4 pilares:
  1. Intuición física causal: qué ocurre microscópica y cualitativamente antes de cualquier matemática.
  2. Hipótesis y límites de validez: por qué este modelo, bajo qué suposiciones exactas y cuándo se rompe.
  3. Condiciones de contorno y traducción matemática: cómo se plantea en un examen real de la UVa y qué términos se anulan justificadamente.
  4. Casos límite y trampas de examen: qué pasa en extremos asintóticos y qué errores típicos restan puntos en las correcciones de los profesores de la UVa.
- Si detectas una laguna, duda o justificación vacía, detente y hazle reconstruir la idea con preguntas guía antes de avanzar.
- Demuestra las propiedades no inmediatas desde las definiciones y muestra los pasos intermedios necesarios. No presentes identidades o criterios importantes como hechos aislados: distingue definición, demostración y consecuencia.
- Traduce cada ecuación no trivial antes de usarla: identifica los objetos, la operación, el significado de la igualdad y su interpretación física. En ecuaciones de operadores, aclara qué significa al actuar sobre un ket arbitrario.
- Separa la manipulación algebraica de la conclusión física y explica el puente entre ambas.
- Lleva un registro interno de conceptos sólidos, parciales, débiles y pistas utilizadas.
- Cuando diga exactamente «CIERRE ESTRUCTURADO DEL PASEO», no sigas enseñando. Genera el informe JSON de cierre. No respondas con una despedida normal ni con un resumen en prosa.
{{"tipo":"{mode}","duracion_minutos":0,"nodos":[{{"id":"...","resultado":"solido|parcial|debil|no_trabajado","calidad":0.0,"dominado":[],"dudas":[],"evidencias":[],"siguiente_accion":""}}],"resumen":"","errores_recurrentes":[],"siguiente_accion":"","apuntes":[{{"node_id":"...","explicacion_validada":[],"explicacion_para_mi":[],"bien_entendido":[],"dificultades":[],"errores":[],"procedimiento_examen":[],"ejemplos":[]}}]}}
- Usa solo ids de los conceptos del plan. La calidad debe ser acorde al estándar de un 10: solo 0.95 para respuestas impecables de Matrícula de Honor, 0.60 parcial, 0.25 débil y 0.0 no trabajado.
- `apuntes` no es una transcripción: escribe solo las ideas que hayan quedado explicadas o comprobadas durante la conversación. Cada entrada debe usar un `node_id` del plan. Separa la explicación física general de la explicación o regla mnemotécnica que funciona específicamente para este estudiante. Si no hay evidencia suficiente, deja la lista vacía.
{f'- Como esta es una sesión Remote, guarda ese JSON UTF-8, sin Markdown ni texto adicional, exactamente en: {report_path}. Al guardarlo el Centro de Estudio lo incorporará automáticamente.' if report_path else '- Devuelve únicamente el JSON, sin Markdown ni texto adicional. Yo lo copiaré después a la aplicación.'}
"""


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
        base.update({k: v for k, v in state.items() if k in base})
        base["skills"].setdefault("study_method", {"stage": "relevance", "logs": []})
        base["pacer_overrides"] = base.get("pacer_overrides") or {}
        base["sessions"] = base.get("sessions") or []
        return base


def save_state(state: dict) -> None:
    with _LOCK:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        temp_path = STATE_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, STATE_PATH)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _slug(value: str) -> str:
    return str(value or "").strip().lower()


def classify_pacer(node: dict, override: str | None = None) -> dict:
    """Clasificación inicial explicable; el estudiante puede corregirla después."""
    code = override if override in PACER else None
    text = " ".join(str(node.get(k, "")) for k in ("nombre", "descripcion"))
    lower = _slug(text)
    if not code:
        if any(word in lower for word in ("procedimiento", "método", "resolver", "cálculo", "integral", "algoritmo", "ecuación diferencial")):
            code = "P"
        elif any(word in lower for word in ("ejemplo", "aplicación", "fenómeno", "experimento", "caso límite", "interpretación física")):
            code = "E"
        elif any(word in lower for word in ("definición", "identidad", "notación", "unidad", "constante", "clasificación")):
            code = "R"
        elif any(word in lower for word in ("analogía", "análogo", "comparación", "relación")):
            code = "A"
        else:
            code = "C"
    info = PACER[code]
    return {
        "codigo": code,
        "nombre": info["nombre"],
        "color": info["color"],
        "accion": info["accion"],
        "estimado": override not in PACER,
    }


def rail_snapshot(state: dict | None = None) -> dict:
    state = state or load_state()
    skill = state["skills"].setdefault("study_method", {"stage": "relevance", "logs": []})
    stage = skill.get("stage", "relevance")
    if stage not in RAIL:
        stage = "relevance"
    return {"stage": stage, **RAIL[stage], "logs": skill.get("logs", [])[-5:]}


def _node_preview(item: dict, nodes: dict, profile: dict, overrides: dict) -> dict:
    node = nodes.get(item.get("id"), {})
    profile_entry = profile.get("nodos", {}).get(item.get("id"), {})
    prerequisitos = []
    for prereq in node.get("prerequisitos", []):
        target = nodes.get(prereq.get("id"))
        if target:
            prerequisitos.append({
                "id": prereq["id"],
                "nombre": target.get("nombre", prereq["id"]),
                "peso": prereq.get("peso", 1.0),
            })
    pacer = classify_pacer(node, overrides.get(item.get("id")))
    tipo = item.get("tipo", "nuevo")
    if tipo == "repaso":
        motivo = f"Repaso programado · {item.get('retraso', 0)} días de retraso" if item.get("retraso") else "Repaso programado hoy"
    elif tipo == "continuacion":
        motivo = "Continuación del último punto trabajado"
    elif tipo == "inicio":
        motivo = "Inicio por el orden del grafo"
    elif tipo == "eleccion":
        motivo = "Nodo elegido por el estudiante"
    else:
        motivo = "Nodo incluido en la sesión"
    theory_seen = bool(profile_entry.get("teoria_vista", False))
    return {
        "id": item.get("id"),
        "nombre": item.get("nombre", node.get("nombre", item.get("id"))),
        "materia": item.get("materia", node.get("materia", "")),
        "tipo": tipo,
        "motivo": motivo,
        "descripcion": node.get("descripcion", ""),
        "prerequisitos": prerequisitos,
        "pacer": pacer,
        "dominio": item.get("dominio", profile_entry.get("dominio", 0)),
        "teoria_vista": theory_seen,
        "theory_status": "vista" if theory_seen else "pendiente",
        "pregunta_preview": f"¿Qué recuerdas ya sobre {item.get('nombre', 'este concepto')} y con qué idea lo conectarías?",
    }


def build_preview(plan: dict, nodes: dict, profile: dict) -> list[dict]:
    state = load_state()
    overrides = state.get("pacer_overrides", {})
    items = []
    for item in plan.get("repasos", []):
        items.append(_node_preview({**item, "tipo": "repaso"}, nodes, profile, overrides))
    for item in plan.get("nuevos", []):
        items.append(_node_preview({**item, "tipo": "nuevo"}, nodes, profile, overrides))
    return items


def start_session(data: dict) -> dict:
    now = _now()
    session_type = str(data.get("session_type", "desk_guided"))[:40]
    if session_type not in {"desk_guided", "work_guided", *WALK_MODES}:
        session_type = "desk_guided"
    materia = str(data.get("materia", ""))[:160]
    problem_ids = []
    for problem_id in data.get("problem_ids", []) or []:
        value = str(problem_id).strip()
        if value and value not in problem_ids:
            problem_ids.append(value[:120])
        if len(problem_ids) >= 60:
            break
    session = {
        "id": uuid.uuid4().hex[:12],
        "status": "active",
        "started_at": now,
        "ended_at": None,
        "context": {
            "energy": max(1, min(5, int(data.get("energy", 3)))),
            "focus": max(1, min(5, int(data.get("focus", 3)))),
            "available_minutes": max(5, min(600, int(data.get("available_minutes", 60)))),
            "goal": str(data.get("goal", "aprender"))[:40],
            "obstacle": str(data.get("obstacle", ""))[:300],
        },
        "session_type": session_type,
        "materia": materia,
        "walk_protocol": walk_mode_info(session_type) if session_type in WALK_MODES else None,
        "plan_ids": [str(x)[:80] for x in data.get("plan_ids", [])][:60],
        "problem_ids": problem_ids,
        "preview_ack": bool(data.get("preview_ack", False)),
        "events": [],
        "reflection": None,
        "grind": None,
        "rail": None,
    }
    state = load_state()
    state["sessions"].append(session)
    state["sessions"] = state["sessions"][-120:]
    save_state(state)
    return copy.deepcopy(session)


def retarget_session(session_id: str, plan_ids: list[str],
                     problem_ids: list[str] | None = None) -> dict:
    """Cambia el alcance de una sesión activa por una continuación explícita.

    El alcance lo decide el estudiante o la continuidad del historial; los ids
    conservan el límite de nodos y problemas que puede registrar la sesión.
    La sesión conserva su identidad y su historial; solo se sustituye el alcance
    pendiente antes de registrar evidencias.
    """
    state = load_state()
    session = next((item for item in state["sessions"] if item.get("id") == session_id), None)
    if not session:
        raise KeyError("Sesión no encontrada")
    if session.get("status") != "active":
        raise ValueError("Solo se puede reorientar una sesión activa")

    def _unique(values: list[str] | None, limit: int) -> list[str]:
        result = []
        for value in values or []:
            item = str(value).strip()
            if item and item not in result:
                result.append(item[:120])
            if len(result) >= limit:
                break
        return result

    session["plan_ids"] = _unique(plan_ids, 60)
    if problem_ids is not None:
        session["problem_ids"] = _unique(problem_ids, 60)
    save_state(state)
    return copy.deepcopy(session)


def record_event(session_id: str, data: dict) -> dict:
    state = load_state()
    session = next((s for s in state["sessions"] if s.get("id") == session_id), None)
    if not session:
        raise KeyError("Sesión no encontrada")
    event = {
        "at": _now(),
        "type": str(data.get("type", "practice"))[:40],
        "node_id": str(data.get("node_id", ""))[:80],
        "pacer": str(data.get("pacer", "C"))[:1],
        "quality": max(0.0, min(1.0, float(data.get("quality", 0)))),
        "encoding_response": str(data.get("encoding_response", ""))[:2000],
        "problem_results": data.get("problem_results", {}),
    }
    session["events"].append(event)
    save_state(state)
    return copy.deepcopy(event)


def finish_session(session_id: str, data: dict) -> dict:
    state = load_state()
    session = next((s for s in state["sessions"] if s.get("id") == session_id), None)
    if not session:
        raise KeyError("Sesión no encontrada")
    session["status"] = "completed"
    session["ended_at"] = _now()
    try:
        start = datetime.fromisoformat(session["started_at"])
        end = datetime.fromisoformat(session["ended_at"])
        session["duration_minutes"] = round(max(0, (end - start).total_seconds()) / 60, 1)
    except ValueError:
        session["duration_minutes"] = None
    session["reflection"] = {
        "worked": str(data.get("worked", ""))[:2000],
        "friction": str(data.get("friction", ""))[:1000],
        "next_change": str(data.get("next_change", ""))[:1000],
        "energy_after": max(1, min(5, int(data.get("energy_after", session["context"]["energy"])))),
    }
    session["grind"] = {
        key: bool(data.get(key, False))
        for key in ("grouping", "relational", "interconnected", "nonverbal", "directional", "emphasized")
    }
    session["grind"]["map_note"] = str(data.get("map_note", ""))[:2000]
    stage = str(data.get("rail_stage", "relevance"))
    if stage not in RAIL:
        stage = "relevance"
    action = str(data.get("rail_action", ""))[:40]
    rail = {"stage": stage, "action": action, "experiment": str(data.get("rail_experiment", ""))[:1200]}
    session["rail"] = rail
    skill = state["skills"].setdefault("study_method", {"stage": "relevance", "logs": []})
    skill["stage"] = stage
    skill["logs"].append({"at": session["ended_at"], **rail, "session_id": session_id})
    skill["logs"] = skill["logs"][-40:]
    save_state(state)
    return copy.deepcopy(session)


def normalize_walk_report(report: dict, allowed_ids: list[str]) -> dict:
    """Valida el cierre de voz sin guardar transcripción ni aceptar nodos ajenos al plan."""
    if not isinstance(report, dict):
        raise ValueError("El cierre del paseo debe ser un objeto JSON")
    allowed = {str(item) for item in allowed_ids}
    nodes = []
    for raw in report.get("nodos", []) or []:
        if not isinstance(raw, dict) or str(raw.get("id", "")) not in allowed:
            continue
        quality = max(0.0, min(1.0, float(raw.get("calidad", 0))))
        result = str(raw.get("resultado", "parcial"))
        if result not in {"solido", "parcial", "debil", "no_trabajado"}:
            result = "parcial"
        nodes.append({
            "id": str(raw["id"])[:80],
            "resultado": result,
            "calidad": round(quality, 2),
            "dominado": [str(x)[:300] for x in (raw.get("dominado", []) or [])[:12]],
            "dudas": [str(x)[:300] for x in (raw.get("dudas", []) or [])[:12]],
            "evidencias": [str(x)[:500] for x in (raw.get("evidencias", []) or [])[:12]],
            "siguiente_accion": str(raw.get("siguiente_accion", ""))[:500],
            "teoria_vista": bool(raw["teoria_vista"]) if "teoria_vista" in raw else None,
        })
    note_updates = []
    for raw in report.get("apuntes", []) or []:
        if not isinstance(raw, dict):
            continue
        node_id = str(raw.get("node_id", raw.get("id", "")))
        if node_id not in allowed:
            continue
        raw_teoria = raw.get("teoria", [])
        if isinstance(raw_teoria, str):
            teoria = [raw_teoria[:50000]] if raw_teoria.strip() else []
        elif isinstance(raw_teoria, list):
            teoria = [str(x)[:25000] for x in raw_teoria if str(x).strip()][:8]
        else:
            teoria = []

        raw_aclaraciones = raw.get("aclaraciones", raw.get("dudas_resueltas", []))
        aclaraciones = []
        if isinstance(raw_aclaraciones, list):
            for item in raw_aclaraciones[:15]:
                if isinstance(item, dict):
                    aclaraciones.append({
                        "duda": str(item.get("duda", item.get("pregunta", "")))[:1000],
                        "aclaracion": str(item.get("aclaracion", item.get("respuesta", "")))[:4000],
                    })
                elif isinstance(item, str) and item.strip():
                    aclaraciones.append(item.strip()[:4000])
        elif isinstance(raw_aclaraciones, dict):
            aclaraciones.append({
                "duda": str(raw_aclaraciones.get("duda", raw_aclaraciones.get("pregunta", "")))[:1000],
                "aclaracion": str(raw_aclaraciones.get("aclaracion", raw_aclaraciones.get("respuesta", "")))[:4000],
            })
        elif isinstance(raw_aclaraciones, str) and raw_aclaraciones.strip():
            aclaraciones.append(raw_aclaraciones.strip()[:4000])

        note_updates.append({
            "node_id": node_id[:80],
            "teoria": teoria,
            "aclaraciones": aclaraciones,
            "explicacion_validada": [str(x)[:1400] for x in (raw.get("explicacion_validada", []) or [])[:8]],
            "explicacion_para_mi": [str(x)[:1400] for x in (raw.get("explicacion_para_mi", []) or [])[:8]],
            "bien_entendido": [str(x)[:500] for x in (raw.get("bien_entendido", []) or [])[:12]],
            "dificultades": [str(x)[:700] for x in (raw.get("dificultades", []) or [])[:12]],
            "errores": [str(x)[:700] for x in (raw.get("errores", []) or [])[:12]],
            "procedimiento_examen": [str(x)[:900] for x in (raw.get("procedimiento_examen", []) or [])[:12]],
            "ejemplos": [str(x)[:1000] for x in (raw.get("ejemplos", []) or [])[:8]],
        })
    siguiente_accion = str(
        report.get("siguiente_accion", report.get("recomendacion", ""))
    )[:1200]
    return {
        "tipo": str(report.get("tipo", "walk_review"))[:40],
        "duracion_minutos": max(0, min(600, int(report.get("duracion_minutos", 0) or 0))),
        "nodos": nodes,
        "resumen": str(report.get("resumen", ""))[:3000],
        "errores_recurrentes": [str(x)[:400] for x in (report.get("errores_recurrentes", []) or [])[:20]],
        "siguiente_accion": siguiente_accion,
        "apuntes": note_updates,
    }


def finish_walk_session(session_id: str, report: dict) -> dict:
    state = load_state()
    session = next((s for s in state["sessions"] if s.get("id") == session_id), None)
    if not session:
        raise KeyError("Sesión no encontrada")
    import knowledge_graph.perfil as kg_perfil
    all_nodes = kg_perfil.cargar_grafos()
    materia = str(session.get("materia", "")).strip()
    allowed = set(session.get("plan_ids", []))
    if materia:
        allowed |= {
            nid for nid, n in all_nodes.items()
            if str(n.get("materia", "")).strip().casefold() == materia.casefold()
        }
    if not allowed:
        allowed = set(all_nodes.keys())
    normalized = normalize_walk_report(report, list(allowed))
    worked_ids = [item["id"] for item in normalized.get("nodos", [])]
    if worked_ids:
        cur = set(session.get("plan_ids", []))
        for nid in worked_ids:
            if nid not in cur:
                session.setdefault("plan_ids", []).append(nid)
                cur.add(nid)
    session["status"] = "completed"
    session["ended_at"] = _now()
    try:
        start = datetime.fromisoformat(session["started_at"])
        end = datetime.fromisoformat(session["ended_at"])
        session["duration_minutes"] = round(max(0, (end - start).total_seconds()) / 60, 1)
    except ValueError:
        session["duration_minutes"] = None
    session["walk_report"] = normalized
    session["reflection"] = {
        "worked": normalized["resumen"],
        "friction": "; ".join(normalized["errores_recurrentes"]),
        "next_change": normalized["siguiente_accion"],
        "energy_after": session["context"]["energy"],
    }
    save_state(state)
    return copy.deepcopy(session)


def get_session(session_id: str) -> dict:
    """Consulta de solo lectura para que la interfaz pueda seguir un cierre remoto."""
    state = load_state()
    session = next((s for s in state["sessions"] if s.get("id") == session_id), None)
    if not session:
        raise KeyError("Sesión no encontrada")
    return copy.deepcopy(session)


def set_pacer_override(node_id: str, code: str) -> dict:
    code = str(code or "").upper()
    if code not in PACER:
        raise ValueError("Tipo PACER no válido")
    state = load_state()
    state.setdefault("pacer_overrides", {})[str(node_id)[:80]] = code
    save_state(state)
    return classify_pacer({}, code)


def insights() -> dict:
    state = load_state()
    sessions = [s for s in state.get("sessions", []) if s.get("status") == "completed"]
    recent = sessions[-7:]
    energies = [s.get("context", {}).get("energy") for s in recent if s.get("context", {}).get("energy")]
    focuses = [s.get("context", {}).get("focus") for s in recent if s.get("context", {}).get("focus")]
    skill = rail_snapshot(state)
    return {
        "completed_sessions": len(sessions),
        "recent_sessions": len(recent),
        "average_energy": round(sum(energies) / len(energies), 1) if energies else None,
        "average_focus": round(sum(focuses) / len(focuses), 1) if focuses else None,
        "skill": skill,
        "last_reflection": sessions[-1].get("reflection") if sessions else None,
    }
