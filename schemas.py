from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from google.genai import types

# =====================================================================
# 1. Esquemas Pydantic para uso en Python (Tipado y Validación)
# =====================================================================

class ConceptoDominio(BaseModel):
    model_config = ConfigDict(extra='forbid')
    concepto: str = Field(description="Nombre del concepto físico")
    dominio: float = Field(description="Nivel de dominio estimado (de 0.0 a 1.0)")

class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra='forbid')
    titulo: str = Field(description="Título corto del error")
    tipo_error: List[str] = Field(
        default_factory=list,
        description="Tipos de error: algebraico, conceptual, calculo, interpretacion_fisica, planteamiento, unidades_dimensiones, otros"
    )
    descripcion: str = Field(description="Descripción técnica y física de dónde y cómo se cometió el error")
    razon: str = Field(description="Explicación cualitativa de por qué ocurrió (despiste, confusión de conceptos, etc.)")
    como_evitarlo: str = Field(description="Regla de oro o recomendación para no volver a cometerlo en el futuro")
    ejemplo_incorrecto: str = Field(description="La ecuación o paso incorrecto escrito en LaTeX")
    ejemplo_correcto: str = Field(description="La ecuación o paso correcto desarrollado en LaTeX")

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    asignatura_detectada: str = Field(
        description="Nombre de la asignatura clasificada según la taxonomía oficial de la UVa"
    )
    tema_detectado: str = Field(
        description="Nombre del tema clasificado según la taxonomía oficial de la UVa"
    )
    titulo_corto: str = Field(
        description="Título corto descriptivo del problema en español, muy breve (ej: 'Efecto Hall en semiconductor', 'Esfera conductora en campo uniforme')"
    )
    codigo_problema: Optional[str] = Field(
        None,
        description="Si el estudiante escribió a mano un código identificador del problema (formato hoja.problema, ej: '3.1', 'H3.1', '3-1'), devuélvelo aquí normalizado como 'hoja.problema' (ej: '3.1'). Si no hay código, deja vacío."
    )
    resumen_correccion: Optional[str] = Field(
        None,
        description="Resumen MUY directo del feedback en 2-4 frases: qué ha hecho BIEN y qué ha hecho MAL, para leer de un vistazo sin abrir el análisis completo. En español, al grano."
    )
    transcripcion_enunciado: str = Field(
        description="Transcripción matemática y de texto completa del enunciado del problema en formato LaTeX/Markdown. Asegúrate de transcribir SOLO el enunciado original del problema. Ignora comentarios manuales, soluciones de compañeros o anotaciones hechas a mano sobre el enunciado por otras personas."
    )
    dudas_transcripcion: bool = Field(
        description="Indica si tienes dudas sobre cuál es el enunciado frente a respuestas/anotaciones de compañeros, o si hay partes ilegibles que no se pueden transcribir con certeza."
    )
    mensaje_duda: Optional[str] = Field(
        None,
        description="Mensaje explicativo detallando las dudas de transcripción o si se sospecha de la presencia de soluciones ajenas."
    )
    transcripcion_manuscrito: str = Field(
        description="Transcripción matemática literal y detallada paso a paso de toda la solución manuscrita del estudiante en formato LaTeX"
    )
    conceptos_dominio: List[ConceptoDominio] = Field(
        default_factory=list,
        description="Lista de conceptos físicos clave mapeados a una estimación de dominio del estudiante (de 0.0 a 1.0) para este ejercicio"
    )
    nodos_detectados: List[str] = Field(
        default_factory=list,
        description="Ids de los nodos del knowledge graph (ej: 'em.1.07') que este ejercicio ejercita directamente, de 1 a 5, elegidos del catálogo proporcionado"
    )
    resultado: str = Field(
        description="Estado global del intento: 'correcto', 'incorrecto' o 'incompleto'"
    )
    tiene_error: bool = Field(description="Indica si la solución del estudiante contiene algún error")
    confianza_analisis: float = Field(description="Nivel de confianza en la interpretación matemática y OCR (de 0.0 a 1.0)")
    motivo_baja_confianza: Optional[str] = Field(None, description="Explicación si la confianza es baja (ej: letra ilegible en la línea 3)")
    analisis_detallado: str = Field(description="Análisis paso a paso del intento del estudiante en formato Markdown")
    errores: List[ErrorDetail] = Field(
        default_factory=list,
        description="Lista de errores identificados en el manuscrito"
    )

class MultiAnalysisResponse(BaseModel):
    """Respuesta para una HOJA con VARIOS problemas resueltos: una entrada de
    análisis por cada problema que el estudiante haya resuelto (identificado por
    su código manuscrito 3.1, 3.2, ...)."""
    model_config = ConfigDict(extra='forbid')
    soluciones: List[AnalysisResponse] = Field(
        default_factory=list,
        description="Una entrada por cada problema RESUELTO a mano en la hoja. Si solo hay uno, la lista tendrá un elemento."
    )

