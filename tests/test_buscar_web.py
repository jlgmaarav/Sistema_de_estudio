from pathlib import Path

import buscar_web


def test_prepare_search_handoff_uses_local_catalog_and_gemini_web(tmp_path, monkeypatch):
    subjects_dir = tmp_path / "Asignaturas"
    subjects_dir.mkdir()
    (subjects_dir / "ejercicio_001.md").write_text(
        "---\n"
        "id: ejercicio_001\n"
        "asignatura: Mecánica Cuántica\n"
        "tema: Espín\n"
        "estado: nuevo\n"
        "tiene_error: false\n"
        "conceptos:\n"
        "  - momento angular\n"
        "---\n"
        "Problema sobre espines.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(buscar_web.config, "ASIGNATURAS_DIR", str(subjects_dir))
    monkeypatch.setattr(buscar_web.config, "INTENTOS_DIR", str(tmp_path / "Intentos"))
    monkeypatch.setattr(buscar_web.config, "ERRORES_DIR", str(tmp_path / "Errores"))
    monkeypatch.setattr(buscar_web.config, "CONCEPTOS_DIR", str(tmp_path / "Conceptos"))
    handoff_dir = tmp_path / "encargos_gemini"
    monkeypatch.setattr(buscar_web, "HANDOFF_DIR", handoff_dir)
    monkeypatch.setattr(buscar_web, "_copy_to_clipboard", lambda text: True)
    monkeypatch.setattr(buscar_web.webbrowser, "open", lambda url: True)

    result = buscar_web.prepare_search_handoff("errores de espín")

    assert result["model"] == "Gemini 3.8 Flash"
    assert result["copied"] is True
    assert result["opened"] is True
    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    assert "errores de espín" in prompt
    assert "[[ejercicio_001]]" in prompt
    assert "CATÁLOGO LOCAL" in prompt


def test_markdown_to_html_sanitizes_response_and_links_exercises():
    rendered = buscar_web.markdown_to_html(
        "# Resultados\n"
        "- [[ejercicio_001]] es relevante\n"
        "- [[error_001]] relacionado\n"
        "<script>alert('xss')</script>\n"
    )

    assert "viewExercise(this.dataset.exerciseId)" in rendered
    assert "obsidian-badge error" in rendered
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
