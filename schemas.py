# -*- coding: utf-8 -*-
"""Esquemas de validación locales para el flujo Whisper + Gemini Web.

Este módulo no contiene esquemas del SDK de Gemini: la respuesta se copia
desde la web y se valida localmente antes de tocar el grafo de estudio.
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConceptoDominio(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concepto: str = Field(description="Nombre del concepto físico")
    dominio: float = Field(description="Nivel de dominio estimado (de 0.0 a 1.0)")


class Checkpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descripcion: str = Field(description="Qué sub-paso es este checkpoint")
    resultado_dicho: str = Field(description="Resultado parcial narrado, en LaTeX")
    correcto: bool = Field(description="Si el resultado parcial es correcto")
    nota: Optional[str] = Field(None, description="Qué falla en el checkpoint, si falla")


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str = Field(description="Título corto del error")
    tipo_error: List[str] = Field(default_factory=list)
    descripcion: str
    razon: str
    como_evitarlo: str
    ejemplo_incorrecto: str
    ejemplo_correcto: str


class AnalysisResponse(BaseModel):
    """Respuesta JSON devuelta por Gemini Web para una narración."""
    model_config = ConfigDict(extra="forbid")
    asignatura_detectada: str
    tema_detectado: str
    titulo_corto: str
    codigo_problema: Optional[str] = None
    resumen_correccion: Optional[str] = None
    transcripcion_enunciado: str
    dudas_transcripcion: bool
    mensaje_duda: Optional[str] = None
    transcripcion_manuscrito: str
    conceptos_dominio: List[ConceptoDominio] = Field(default_factory=list)
    nodos_detectados: List[str] = Field(default_factory=list)
    nodos_hueco_teorico: List[str] = Field(
        default_factory=list,
        description="Ids de nodos donde hay un hueco de explicación o justificación teórica",
    )
    nodos_error: List[str] = Field(
        default_factory=list,
        description="Ids de nodos directamente afectados por un error de resolución",
    )
    resultado: str
    tiene_error: bool
    confianza_analisis: float
    motivo_baja_confianza: Optional[str] = None
    analisis_detallado: str
    errores: List[ErrorDetail] = Field(default_factory=list)
    checkpoints: List[Checkpoint] = Field(default_factory=list)


class MultiAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    soluciones: List[AnalysisResponse] = Field(default_factory=list)


class EjercicioExamen(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero: str
    titulo_corto: str
    tema_detectado: str
    enunciado_transcrito: str
    dudas_transcripcion: bool
    mensaje_duda: Optional[str] = None


class ExamExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asignatura_detectada: str
    anio: Optional[str] = None
    convocatoria: Optional[str] = None
    ejercicios: List[EjercicioExamen] = Field(default_factory=list)
