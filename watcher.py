import os
import time
import shutil
import re
import sys
from datetime import datetime, timedelta

import config
import file_manager
import gemini_client
import templates
import generar_dashboard

# Escaneo automático de las carpetas Exámenes/Ejercicios de cada asignatura en
# `4º Física/`. Desactivado por defecto: esos exámenes ya están transcritos a mano
# en el banco de problemas y reprocesarlos con Gemini genera DUPLICADOS (y gasta
# cuota). Actívalo con WATCHER_SCAN_SUBJECT_FOLDERS=true en el .env si algún día
# quieres volver a procesarlos automáticamente. El Inbox (apuntes del reMarkable)
# se sigue procesando siempre.
SCAN_SUBJECT_FOLDERS = os.getenv("WATCHER_SCAN_SUBJECT_FOLDERS", "false").strip().lower() in ("1", "true", "yes")

# Mapeo de nombres de carpetas físicas a asignaturas oficiales de la taxonomía UVa
FOLDER_TO_SUBJECT = {
    "electrodinamica": "Electrodinámica clásica",
    "solido": "Física del Estado Sólido",
    "nuclear": "Física Nuclear y de Partículas",
    "tef iv": "Técnicas experimentales en Física IV",
    "tfg": "Trabajo de Fin de Grado",
    "mecanica cuantica": "Mecánica Cuántica",
    "electronica": "Electrónica"
}

# Directorio padre del sistema de estudio (contiene todas las asignaturas)
STUDY_PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace("\\", "/")

def get_subject_directories() -> list[tuple[str, str]]:
    """
    Escanea el directorio padre y devuelve una lista de tuplas (ruta_carpeta, asignatura_oficial)
    para cada asignatura activa.
    """
    subjects = []
    if not os.path.exists(STUDY_PARENT_DIR):
        return subjects
        
    for name in os.listdir(STUDY_PARENT_DIR):
        dir_path = os.path.join(STUDY_PARENT_DIR, name).replace("\\", "/")
        if os.path.isdir(dir_path):
            slug = file_manager.slugify(name)
            # Ignorar carpetas del sistema
            if slug in ["sistema_de_estudio", "venv", "__pycache__"] or name.startswith("."):
                continue
                
            official_subject = FOLDER_TO_SUBJECT.get(slug, name)
            subjects.append((dir_path, official_subject))
            
    return subjects

def wait_for_file_stable(path: str, timeout: int = 15) -> bool:
    """Espera a que el archivo termine de copiarse (su tamaño no cambie) y esté accesible."""
    if not os.path.exists(path):
        return False
    
    last_size = -1
    for _ in range(timeout):
        try:
            current_size = os.path.getsize(path)
            if current_size == last_size and current_size > 0:
                with open(path, 'rb') as f:
                    pass
                return True
            last_size = current_size
        except (IOError, OSError):
            pass
        time.sleep(1.5)
    return False

def parse_companion_txt(txt_path: str) -> tuple[str, str]:
    """Busca contexto e intento_mental opcionales en un archivo .txt acompañante."""
    contexto = ""
    intento_mental = ""
    if not os.path.exists(txt_path):
        return contexto, intento_mental
        
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        contexto_match = re.search(r'contexto:\s*(.*?)(?:\n\w+:|$)', content, re.DOTALL | re.IGNORECASE)
        intento_match = re.search(r'intento_mental:\s*(.*?)(?:\n\w+:|$)', content, re.DOTALL | re.IGNORECASE)
        
        if contexto_match:
            contexto = contexto_match.group(1).strip()
        if intento_match:
            intento_mental = intento_match.group(1).strip()
    except Exception as e:
        print(f"Error al leer archivo de metadatos acompañante {txt_path}: {e}")
        
    return contexto, intento_mental

