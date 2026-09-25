import json

import study_context


def test_build_context_unifica_grafo_perfil_banco_y_estado(monkeypatch, tmp_path):
    kg_dir = tmp_path / "knowledge_graph"
    kg_dir.mkdir()
    (kg_dir / "asignatura_a.json").write_text(json.dumps({
        "materia": "Asignatura A",
        "curso": 4,
        "temas": {"1": "Tema 1"},
        "nodos": [{
            "id": "a.1",
            "nombre": "Concepto A",
            "descripcion": "Base",
            "tema": 1,
            "prerequisitos": [],
        }],
    }), encoding="utf-8")
    (kg_dir / "examenes.json").write_text(json.dumps({"examenes": []}), encoding="utf-8")
    (kg_dir / "errores_tipicos.json").write_text("{}", encoding="utf-8")
    (tmp_path / "taxonomy_uva.json").write_text("{}", encoding="utf-8")

    profile = {
        "actualizado": "2026-09-15T10:00:00",
        "nodos": {
            "a.1": {
                "dominio": 0.8,
                "fluidez": 0.7,
                "intervalo": 30,
                "proxima": "2099-01-01",
                "historial": [],
            }
        },
    }
    bank = {"Asignatura A": {"problemas": [{
        "id": "A-001",
        "titulo": "Problema A",
        "nodos_requeridos": ["a.1"],
    }]}}

    monkeypatch.setattr(study_context, "KG_DIR", str(kg_dir))
    monkeypatch.setattr(study_context, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(study_context.config, "CONCEPTOS_DIR", str(tmp_path / "conceptos"))
    monkeypatch.setattr(study_context.config, "ASIGNATURAS_DIR", str(tmp_path / "asignaturas"))
    monkeypatch.setattr(study_context.config, "INTENTOS_DIR", str(tmp_path / "intentos"))
    monkeypatch.setattr(study_context.config, "ERRORES_DIR", str(tmp_path / "errores"))
    monkeypatch.setattr(study_context.config, "ESTUDIOS_DIR", str(tmp_path / "estudios"))
    monkeypatch.setattr(study_context.config, "INBOX_DIR", str(tmp_path / "inbox"))
    monkeypatch.setattr(study_context.config, "VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setattr(study_context.kg_perfil, "cargar_perfil", lambda: profile)
    monkeypatch.setattr(study_context.kg_problemas, "cargar_banco", lambda: bank)
    monkeypatch.setattr(study_context.study_sessions, "load_state", lambda: {"sessions": []})
    monkeypatch.setattr(study_context.apuntes, "load_state", lambda: {"subjects": {}})
    monkeypatch.setattr(study_context.generar_dashboard, "scan_vault", lambda: {"ejercicios": [], "intentos": [], "errores": [], "conceptos": []})
    monkeypatch.setattr(study_context.kg_perfil, "pendientes_repaso", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(study_context.kg_perfil, "frontera", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(study_context.kg_problemas, "resumen_para_plan", lambda *_args, **_kwargs: {"total_listos": 1, "problemas_listos": [], "por_materia": []})
    monkeypatch.setattr(study_context.kg_planificar, "calcular", lambda **_kwargs: {"hoy": "2026-09-15", "plan": {}, "viabilidad": [], "recomendacion": {}})

    context = study_context.build_context(include_documents=False)

    assert context["scope"]["complete_system"] is True
    assert context["stats"]["asignaturas"] == 1
    assert context["stats"]["nodos_grafo"] == 1
    assert context["stats"]["problemas_banco"] == 1
    assert context["student"]["profile"]["estado_efectivo"]["a.1"]["dominio_efectivo"] == 0.8
    assert context["problem_bank"]["Asignatura A"]["problemas"][0]["id"] == "A-001"


def test_export_context_crea_json_y_markdown(tmp_path, monkeypatch):
    context = {
        "context_schema_version": 1,
        "generated_at": "2026-09-15T10:00:00",
        "stats": {"documentos": 0, "problemas_banco": 1, "nodos_grafo": 1},
        "scope": {"materia": None, "node_ids": None, "complete_system": True},
        "derived": {},
    }
    monkeypatch.setattr(study_context, "CONTEXT_JSON_PATH", str(tmp_path / "contexto_ia.json"))
    monkeypatch.setattr(study_context, "CONTEXT_MD_PATH", str(tmp_path / "contexto_ia.md"))
    monkeypatch.setattr(study_context, "build_context", lambda *args, **kwargs: context)

    result = study_context.export_context()

    assert result["success"] is True
    assert (tmp_path / "contexto_ia.json").exists()
    assert (tmp_path / "contexto_ia.md").exists()
    assert "Contexto vivo" in (tmp_path / "contexto_ia.md").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "contexto_ia.json").read_text(encoding="utf-8"))["stats"]["problemas_banco"] == 1


def test_apply_event_concept_review_solo_acepta_nodos_existentes(monkeypatch):
    calls = []
    monkeypatch.setattr(study_context.kg_perfil, "cargar_grafos", lambda: {"a.1": {"id": "a.1"}})
    monkeypatch.setattr(
        study_context.kg_perfil,
        "registrar_y_guardar",
        lambda *args, **kwargs: calls.append((args, kwargs)) or ["registrado"],
    )

    result = study_context.apply_event({
        "type": "concept_review",
        "node_ids": ["a.1"],
        "success": True,
        "quality": 0.8,
        "origin": "chatgpt",
    })

    assert result["type"] == "concept_review"
    assert calls[0][0][0] == ["a.1"]
    assert calls[0][1]["origen"] == "chatgpt"

    try:
        study_context.apply_event({"type": "concept_review", "node_ids": ["no.existe"]})
    except ValueError as exc:
        assert "Nodos no encontrados" in str(exc)
    else:
        raise AssertionError("Se aceptó un nodo inexistente")
