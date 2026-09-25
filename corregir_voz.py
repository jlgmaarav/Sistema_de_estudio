# -*- coding: utf-8 -*-
"""Corrige una narración hablada (método Feynman) usando Gemini Web, sin API.

El estudiante resuelve el ejercicio en papel mientras narra en alto su
razonamiento (incluidos los caminos equivocados). Ese audio se transcribe con
`transcribir.py` y aquí se prepara un encargo para Gemini en la web/app (usa tu
suscripción, no la API). Se reutiliza el MISMO esquema `AnalysisResponse`
y el downstream del watcher, así que la corrección por voz crea las mismas fichas
y mueve el knowledge graph igual que una corrección desde el Inbox.

Uso:
    python corregir_voz.py <transcripcion.txt>   # corrige esa transcripción
    python corregir_voz.py <audio.m4a>           # transcribe y luego corrige
    python corregir_voz.py                        # coge lo más nuevo de grabaciones/
    python corregir_voz.py <archivo> --solo-json  # NO toca el grafo; solo análisis

El modelo debe verificarse en el selector de Gemini Web antes de enviar cada
encargo; el Centro de Estudio impide integrar la respuesta si no se marca esa
verificación.
"""
import os
import re
import sys
import json
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import schemas  # noqa: E402  (reutilizamos el mismo esquema del resto del sistema)
import config  # noqa: E402

EXTS_AUDIO = {".m4a", ".mp3", ".wav", ".ogg", ".opus", ".flac", ".aac", ".wma", ".mp4", ".webm"}
GRABACIONES_DIR = os.path.join(BASE, "grabaciones")
GEMINI_HANDOFF_DIR = os.path.join(BASE, "knowledge_graph", "encargos_gemini")
GEMINI_WEB_URL = config.GEMINI_WEB_URL
GEMINI_REQUIRED_MODEL = config.GEMINI_REQUIRED_MODEL


# ---------------------------------------------------------------------------
# Catálogo de nodos y taxonomía (para etiquetar los fallos por nodo del grafo)
# ---------------------------------------------------------------------------
def _catalogo_nodos() -> str:
    """Catálogo compacto `id: nombre` de todos los nodos del knowledge graph."""
    import glob
    kg_dir = os.path.join(BASE, "knowledge_graph")
    NO_GRAFOS = {"perfil.json", "banco_problemas.json", "examenes.json", "correcciones.json"}
    lineas = []
    for ruta in sorted(glob.glob(os.path.join(kg_dir, "*.json"))):
        if os.path.basename(ruta) in NO_GRAFOS:
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                g = json.load(f)
        except Exception:
            continue
        if not isinstance(g, dict) or "nodos" not in g:
            continue
        lineas.append(f"## {g.get('materia', '?')}")
        for n in g.get("nodos", []):
            lineas.append(f"{n['id']}: {n['nombre']}")
    return "\n".join(lineas)


def _taxonomia() -> str:
    ruta = os.path.join(BASE, "taxonomy_uva.json")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# ---------------------------------------------------------------------------