def process_exam_file(file_path: str, hint_subject: str = None, custom_dest_dir: str = None):
    """Procesa un examen completo dividiéndolo en problemas independientes y catalogándolo."""
    print(f"\n[EXAMEN] Detectado archivo de examen: {file_path}")
    
    # 1. Llamar a Gemini para la extracción estructurada
    response = gemini_client.call_gemini_exam_extraction(file_path, hint_subject=hint_subject)
    if not response:
        print("  [ERROR] No se pudo extraer la información del examen.")
        return
        
    asignatura = response.asignatura_detectada or hint_subject or "Física"
    anio = response.anio or ""
    convocatoria = response.convocatoria or ""
    print(f"  [IA] Asignatura detectada: '{asignatura}' (Año: {anio}, Convocatoria: {convocatoria})")
    
    # 2. Copiar examen original a Assets
    exam_asset_name = file_manager.copy_to_assets(file_path, asignatura, f"examen_{convocatoria}_{anio}")
    
    # 3. Procesar cada ejercicio
    for ex in response.ejercicios:
        tema = ex.tema_detectado
        print(f"  -> Extrayendo {ex.numero}: '{ex.titulo_corto}' en el tema '{tema}'")
        
        # Asegurar directorios y nota del tema
        file_manager.ensure_topic_note(asignatura, tema)
        exerc_dir = file_manager.ensure_subject_topic_dirs(asignatura, tema)
        
        # Obtener un ID de ejercicio descriptivo único
        base_id = ex.titulo_corto
        if anio:
            base_id += f"_{anio}"
        exerc_id = file_manager.get_unique_exercise_id(exerc_dir, base_id)
        exerc_file_path = f"{exerc_dir}/{exerc_id}.md"
        
        warning_text = ""
        if ex.dudas_transcripcion:
            warning_text = ex.mensaje_duda or "Dudas de transcripción en el enunciado (posibles anotaciones ajenas)."
            log_watcher(f"[WARNING] PROBLEMA EN ESTE ARCHIVO (Examen), REVISAR: {os.path.basename(file_path)} - {warning_text}")
        
        # Generar contenido de ejercicio (sin intento previo)
        exerc_markdown = templates.render_exercise_template(
            exerc_id=exerc_id,
            asignatura=asignatura,
            tema=tema,
            conceptos=[],
            tiene_error=False,
            enunciado_asset=exam_asset_name,
            enunciado_transcrito=ex.enunciado_transcrito,
            attempt_id="",
            estado="nuevo",
            proxima_revision=(datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y"),
            tipo_recurso="examen",
            origen=f"Examen {convocatoria}".strip() if convocatoria else "Examen",
            fecha_origen=anio,
            warning_transcripcion=warning_text
        )
        
        with open(exerc_file_path, 'w', encoding='utf-8') as f:
            f.write(exerc_markdown)
        print(f"     [OK] Creada ficha de ejercicio: {exerc_id}.md")
        
        # Enlazar ejercicio en Asignatura y Tema
        file_manager.link_exercise_to_indices(exerc_id, asignatura, tema)
        
    # 4. Mover a Procesados
    move_to_procesados(file_path, custom_dest_dir)

def process_exercise_file(file_path: str, hint_subject: str = None, custom_dest_dir: str = None):
    """Procesa una hoja de ejercicios del reMarkable. La hoja puede contener UNO
    O VARIOS problemas resueltos a mano (cada uno con su código, ej. 3.1, 3.2):
    se hace UNA sola llamada a Gemini para toda la hoja y se procesa cada problema."""
    print(f"\n[EJERCICIO] Detectada hoja de ejercicios: {file_path}")

    # 1. Comprobar si hay un archivo .txt con metadatos acompañantes
    base_path = os.path.splitext(file_path)[0]
    txt_path = base_path + ".txt"
    contexto, intento_mental = parse_companion_txt(txt_path)

    # 2. Una sola llamada a Gemini para toda la hoja -> lista de problemas resueltos
    resultado = gemini_client.call_gemini_analysis_multi(
        exercise_path=file_path,
        solution_path=file_path,
        official_path=None,
        contexto=contexto,
        intento_mental=intento_mental,
        hint_subject=hint_subject
    )

    if not resultado or not resultado[0]:
        print("  [ERROR] No se pudo procesar el análisis de Gemini (ningún problema resuelto detectado).")
        return
    soluciones, modelo_ia, es_fallback = resultado
    if es_fallback:
        print(f"  [AVISO] Corregido con el modelo de RESPALDO ({modelo_ia}); menos fiable, revisa las correcciones.")

    # Preparar el motor del knowledge graph una sola vez
    kg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_graph")
    if kg_dir not in sys.path:
        sys.path.insert(0, kg_dir)
    try:
        import perfil as kg_perfil
    except Exception:
        kg_perfil = None

    # Copiar la hoja a /Assets una sola vez (compartida por todos los problemas)
    asignatura_hoja = soluciones[0].asignatura_detectada or hint_subject or "Física"
    sol_assets = file_manager.process_and_copy_solution(file_path, asignatura_hoja)
    enunciado_asset = sol_assets[0] if sol_assets else ""

    print(f"  [IA] {len(soluciones)} problema(s) resuelto(s) detectado(s) en la hoja.")
    for n, sol in enumerate(soluciones, 1):
        cod = getattr(sol, "codigo_problema", "") or f"#{n}"
        print(f"\n  --- Problema {n}/{len(soluciones)} (código {cod}) ---")
        try:
            _procesar_una_solucion(sol, file_path, hint_subject, kg_perfil,
                                   sol_assets, enunciado_asset, contexto, intento_mental,
                                   modelo_ia, es_fallback)
        except Exception as e_sol:
            print(f"     [ERROR] No se pudo procesar el problema {cod}: {e_sol}")

    # Mover archivos originales a Procesados (una vez procesada toda la hoja)
    move_to_procesados(file_path, custom_dest_dir)
    if os.path.exists(txt_path):
        move_to_procesados(txt_path, custom_dest_dir)
    print(f"  [OK] Hoja procesada: {len(soluciones)} problema(s).")


def _procesar_una_solucion(response, file_path, hint_subject, kg_perfil,
                           sol_assets, enunciado_asset, contexto, intento_mental,
                           modelo_ia="", es_fallback=False):
    """Procesa UN problema resuelto de la hoja: crea las fichas de Obsidian,
    actualiza el perfil del knowledge graph y guarda la corrección para la app."""
    asignatura = response.asignatura_detectada or hint_subject or "Física"
    tema = response.tema_detectado
    print(f"  [IA] Asignatura/Tema: {asignatura} -> {tema}")

    # 2.5 Determinar los nodos del knowledge graph que ejercita este intento
    nodos_ids = list(getattr(response, "nodos_detectados", []) or [])
    if kg_perfil and not nodos_ids:
        try:
            nodos_ids = kg_perfil.resolver_conceptos(
                asignatura, [c.concepto for c in response.conceptos_dominio])
        except Exception:
            nodos_ids = []

    # 3. Asegurar rutas y notas auxiliares
    file_manager.ensure_topic_note(asignatura, tema)
    exerc_dir = file_manager.ensure_subject_topic_dirs(asignatura, tema)

    # 4. Determinar IDs descriptivos
    base_id = response.titulo_corto
    exerc_id = file_manager.get_unique_exercise_id(exerc_dir, base_id)
    exerc_file_path = f"{exerc_dir}/{exerc_id}.md"
    attempt_id = file_manager.get_next_attempt_id()
    attempt_file_path = f"{config.INTENTOS_DIR}/{attempt_id}.md"

    # 6. Procesar errores
    errors_ids = []
    if response.tiene_error and response.errores:
        for err in response.errores:
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
            print(f"     -> Creada ficha de error: {error_id}.md")
            errors_ids.append(error_id)
            
    # 7. Calcular repetición espaciada
    current_state, _ = file_manager.get_exercise_repetition_state(exerc_file_path)
    new_state, next_revision = file_manager.calculate_next_review(current_state, response.tiene_error)
    
    # 8. Guardar Ficha de Intento
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
        off_assets=[],
        contexto=contexto,
        intento_mental=intento_mental,
        errors_ids=errors_ids
    )
    
    with open(attempt_file_path, 'w', encoding='utf-8') as f:
        f.write(attempt_markdown)
    print(f"     -> Creada ficha de intento: {attempt_id}.md")
    
    warning_text = ""
    if response.dudas_transcripcion:
        warning_text = response.mensaje_duda or "Dudas de transcripción en el enunciado (posibles anotaciones ajenas o letra ilegible)."
        log_watcher(f"[WARNING] PROBLEMA EN ESTE ARCHIVO (Ejercicio), REVISAR: {os.path.basename(file_path)} - {warning_text}")
    
    # 9. Guardar Ficha de Ejercicio
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
        tipo_recurso="ejercicio",
        origen="Práctica / Solución Escaneada",
        fecha_origen=datetime.now().strftime("%d/%m/%Y"),
        warning_transcripcion=warning_text,
        nodos=nodos_ids
    )
    with open(exerc_file_path, 'w', encoding='utf-8') as f:
        f.write(exerc_markdown)
    print(f"     -> Creada ficha de ejercicio: {exerc_id}.md (Próxima revisión: {next_revision})")
    
    # 10. Actualizar conceptos e historiales de dominio
    for item in response.conceptos_dominio:
        file_manager.update_concept_domain_score(item.concepto, item.dominio, exerc_id, attempt_id)
        
    # 11. Enlazar en Asignatura y Tema
    file_manager.link_exercise_to_indices(exerc_id, asignatura, tema)

    # 11.5 Actualizar el perfil del knowledge graph (dominio/fluidez/XP) con la
    #      CALIDAD GRADUADA derivada del veredicto de Gemini. Es lo que hace que
    #      resolver ejercicios en el reMarkable mueva el mapa, los repasos y el XP.
    #      Guardamos un `reverso` para poder deshacerlo si la corrección fue mala.
    calidad = None
    reverso = None
    if kg_perfil and nodos_ids:
        exito = (response.resultado == "correcto") and not response.tiene_error
        if response.resultado == "correcto":
            calidad = 1.0 if not response.tiene_error else 0.75   # bien / desliz
            etiqueta_cal = "resuelto" if not response.tiene_error else "desliz"
        elif response.resultado == "incompleto":
            calidad = 0.5                                          # a medias
            etiqueta_cal = "a medias"
        else:
            calidad = 0.25                                        # bloqueado/incorrecto
            etiqueta_cal = "bloqueado"
        try:
            print(f"     -> KG: registrando calidad {calidad:.2f} ({etiqueta_cal}) en {', '.join(nodos_ids)}")
            pid = kg_perfil.emparejar_enunciado(response.transcripcion_enunciado, nodos_ids)
            mensajes, reverso = kg_perfil.registrar_manuscrito(
                nodos_ids, exito, origen=exerc_id, calidad=calidad, problema_id=pid)
            for msg in mensajes:
                print(f"        {msg}")
            if pid:
                print(f"        Problema del banco identificado y marcado: {pid}")
        except Exception as e_kg:
            print(f"     [aviso] no se pudo actualizar el perfil KG: {e_kg}")
    elif kg_perfil:
        print("     -> KG: no se pudo mapear el intento a nodos del grafo.")

    # 11.6 Guardar la corrección para verla en la app web (no en Obsidian).
    try:
        import correcciones as kg_correcciones
        kg_correcciones.registrar_desde_respuesta(
            response, exerc_id=exerc_id, asignatura=asignatura, tema=tema,
            calidad=calidad, asset=enunciado_asset, reverso=reverso,
            modelo=modelo_ia, es_fallback=es_fallback)
        cod = getattr(response, "codigo_problema", "") or "?"
        print(f"     -> Corrección guardada para la app (código {cod}).")
    except Exception as e_corr:
        print(f"     [aviso] no se pudo guardar la corrección: {e_corr}")

    print(f"  [OK] Problema '{exerc_id}' procesado y enlazado.")