# Schemas para la extracción automática de exámenes
class EjercicioExamen(BaseModel):
    model_config = ConfigDict(extra='forbid')
    numero: str = Field(description="Número o identificador del ejercicio (ej: 'Problema 1')")
    titulo_corto: str = Field(description="Título corto descriptivo del problema en español")
    tema_detectado: str = Field(description="Nombre del tema clasificado según la taxonomía oficial de la UVa")
    enunciado_transcrito: str = Field(
        description="El enunciado del problema completo, transcrito en formato LaTeX/Markdown. Asegúrate de transcribir SOLO el enunciado original del problema. Ignora comentarios manuales, soluciones de compañeros o anotaciones hechas a mano sobre el examen."
    )
    dudas_transcripcion: bool = Field(
        description="Indica si tienes dudas sobre cuál es el enunciado o si hay anotaciones de compañeros mezcladas."
    )
    mensaje_duda: Optional[str] = Field(
        None,
        description="Mensaje explicativo detallando las dudas de transcripción o si se sospecha de la presencia de soluciones ajenas."
    )

class ExamExtractionResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    asignatura_detectada: str = Field(description="Nombre de la asignatura clasificada según la taxonomía oficial de la UVa")
    anio: Optional[str] = Field(None, description="Año o curso académico del examen, ej: '2026', '24-25'")
    convocatoria: Optional[str] = Field(None, description="Tipo o convocatoria de examen, ej: 'Ordinaria', 'Extraordinaria', 'Parcial 1', 'Parcial 2'")
    ejercicios: List[EjercicioExamen] = Field(default_factory=list, description="Lista de problemas identificados y extraídos del examen")

# =====================================================================
# 2. Esquemas nativos types.Schema para compatibilidad con API Developer
# =====================================================================

concepto_dominio_schema = types.Schema(
    type=types.Type.OBJECT,
    description="Concepto físico y su estimación de dominio",
    properties={
        "concepto": types.Schema(type=types.Type.STRING, description="Nombre del concepto físico"),
        "dominio": types.Schema(type=types.Type.NUMBER, description="Nivel de dominio estimado (de 0.0 a 1.0)"),
    },
    required=["concepto", "dominio"]
)

error_detail_schema = types.Schema(
    type=types.Type.OBJECT,
    description="Detalle del error identificado",
    properties={
        "titulo": types.Schema(type=types.Type.STRING, description="Título corto del error"),
        "tipo_error": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="Tipos de error: algebraico, conceptual, calculo, interpretacion_fisica, planteamiento, unidades_dimensiones, otros"
        ),
        "descripcion": types.Schema(type=types.Type.STRING, description="Descripción técnica y física de dónde y cómo se cometió el error"),
        "razon": types.Schema(type=types.Type.STRING, description="Explicación cualitativa de por qué ocurrió (despiste, confusión de conceptos, etc.)"),
        "como_evitarlo": types.Schema(type=types.Type.STRING, description="Regla de oro o recomendación para no volver a cometerlo en el futuro"),
        "ejemplo_incorrecto": types.Schema(type=types.Type.STRING, description="La ecuación o paso incorrecto escrito en LaTeX"),
        "ejemplo_correcto": types.Schema(type=types.Type.STRING, description="La ecuación o paso correcto desarrollado en LaTeX"),
    },
    required=["titulo", "descripcion", "razon", "como_evitarlo", "ejemplo_incorrecto", "ejemplo_correcto"]
)

