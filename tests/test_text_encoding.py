from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_TEXT_FILES = (
    ROOT / "knowledge_graph" / "planificar.py",
    ROOT / "generar_informe_auditoria.py",
    ROOT / "informe_auditoria_sistema_estudio.tex",
)
MOJIBAKE_MARKERS = ("Ã", "Â", "�", "Eval?", "â€", "ðŸ")


def test_archivos_activos_se_leen_en_utf8_y_no_contienen_mojibake():
    for path in ACTIVE_TEXT_FILES:
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in MOJIBAKE_MARKERS), path
