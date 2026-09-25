import json

import study_context
import study_sessions


def test_session_outline_is_granular_and_scoped_to_selected_nodes():
    outline = study_context.build_session_outline(
        nodes=[{
            "id": "mc.1.01",
            "nombre": "Traza de un operador",
            "tipo": "nuevo",
            "descripcion": "Definición, cálculo en una base y propiedad cíclica; degeneración.",
            "prerequisitos": [{"id": "al.01", "nombre": "Álgebra lineal"}],
        }],
        problems=[{
            "id": "MC-001",
            "titulo": "Calcula una traza",
            "nodos_requeridos": ["mc.1.01"],
        }],
        session={"goal": "aprender", "available_minutes": 60},
    )

    node_block = next(block for block in outline["blocks"] if block["type"] == "node")
    assert node_block["node_id"] == "mc.1.01"
    assert node_block["items"] == ["Definición", "cálculo en una base", "propiedad cíclica", "degeneración"]
    assert node_block["prerequisites"][0]["id"] == "al.01"
    assert node_block["practice"][0]["id"] == "MC-001"
    assert node_block["theory_status"] == "pendiente"
    rendered = study_context.render_session_outline(outline)
    assert "1. Orientación inicial" in rendered
    assert "2. Nuevo · Traza de un operador [mc.1.01]" in rendered


def test_work_prompt_requires_index_before_diagnosis():
    outline = study_context.build_session_outline(
        nodes=[{"id": "a.1", "nombre": "Concepto A", "descripcion": "Definición y aplicación"}],
        session={"goal": "aprender", "available_minutes": 30},
    )
    prompt = study_context._work_prompt({
        "session": {"id": "s1", "materia": "Asignatura A", "goal": "aprender", "available_minutes": 30, "energy": 3},
        "state": {},
        "outline": outline,
    })

    assert "ÍNDICE GRANULAR DE LA SESIÓN" in prompt
    assert "Primera respuesta obligatoria" in prompt
    assert "antes de explicar teoría o lanzar una pregunta" in prompt
    assert "Concepto A" in prompt
    assert "Teoría ya impartida" in prompt
    assert "hueco concreto" in prompt
    assert "pasos" in prompt and "intermedios necesarios" in prompt
    assert "interpretación física" in prompt
    assert "hipótesis" in prompt and "antecedente" in prompt


def test_session_outline_marks_taught_theory_without_increasing_mastery():
    outline = study_context.build_session_outline(
        nodes=[{"id": "a.1", "nombre": "Concepto A", "descripcion": "Definición"}],
        profile={"nodos": {"a.1": {"teoria_vista": True, "dominio": 0.1}}},
        session={"goal": "practicar", "available_minutes": 30},
    )
    node_block = next(block for block in outline["blocks"] if block["type"] == "node")
    assert node_block["theory_status"] == "vista"
    assert "práctica directa" in study_context.render_session_outline(outline)


def test_work_session_persists_subject_and_problem_scope(tmp_path, monkeypatch):
    state_path = tmp_path / "study_sessions.json"
    monkeypatch.setattr(study_sessions, "STATE_PATH", str(state_path))

    session = study_sessions.start_session({
        "session_type": "work_guided",
        "materia": "Electromagnetismo",
        "plan_ids": ["em.1.01"],
        "problem_ids": ["EM-001"],
        "available_minutes": 45,
    })

    assert session["session_type"] == "work_guided"
    assert session["materia"] == "Electromagnetismo"
    assert session["problem_ids"] == ["EM-001"]
    assert json.loads(state_path.read_text(encoding="utf-8"))["sessions"][0]["materia"] == "Electromagnetismo"


def test_work_report_is_limited_to_the_active_session(monkeypatch):
    monkeypatch.setattr(study_context.kg_problemas, "cargar_banco", lambda: {
        "Electromagnetismo": {"problemas": [
            {"id": "EM-001", "nodos_requeridos": ["em.1.01"]},
        ]}
    })
    session = {
        "id": "session-1",
        "plan_ids": ["em.1.01"],
        "problem_ids": ["EM-001"],
    }

    normalized = study_context._normalize_work_report({
        "session_id": "session-1",
        "nodos": [
            {"id": "em.1.01", "resultado": "solido", "calidad": 0.95},
            {"id": "fuera-de-sesion", "resultado": "solido", "calidad": 1},
        ],
        "problem_attempts": [
            {"problem_id": "EM-001", "verdict": "resuelto", "quality": 1},
            {"problem_id": "otro", "verdict": "resuelto", "quality": 1},
        ],
    }, session)

    assert [item["id"] for item in normalized["nodos"]] == ["em.1.01"]
    assert [item["problem_id"] for item in normalized["problem_attempts"]] == ["EM-001"]


def test_auto_imports_ready_work_report(monkeypatch):
    status = {
        "active": True,
        "report_ready": True,
        "session": {"id": "session-1"},
    }
    report = {"session_id": "session-1", "nodos": []}
    calls = []

    monkeypatch.setattr(study_context, "active_study_status", lambda: status)
    monkeypatch.setattr(study_context, "load_active_study_report", lambda: report)
    monkeypatch.setattr(
        study_context,
        "finish_work_report",
        lambda session_id, value: calls.append((session_id, value)) or {"ok": True},
    )

    result = study_context.auto_import_ready_work_report()

    assert result["imported"] is True
    assert calls == [("session-1", report)]


def test_work_report_accepts_other_subject_nodes_and_problems_from_bank(monkeypatch):
    monkeypatch.setattr(study_context.kg_perfil, "cargar_grafos", lambda: {
        "el.1.01": {"id": "el.1.01", "materia": "Electrónica"},
        "el.1.04": {"id": "el.1.04", "materia": "Electrónica"},
        "el.2.01": {"id": "el.2.01", "materia": "Electrónica"},
    })
    monkeypatch.setattr(study_context.kg_problemas, "cargar_banco", lambda: {
        "Electrónica": {"problemas": [
            {"id": "EL-001", "nodos_requeridos": ["el.1.01"]},
            {"id": "EL-002", "nodos_requeridos": ["el.1.04"]},
        ]}
    })
    session = {
        "id": "s-elec",
        "materia": "Electrónica",
        "plan_ids": ["el.1.01"],
        "problem_ids": ["EL-001"],
    }
    normalized = study_context._normalize_work_report({
        "session_id": "s-elec",
        "nodos": [
            {"id": "el.1.01", "calidad": 0.8},
            {"id": "el.1.04", "calidad": 0.75},
            {"id": "no-existe", "calidad": 0.5},
        ],
        "problem_attempts": [
            {"problem_id": "EL-001", "verdict": "resuelto", "quality": 1},
            {"problem_id": "EL-002", "verdict": "resuelto", "quality": 1},
            {"problem_id": "no-bank", "verdict": "resuelto", "quality": 1},
        ],
    }, session)
    assert set(item["id"] for item in normalized["nodos"]) == {"el.1.01", "el.1.04"}
    assert set(item["problem_id"] for item in normalized["problem_attempts"]) == {"EL-001", "EL-002"}