# Construcción del prompt "corrector riguroso" para voz
# ---------------------------------------------------------------------------
def construir_prompt(transcripcion: str) -> str:
    esquema = (
        "{\n"
        '  "asignatura_detectada": str,  // asignatura de la taxonomía UVa\n'
        '  "tema_detectado": str,        // tema concreto de esa asignatura\n'
        '  "titulo_corto": str,          // 4-5 palabras, ej: "Esfera conductora en campo"\n'
        '  "codigo_problema": str|null,  // si el estudiante dijo un código tipo "3.1"\n'
        '  "resumen_correccion": str,    // 2-4 frases al grano: qué está bien y qué mal\n'
        '  "transcripcion_enunciado": str,   // el enunciado, reconstruido de la narración, en LaTeX/Markdown\n'
        '  "dudas_transcripcion": bool,      // true si la transcripción de voz es ambigua/ilegible\n'
        '  "mensaje_duda": str|null,\n'
        '  "transcripcion_manuscrito": str,  // los pasos de la solución que narró, reconstruidos en LaTeX\n'
        '  "conceptos_dominio": [{"concepto": str, "dominio": float}],  // 0.0-1.0 por concepto\n'
        '  "nodos_detectados": [str],    // 1-5 ids EXACTOS del catálogo de nodos (ej: "em.1.07")\n'
        '  "nodos_hueco_teorico": [str], // ids donde la explicación o justificación queda incompleta\n'
        '  "nodos_error": [str],         // ids directamente afectados por un error de resolución\n'
        '  "resultado": str,             // "correcto" | "incorrecto" | "incompleto"\n'
        '  "tiene_error": bool,\n'
        '  "confianza_analisis": float,  // 0.0-1.0\n'
        '  "motivo_baja_confianza": str|null,\n'
        '  "analisis_detallado": str,    // análisis paso a paso en Markdown\n'
        '  "errores": [{\n'
        '      "titulo": str,\n'
        '      "tipo_error": [str],      // algebraico|conceptual|calculo|interpretacion_fisica|planteamiento|unidades_dimensiones|otros\n'
        '      "descripcion": str, "razon": str, "como_evitarlo": str,\n'
        '      "ejemplo_incorrecto": str, "ejemplo_correcto": str  // en LaTeX\n'
        "  }],\n"
        '  "checkpoints": [{\n'
        '      "descripcion": str,       // qué sub-paso es, ej: "1ª integración por partes"\n'
        '      "resultado_dicho": str,   // el resultado parcial que narró, en LaTeX\n'
        '      "correcto": bool,         // verificado de forma independiente (recalculado por ti)\n'
        '      "nota": str|null          // si es incorrecto, qué falla EN ESE checkpoint concreto\n'
        "  }]\n"
        "}"
    )

    return (
        "Eres un catedrático y examinador de Física de máxima exigencia en la Universidad de Valladolid (UVa).\n"
        "OBJETIVO DEL ESTUDIANTE: SACAR MATRÍCULA DE HONOR (10.0) EN TODAS LAS ASIGNATURAS DE 4º DE FÍSICA.\n"
        "Por tanto, tu corrección debe ser RIGOROSÍSIMA E IMPLACABLE. Cero complacencia: calificar con benevolencia o tolerar justificaciones a medias perjudica directamente su objetivo de alcanzar el 10.\n"
        f"MODELO OBLIGATORIO: {GEMINI_REQUIRED_MODEL}. Antes de analizar, verifica en el selector de Gemini Web que aparece exactamente ese modelo. Si no aparece, no analices ni devuelvas JSON.\n\n"
        "El estudiante ha resuelto un ejercicio en papel MIENTRAS NARRABA EN ALTO su razonamiento "
        "(método Feynman). Lo que recibes es la TRANSCRIPCIÓN AUTOMÁTICA de esa narración: puede tener "
        "ruido de transcripción, muletillas y autocorrecciones (ej. 'espérate, no es 3x sino 5x'). "
        "Interpreta el RAZONAMIENTO, no las palabras literales.\n\n"

        "Tu trabajo es evaluar con el estándar de un 10.0 en un tribunal de examen:\n"
        "1. Reconstruye el ENUNCIADO del problema a partir de la narración (`transcripcion_enunciado`).\n"
        "2. Reconstruye los PASOS de su solución en LaTeX (`transcripcion_manuscrito`).\n"
        "3. EXIGENCIA DE 10 EN JUSTIFICACIÓN: Marca CADA salto lógico no justificado. Si dice 'aquí uso Gauss' sin argumentar la simetría, si aplica una condición de contorno sin justificarla físicamente, o si desprecia un término sin verificar la hipótesis de validez (ej. baja inyección, régimen no relativista, aproximación dipolar, canal largo), es un HUECO GRAVE: recógelo como error.\n"
        "4. RIGOR EN SIGNOS Y UNIDADES: En 4º de Física un error de signos en un potencial o tensor, o una incongruencia dimensional destruye una Matrícula de Honor. No lo trates como 'mero despiste', clasifícalo y señálalo con severidad en `tipo_error`.\n"
        "5. Distingue con total precisión ERROR CONCEPTUAL vs ERROR MATEMÁTICO/algebraico/cálculo en `tipo_error`.\n"
        "6. Sigue los CAMINOS EQUIVOCADOS: si fue por un derrotero erróneo y luego rectificó, identifica la justificación defectuosa que le indujo al error — ahí radica la laguna que le impediría sacar el 10.\n"
        "7. PUNTOS DE BAJA CONFIANZA: donde el razonamiento sea titubeante, vago o circular, señálalo en `analisis_detallado`; si refleja duda en la base teórica, regístralo como `error`.\n"
        "8. En `errores`, para cada uno: por qué ocurrió (`razon`), cómo evitarlo (`como_evitarlo`) y el paso incorrecto y el corregido en LaTeX.\n"
        "9. CHECKPOINTS: el estudiante narra RESULTADOS PARCIALES de sub-pasos (ej. el resultado de cada integración, cada término de simetría, cada límite). Recalcúlalo tú de forma INDEPENDIENTE y sé riguroso: si un sub-paso no es exacto, `correcto: false` y explícalo en `nota`.\n"
        "10. `nodos_detectados`: elige de 1 a 5 ids EXACTOS del catálogo de abajo, los que este ejercicio ejercita de verdad. Prioriza la asignatura detectada.\n"
        "11. RETROALIMENTACIÓN POR NODO: en `nodos_hueco_teorico` pon solo ids donde falte una explicación, justificación o condición física aunque el cálculo global salga; en `nodos_error` pon solo ids donde el procedimiento esté mal. Usa ids del catálogo exactos y deja ambas listas vacías si no hay un diagnóstico fiable.\n"
        "12. Calificación honesta: para que `resultado` sea 'correcto', la resolución debe ser impecable (digna de un 10). Si hay lagunas conceptuales o justificaciones a medias, califícalo como 'incompleto' o 'incorrecto'.\n\n"

        "IMPORTANTE sobre el formato de salida:\n"
        "- Devuelve EXCLUSIVAMENTE un objeto JSON válido con esta forma (sin ``` ni texto alrededor):\n"
        f"{esquema}\n\n"

        "Taxonomía oficial de asignaturas y temas (UVa):\n"
        f"{_taxonomia()}\n\n"

        "Catálogo de nodos del knowledge graph (usa estos ids exactos en `nodos_detectados`):\n"
        f"{_catalogo_nodos()}\n\n"

        "TRANSCRIPCIÓN DE LA NARRACIÓN DEL ESTUDIANTE:\n"
        "\"\"\"\n"
        f"{transcripcion.strip()}\n"
        "\"\"\"\n"
    )


