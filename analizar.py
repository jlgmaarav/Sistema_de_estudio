import os
import sys
import argparse
import re
from datetime import datetime

import config
import file_manager
import gemini_client
import templates
import generar_dashboard

def main():
    parser = argparse.ArgumentParser(description="Analizador de Ejercicios de Física con IA para Obsidian")
    parser.add_argument("--ejercicio", required=True, help="Ruta al archivo del enunciado (imagen/PDF/texto) o texto directo del enunciado")
    parser.add_argument("--solucion", required=True, help="Ruta al archivo PDF/imagen de tu solución manuscrita")
    parser.add_argument("--oficial", help="Ruta al archivo PDF/imagen de la solución oficial (opcional)")
    parser.add_argument("--asignatura", help="Nombre de la asignatura (opcional, se auto-clasificará si se omite)")
    parser.add_argument("--tema", help="Nombre del tema (opcional, se auto-clasificará si se omite)")
    parser.add_argument("--contexto", help="Contexto adicional sobre el intento (opcional)")
    parser.add_argument("--intento_mental", help="Tus notas, hipótesis o dudas previas (opcional)")
    parser.add_argument("--ejercicio_id", help="ID de un ejercicio existente en Obsidian (ej: ejercicio_001).")
    
    args = parser.parse_args()
    
    # 1. Inicializar la estructura de directorios del vault
    config.init_vault_structure()
    
    # 2. Llamar a la API de Gemini primero para analizar y clasificar
    print("Llamando a la API de Gemini para el análisis y clasificación (esto puede tardar unos segundos)...")
    response = gemini_client.call_gemini_analysis(
        exercise_path=args.ejercicio,
        solution_path=args.solucion,
        official_path=args.oficial,
        contexto=args.contexto,
        intento_mental=args.intento_mental
    )
    
    if not response:
        print("Error: No se pudo obtener el análisis de Gemini.")
        sys.exit(1)
        
    print("¡Análisis recibido con éxito!")
    
    # 3. Determinar Asignatura y Tema (preferir argumento CLI, si no usar auto-clasificación de la IA)
    asignatura = args.asignatura if args.asignatura else response.asignatura_detectada
    tema = args.tema if args.tema else response.tema_detectado
    
    print(f"Asignatura asignada: '{asignatura}'")
    print(f"Tema asignado: '{tema}'")
    
    # 4. Asegurar notas de Asignatura y Tema en Obsidian
    file_manager.ensure_topic_note(asignatura, tema)
    exerc_dir = file_manager.ensure_subject_topic_dirs(asignatura, tema)
    
    # 5. Determinar/crear ID de Ejercicio e ID de Intento
    if args.ejercicio_id:
        exerc_id = args.ejercicio_id
        exerc_file_path = f"{exerc_dir}/{exerc_id}.md"
        if not os.path.exists(exerc_file_path):
            print(f"Error: El ejercicio especificado ({exerc_id}) no existe en: {exerc_file_path}")
            sys.exit(1)
        print(f"Vinculando intento a un ejercicio existente: {exerc_id}")
        is_new_exercise = False
    else:
        exerc_id = file_manager.get_next_exercise_id(asignatura, tema)
        exerc_file_path = f"{exerc_dir}/{exerc_id}.md"
        print(f"Se creará un nuevo ejercicio: {exerc_id}")
        is_new_exercise = True
        
    attempt_id = file_manager.get_next_attempt_id()
    attempt_file_path = f"{config.INTENTOS_DIR}/{attempt_id}.md"
    print(f"ID asignado para este intento: {attempt_id}")
    
    # 6. Copiar assets originales a /Assets
    print("Copiando recursos a la carpeta /Assets...")
    enunciado_asset = ""
    if os.path.exists(args.ejercicio):
        enunciado_asset = file_manager.copy_to_assets(args.ejercicio, asignatura, f"{exerc_id}_enunciado")
    else:
        print("El enunciado se ingresó como texto plano.")
        
    sol_assets = file_manager.process_and_copy_solution(args.solucion, asignatura)
    
    off_assets = []
    if args.oficial:
        off_assets = file_manager.process_and_copy_solution(args.oficial, asignatura)
        
    # 7. Procesar y guardar errores si existen
    errors_ids = []
    if response.tiene_error and response.errores:
        for err_idx, err in enumerate(response.errores):
            error_id = file_manager.get_next_error_id()
            error_file_path = f"{config.ERRORES_DIR}/{error_id}.md"
            
            err_markdown = templates.render_error_template(
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
                attempt_id=attempt_id
            )
            
            with open(error_file_path, 'w', encoding='utf-8') as f:
                f.write(err_markdown)
                
            print(f"  -> Creada ficha de error: {error_id}.md")
            errors_ids.append(error_id)
            
    # 8. Calcular Repetición Espaciada
    current_state, _ = file_manager.get_exercise_repetition_state(exerc_file_path)
    new_state, next_revision = file_manager.calculate_next_review(current_state, response.tiene_error)
    print(f"Repetición espaciada: Estado anterior '{current_state}' -> Nuevo '{new_state}'. Próxima revisión: {next_revision}")
    
    # 9. Crear la nota de Intento
    attempt_markdown = templates.render_attempt_template(
        attempt_id=attempt_id,
        exerc_id=exerc_id,
        asignatura=asignatura,
        tema=tema,
        resultado=response.resultado,
        tiene_error=response.tiene_error,
        confianza=response.confianza_analisis,
        motivo_baja_confianza=response.motivo_baja_confianza if response.motivo_baja_confianza else "",
        transcripcion=response.transcripcion_manuscrito,
        analisis=response.analisis_detallado,
        conceptos_dominio=response.conceptos_dominio,
        sol_assets=sol_assets,
        off_assets=off_assets,
        contexto=args.contexto,
        intento_mental=args.intento_mental,
        errors_ids=errors_ids
    )
    
    with open(attempt_file_path, 'w', encoding='utf-8') as f:
        f.write(attempt_markdown)
    print(f"  -> Creada ficha de intento: {attempt_id}.md")
    
    # 9.5 Determinar los nodos del knowledge graph que ejercita este intento
    kg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_graph")
    if kg_dir not in sys.path:
        sys.path.insert(0, kg_dir)
    nodos_ids = list(getattr(response, "nodos_detectados", []) or [])
    try:
        import perfil as kg_perfil
        if not nodos_ids:
            nodos_ids = kg_perfil.resolver_conceptos(
                asignatura, [c.concepto for c in response.conceptos_dominio])
    except Exception:
        kg_perfil = None

    # 10. Crear o actualizar la nota de Ejercicio
    if is_new_exercise:
        exerc_markdown = templates.render_exercise_template(
            exerc_id=exerc_id,
            asignatura=asignatura,
            tema=tema,
            conceptos=[c.concepto for c in response.conceptos_dominio],
            tiene_error=response.tiene_error,
            enunciado_asset=enunciado_asset,
            enunciado_transcrito=response.transcripcion_enunciado,
            attempt_id=attempt_id,
            estado=new_state,
            proxima_revision=next_revision,
            nodos=nodos_ids
        )
        with open(exerc_file_path, 'w', encoding='utf-8') as f:
            f.write(exerc_markdown)
        print(f"  -> Creada ficha de ejercicio: {exerc_id}.md")
    else:
        print(f"Actualizando historial en ejercicio existente: {exerc_id}")
        update_existing_exercise(exerc_file_path, attempt_id, response.tiene_error, new_state, next_revision)
        
    # 11. Crear/Actualizar Conceptos y sus evaluaciones de dominio
    for item in response.conceptos_dominio:
        file_manager.update_concept_domain_score(item.concepto, item.dominio, exerc_id, attempt_id)

    # 11.5 Actualizar el perfil de conocimiento del knowledge graph
    try:
        exito = (response.resultado == "correcto") and not response.tiene_error
        # Calidad graduada a partir del veredicto de Gemini: correcto y limpio =
        # resuelto; correcto con algún error = desliz; incompleto = a-medias;
        # incorrecto = bloqueado.
        if response.resultado == "correcto":
            calidad = 1.0 if not response.tiene_error else 0.75
        elif response.resultado == "incompleto":
            calidad = 0.5
        else:  # incorrecto
            calidad = 0.25
        if kg_perfil and nodos_ids:
            print(f"Perfil de conocimiento: registrando calidad {calidad:.2f} "
                  f"({'ÉXITO' if exito else 'FALLO'}) en {', '.join(nodos_ids)}")
            for msg in kg_perfil.registrar_y_guardar(nodos_ids, exito, origen=attempt_id, calidad=calidad):
                print(f"  -> {msg}")
            # Identificar si era un problema del banco y marcarlo como hecho
            try:
                pid = kg_perfil.emparejar_enunciado(response.transcripcion_enunciado, nodos_ids)
                if pid:
                    kg_perfil.marcar_problema_y_guardar(pid, exito)
                    print(f"  -> Problema del banco identificado y marcado como hecho: {pid}")
            except Exception:
                pass
        else:
            print("Perfil de conocimiento: no se pudo mapear el intento a nodos del grafo.")
    except Exception as e:
        print(f"Aviso: no se pudo actualizar el perfil de conocimiento: {e}")

    # 12. Enlazar ejercicio en Asignatura y Tema
    file_manager.link_exercise_to_indices(exerc_id, asignatura, tema)
    
    # 13. Actualizar Dashboard central
    generar_dashboard.run()
    
    print("\n========================================================")
    print("¡PROCESAMIENTO FINALIZADO CON ÉXITO!")
    print(f"Asignatura/Tema: {asignatura} -> {tema}")
    print(f"Ejercicio: {exerc_id} (Revisión: {next_revision})")
    print(f"Intento: {attempt_id} ({response.resultado.upper()})")
    if errors_ids:
        print(f"Errores generados: {', '.join(errors_ids)}")
    print("========================================================")

def update_existing_exercise(exerc_path: str, attempt_id: str, tiene_error: bool, estado: str, proxima_revision: str):
    """Actualiza los campos YAML y añade el nuevo intento al historial de un ejercicio existente."""
    with open(exerc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Actualizar metadatos
    content = re.sub(r'tiene_error:\s*(true|false)', f'tiene_error: {str(tiene_error).lower()}', content)
    content = re.sub(r'estado:\s*\w+', f'estado: {estado}', content)
    content = re.sub(r'proxima_revision:\s*[\d\-]+', f'proxima_revision: {proxima_revision}', content)
    
    # 2. Agregar intento al historial
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    status_str = 'Con errores' if tiene_error else 'Correcto'
    link_line = f"* [[{attempt_id}]] - {fecha_hoy} ({status_str})"
    
    if "<!-- intentos_inicio -->" in content and "<!-- intentos_fin -->" in content:
        content = file_manager.insert_between_markers(content, "<!-- intentos_inicio -->", "<!-- intentos_fin -->", link_line)
    else:
        content += f"\n{link_line}"
        
    with open(exerc_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
