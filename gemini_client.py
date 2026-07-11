import os
import io
import glob
import json
import fitz  # PyMuPDF
from typing import Optional
from PIL import Image
from google import genai
from google.genai import types

import config
import schemas

def _generar_con_fallback(client, contents, response_schema):
    """Genera contenido estructurado probando el modelo principal y, si falla
    (cuota/429/503/error de red), reintentando con el modelo de respaldo.
    Devuelve una tupla (texto_json, modelo_usado, es_fallback), o (None, None, False)."""
    modelos = [config.GEMINI_MODEL]
    if config.GEMINI_MODEL_FALLBACK and config.GEMINI_MODEL_FALLBACK != config.GEMINI_MODEL:
        modelos.append(config.GEMINI_MODEL_FALLBACK)
    ultimo_error = None
    for i, modelo in enumerate(modelos):
        etiqueta = "principal" if i == 0 else "respaldo"
        try:
            print(f"Enviando petición a Gemini ({modelo}, modelo {etiqueta})...")
            response = client.models.generate_content(
                model=modelo,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=config.TEMPERATURE,
                ),
            )
            if i > 0:
                print(f"  -> ¡OJO! Respondió el modelo de RESPALDO ({modelo}), menos fiable. Revisa esta corrección.")
            return response.text, modelo, (i > 0)
        except Exception as e:
            ultimo_error = e
            if i + 1 < len(modelos):
                print(f"  -> Falló el modelo {etiqueta} ({modelo}): {e}. Reintentando con el de respaldo...")
            else:
                print(f"  -> Falló también el modelo de respaldo ({modelo}): {e}")
    if ultimo_error:
        raise ultimo_error
    return None, None, False


def build_node_catalog() -> str:
    """Catálogo compacto (id: nombre) de todos los nodos del knowledge graph."""
    kg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_graph")
    # Archivos de datos que NO son grafos (perfil, banco, exámenes, correcciones);
    # algunos son listas de nivel superior, así que hay que excluirlos.
    NO_GRAFOS = {"perfil.json", "banco_problemas.json", "examenes.json", "correcciones.json"}
    lineas = []
    for ruta in sorted(glob.glob(os.path.join(kg_dir, "*.json"))):
        if os.path.basename(ruta) in NO_GRAFOS:
            continue
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                g = json.load(f)
        except Exception:
            continue
        # Solo grafos válidos (dict con 'nodos'); ignora cualquier otro JSON.
        if not isinstance(g, dict) or "nodos" not in g:
            continue
        lineas.append(f"## {g.get('materia', '?')}")
        for n in g.get("nodos", []):
            lineas.append(f"{n['id']}: {n['nombre']}")
    return "\n".join(lineas)

def process_and_optimize_file(path: str, role_name: str):
    """
    Carga y optimiza un archivo local para minimizar el payload de la API.
    """
    if not os.path.exists(path):
        print(f"Tratando argumento {role_name} como texto directo (no se encontró archivo físico).")
        return path
        
    ext = os.path.splitext(path)[1].lower()
    
    if ext == '.pdf':
        print(f"Procesando PDF para {role_name} ({path}) en memoria...")
        doc = fitz.open(path)
        pages_parts = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("jpeg")
            img = Image.open(io.BytesIO(img_data))
            
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
                
            # Redimensionar a max_width de 1200px para ahorrar ancho de banda
            max_width = 1200
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Guardar a JPEG comprimido
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=60)
            compressed_bytes = buf.getvalue()
            img.close()
            part = types.Part.from_bytes(data=compressed_bytes, mime_type="image/jpeg")
            pages_parts.append(part)
            print(f"  -> Página {i+1} cargada y optimizada en memoria ({len(compressed_bytes)/1024:.2f} KB)")
        return pages_parts
        
    elif ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']:
        print(f"Cargando e ingresando imagen para {role_name} ({path}) optimizada...")
        img = Image.open(path)
        
        # Convertir a RGB si la imagen tiene transparencia (RGBA/LA) o paleta (P)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
            
        # Redimensionar a max_width de 1200px
        max_width = 1200
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        compressed_bytes = buf.getvalue()
        img.close()
        
        print(f"  -> Imagen {role_name} optimizada en memoria ({len(compressed_bytes)/1024:.2f} KB)")
        return types.Part.from_bytes(data=compressed_bytes, mime_type="image/jpeg")
        
    elif ext in ['.txt', '.md']:
        print(f"Cargando archivo de texto para {role_name} ({path})...")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"Extensión '{ext}' no reconocida. Tratando como archivo de texto para {role_name} ({path})...")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return path

