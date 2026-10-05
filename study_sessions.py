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
import re
import threading
import uuid
from datetime import datetime

from study_output_guidance import OUTPUT_FORMAT_GUIDANCE


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
        "nombre": "Teoría guiada (paseo o bus)",
        "descripcion": "La IA desarrolla cada nodo con rigor y comprueba su aplicación con problemas disponibles en el banco; puedes responder hablando o escribiendo.",
        "reparto": "La IA explica el nodo y plantea después un problema registrado en el banco si existe uno asociado.",
        "instrucciones": "Trabaja un nodo cada vez. Explica la teoría con profundidad y plantea solo problemas existentes en la base de datos. Si no hay uno asociado, dilo y no inventes un sustituto.",
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
        "instrucciones": "Trabaja cada nodo con los problemas asociados que existan en el banco. No inventes ejercicios. Haz preguntas de conceptos, hipótesis, relaciones, unidades y casos límite al analizar el material del banco.",
    },
    "walk_oral_exam": {
        "nombre": "Paseo de examen oral",
        "descripcion": "La IA plantea una situación y evalúa tu enfoque físico y tu razonamiento.",
        "reparto": "El estudiante dirige la resolución; la IA actúa como examinador.",
        "instrucciones": "Plantea únicamente problemas asociados existentes en el banco. Si un nodo no tiene uno, indícalo y no lo sustituyas por un ejercicio inventado. No corrijas un intento hasta que el estudiante termine su razonamiento; pregunta por hipótesis, signos y significado físico al corregir.",
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
        method = """Esta es mi segunda cursada de Electromagnetismo. Empieza con el resumen completo de la sesión y después usa solo cuestiones y problemas existentes en el banco para descubrir huecos. No inventes ejercicios. Explica con detalle cada hueco que aparezca y vuelve a comprobarlo con otra cuestión real del banco cuando exista."""
        first_rule = "- En Electromagnetismo, presenta primero el resumen completo de la sesión; después empieza con una cuestión o ejercicio real del banco. No inventes ejercicios."
        theory_rule = "- En Electromagnetismo, explica con suficiente profundidad cada hueco: definición, intuición física, hipótesis, derivación necesaria, significado y límites de validez."
        cycle_rule = "- En Electromagnetismo, sigue: problema real del banco → intento → diagnóstico → explicación completa del hueco si hace falta → siguiente problema real disponible. Si no existe otro, no lo inventes."
    else:
        method = "Se trabaja un nodo cada vez con una explicación de profesor completa y rigurosa. Se usan solo problemas registrados en el banco; se espera el intento y se corrige antes de pasar al siguiente nodo."
        first_rule = "- Antes de explicar o preguntar, presenta un resumen completo del objetivo, los nodos con ID y nombre, su condición de repaso/nuevo, todos los problemas previstos con ID y título, y los nodos sin problema asociado."
        theory_rule = "- Explica con profundidad suficiente para reconstruir y aplicar la teoría: motivación e intuición física, definiciones, símbolos, hipótesis, derivación paso a paso, significado de las ecuaciones, interpretación física, condiciones de validez y límites. Evita los resúmenes superficiales y las listas de fórmulas."
        cycle_rule = "- Después de explicar cada nodo, plantea solo el siguiente problema existente en el banco que esté vinculado al nodo. Conserva ID y enunciado exactos; espera el intento, corrige y aclara antes de avanzar. Si no existe un problema adecuado, dilo y no inventes uno."
    type_labels = {
        "repaso": "repaso",
        "continuacion": "continuación",
        "inicio": "inicio",
        "eleccion": "elección del estudiante",
        "nuevo": "nuevo",
    }
    concept_lines = []
    for item in preview:
        type_label = type_labels.get(str(item.get("tipo", "")), "tipo no indicado")
        concept_lines.append(
            f"- {item.get('id')}: {item.get('nombre')} [{type_label}] — {item.get('descripcion', '')}"
        )
    conceptos = "\n".join(concept_lines) or (
        "- No hay nodos seleccionados. Consulta el progreso y el historial antes de iniciar; "
        "no empieces un repaso genérico ni pidas elegir tema si la continuidad está registrada."
    )
    problem_by_id = {}
    for item in preview:
        for problem in item.get("problemas", []) or []:
            problem_id = str(problem.get("id", "")).strip()
            if problem_id:
                problem_by_id.setdefault(problem_id, problem)
    problem_lines = []
    for problem in problem_by_id.values():
        source = str(problem.get("hoja", "")).strip()
        provenance = f" · {source}" if source else ""
        problem_lines.append(
            f"- {problem.get('id')}: {problem.get('titulo', 'Problema')}{provenance} — "
            f"nodos: {', '.join(problem.get('nodos_requeridos', []))} — {problem.get('enunciado', '')}"
        )
    for item in preview:
        if not (item.get("problemas", []) or []):
            problem_lines.append(
                f"- Sin problema del banco asociado a {item.get('id')}: "
                "no se propondrá un ejercicio sustituto."
            )
    problemas = "\n".join(problem_lines) or "- No hay problemas del banco seleccionados; no se propondrán problemas inventados."
    return f"""ENCARGO DE PASEO DE ESTUDIO INTEGRADO
Este texto es el encargo completo de una sesión de estudio. Pégalo entero en NotebookLM o en el chat remoto que vayas a utilizar. No conviertas la sesión en una conversación genérica: trabaja sobre los conceptos indicados y respeta el cierre estructurado.

MODO: {info['nombre']}

PROPÓSITO DEL PASEO:
Usa los nodos y problemas reales incluidos en el encargo para trabajar en ciclos de explicación, intento y corrección. El estudiante decide el ritmo y cuándo cerrar; cada explicación debe seguir siendo completa y rigurosa para el nodo trabajado.
Tu función es actuar como tutor y examinador exigente cuando resulte útil: señala lagunas, dudas de planteamiento y falta de rigor en hipótesis o condiciones de contorno, pero no conviertas la conversación en una cuota de rendimiento.

MÉTODO ESPECÍFICO:
{method}

Lee docs/protocolo_de_tutoria.md si tienes acceso al repositorio. Sus reglas de apertura,
profundidad explicativa y uso exclusivo de la base de problemas son obligatorias.
Guarda también en GitHub privado o Drive privado cada resultado sustantivo de esta sesión
y verifica que se puede leer desde el destino remoto. El portátil no puede ser la única
copia. No subas el perfil ni el progreso personal a un repositorio público.

{OUTPUT_FORMAT_GUIDANCE}

La duración del paseo es flexible; el valor de disponibilidad, si existe, solo se conserva como contexto y no limita la conversación.
{info['instrucciones']}
{info['reparto']}

NODOS DE LA SESIÓN:
{conceptos}

PROBLEMAS DEL BANCO PREVISTOS Y DISPONIBLES:
{problemas}

APUNTES PERSONALES PREVIOS DE ESOS NODOS:
{note_context or '- No hay apuntes previos: este será el primer registro personal de estos nodos.'}
Usa esta información solo para comprobar continuidad. No la des por cierta si el estudiante la corrige durante la conversación.

REGLAS DIDÁCTICAS OBLIGATORIAS (MÁXIMA EXIGENCIA - NIVEL 10):
- Haz una sola pregunta cada vez y espera la respuesta del estudiante.
{first_rule}
{theory_rule}
- Al terminar la explicación, presenta únicamente el siguiente problema listado del banco que esté vinculado al nodo; conserva su enunciado exacto, ID y nodos. Espera el intento, corrige y revisa las dudas antes de pasar al nodo siguiente.
- Si no hay un problema adecuado en el banco, dilo. No inventes ejercicios, no sustituyas por problemas de otro nodo y no presentes una pregunta conceptual como ejercicio del banco.
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
{{"tipo":"{mode}","duracion_minutos":0,"nodos":[{{"id":"...","resultado":"solido|parcial|debil|no_trabajado","calidad":0.0,"dominado":[],"dudas":[],"evidencias":[],"siguiente_accion":"","practica_realizada":false,"practica_sin_id":false,"practica_descripcion":""}}],"problem_attempts":[{{"problem_id":"id-exacto-del-banco","verdict":"resuelto|hueco_teorico|incorrecto","quality":0.0,"theory_gap_nodes":[],"error_nodes":[],"comments":"","seconds":0}}],"resumen":"","errores_recurrentes":[],"siguiente_accion":"","apuntes":[{{"node_id":"...","explicacion_validada":[],"explicacion_para_mi":[],"bien_entendido":[],"dificultades":[],"errores":[],"procedimiento_examen":[],"ejemplos":[],"recursos_visuales":[{{"tipo":"imagen|diagrama_svg|html_interactivo|video|guion_video","titulo":"","descripcion":"","ruta":"recursos_visuales/archivo"}}]}}]}}
- Usa solo ids de los conceptos del plan. La calidad debe ser acorde al estándar de un 10: solo 0.95 para respuestas impecables de Matrícula de Honor, 0.60 parcial, 0.25 débil y 0.0 no trabajado.
- Registra en `apuntes.recursos_visuales` solo recursos creados y guardados, con tipo, título, descripción y ruta relativa. No inventes rutas ni incluyas el código HTML entero en el JSON.
- Incluye un intento por cada problema del banco que realmente se haya trabajado e informa su ID y resultado en `problem_attempts`. No registres problemas inventados.
- `apuntes` no es una transcripción: escribe solo las ideas que hayan quedado explicadas o comprobadas durante la conversación. Cada entrada debe usar un `node_id` del plan. Separa la explicación física general de la explicación o regla mnemotécnica que funciona específicamente para este estudiante. Si no hay evidencia suficiente, deja la lista vacía.
{f'- Como esta es una sesión Remote, guarda ese JSON UTF-8, sin Markdown ni texto adicional, exactamente en: {report_path}. Al guardarlo el Centro de Estudio lo incorporará automáticamente.' if report_path else '- Devuelve únicamente el JSON, sin Markdown ni texto adicional. Yo lo copiaré después a la aplicación.'}
Después de guardar e incorporar el informe, conserva una copia remota privada del informe y
de cualquier recurso creado. Comprueba la copia con una lectura del destino antes de decir
que la sesión quedó respaldada.
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
    theory_origin = str(profile_entry.get("teoria_vista_origen", "")).casefold()
    theory_certainty = "probable" if theory_seen and "probable" in theory_origin else (
        "confirmada" if theory_seen else "no_registrada"
    )
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
        "theory_certainty": theory_certainty,
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


def _normalize_visual_resources(raw_resources) -> list[dict]:
    """Conserva solo referencias locales válidas a recursos guardados."""
    if not isinstance(raw_resources, list):
        return []
    extensions = {
        "imagen": (".png", ".jpg", ".jpeg", ".webp"),
        "diagrama_svg": ".svg",
        "html_interactivo": ".html",
        "video": (".mp4", ".webm"),
        "guion_video": ".md",
    }
    result = []
    for raw in raw_resources[:8]:
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("tipo", "")).strip().lower()
        if kind not in extensions:
            continue
        path = str(raw.get("ruta", "")).strip().replace("\\", "/")
        parts = path.split("/")
        if (not path.startswith("recursos_visuales/") or ".." in parts
                or not re.fullmatch(r"recursos_visuales/[A-Za-z0-9._/-]+", path)):
            continue
        suffix = os.path.splitext(path)[1].lower()
        allowed_suffixes = extensions[kind]
        if suffix not in (allowed_suffixes if isinstance(allowed_suffixes, tuple) else (allowed_suffixes,)):
            continue
        title = str(raw.get("titulo", "")).strip()[:200]
        description = str(raw.get("descripcion", "")).strip()[:800]
        if not title:
            continue
        result.append({
            "tipo": kind,
            "titulo": title,
            "descripcion": description,
            "ruta": path,
        })
    return result


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
            "practica_realizada": bool(raw.get("practica_realizada", False)),
            "practica_sin_id": bool(raw.get("practica_sin_id", False)),
            "practica_descripcion": str(raw.get("practica_descripcion", ""))[:2000],
        })
    problem_attempts = []
    for raw in report.get("problem_attempts", []) or []:
        if not isinstance(raw, dict):
            continue
        problem_id = str(raw.get("problem_id", raw.get("id", ""))).strip()
        if not problem_id:
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
        try:
            quality = max(0.0, min(1.0, float(raw.get("quality", raw.get("calidad", 0)))))
        except (TypeError, ValueError):
            quality = 0.0
        problem_attempts.append({
            "problem_id": problem_id[:120],
            "verdict": verdict,
            "quality": round(quality, 2),
            "theory_gap_nodes": [str(x) for x in (raw.get("theory_gap_nodes", []) or []) if str(x) in allowed][:20],
            "error_nodes": [str(x) for x in (raw.get("error_nodes", []) or []) if str(x) in allowed][:20],
            "comments": str(raw.get("comments", "") or "")[:2000],
            "seconds": max(0, min(86400, int(raw.get("seconds", 0) or 0))),
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
            "recursos_visuales": _normalize_visual_resources(raw.get("recursos_visuales", [])),
        })
    siguiente_accion = str(
        report.get("siguiente_accion", report.get("recomendacion", ""))
    )[:1200]
    return {
        "tipo": str(report.get("tipo", "walk_review"))[:40],
        "duracion_minutos": max(0, min(600, int(report.get("duracion_minutos", 0) or 0))),
        "nodos": nodes,
        "problem_attempts": problem_attempts,
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