analysis_response_schema = types.Schema(
    type=types.Type.OBJECT,
    description="Análisis estructurado del intento de resolución",
    properties={
        "asignatura_detectada": types.Schema(
            type=types.Type.STRING,
            description="Nombre de la asignatura clasificada según la taxonomía oficial de la UVa"
        ),
        "tema_detectado": types.Schema(
            type=types.Type.STRING,
            description="Nombre del tema clasificado según la taxonomía oficial de la UVa"
        ),
        "titulo_corto": types.Schema(
            type=types.Type.STRING,
            description="Título corto descriptivo del problema en español, muy breve (ej: 'Efecto Hall en semiconductor', 'Esfera conductora en campo uniforme')"
        ),
        "codigo_problema": types.Schema(
            type=types.Type.STRING,
            description="Código identificador escrito a mano por el estudiante en formato hoja.problema (ej: '3.1'), normalizado. Vacío si no lo hay."
        ),
        "resumen_correccion": types.Schema(
            type=types.Type.STRING,
            description="Resumen muy directo del feedback en 2-4 frases (qué está bien y qué está mal) para leer de un vistazo. En español, al grano."
        ),
        "transcripcion_enunciado": types.Schema(
            type=types.Type.STRING,
            description="Transcripción matemática y de texto completa del enunciado original del problema en formato LaTeX/Markdown. Ignora cualquier anotación manuscrita, respuestas o notas de compañeros."
        ),
        "dudas_transcripcion": types.Schema(
            type=types.Type.BOOLEAN,
            description="Indica si hay dudas de si lo que transcribes es el enunciado o si hay respuestas de compañeros manuscritas en el mismo papel que puedan confundirse."
        ),
        "mensaje_duda": types.Schema(
            type=types.Type.STRING,
            description="Explicación del problema o dudas con la transcripción (ej. presencia de anotaciones de compañeros)."
        ),
        "transcripcion_manuscrito": types.Schema(
            type=types.Type.STRING,
            description="Transcripción matemática literal y detallada paso a paso de toda la solución manuscrita del estudiante en formato LaTeX"
        ),
        "conceptos_dominio": types.Schema(
            type=types.Type.ARRAY,
            items=concepto_dominio_schema,
            description="Lista de conceptos físicos clave mapeados a una estimación de dominio del estudiante (de 0.0 a 1.0) para este ejercicio"
        ),
        "nodos_detectados": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="Ids de los nodos del knowledge graph (ej: 'em.1.07') que este ejercicio ejercita directamente, de 1 a 5, elegidos del catálogo proporcionado"
        ),
        "resultado": types.Schema(
            type=types.Type.STRING,
            description="Estado global del intento: 'correcto', 'incorrecto' o 'incompleto'"
        ),
        "tiene_error": types.Schema(
            type=types.Type.BOOLEAN,
            description="Indica si la solución del estudiante contiene algún error"
        ),
        "confianza_analisis": types.Schema(
            type=types.Type.NUMBER,
            description="Nivel de confianza en la interpretación matemática y OCR (de 0.0 a 1.0)"
        ),
        "motivo_baja_confianza": types.Schema(
            type=types.Type.STRING,
            description="Explicación si la confianza es baja (ej: letra ilegible en la línea 3)"
        ),
        "analisis_detallado": types.Schema(
            type=types.Type.STRING,
            description="Análisis paso a paso del intento del estudiante en formato Markdown"
        ),
        "errores": types.Schema(
            type=types.Type.ARRAY,
            items=error_detail_schema,
            description="Lista de errores identificados en el manuscrito"
        )
    },
    required=["asignatura_detectada", "tema_detectado", "titulo_corto", "transcripcion_enunciado", "dudas_transcripcion", "transcripcion_manuscrito", "resultado", "tiene_error", "confianza_analisis", "analisis_detallado"]
)

multi_analysis_response_schema = types.Schema(
    type=types.Type.OBJECT,
    description="Análisis de una hoja con uno o varios problemas resueltos a mano",
    properties={
        "soluciones": types.Schema(
            type=types.Type.ARRAY,
            items=analysis_response_schema,
            description="Una entrada por cada problema RESUELTO a mano en la hoja (identificado por su código manuscrito, ej: 3.1, 3.2). Si solo hay uno, la lista tendrá un elemento."
        ),
    },
    required=["soluciones"]
)

# Esquemas nativos para la extracción de exámenes
ejercicio_examen_schema = types.Schema(
    type=types.Type.OBJECT,
    description="Ejercicio extraído de un examen",
    properties={
        "numero": types.Schema(type=types.Type.STRING, description="Número o identificador del ejercicio (ej: 'Problema 1')"),
        "titulo_corto": types.Schema(type=types.Type.STRING, description="Título corto descriptivo del problema en español"),
        "tema_detectado": types.Schema(type=types.Type.STRING, description="Nombre del tema clasificado según la taxonomía oficial de la UVa"),
        "enunciado_transcrito": types.Schema(type=types.Type.STRING, description="El enunciado del problema completo, transcrito en formato LaTeX/Markdown. Ignora notas manuscritas de compañeros."),
        "dudas_transcripcion": types.Schema(type=types.Type.BOOLEAN, description="Indica si tienes dudas sobre si hay respuestas de compañeros mezcladas o si hay partes ilegibles en el enunciado."),
        "mensaje_duda": types.Schema(type=types.Type.STRING, description="Mensaje explicativo indicando por qué se duda de la transcripción.")
    },
    required=["numero", "titulo_corto", "tema_detectado", "enunciado_transcrito", "dudas_transcripcion"]
)

exam_extraction_response_schema = types.Schema(
    type=types.Type.OBJECT,
    description="Respuesta con la lista de ejercicios extraídos de un examen",
    properties={
        "asignatura_detectada": types.Schema(type=types.Type.STRING, description="Nombre de la asignatura clasificada según la taxonomía oficial de la UVa"),
        "anio": types.Schema(type=types.Type.STRING, description="Año o curso académico del examen (ej: '2026', '2024-25')"),
        "convocatoria": types.Schema(type=types.Type.STRING, description="Convocatoria o tipo de examen (ej: 'Ordinaria', 'Extraordinaria', 'Parcial 1', 'Parcial 2', 'Cuestiones')"),
        "ejercicios": types.Schema(
            type=types.Type.ARRAY,
            items=ejercicio_examen_schema,
            description="Lista de problemas identificados y extraídos del examen"
        ),
    },
    required=["asignatura_detectada", "ejercicios"]
)
