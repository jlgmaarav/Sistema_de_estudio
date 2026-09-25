import study_sessions


def test_pacer_classifier_is_explicable():
    result = study_sessions.classify_pacer({"nombre": "Teorema de la divergencia", "descripcion": "Uso para convertir integrales"})
    assert result["codigo"] in {"P", "C"}
    assert result["accion"]


def test_session_lifecycle_persists_reflection(tmp_path, monkeypatch):
    monkeypatch.setattr(study_sessions, "STATE_PATH", str(tmp_path / "study_sessions.json"))
    session = study_sessions.start_session({
        "plan_ids": ["em.0.01"],
        "energy": 2,
        "focus": 4,
        "available_minutes": 35,
        "goal": "consolidar",
        "preview_ack": True,
    })
    assert session["status"] == "active"

    event = study_sessions.record_event(session["id"], {
        "node_id": "em.0.01",
        "pacer": "C",
        "quality": 0.75,
        "encoding_response": "Lo relaciono con componentes y producto escalar.",
    })
    assert event["quality"] == 0.75

    finished = study_sessions.finish_session(session["id"], {
        "worked": "Escribir primero la relación me ayudó.",
        "friction": "Me costó recordar la definición exacta.",
        "next_change": "Haré un dibujo antes de calcular.",
        "energy_after": 3,
        "grouping": True,
        "relational": True,
        "rail_stage": "awareness",
        "rail_action": "experimentar",
        "rail_experiment": "Probaré el preview antes de mirar la lección.",
    })
    assert finished["status"] == "completed"
    assert finished["reflection"]["next_change"]
    assert finished["grind"]["grouping"] is True
    assert study_sessions.insights()["skill"]["stage"] == "awareness"


def test_retarget_active_session_changes_only_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(study_sessions, "STATE_PATH", str(tmp_path / "study_sessions.json"))
    session = study_sessions.start_session({
        "materia": "Mecánica Cuántica",
        "plan_ids": ["mc.1.01"],
        "problem_ids": ["MC-001"],
        "preview_ack": True,
    })

    updated = study_sessions.retarget_session(
        session["id"], ["mc.1.08"], ["MC-008", "MC-009"],
    )

    assert updated["id"] == session["id"]
    assert updated["plan_ids"] == ["mc.1.08"]
    assert updated["problem_ids"] == ["MC-008", "MC-009"]
    assert updated["started_at"] == session["started_at"]


def test_build_preview_adds_relations_and_pacer(monkeypatch, tmp_path):
    monkeypatch.setattr(study_sessions, "STATE_PATH", str(tmp_path / "study_sessions.json"))
    preview = study_sessions.build_preview(
        {"repasos": [], "nuevos": [{"id": "b", "nombre": "B", "materia": "M", "tipo": "nuevo"}]},
        {"a": {"id": "a", "nombre": "A", "materia": "M"}, "b": {"id": "b", "nombre": "B", "materia": "M", "prerequisitos": [{"id": "a", "peso": 1.0}], "descripcion": "Relación y aplicación"}},
        {"nodos": {}},
    )
    assert preview[0]["prerequisitos"][0]["nombre"] == "A"
    assert preview[0]["pacer"]["codigo"] in {"A", "C", "E", "P", "R"}


def test_walk_report_is_structured_and_scoped_to_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(study_sessions, "STATE_PATH", str(tmp_path / "study_sessions.json"))
    session = study_sessions.start_session({
        "plan_ids": ["em.1.07"],
        "session_type": "walk_rescue",
        "available_minutes": 60,
        "preview_ack": True,
    })
    finished = study_sessions.finish_walk_session(session["id"], {
        "tipo": "walk_rescue",
        "duracion_minutos": 58,
        "resumen": "Aclaré la diferencia entre campo y potencial.",
        "nodos": [
            {"id": "em.1.07", "resultado": "solido", "calidad": 0.95,
             "dominado": ["Interpretación física"], "dudas": []},
            {"id": "fuera.del.plan", "resultado": "solido", "calidad": 1.0},
        ],
    })
    assert finished["session_type"] == "walk_rescue"
    assert len(finished["walk_report"]["nodos"]) == 1
    assert finished["walk_report"]["nodos"][0]["calidad"] == 0.95
    assert finished["reflection"]["worked"]


def test_walk_prompt_contains_close_contract():
    prompt = study_sessions.build_walk_prompt(
        "walk_review",
        {"available_minutes": 60},
        [{"id": "em.1.07", "nombre": "Potencial", "materia": "EM"}],
    )
    assert "CIERRE ESTRUCTURADO DEL PASEO" in prompt
    assert '"nodos"' in prompt
    assert "em.1.07" in prompt


def test_walk_introduction_is_silent_bus_compatible_and_theory_first():
    mode = study_sessions.WALK_MODES["walk_introduction"]
    assert "bus" in mode["reparto"].lower()
    assert "por texto" in mode["reparto"].lower()
    assert "primero" in mode["instrucciones"].lower()
    assert "no plantees problemas" in mode["instrucciones"].lower()


def test_remote_walk_prompt_has_a_scoped_report_path(tmp_path, monkeypatch):
    monkeypatch.setattr(study_sessions, "WALK_REPORTS_DIR", str(tmp_path))
    path = study_sessions.walk_report_path("abc-123")
    prompt = study_sessions.build_walk_prompt(
        "walk_review", {"available_minutes": 60}, [], report_path=path
    )
    assert path.endswith("abc123.json")
    assert path in prompt
    assert "Remote" in prompt


def test_active_walk_context_keeps_only_current_session(tmp_path, monkeypatch):
    monkeypatch.setattr(study_sessions, "ACTIVE_WALK_PATH", str(tmp_path / "paseo_actual.json"))
    saved = study_sessions.save_active_walk_context(
        {"id": "walk123", "session_type": "walk_review", "status": "active"},
        "instrucciones", str(tmp_path / "walk123.json")
    )
    assert saved["session_id"] == "walk123"
    assert study_sessions.load_state()  # no altera el estado de sesiones
    assert (tmp_path / "paseo_actual.json").exists()