def move_to_procesados(file_path: str, custom_dest_dir: str = None):
    """Mueve un archivo procesado a su carpeta correspondiente de procesados."""
    filename = os.path.basename(file_path)
    dest_dir = custom_dest_dir if custom_dest_dir else config.INBOX_PROCESADOS_DIR
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    
    # Evitar colisiones renombrando con timestamp
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%H%M%S")
        dest_path = os.path.join(dest_dir, f"{base}_{timestamp}{ext}")
        
    try:
        shutil.move(file_path, dest_path)
        print(f"  [Watcher] Archivo movido a: {dest_path}")
    except Exception as e:
        print(f"  [WARNING] No se pudo mover el archivo {file_path} a Procesados: {e}")

def log_watcher(msg: str):
    """Registra eventos en el log del watcher."""
    log_path = os.path.join(config.INBOX_DIR, "watcher.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}\n"
    print(formatted_msg, end="")
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(formatted_msg)
    except Exception:
        pass

# Cortacircuitos: cuántas veces ha fallado cada archivo del Inbox. Tras
# MAX_FALLOS se aparta a `_fallidos/` para que el watcher no lo reintente en
# bucle infinito (evita machacar la cuota/CPU cada 3 s con un archivo roto).
_fallos_inbox: dict[str, int] = {}
MAX_FALLOS = 2


def _apartar_fallido(file_path: str, filename: str):
    """Mueve un archivo que falla repetidamente a Inbox/_fallidos para no reintentarlo sin fin."""
    dest_dir = os.path.join(config.INBOX_DIR, "_fallidos")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        dest_path = os.path.join(dest_dir, f"{base}_{datetime.now():%H%M%S}{ext}")
    try:
        shutil.move(file_path, dest_path)
        log_watcher(f"[INBOX] '{filename}' apartado a _fallidos tras {MAX_FALLOS} intentos. Revisa el archivo; el watcher sigue.")
    except Exception as e:
        log_watcher(f"[INBOX] No se pudo apartar '{filename}': {e}")
    _fallos_inbox.pop(filename, None)


# Cerrojo de instancia única: impide que dos watchers (p. ej. el de bucle
# continuo y uno lanzado con --once o desde corregir.py) procesen el Inbox a la
# vez y dupliquen todo (notas, correcciones, XP, cuota de Gemini).
_LOCK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watcher.lock")
_LOCK_STALE_S = 1800   # si el lock es más viejo que esto, se considera huérfano


def _adquirir_lock() -> bool:
    """Crea el lock de forma atómica. False si ya lo tiene otro watcher vivo."""
    try:
        fd = os.open(_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            edad = time.time() - os.path.getmtime(_LOCK_PATH)
        except OSError:
            edad = 0
        if edad > _LOCK_STALE_S:          # lock huérfano (watcher que murió sin limpiar)
            try:
                os.remove(_LOCK_PATH)
            except OSError:
                return False
            return _adquirir_lock()
        return False


def _liberar_lock() -> None:
    try:
        os.remove(_LOCK_PATH)
    except OSError:
        pass


def scan_once():
    """Pasada de escaneo protegida por el cerrojo de instancia única."""
    if not _adquirir_lock():
        log_watcher("[LOCK] Otro watcher ya está procesando; se omite esta pasada (evita duplicados).")
        return
    try:
        _scan_once_body()
    finally:
        _liberar_lock()


def _scan_once_body():
    """Realiza una única pasada de escaneo sobre el Inbox y las carpetas de asignaturas."""
    # 1. Escanear el Inbox global del Vault
    if os.path.exists(config.INBOX_DIR):
        for filename in os.listdir(config.INBOX_DIR):
            file_path = os.path.join(config.INBOX_DIR, filename)
            if os.path.isdir(file_path) or filename.lower() == "watcher.log":
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.webp']:
                log_watcher(f"[INBOX] Detectado archivo: {filename}")
                if wait_for_file_stable(file_path):
                    log_watcher(f"[INBOX] Archivo estable. Procesando...")
                    try:
                        if "examen" in filename.lower():
                            process_exam_file(file_path)
                        else:
                            process_exercise_file(file_path)
                        generar_dashboard.run()
                        _fallos_inbox.pop(filename, None)
                        log_watcher(f"[INBOX] Completado con éxito.")
                    except Exception as e:
                        _fallos_inbox[filename] = _fallos_inbox.get(filename, 0) + 1
                        n = _fallos_inbox[filename]
                        log_watcher(f"[INBOX] Error procesando {filename} (intento {n}/{MAX_FALLOS}): {e}")
                        if n >= MAX_FALLOS:
                            _apartar_fallido(file_path, filename)
    
    # 2. Escanear carpetas de asignaturas en 4º Física (DESACTIVADO por defecto:
    #    esos exámenes ya están transcritos en el banco; evitamos duplicados).
    if not SCAN_SUBJECT_FOLDERS:
        return
    subject_dirs = get_subject_directories()
    for subj_dir, official_subj in subject_dirs:
        # 2.1 Escanear carpeta de Exámenes
        examenes_path = os.path.join(subj_dir, "Exámenes")
        if not os.path.exists(examenes_path):
            examenes_path = os.path.join(subj_dir, "Examenes")
            
        if os.path.exists(examenes_path) and os.path.isdir(examenes_path):
            for filename in os.listdir(examenes_path):
                file_path = os.path.join(examenes_path, filename)
                if os.path.isdir(file_path) or filename.lower() == "procesados":
                    continue
                    
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.webp']:
                    log_watcher(f"[{official_subj} - EXAMEN] Detectado archivo: {filename}")
                    if wait_for_file_stable(file_path):
                        log_watcher(f"[{official_subj} - EXAMEN] Archivo estable. Procesando...")
                        try:
                            local_dest = os.path.join(examenes_path, "Procesados")
                            process_exam_file(file_path, hint_subject=official_subj, custom_dest_dir=local_dest)
                            generar_dashboard.run()
                            log_watcher(f"[{official_subj} - EXAMEN] Completado con éxito.")
                        except Exception as e:
                            log_watcher(f"[{official_subj} - EXAMEN] Error: {e}")
                            
        # 2.2 Escanear carpeta de Ejercicios
        ejercicios_path = os.path.join(subj_dir, "Ejercicios")
        if os.path.exists(ejercicios_path) and os.path.isdir(ejercicios_path):
            for filename in os.listdir(ejercicios_path):
                file_path = os.path.join(ejercicios_path, filename)
                if os.path.isdir(file_path) or filename.lower() == "procesados":
                    continue
                    
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.webp']:
                    log_watcher(f"[{official_subj} - EJERCICIO] Detectado archivo: {filename}")
                    if wait_for_file_stable(file_path):
                        log_watcher(f"[{official_subj} - EJERCICIO] Archivo estable. Procesando...")
                        try:
                            local_dest = os.path.join(ejercicios_path, "Procesados")
                            process_exercise_file(file_path, hint_subject=official_subj, custom_dest_dir=local_dest)
                            generar_dashboard.run()
                            log_watcher(f"[{official_subj} - EJERCICIO] Completado con éxito.")
                        except Exception as e:
                            log_watcher(f"[{official_subj} - EJERCICIO] Error: {e}")

def main():
    # Inicializar directorios de la bóveda
    config.init_vault_structure()
    
    once_mode = "--once" in sys.argv
    
    log_watcher("==================================================")
    log_watcher(f"Watcher Multidirectorio Iniciado ({'Modo Una Vez' if once_mode else 'Modo Bucle continuo'})...")
    log_watcher(f"Bóveda Inbox: {config.INBOX_DIR}")
    if SCAN_SUBJECT_FOLDERS:
        log_watcher(f"Escaneo de carpetas de asignatura ACTIVADO: {STUDY_PARENT_DIR}")
    else:
        log_watcher("Escaneo de carpetas de asignatura DESACTIVADO (solo Inbox; evita duplicados del banco).")
    log_watcher("==================================================")
    
    try:
        if once_mode:
            scan_once()
            log_watcher("Escaneo único completado. Saliendo del programa.")
        else:
            while True:
                scan_once()
                time.sleep(3)
    except KeyboardInterrupt:
        log_watcher("Watcher detenido por el usuario.")

if __name__ == "__main__":
    main()