# ---------------------------------------------------------------------------
# Handoff a Gemini Web — usa la suscripción, no la API
# ---------------------------------------------------------------------------
def _copiar_portapapeles(texto: str) -> bool:
    """Deja el encargo completo listo para pegarlo en Gemini.

    `clip.exe` forma parte de Windows y no envía nada a Internet; únicamente
    escribe el portapapeles local. Si no está disponible, el archivo .md sigue
    siendo la alternativa manual.
    """
    try:
        subprocess.run(
            ["clip.exe"], input=texto, text=True, check=True,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def preparar_encargo_gemini(transcripcion: str, ruta_txt: str) -> tuple[str, str]:
    """Prepara un encargo para Gemini Web sin usar ninguna API.

    La respuesta de Gemini no puede escribir directamente en el disco desde la
    web. Por eso el prompt se copia al portapapeles, se abre Gemini y el centro
    de estudio ofrece un cuadro para pegar de vuelta la respuesta JSON.
    """
    os.makedirs(GEMINI_HANDOFF_DIR, exist_ok=True)
    stem = os.path.splitext(os.path.basename(ruta_txt))[0]
    resultado = os.path.join(GEMINI_HANDOFF_DIR, f"{stem}_resultado.json")
    encargo = os.path.join(GEMINI_HANDOFF_DIR, f"{stem}_encargo.md")
    prompt = construir_prompt(transcripcion)
    with open(encargo, "w", encoding="utf-8") as f:
        f.write(prompt)

    copiado = _copiar_portapapeles(prompt)
    try:
        import webbrowser
        webbrowser.open(GEMINI_WEB_URL)
    except Exception:
        pass

    estado = (f"Prompt copiado al portapapeles. Comprueba que el selector muestra {GEMINI_REQUIRED_MODEL}."
              if copiado else f"Abre el encargo guardado en disco y verifica {GEMINI_REQUIRED_MODEL}.")
    print(f"GEMINI_HANDOFF:{encargo}|{resultado}|{estado}")
    return encargo, resultado


def importar_resultado_gemini(ruta_resultado: str, ruta_txt: str, solo_json: bool = False,
                              modelo: str | None = None) -> schemas.AnalysisResponse:
    """Valida e integra una respuesta de Gemini Web con el modelo confirmado."""
    modelo_utilizado = (modelo or GEMINI_REQUIRED_MODEL).strip()
    if modelo_utilizado != GEMINI_REQUIRED_MODEL:
        raise ValueError(
            f"Modelo no admitido: se esperaba {GEMINI_REQUIRED_MODEL!r}, "
            f"pero se recibió {modelo_utilizado!r}."
        )
    with open(ruta_resultado, "r", encoding="utf-8") as f:
        resp = schemas.AnalysisResponse.model_validate_json(_extraer_json(f.read()))
    md = guardar_markdown(resp, ruta_txt)
    if not solo_json:
        integrar_en_grafo(resp, ruta_txt, modelo_ia=modelo_utilizado)
    print(f"[OK] Corrección de Gemini guardada en: {md}")
    return resp


def _extraer_json(texto: str) -> str:
    """Quita vallas ```json y quédate con el objeto {...} más externo."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    ini, fin = t.find("{"), t.rfind("}")
    if ini != -1 and fin != -1 and fin > ini:
        return t[ini:fin + 1]
    return t


# ---------------------------------------------------------------------------
# Guardado del feedback legible + integración con el grafo
# ---------------------------------------------------------------------------
def guardar_markdown(resp: schemas.AnalysisResponse, ruta_txt: str) -> str:
    salida = os.path.splitext(ruta_txt)[0] + "_correccion.md"
    L = []
    L.append(f"# {resp.titulo_corto}")
    L.append(f"*{resp.asignatura_detectada} — {resp.tema_detectado}*  ·  "
             f"**{resp.resultado.upper()}**  ·  confianza {resp.confianza_analisis:.0%}")
    if resp.nodos_detectados:
        L.append(f"\n**Nodos:** {', '.join(resp.nodos_detectados)}")
    if resp.nodos_hueco_teorico:
        L.append(f"\n**Huecos teóricos:** {', '.join(resp.nodos_hueco_teorico)}")
    if resp.nodos_error:
        L.append(f"\n**Nodos afectados por errores:** {', '.join(resp.nodos_error)}")
    if resp.resumen_correccion:
        L.append(f"\n> {resp.resumen_correccion}")
    L.append("\n## Análisis\n")
    L.append(resp.analisis_detallado or "")
    if resp.checkpoints:
        L.append("\n## Checkpoints\n")
        for i, cp in enumerate(resp.checkpoints, 1):
            marca = "✅" if cp.correcto else "❌"
            L.append(f"{i}. {marca} **{cp.descripcion}** → `{cp.resultado_dicho}`")
            if not cp.correcto and cp.nota:
                L.append(f"   - {cp.nota}")
    if resp.errores:
        L.append("\n## Errores detectados\n")
        for i, e in enumerate(resp.errores, 1):
            tipos = ", ".join(e.tipo_error) if e.tipo_error else "—"
            L.append(f"### {i}. {e.titulo}  _({tipos})_")
            L.append(f"- **Qué pasó:** {e.descripcion}")
            L.append(f"- **Por qué:** {e.razon}")
            L.append(f"- **Cómo evitarlo:** {e.como_evitarlo}")
            L.append(f"- **Incorrecto:** {e.ejemplo_incorrecto}")
            L.append(f"- **Correcto:** {e.ejemplo_correcto}\n")
    if resp.conceptos_dominio:
        L.append("\n## Dominio por concepto\n")
        for c in resp.conceptos_dominio:
            L.append(f"- {c.concepto}: {c.dominio:.0%}")
    with open(salida, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return salida


def integrar_en_grafo(resp: schemas.AnalysisResponse, ruta_txt: str,
                      modelo_ia: str | None = None):
    """Reutiliza el downstream del watcher: fichas Obsidian + actualización del grafo/XP + app."""
    import config
    config.init_vault_structure()
    import watcher

    kg_dir = os.path.join(BASE, "knowledge_graph")
    if kg_dir not in sys.path:
        sys.path.insert(0, kg_dir)
    try:
        import perfil as kg_perfil
    except Exception:
        kg_perfil = None

    watcher._procesar_una_solucion(
        resp, ruta_txt, None, kg_perfil,
        sol_assets=[], enunciado_asset="",
        contexto="Narración de voz (método Feynman)", intento_mental="",
        modelo_ia=modelo_ia or GEMINI_REQUIRED_MODEL, es_fallback=False,
    )


# ---------------------------------------------------------------------------
def _resolver_entrada(args) -> str | None:
    rutas = [a for a in args if not a.startswith("--")]
    if rutas:
        ruta = os.path.abspath(rutas[0])
        return ruta if os.path.isfile(ruta) else None
    # sin argumento: lo más nuevo de grabaciones/
    if not os.path.isdir(GRABACIONES_DIR):
        return None
    cands = [os.path.join(GRABACIONES_DIR, f) for f in os.listdir(GRABACIONES_DIR)
             if os.path.splitext(f)[1].lower() in (EXTS_AUDIO | {".txt"})]
    return max(cands, key=os.path.getmtime) if cands else None


def main():
    solo_json = "--solo-json" in sys.argv
    if "--importar-gemini" in sys.argv:
        pos = sys.argv.index("--importar-gemini")
        try:
            modelo = GEMINI_REQUIRED_MODEL
            if "--modelo" in sys.argv:
                modelo_pos = sys.argv.index("--modelo")
                if modelo_pos + 1 >= len(sys.argv):
                    raise ValueError("Falta el nombre del modelo después de --modelo.")
                modelo = sys.argv[modelo_pos + 1]
            importar_resultado_gemini(
                sys.argv[pos + 1], sys.argv[pos + 2], solo_json, modelo=modelo
            )
        except Exception as e:
            print(f"[ERROR] No se pudo importar la corrección de Gemini: {e}")
            sys.exit(1)
        return
    ruta = _resolver_entrada(sys.argv[1:])
    if not ruta:
        print("[ERROR] No encuentro entrada. Pasa una transcripción .txt o un audio, "
              "o deja algo en grabaciones/.")
        sys.exit(1)

    ext = os.path.splitext(ruta)[1].lower()
    if ext in EXTS_AUDIO:
        print(f"Es un audio; lo transcribo primero: {os.path.basename(ruta)}")
        import transcribir
        texto = transcribir.transcribir(ruta)
        ruta_txt = os.path.splitext(ruta)[0] + ".txt"
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(texto)
    else:
        ruta_txt = ruta
        with open(ruta_txt, "r", encoding="utf-8") as f:
            texto = f.read()

    if not texto.strip():
        print("[ERROR] La transcripción está vacía.")
        sys.exit(1)

    encargo, resultado = preparar_encargo_gemini(texto, ruta_txt)
    print("[LISTO] Gemini se ha abierto. El prompt completo está en el portapapeles.")
    print(f"        Comprueba que el modelo sea exactamente {GEMINI_REQUIRED_MODEL}.")
    print("        Pégalo en Gemini, copia su respuesta JSON y devuélvela al Centro de Estudio.")
    print(f"        Encargo guardado en: {encargo}")


if __name__ == "__main__":
    main()
