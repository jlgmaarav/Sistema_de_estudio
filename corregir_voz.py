# -*- coding: utf-8 -*-
"""Corrige una narración hablada (método Feynman) con Claude Code, sin API de pago.

El estudiante resuelve el ejercicio en papel/reMarkable mientras narra en alto su
razonamiento (incluidos los caminos equivocados). Ese audio se transcribe con
`transcribir.py` y aquí se corrige llamando a `claude -p` (usa tu suscripción de
Claude Code, no la API de Gemini). Se reutiliza el MISMO esquema `AnalysisResponse`
y el downstream del watcher, así que la corrección por voz crea las mismas fichas
y mueve el knowledge graph igual que una hoja del reMarkable.

Uso:
    python corregir_voz.py <transcripcion.txt>   # corrige esa transcripción
    python corregir_voz.py <audio.m4a>           # transcribe y luego corrige
    python corregir_voz.py                        # coge lo más nuevo de grabaciones/
    python corregir_voz.py <archivo> --solo-json  # NO toca el grafo; solo análisis

El modelo se puede cambiar con la variable CLAUDE_MODEL (por defecto, el de tu
sesión de Claude Code).
"""
import os
import re
import sys
import json
import shutil
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import schemas  # noqa: E402  (reutilizamos el mismo esquema del resto del sistema)

EXTS_AUDIO = {".m4a", ".mp3", ".wav", ".ogg", ".opus", ".flac", ".aac", ".wma", ".mp4", ".webm"}
GRABACIONES_DIR = os.path.join(BASE, "grabaciones")
# Opus 4.8 por defecto (máxima exigencia). Si se agota el límite del plan, se
# reintenta automáticamente con el modelo de respaldo (sonnet).
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
CLAUDE_MODEL_FALLBACK = os.getenv("CLAUDE_MODEL_FALLBACK", "claude-sonnet-5")


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
        "  }]\n"
        "}"
    )

    return (
        "Eres un profesor de Física exigente y riguroso que corrige a un estudiante del Grado en Física.\n"
        "El estudiante ha resuelto un ejercicio en papel MIENTRAS NARRABA EN ALTO su razonamiento "
        "(método Feynman). Lo que recibes es la TRANSCRIPCIÓN AUTOMÁTICA de esa narración: puede tener "
        "ruido de transcripción, muletillas y autocorrecciones (ej. 'espérate, no es 3x sino 5x'). "
        "Interpreta el RAZONAMIENTO, no las palabras literales.\n\n"

        "Tu trabajo es corregir con rigor de profesor, no ser amable de más:\n"
        "1. Reconstruye el ENUNCIADO del problema a partir de la narración (`transcripcion_enunciado`).\n"
        "2. Reconstruye los PASOS de su solución en LaTeX (`transcripcion_manuscrito`).\n"
        "3. Marca CADA salto lógico no justificado y cada concepto usado sin justificar. Si dice "
        "'aquí uso Gauss' sin argumentar la simetría, eso es un hueco: recógelo.\n"
        "4. Distingue con claridad ERROR CONCEPTUAL vs ERROR MATEMÁTICO/algebraico/cálculo en `tipo_error`.\n"
        "5. Sigue también los CAMINOS EQUIVOCADOS: si fue por un derrotero que estaba mal y luego rectificó, "
        "identifica la justificación errónea que le llevó ahí — ahí suele estar el hueco conceptual real.\n"
        "6. PUNTOS DE BAJA CONFIANZA: donde el razonamiento sea vago, circular o dé marcha atrás, señálalo "
        "en `analisis_detallado`; y si refleja un hueco real de comprensión, conviértelo en un `error`.\n"
        "7. En `errores`, para cada uno: por qué ocurrió (`razon`), cómo evitarlo (`como_evitarlo`) y el paso "
        "incorrecto y el corregido en LaTeX.\n"
        "8. `nodos_detectados`: elige de 1 a 5 ids EXACTOS del catálogo de abajo, los que este ejercicio "
        "ejercita de verdad. Prioriza la asignatura detectada.\n"
        "9. Todo en español. Sé honesto en `resultado` y `tiene_error`.\n\n"

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
# Llamada a Claude Code (claude -p) — usa la suscripción, no la API
# ---------------------------------------------------------------------------
def llamar_claude(prompt: str, model: str, timeout: int = 900) -> str:
    exe = shutil.which("claude") or "claude"
    cmd = [exe, "-p", "--output-format", "json", "--model", model]
    print(f"Llamando a Claude ({model})... (puede tardar ~1-2 min)")
    proc = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=BASE, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude falló (código {proc.returncode}): {proc.stderr[:800]}")
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"No se pudo leer la respuesta de claude: {proc.stdout[:800]}")
    if envelope.get("is_error"):
        raise RuntimeError(f"claude devolvió error: {envelope.get('result')}")
    return envelope.get("result", "")


def _extraer_json(texto: str) -> str:
    """Quita vallas ```json y quédate con el objeto {...} más externo."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    ini, fin = t.find("{"), t.rfind("}")
    if ini != -1 and fin != -1 and fin > ini:
        return t[ini:fin + 1]
    return t


def corregir_texto(transcripcion: str) -> schemas.AnalysisResponse:
    prompt = construir_prompt(transcripcion)
    modelos = [CLAUDE_MODEL]
    if CLAUDE_MODEL_FALLBACK and CLAUDE_MODEL_FALLBACK != CLAUDE_MODEL:
        modelos.append(CLAUDE_MODEL_FALLBACK)
    ultimo_error = None
    for i, m in enumerate(modelos):
        try:
            crudo = llamar_claude(prompt, m)
            data = _extraer_json(crudo)
            return schemas.AnalysisResponse.model_validate_json(data)
        except Exception as e:
            ultimo_error = e
            if i + 1 < len(modelos):
                print(f"  -> Falló con {m} ({e}). Puede ser el límite del plan; "
                      f"reintento con el modelo de respaldo {modelos[i + 1]}...")
            else:
                print(f"  -> Falló también con {m}.")
    raise ultimo_error


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
    if resp.resumen_correccion:
        L.append(f"\n> {resp.resumen_correccion}")
    L.append("\n## Análisis\n")
    L.append(resp.analisis_detallado or "")
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


def integrar_en_grafo(resp: schemas.AnalysisResponse, ruta_txt: str):
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
        modelo_ia="claude-voz", es_fallback=False,
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

    print(f"Corrigiendo la narración ({len(texto.split())} palabras)...")
    resp = corregir_texto(texto)

    md = guardar_markdown(resp, ruta_txt)
    print(f"\n[OK] Corrección guardada en: {md}")
    print(f"     Resultado: {resp.resultado} · errores: {len(resp.errores)} · "
          f"nodos: {', '.join(resp.nodos_detectados) or '—'}")

    if solo_json:
        print("     (--solo-json) No se ha tocado el grafo.")
    else:
        try:
            integrar_en_grafo(resp, ruta_txt)
            print("     Grafo, fichas y corrección de la app actualizados.")
        except Exception as e:
            print(f"     [aviso] No se pudo integrar en el grafo: {e}")
            print("     El análisis en Markdown sí está guardado.")


if __name__ == "__main__":
    main()
