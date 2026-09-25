import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "knowledge_graph"


def test_billares_proyectivos_esta_fuera_del_sistema():
    assert not (KG / "billares_proyectivos.json").exists()
    assert not (KG / "REVISION_Billares_proyectivos.md").exists()

    taxonomy = json.loads((ROOT / "taxonomy_uva.json").read_text(encoding="utf-8"))
    assert "Billares proyectivos" not in taxonomy

    graph_subjects = []
    for path in KG.glob("*.json"):
        if path.name in {"perfil.json", "banco_problemas.json", "examenes.json", "correcciones.json"}:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "materia" in data and "nodos" in data:
            graph_subjects.append(data["materia"])
    assert "Billares proyectivos" not in graph_subjects

    mapa = (KG / "mapa_conocimiento.html").read_text(encoding="utf-8")
    assert "Billares proyectivos" not in mapa


def test_aplicacion_no_depende_del_archivo_legacy():
    """La carpeta histórica puede faltar sin impedir el arranque de la app."""
    app_code = (ROOT / "app.py").read_text(encoding="utf-8")
    legacy_import = re.compile(r"(?m)^\s*(?:from|import)\s+_archivo(?:\.|\s|$)")
    legacy_path_injection = re.compile(r"(?i)_archivo[\\/].*(?:sys\.path|import)")

    assert not legacy_import.search(app_code)
    assert not legacy_path_injection.search(app_code)