def _cargar_contents_ejercicio(exercise_path, solution_path, official_path):
    """Carga (y optimiza) los archivos de entrada del análisis en una lista de
    `contents` para Gemini. En el flujo reMarkable enunciado y solución son el
    MISMO archivo: no se manda dos veces (más rápido y gasta menos cuota)."""
    contents = []
    ex_item = process_and_optimize_file(exercise_path, "enunciado")
    contents.extend(ex_item) if isinstance(ex_item, list) else contents.append(ex_item)

    mismo_archivo = (os.path.abspath(solution_path) == os.path.abspath(exercise_path)) \
        if (os.path.exists(solution_path) and os.path.exists(exercise_path)) else (solution_path == exercise_path)
    if not mismo_archivo:
        sol_item = process_and_optimize_file(solution_path, "solución")
        contents.extend(sol_item) if isinstance(sol_item, list) else contents.append(sol_item)

    if official_path:
        off_item = process_and_optimize_file(official_path, "solución oficial")
        contents.extend(off_item) if isinstance(off_item, list) else contents.append(off_item)
    return contents


def _build_analysis_prompt(contexto=None, intento_mental=None, hint_subject=None, multi=False):
    """Construye el prompt pedagógico. Si `multi`, pide una entrada por cada
    problema resuelto en la hoja (formato hoja.problema)."""
    taxonomy_str = ""
    taxonomy_path = "taxonomy_uva.json"
    if os.path.exists(taxonomy_path):
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            taxonomy_str = f.read()

    if multi:
        intro = (
            "Eres un profesor de Física experto y un asistente de aprendizaje personalizado. "
            "Se te da una HOJA DE PROBLEMAS en la que el estudiante ha resuelto a mano UNO O VARIOS problemas. "
            "Cada problema resuelto lleva escrito a mano un CÓDIGO al principio con el formato hoja.problema "
            "(ej: '3.1' = Hoja 3, Problema 1; a veces 'H3.1' o '3-1'). "
            "Tu tarea es localizar TODOS los problemas que el estudiante ha resuelto a mano y devolver en `soluciones` "
            "UNA entrada de análisis completa POR CADA UNO de ellos. NO analices problemas del enunciado que el "
            "estudiante no haya resuelto. Para cada solución rellena todos los campos como se indica abajo.\n\n"
        )
        caso_hoja = (
            "   - CÓDIGO DEL PROBLEMA (MUY IMPORTANTE): busca el código manuscrito al principio de CADA solución, "
            "normalízalo a 'hoja.problema' (ej: '3.1') y devuélvelo en `codigo_problema`. En `transcripcion_enunciado` "
            "pon SOLO el enunciado del problema resuelto en esa entrada. Si el enunciado impreso no está visible, "
            "reconstrúyelo a partir de la solución lo mejor posible e indícalo. El título y los nodos se refieren solo a ESE problema.\n"
        )
    else:
        intro = (
            "Eres un profesor de Física experto y un asistente de aprendizaje personalizado. "
            "Tu tarea es analizar el intento de resolución de un ejercicio por parte de un estudiante y compararlo "
            "con el enunciado y, si se proporciona, con la solución oficial.\n\n"
        )
        caso_hoja = (
            "   - CASO HOJA DE PROBLEMAS (MUY IMPORTANTE): el estudiante resuelve UN problema escribiendo su solución a mano. "
            "Para decirte cuál es, escribe a mano un CÓDIGO al principio de su solución con el formato hoja.problema "
            "(ej: '3.1' = Hoja 3, Problema 1; a veces 'H3.1' o '3-1'). Busca ese código manuscrito, normalízalo a "
            "'hoja.problema' y devuélvelo en `codigo_problema`. Identifica ese problema y transcribe en "
            "`transcripcion_enunciado` SOLO su enunciado. Si el enunciado impreso no está visible (solo te llega la "
            "página con la solución), reconstruye el enunciado a partir de la solución lo mejor posible e indícalo. "
            "NO transcribas otros enunciados sin resolver. El título y los nodos se refieren solo a ese problema.\n"
        )

    prompt = (
        f"{intro}"
        "Taxonomía oficial de asignaturas y temas del Grado en Física (UVa):\n"
        f"{taxonomy_str}\n\n"
        "Instrucciones específicas de análisis (aplícalas a CADA problema resuelto):\n"
        "1. Clasificación:\n"
        "   - Identifica a qué Asignatura de la taxonomía anterior pertenece este ejercicio y devuélvelo en `asignatura_detectada`.\n"
        "   - Identifica a qué Tema concreto de esa asignatura pertenece y devuélvelo en `tema_detectado`.\n"
        "2. Título Corto:\n"
        "   - Define un título corto y descriptivo del problema en español, muy breve (máximo 4-5 palabras, ej: 'Efecto Hall en semiconductor', 'Esfera conductora en campo uniforme') y devuélvelo en `titulo_corto`.\n"
        "3. Transcripción del Enunciado:\n"
        "   - Transcribe y extrae de forma completa e íntegra el enunciado del problema en formato LaTeX/Markdown. "
        "Utiliza delimitadores $$ para ecuaciones en bloque y \\( y \\) para ecuaciones en línea. Devuélvelo en `transcripcion_enunciado`.\n"
        "   - CRÍTICO: Asegúrate de transcribir SOLO el enunciado original del problema. Ignora comentarios manuales, resoluciones escritas de compañeros, tachaduras o notas añadidas a mano sobre el enunciado por otras personas. Si detectas estas notas ajenas, NO las incluyas en la transcripción.\n"
        f"{caso_hoja}"
        "   - RESUMEN DIRECTO: rellena `resumen_correccion` con 2-4 frases al grano diciendo qué está BIEN y qué está MAL, para que el estudiante lo lea de un vistazo sin abrir el análisis completo.\n"
        "   - Si tienes dudas sobre qué parte es el enunciado frente a respuestas/anotaciones de compañeros, si no está claro cuál de los problemas de la hoja resolvió el estudiante, o si hay partes ilegibles que no se pueden transcribir con certeza, pon `dudas_transcripcion` como true y explica el motivo detalladamente en `mensaje_duda`.\n"
        "4. Transcripción del Manuscrito:\n"
        "   - Transcribe de forma detallada, matemática y literal paso a paso toda la solución escrita a mano por el estudiante. "
        "No resumas lo que hizo; en su lugar, escribe todas las ecuaciones y desarrollos intermedios en LaTeX (con delimitadores $ y $$) tal como aparecen en el papel. "
        "Esta transcripción es lo que el estudiante leerá para verificar qué has entendido de su letra, así que sé fiel a lo que ves. "
        "Devuélvelo en `transcripcion_manuscrito`.\n"
        "5. Evaluación pedagógica:\n"
        "   - No asumas que una diferencia con la solución oficial es un error si el estudiante ha seguido un camino "
        "físico o matemático alternativo totalmente válido (ej. conservación de la energía en lugar de leyes de Newton). "
        "Valora la consistencia física del método utilizado.\n"
        "   - Si no se proporciona solución oficial, debes evaluar con rigor si el planteamiento es físicamente consistente, "
        "si las dimensiones y unidades son correctas, y si el comportamiento en los límites físicos tiene sentido.\n"
        "6. Identificación de errores:\n"
        "   - Si detectas errores, descríbelos detalladamente e indica su clasificación (algebraico, conceptual, cálculo, "
        "interpretación física, planteamiento, unidades/dimensiones, otros).\n"
        "   - Explica claramente *por qué* ocurrió el error y da una recomendación/regla de oro sobre cómo evitarlo.\n"
        "   - Proporciona la expresión o paso incorrecto exacto (en LaTeX) y la versión corregida (en LaTeX).\n"
        "7. Estimación de dominio de conceptos:\n"
        "   - Identifica los conceptos físicos clave del ejercicio.\n"
        "   - Para cada concepto, estima el nivel de dominio demostrado por el estudiante en este intento específico "
        "en un rango de 0.0 a 1.0 (ej. 'Ley de Gauss': 0.9).\n"
        "8. Estado global del intento:\n"
        "   - Clasifica el resultado en 'correcto' (si llegó al resultado correcto por un camino correcto), "
        "'incorrecto' (si cometió errores significativos), o 'incompleto'.\n"
        "9. Confianza del análisis:\n"
        "   - Indica tu nivel de confianza (de 0.0 a 1.0). Si es menor a 0.8, detalla el motivo en `motivo_baja_confianza`.\n"
        "10. Nodos del knowledge graph:\n"
        "   - Más abajo tienes el catálogo de nodos del grafo de conocimiento del estudiante (formato `id: nombre`, agrupados por asignatura).\n"
        "   - Devuelve en `nodos_detectados` los ids (entre 1 y 5) de los nodos que este ejercicio ejercita DIRECTAMENTE, es decir, "
        "las técnicas o conceptos principales que hay que dominar para resolverlo. Prioriza nodos de la asignatura detectada. "
        "Usa los ids EXACTOS del catálogo (ej: 'em.1.07'). No incluyas prerrequisitos lejanos, solo lo que se practica de verdad en este ejercicio.\n\n"
        "Catálogo de nodos del knowledge graph:\n"
        f"{build_node_catalog()}\n"
    )

    if contexto:
        prompt += f"\nContexto del intento aportado por el estudiante: {contexto}\n"
    if intento_mental:
        prompt += f"\nIntento mental / Notas previas del estudiante: {intento_mental}\n"
    if hint_subject:
        prompt += f"\nNota: Este ejercicio pertenece a la asignatura '{hint_subject}'. Asegúrate de clasificarlo bajo esta asignatura en 'asignatura_detectada'.\n"
    return prompt


