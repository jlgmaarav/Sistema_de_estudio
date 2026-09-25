import apuntes
import study_sessions


def test_apuntes_se_construyen_por_nodo_y_no_por_temas(tmp_path, monkeypatch):
    monkeypatch.setattr(apuntes, "STATE_PATH", str(tmp_path / "apuntes.json"))
    monkeypatch.setattr(apuntes, "OUTPUT_DIR", str(tmp_path / "salida"))

    nodes = {
        "a.1": {
            "id": "a.1", "materia": "Asignatura A", "nombre": "Nodo inicial",
            "descripcion": "Una explicación base.", "prerequisitos": [],
        },
        "a.2": {
            "id": "a.2", "materia": "Asignatura A", "nombre": "Nodo siguiente",
            "descripcion": "Todavía no estudiado.",
            "prerequisitos": [{"id": "a.1", "peso": 1.0}],
        },
    }
    session = {"id": "walk1", "plan_ids": ["a.1", "a.2"]}
    report = {
        "resumen": "La conexión quedó clara.",
        "nodos": [{
            "id": "a.1", "resultado": "solido", "calidad": 0.95,
            "dominado": ["La idea causal"], "dudas": [],
        }],
        "errores_recurrentes": [],
        "apuntes": [{
            "node_id": "a.1",
            "explicacion_validada": ["La explicación propia del nodo."],
            "explicacion_para_mi": ["Primero pienso en la causa y luego en la fórmula."],
            "procedimiento_examen": ["Escribir hipótesis antes de calcular."],
        }],
    }

    result = apuntes.apply_walk_report(session, report, nodes)
    assert result["subjects"] == ["Asignatura A"]
    state = apuntes.load_state()
    subject = state["subjects"]["Asignatura A"]
    assert set(subject["nodes"]) == {"a-1"}

    generated = apuntes.generate("Asignatura A", nodes)
    tex = (tmp_path / "salida" / "asignatura-a" / "main.tex").read_text(encoding="utf-8")
    assert generated["files"]
    assert "Nodo inicial" in tex
    assert "Nodo siguiente" not in tex
    assert "La explicación propia del nodo." in tex
    assert "Tema 1" not in tex


def test_normalize_walk_report_limita_apuntes_a_nodos_del_plan():
    normalized = study_sessions.normalize_walk_report({
        "nodos": [],
        "apuntes": [
            {"node_id": "ok", "explicacion_validada": ["válida"]},
            {"node_id": "fuera", "explicacion_validada": ["no debe entrar"]},
        ],
    }, ["ok"])
    assert len(normalized["apuntes"]) == 1
    assert normalized["apuntes"][0]["node_id"] == "ok"


def test_apuntes_de_estudio_prima_la_teoria_y_separa_el_registro_personal():
    subject = {
        "materia": "Electromagnetismo",
        "nodes": {
            "em-0-05": {
                "id": "em.0.05",
                "title": "Integrales de línea, superficie y volumen",
                "description": "Flujo de un campo vectorial.",
                "recurrent_errors": [
                    "Confundir el elemento escalar de superficie con el elemento vectorial orientado."
                ],
                "difficulties": ["Mantener la orientación de la superficie."],
                "strengths": [],
                "personal_explanations": [],
                "explanations": [],
                "procedures": [],
                "examples": [],
            }
        },
        "recurrent_errors": [
            "Confundir el elemento escalar de superficie con el elemento vectorial orientado."
        ],
    }
    graph_node = {
        "id": "em.0.05",
        "nombre": "Integrales de línea, superficie y volumen",
        "descripcion": "Flujo de un campo vectorial.",
        "fuentes": {"griffiths": "1.3.1"},
    }

    tex = apuntes.render_subject(subject, [graph_node])

    assert "Desarrollo conceptual" in tex
    assert "Anotaciones personales nacidas de la práctica" in tex
    assert "Registro de errores personales" in tex
    assert "Checklist de reconstrucción y examen" not in tex
    assert "Estado actual:" not in tex


def test_apuntes_captura_teoria_y_aclaraciones_personalizadas(tmp_path, monkeypatch):
    monkeypatch.setattr(apuntes, "STATE_PATH", str(tmp_path / "apuntes.json"))
    monkeypatch.setattr(apuntes, "OUTPUT_DIR", str(tmp_path / "salida"))

    nodes = {
        "mc.1.08": {
            "id": "mc.1.08",
            "materia": "Mecánica Cuántica",
            "nombre": "Operador paridad",
            "descripcion": "Simetría de inversión espacial y conservación de la paridad.",
            "prerequisitos": [],
        }
    }
    session = {"id": "session_mc", "plan_ids": ["mc.1.08"]}
    report = {
        "nodos": [{
            "id": "mc.1.08", "resultado": "solido", "calidad": 0.9,
            "dominado": ["Autovalores y relaciones de conmutación"],
            "dudas": [],
        }],
        "resumen": "Sesión de paridad con desarrollo matemático riguroso.",
        "apuntes": [{
            "node_id": "mc.1.08",
            "teoria": (
                "### 1. Concepto y principios físicos\n"
                "El operador paridad $\\hat{\\Pi}$ describe la inversión del espacio.\n"
                "- **Transformación:** En 1D cambia $x \\to -x$.\n\n"
                "### 2. Estructura matemática\n"
                "$$\\hat{\\Pi}^2 = \\mathbb{I}$$\n"
                "Por tanto, sus autovalores son $\\pm 1$."
            ),
            "aclaraciones": [
                {
                    "duda": "¿Por qué en 3D la paridad no equivale a una rotación de 180 grados?",
                    "aclaracion": "Porque en 3D el determinante es -1 (inversión impropia) mientras que en SO(3) cualquier rotación tiene determinante +1."
                }
            ],
            "procedimiento_examen": [
                "Para comprobar paridad de un estado, aplicar $\\hat{\\Pi}$ y comprobar si devuelve $\\pm |\\psi\\rangle$."
            ],
            "ejemplos": [
                "Comprobación en el oscilador armónico 1D con funciones de Hermite."
            ],
        }],
    }

    result = apuntes.apply_walk_report(session, report, nodes)
    assert result["subjects"] == ["Mecánica Cuántica"]

    generated = apuntes.generate("Mecánica Cuántica", nodes)
    tex_path = tmp_path / "salida" / "mecanica-cuantica" / "main.tex"
    assert tex_path.exists()
    tex = tex_path.read_text(encoding="utf-8")

    # Verifica encabezado dinámico de materia
    assert r"\lhead{\small\textit{Mecánica Cuántica}}" in tex
    # Verifica sección de fundamentos teóricos con matemáticas
    assert "Fundamentos teóricos y estructura matemática" in tex
    assert r"\[\hat{\Pi}^2 = \mathbb{I}\]" in tex
    # Verifica sección de aclaraciones personalizadas del estudiante
    assert "Aclaraciones y preguntas clave resueltas" in tex
    assert "rotación de 180 grados" in tex
    assert "inversión impropia" in tex
    assert "qaline" in tex and "qabg" in tex
    # Verifica procedimientos y ejemplos
    assert "Caja de herramientas y procedimiento operativo" in tex
    assert "oscilador armónico" in tex

    # Verifica compilación automática a PDF con pdflatex
    pdf_path = tmp_path / "salida" / "mecanica-cuantica" / "main.pdf"
    assert pdf_path.exists()
    assert str(pdf_path) in generated["pdf_files"]
