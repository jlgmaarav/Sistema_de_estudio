# -*- coding: utf-8 -*-
"""Persistencia del resultado de una corrección de voz.

El sistema actual no vigila PDFs ni llama a ninguna API de Gemini. Whisper
transcribe la narración y Gemini Web devuelve un ``AnalysisResponse`` que este
módulo convierte en notas de Obsidian, correcciones y actualizaciones del grafo.
"""
import os
import sys
from datetime import datetime

import config
import file_manager
import templates
import apuntes
import repeticion
import study_context


def log_watcher(msg: str) -> None:
    """Mantiene un registro compatible con las notas antiguas, sin watcher activo."""
    print(msg)


def _procesar_una_solucion(response, file_path, hint_subject, kg_perfil,
                           sol_assets, enunciado_asset, contexto, intento_mental,
                           modelo_ia=None, es_fallback=False):
    """Guarda un ``AnalysisResponse`` y actualiza todas las capas del sistema."""
    modelo_registrado = str(modelo_ia or config.GEMINI_REQUIRED_MODEL).strip()
    if modelo_registrado != config.GEMINI_REQUIRED_MODEL:
        raise ValueError(
            f"No se puede registrar una corrección con {modelo_registrado!r}; "
            f"el modelo vigente es {config.GEMINI_REQUIRED_MODEL!r}."
        )
    asignatura = response.asignatura_detectada or hint_subject or "Física"
    tema = response.tema_detectado or "Sin clasificar"
    print(f"  [IA] Asignatura/Tema: {asignatura} -> {tema}")

    nodos_ids = list(getattr(response, "nodos_detectados", []) or [])
    if kg_perfil and not nodos_ids:
        try:
            nodos_ids = kg_perfil.resolver_conceptos(
                asignatura, [c.concepto for c in response.conceptos_dominio]
            )
        except Exception:
            nodos_ids = []

    file_manager.ensure_topic_note(asignatura, tema)
    exerc_dir = file_manager.ensure_subject_topic_dirs(asignatura, tema)
    exerc_id = file_manager.get_unique_exercise_id(exerc_dir, response.titulo_corto)
    exerc_file_path = os.path.join(exerc_dir, f"{exerc_id}.md")
    attempt_id = file_manager.get_next_attempt_id()
    attempt_file_path = os.path.join(config.INTENTOS_DIR, f"{attempt_id}.md")

    errors_ids = []
    if response.tiene_error and response.errores:
        for err in response.errores:
            error_id = file_manager.get_next_error_id()
            error_path = os.path.join(config.ERRORES_DIR, f"{error_id}.md")
            error_md = templates.render_error_template(
                error_id=error_id,
                title=err.titulo,
                tipo_error=err.tipo_error,
                descripcion=err.descripcion,
                razon=err.razon,
                como_evitarlo=err.como_evitarlo,
                ejemplo_incorrecto=err.ejemplo_incorrecto,
                ejemplo_correcto=err.ejemplo_correcto,
                asignatura=asignatura,
                tema=tema,
                conceptos=[c.concepto for c in response.conceptos_dominio],
                exerc_id=exerc_id,
                attempt_id=attempt_id,
            )
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(error_md)
            errors_ids.append(error_id)

    current_state, _ = file_manager.get_exercise_repetition_state(exerc_file_path)
    calidad = repeticion.calidad_de_correccion(
        response.resultado, response.tiene_error
    )
    new_state = repeticion.estado_ejercicio(current_state, calidad)
    next_retry = repeticion.fecha_reintento(calidad)
    attempt_md = templates.render_attempt_template(
        attempt_id=attempt_id,
        exerc_id=exerc_id,
        asignatura=asignatura,
        tema=tema,
        resultado=response.resultado,
        tiene_error=response.tiene_error,
        confianza=response.confianza_analisis,
        motivo_baja_confianza=response.motivo_baja_confianza or "",
        transcripcion=response.transcripcion_manuscrito,
        analisis=response.analisis_detallado,
        conceptos_dominio=response.conceptos_dominio,
        sol_assets=sol_assets or [],
        off_assets=[],
        contexto=contexto,
        intento_mental=intento_mental,
        errors_ids=errors_ids,
    )
    with open(attempt_file_path, "w", encoding="utf-8") as f:
        f.write(attempt_md)

    warning_text = ""
    if response.dudas_transcripcion:
        warning_text = response.mensaje_duda or "Hay dudas en la transcripción de voz."
        print(f"[AVISO] {warning_text}")
    exercise_md = templates.render_exercise_template(
        exerc_id=exerc_id,
        asignatura=asignatura,
        tema=tema,
        conceptos=[c.concepto for c in response.conceptos_dominio],
        tiene_error=response.tiene_error,
        enunciado_asset=enunciado_asset or "",
        enunciado_transcrito=response.transcripcion_enunciado,
        attempt_id=attempt_id,
        estado=new_state,
        proxima_reintento=next_retry,
        tipo_recurso="ejercicio",
        origen="Práctica narrada (Whisper + Gemini Web)",
        fecha_origen=datetime.now().strftime("%d/%m/%Y"),
        warning_transcripcion=warning_text,
        nodos=nodos_ids,
    )
    with open(exerc_file_path, "w", encoding="utf-8") as f:
        f.write(exercise_md)

    for item in response.conceptos_dominio:
        try:
            file_manager.update_concept_domain_score(
                item.concepto, item.dominio, exerc_id, attempt_id
            )
        except Exception as exc:
            print(f"[aviso] No se pudo escribir el concepto {item.concepto!r}: {exc}")
    file_manager.link_exercise_to_indices(exerc_id, asignatura, tema)

    reverso = None
    if kg_perfil and nodos_ids:
        exito = response.resultado == "correcto" and not response.tiene_error
        if response.resultado == "incorrecto":
            veredicto = "incorrecto"
        elif response.tiene_error or response.resultado == "incompleto":
            veredicto = "hueco_teorico"
        else:
            veredicto = "resuelto"
        nodos_hueco = list(getattr(response, "nodos_hueco_teorico", []) or [])
        nodos_error = list(getattr(response, "nodos_error", []) or [])
        if (veredicto == "hueco_teorico" and not nodos_hueco and not nodos_error):
            # Compatibilidad con respuestas antiguas de Gemini: si marcó un
            # error pero aún no devolvía diagnóstico por nodo, conservamos una
            # señal conservadora en todos los nodos directos.
            nodos_hueco = list(nodos_ids)
        try:
            problema_id = kg_perfil.emparejar_enunciado(
                response.transcripcion_enunciado, nodos_ids
            )
            mensajes, reverso = kg_perfil.registrar_manuscrito(
                nodos_ids, exito, origen=exerc_id, calidad=calidad,
                problema_id=problema_id, veredicto=veredicto,
                nodos_hueco=nodos_hueco, nodos_error=nodos_error,
            )
            for mensaje in mensajes:
                print(f"  -> {mensaje}")
        except Exception as exc:
            print(f"[aviso] No se pudo actualizar el perfil del grafo: {exc}")

    try:
        import correcciones as kg_correcciones
        kg_correcciones.registrar_desde_respuesta(
            response,
            exerc_id=exerc_id,
            asignatura=asignatura,
            tema=tema,
            calidad=calidad,
            asset=enunciado_asset,
            reverso=reverso,
            modelo=modelo_registrado,
            es_fallback=es_fallback,
        )
    except Exception as exc:
        print(f"[aviso] No se pudo guardar la corrección para la app: {exc}")

    try:
        graph_nodes = kg_perfil.cargar_grafos() if kg_perfil else None
        apuntes.apply_problem_response(
            response, exerc_id=exerc_id, attempt_id=attempt_id, nodes=graph_nodes
        )
        apuntes.generate(asignatura, graph_nodes)
    except Exception as exc:
        # La corrección y el grafo son la fuente principal; un fallo del generador
        # de LaTeX no debe impedir guardar el intento.
        print(f"[aviso] No se pudieron actualizar los apuntes LaTeX: {exc}")

    try:
        study_context.export_context(include_documents=True)
    except Exception as exc:
        # El contexto portable es una salida derivada y nunca debe impedir
        # guardar una corrección válida.
        print(f"[aviso] No se pudo actualizar el contexto IA: {exc}")

    print(f"[OK] Problema {exerc_id} procesado y enlazado.")