def call_gemini_analysis(
    exercise_path: str,
    solution_path: str,
    official_path: Optional[str] = None,
    contexto: Optional[str] = None,
    intento_mental: Optional[str] = None,
    hint_subject: Optional[str] = None
) -> Optional[schemas.AnalysisResponse]:
    """
    Carga los inputs, construye el prompt con la taxonomía UVa y llama a Gemini
    con Structured Outputs para obtener una respuesta estructurada (UN problema).
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    contents = _cargar_contents_ejercicio(exercise_path, solution_path, official_path)
    contents.append(_build_analysis_prompt(contexto, intento_mental, hint_subject, multi=False))

    try:
        json_data, _modelo, _es_fallback = _generar_con_fallback(client, contents, schemas.analysis_response_schema)
        parsed_response = schemas.AnalysisResponse.model_validate_json(json_data)
        return parsed_response
    except Exception as e:
        print(f"Error al llamar a Gemini o validar el esquema JSON de análisis: {e}")
        return None


def call_gemini_analysis_multi(
    exercise_path: str,
    solution_path: str,
    official_path: Optional[str] = None,
    contexto: Optional[str] = None,
    intento_mental: Optional[str] = None,
    hint_subject: Optional[str] = None
) -> Optional[tuple]:
    """Analiza una HOJA con uno o varios problemas resueltos a mano. Una sola
    llamada a Gemini para toda la hoja (ahorra cuota). Devuelve una tupla
    (soluciones, modelo_usado, es_fallback) — soluciones es una lista de
    AnalysisResponse (una por problema) — o None si falla."""
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    contents = _cargar_contents_ejercicio(exercise_path, solution_path, official_path)
    contents.append(_build_analysis_prompt(contexto, intento_mental, hint_subject, multi=True))

    try:
        json_data, modelo, es_fallback = _generar_con_fallback(client, contents, schemas.multi_analysis_response_schema)
        parsed = schemas.MultiAnalysisResponse.model_validate_json(json_data)
        return list(parsed.soluciones), modelo, es_fallback
    except Exception as e:
        print(f"Error al llamar a Gemini o validar el esquema JSON multi-problema: {e}")
        return None

def call_gemini_exam_extraction(
    exam_path: str,
    hint_subject: Optional[str] = None
) -> Optional[schemas.ExamExtractionResponse]:
    """
    Carga un examen completo, lo procesa con Gemini y devuelve los problemas
    estructurados e individuales en un ExamExtractionResponse.
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    contents = []
    
    exam_item = process_and_optimize_file(exam_path, "examen")
    if isinstance(exam_item, list):
        contents.extend(exam_item)
    else:
        contents.append(exam_item)
        
    taxonomy_str = ""
    taxonomy_path = "taxonomy_uva.json"
    if os.path.exists(taxonomy_path):
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            taxonomy_str = f.read()
            
    prompt = (
        "Eres un profesor de Física experto. Se te proporciona un archivo PDF o imagen "
        "que contiene un examen de Física de la Universidad de Valladolid (UVa).\n\n"
        "Tu tarea es:\n"
        "1. Identificar la asignatura del examen de entre las siguientes en la taxonomía:\n"
        f"{taxonomy_str}\n"
        "2. Identificar y separar de forma individual cada uno de los problemas/ejercicios redactados en el examen.\n"
        "3. Para cada problema identificado:\n"
        "   - Asignar el número de ejercicio (ej: 'Problema 1').\n"
        "   - Definir un título corto en español (máximo 4-5 palabras, ej: 'Esfera en campo eléctrico').\n"
        "   - Clasificar el tema al que pertenece dentro de la lista de temas de esa asignatura en la taxonomía anterior.\n"
        "   - Transcribir de forma completa e íntegra el enunciado original del problema en formato LaTeX/Markdown (asegúrate de que "
        "todas las fórmulas estén correctamente escritas en notación LaTeX estándar con delimitadores $$ y \\( ).\n"
        "   - CRÍTICO: Asegúrate de transcribir SOLO el enunciado original del problema. Ignora notas manuscritas de compañeros, soluciones u otras marcas manuales en el examen.\n"
        "   - Si tienes dudas sobre si hay anotaciones/soluciones de compañeros mezcladas o si hay partes ilegibles en el enunciado, pon `dudas_transcripcion` como true y explica el motivo detalladamente en `mensaje_duda`.\n\n"
        "Devuelve la respuesta estructurada en formato JSON respetando estrictamente el esquema de salida especificado."
    )
    
    if hint_subject:
        prompt += f"\nNota: Este examen pertenece a la asignatura '{hint_subject}'. Asegúrate de clasificarlo bajo esta asignatura en 'asignatura_detectada'.\n"
    
    contents.append(prompt)
    
    try:
        json_data, _modelo, _es_fallback = _generar_con_fallback(client, contents, schemas.exam_extraction_response_schema)
        parsed_response = schemas.ExamExtractionResponse.model_validate_json(json_data)
        return parsed_response
    except Exception as e:
        print(f"Error al llamar a Gemini para extracción de examen: {e}")
        return None
