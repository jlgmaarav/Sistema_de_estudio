import os
import json
import re
import sys
import subprocess
import threading
import uuid
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from datetime import datetime
from werkzeug.utils import secure_filename

import config
import file_manager
import templates
import generar_dashboard
import buscar_web
import study_sessions as study_flow
import study_context
import apuntes
import repeticion

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 250 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(BASE_DIR, 'grabaciones')
VOICE_EXTENSIONS = {'.m4a', '.mp3', '.wav', '.ogg', '.opus', '.flac', '.aac', '.wma', '.mp4', '.webm'}
_voice_jobs = {}
_voice_jobs_lock = threading.Lock()
_context_export_lock = threading.Lock()
_context_export_timer = None


def _refresh_context_snapshot():
    """Regenera la copia portable después de una mutación del sistema."""
    global _context_export_timer
    try:
        study_context.export_context(include_documents=True)
    except Exception as exc:
        # La instantánea es una salida derivada: nunca debe romper una acción
        # que ya ha guardado correctamente el perfil o el grafo.
        print(f"Aviso: no se pudo actualizar el contexto IA: {exc}")
    finally:
        with _context_export_lock:
            _context_export_timer = None


def _schedule_context_snapshot():
    """Agrupa varias escrituras seguidas en una sola exportación."""
    global _context_export_timer
    with _context_export_lock:
        if _context_export_timer and _context_export_timer.is_alive():
            _context_export_timer.cancel()
        _context_export_timer = threading.Timer(1.0, _refresh_context_snapshot)
        _context_export_timer.daemon = True
        _context_export_timer.start()


@app.after_request
def refresh_context_after_mutation(response):
    if (
        request.path.startswith('/api/')
        and request.path != '/api/context/export'
        and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}
        and response.status_code < 400
    ):
        _schedule_context_snapshot()
    return response


def _agenda_academica():
    """Serializa la única agenda académica: los repasos del perfil de nodos."""
    nodos = kg_perfil.cargar_grafos()
    perfil_d = kg_perfil.cargar_perfil()
    pendientes = kg_perfil.pendientes_repaso(perfil_d, nodos)
    salida = []
    for item in pendientes:
        try:
            proxima = datetime.strptime(item["proxima"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except (KeyError, TypeError, ValueError):
            proxima = "—"
        salida.append({
            "tipo": "concepto",
            "id": item["id"],
            "nombre": item["nombre"],
            "tema": "Concepto",
            "asignatura": item["materia"],
            "estado": "vencido" if item["retraso"] else "hoy",
            "proxima_revision": proxima,
            "retraso": item["retraso"],
            "dominio_efectivo": item["dominio_efectivo"],
        })
    return salida

# Ensure folders exist
config.init_vault_structure()

@app.route('/')
def index():
    return render_template('index.html', gemini_model=config.GEMINI_REQUIRED_MODEL)

@app.route('/assets/<path:filename>')
def serve_asset(filename):
    return send_from_directory(config.ASSETS_DIR, filename)


def _set_voice_job(job_id, **changes):
    with _voice_jobs_lock:
        job = _voice_jobs.get(job_id)
        if job:
            job.update(changes)


def _wait_gemini_voice_result(job_id, result_path, transcript_path):
    """Compatibilidad con un resultado JSON dejado por una integración externa."""
    script = os.path.join(BASE_DIR, 'corregir_voz.py')
    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    for _ in range(900):  # una hora: suficiente para una corrección con calma
        if os.path.exists(result_path):
            try:
                proc = subprocess.run(
                    [sys.executable, script, '--importar-gemini', result_path, transcript_path,
                     '--modelo', config.GEMINI_REQUIRED_MODEL],
                    cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8', errors='replace',
                    creationflags=creationflags,
                )
                if proc.returncode:
                    raise RuntimeError((proc.stdout or proc.stderr or 'No se pudo importar el resultado')[-800:])
                _set_voice_job(job_id, estado='completado',
                               mensaje='Corrección de Gemini terminada. El feedback y el grafo ya están actualizados.',
                               salida=(proc.stdout or '')[-1200:])
            except Exception as exc:
                _set_voice_job(job_id, estado='error', mensaje=str(exc))
            return
        threading.Event().wait(4)
    _set_voice_job(job_id, estado='error', mensaje='Gemini no dejó el resultado en una hora.')


def _run_voice_job(job_id, audio_path):
    """Transcribe and correct a browser recording without blocking Flask."""
    script = os.path.join(BASE_DIR, 'corregir_voz.py')
    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    _set_voice_job(job_id, estado='procesando', mensaje='Whisper está transcribiendo tu razonamiento…')
    try:
        proc = subprocess.Popen(
            [sys.executable, script, audio_path],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creationflags,
        )
        salida, _ = proc.communicate()
        if proc.returncode != 0:
            detalle = (salida or '').strip().splitlines()
            raise RuntimeError(detalle[-1] if detalle else 'El análisis de voz terminó con un error.')
        marker = next((line for line in (salida or '').splitlines() if line.startswith('GEMINI_HANDOFF:')), None)
        if marker:
            partes = marker.split(':', 1)[1].split('|', 2)
            encargo, resultado = partes[:2]
            detalle = partes[2] if len(partes) > 2 else 'Prompt preparado para Gemini.'
            _set_voice_job(
                job_id, estado='esperando_gemini', encargo=encargo, resultado=resultado,
                transcripcion=os.path.splitext(audio_path)[0] + '.txt',
                mensaje=f'Gemini está abierto. {detalle} Pega el prompt, envíalo y devuelve aquí su JSON.',
                salida=(salida or '').strip()[-1200:],
            )
        else:
            _set_voice_job(
                job_id,
                estado='completado',
                mensaje='Análisis terminado. El feedback y el grafo ya están actualizados.',
                salida=(salida or '').strip()[-1200:],
            )
    except Exception as exc:
        _set_voice_job(job_id, estado='error', mensaje=str(exc))


@app.route('/api/hub', methods=['GET'])
def get_hub_status():
    """Estado mínimo que necesita la pantalla central para guiar el siguiente paso."""
    try:
        inbox = []
        if os.path.isdir(config.INBOX_DIR):
            inbox = [
                name for name in os.listdir(config.INBOX_DIR)
                if os.path.isfile(os.path.join(config.INBOX_DIR, name))
            ]
        try:
            import correcciones as kg_corr
            correcciones = kg_corr.cargar()
        except Exception:
            correcciones = []
        with _voice_jobs_lock:
            voz = list(_voice_jobs.values())[-5:]
        return jsonify({
            'inbox_pendientes': len(inbox),
            'correcciones_pendientes': len(correcciones),
            'ultimas_correcciones': correcciones[-3:][::-1],
            'trabajos_voz': voz,
            'estudio': study_flow.insights(),
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        data = generar_dashboard.scan_vault()
        
        total_ejercicios = len(data["ejercicios"])
        total_intentos = len(data["intentos"])
        total_errores = len(data["errores"])

        # Total de problemas del banco (colección completa disponible para practicar,
        # mucho mayor que los ejercicios ya intentados en el vault).
        total_banco = 0
        try:
            import json as _dj
            banco_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'knowledge_graph', 'banco_problemas.json')
            with open(banco_path, encoding='utf-8') as _bf:
                _banco = _dj.load(_bf)
            total_banco = sum(len(v.get('problemas', [])) for v in _banco.values())
        except Exception:
            total_banco = 0
        
        correctos = sum(1 for i in data["intentos"] if i["resultado"] == "correcto")
        incorrectos = total_intentos - correctos
        tasa_exito = (correctos / total_intentos * 100) if total_intentos > 0 else 0.0
        
        # La agenda académica procede únicamente del perfil de nodos. Los
        # ejercicios fallados se mantienen en una cola local separada.
        hoy = datetime.now().date()
        agenda = _agenda_academica()
        reintentos = [
            ex for ex in data["ejercicios"]
            if repeticion.reintento_pendiente(ex, hoy)
        ]
        reintentos.sort(
            key=lambda x: repeticion.fecha_reintento_de_ejercicio(x) or hoy
        )
        
        # Tipos de errores
        error_counts = {}
        for err in data["errores"]:
            for t in err["tipos"]:
                error_counts[t] = error_counts.get(t, 0) + 1
                
        # Conceptos débiles
        conceptos_debiles = sorted(data["conceptos"], key=lambda x: x["dominio"])[:5]
        
        # Intentos recientes
        intentos_recientes = sorted(data["intentos"], key=lambda x: x["fecha"], reverse=True)[:5]
        
        return jsonify({
            "stats": {
                "total_ejercicios": total_ejercicios,
                "total_banco": total_banco,
                "total_intentos": total_intentos,
                "total_errores": total_errores,
                "correctos": correctos,
                "incorrectos": incorrectos,
                "tasa_exito": round(tasa_exito, 1)
            },
            "agenda": agenda,
            "reintentos_ejercicios": reintentos,
            "error_counts": error_counts,
            "conceptos_debiles": conceptos_debiles,
            "intentos_recientes": intentos_recientes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    try:
        data = generar_dashboard.scan_vault()
        subjects = {}
        
        # Inicializar con las asignaturas de la taxonomía por defecto
        taxonomy_path = "taxonomy_uva.json"
        if os.path.exists(taxonomy_path):
            import json
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                tax = json.load(f)
            for k in tax.keys():
                subjects[k] = {
                    "nombre": k,
                    "ejercicios": 0,
                    "intentos": 0,
                    "correctos": 0,
                    "errores": 0,
                    "temas": len(tax[k])
                }
                
        # Contar ejercicios, intentos y errores reales
        for ex in data["ejercicios"]:
            subj = ex["asignatura"]
            if subj not in subjects:
                subjects[subj] = {"nombre": subj, "ejercicios": 0, "intentos": 0, "correctos": 0, "errores": 0, "temas": 0}
            subjects[subj]["ejercicios"] += 1
            
        for i in data["intentos"]:
            ex_origin = next((ex for ex in data["ejercicios"] if ex["id"] == i["ejercicio"]), None)
            if ex_origin:
                subj = ex_origin["asignatura"]
                if subj not in subjects:
                    subjects[subj] = {"nombre": subj, "ejercicios": 0, "intentos": 0, "correctos": 0, "errores": 0, "temas": 0}
                subjects[subj]["intentos"] += 1
                if i["resultado"] == "correcto":
                    subjects[subj]["correctos"] += 1
                    
        for err in data["errores"]:
            subj = err["asignatura"]
            if subj not in subjects:
                subjects[subj] = {"nombre": subj, "ejercicios": 0, "intentos": 0, "correctos": 0, "errores": 0, "temas": 0}
            subjects[subj]["errores"] += 1
            
        return jsonify(list(subjects.values()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/study/subjects', methods=['GET'])
def get_study_subjects():
    """Tarjetas de asignatura para la puerta de entrada del dashboard."""
    try:
        return jsonify(study_context.subject_summaries())
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/subjects/<subject_name>', methods=['GET'])
def get_subject_detail(subject_name):
    try:
        # Normalizar subject_name si viene slugified o con espacios
        data = generar_dashboard.scan_vault()
        
        # Buscar nombre exacto en el vault
        exact_subject = subject_name
        for ex in data["ejercicios"]:
            if file_manager.slugify(ex["asignatura"]) == file_manager.slugify(subject_name):
                exact_subject = ex["asignatura"]
                break
                
        # Cargar temas de la taxonomía si existe
        temas_list = []
        taxonomy_path = "taxonomy_uva.json"
        if os.path.exists(taxonomy_path):
            import json
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                tax = json.load(f)
            # Buscar coincidencia en taxonomía
            for k in tax.keys():
                if file_manager.slugify(k) == file_manager.slugify(subject_name):
                    temas_list = tax[k]
                    exact_subject = k
                    break
                    
        # Filtrar ejercicios, errores e intentos de esta asignatura
        ejercicios = [ex for ex in data["ejercicios"] if file_manager.slugify(ex["asignatura"]) == file_manager.slugify(exact_subject)]
        errores = [err for err in data["errores"] if file_manager.slugify(err["asignatura"]) == file_manager.slugify(exact_subject)]
        
        ejercicio_ids = [ex["id"] for ex in ejercicios]
        intentos = [i for i in data["intentos"] if i["ejercicio"] in ejercicio_ids]
        
        # Intentar leer la nota de asignatura si existe para extraer anotaciones/fechas examen
        slug = file_manager.slugify(exact_subject)
        subject_file = f"{config.ASIGNATURAS_DIR}/{slug}/{slug}.md"
        anotaciones = ""
        fecha_examen = ""
        if os.path.exists(subject_file):
            with open(subject_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Extraer anotaciones (todo lo que no sea frontmatter ni listas marcadas)
            body = content.split("---")[-1].strip()
            anotaciones = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL).strip()
            # Buscar fecha de examen en el YAML si existe
            fecha_match = re.search(r'fecha_examen:\s*([\d\-]+)', content)
            if fecha_match:
                fecha_examen = fecha_match.group(1).strip()
                
        return jsonify({
            "nombre": exact_subject,
            "temas": temas_list,
            "ejercicios": ejercicios,
            "intentos": intentos,
            "errores": errores,
            "anotaciones": anotaciones,
            "fecha_examen": fecha_examen
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/exercise/<exerc_id>', methods=['GET'])
def get_exercise_detail(exerc_id):
    try:
        # Buscar el ejercicio escaneando las carpetas de asignaturas
        target_path = None
        for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
            if f"{exerc_id}.md" in files:
                target_path = os.path.join(root, f"{exerc_id}.md")
                break
                
        if not target_path or not os.path.exists(target_path):
            return jsonify({"error": f"Ejercicio {exerc_id} no encontrado"}), 404
            
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parsear metadatos
        id_ex = parse_yaml_field(content, "id")
        subj = parse_yaml_field(content, "asignatura")
        topic = parse_yaml_field(content, "tema")
        concepts = parse_yaml_list(content, "conceptos")
        state = parse_yaml_field(content, "estado")
        proxima_reintento = parse_yaml_field(content, "proxima_reintento")
        proxima_legacy = parse_yaml_field(content, "proxima_revision")
        tiene_error = parse_yaml_field(content, "tiene_error") == "true"
        
        # Extraer enunciado original (imagen/pdf)
        enunciado_asset = parse_yaml_field(content, "enunciado_asset")
        if not enunciado_asset:
            asset_match = re.search(r'!\[\[(asset_.*?)\]\]', content)
            if asset_match:
                enunciado_asset = asset_match.group(1)
            else:
                asset_match = re.search(r'\[\[(asset_.*?)\|', content)
                if asset_match:
                    enunciado_asset = asset_match.group(1)
        
        # Extraer enunciado transcrito en LaTeX
        enunciado_match = re.search(r'## Enunciado del Problema\s*\n(.*?)(?:\n---|\n##|$)', content, re.DOTALL)
        enunciado = enunciado_match.group(1).strip() if enunciado_match else ""
        
        # Buscar los intentos asociados
        data = generar_dashboard.scan_vault()
        intentos = []
        for i in data["intentos"]:
            if i["ejercicio"] == exerc_id:
                # Leer detalles del intento
                attempt_file = f"{config.INTENTOS_DIR}/{i['id']}.md"
                if os.path.exists(attempt_file):
                    with open(attempt_file, 'r', encoding='utf-8') as af:
                        a_content = af.read()
                    
                    transcripcion_match = re.search(r'## Transcripción Literal de la Solución .*?\n```latex\n(.*?)\n```', a_content, re.DOTALL)
                    transcripcion = transcripcion_match.group(1).strip() if transcripcion_match else ""
                    
                    analisis_match = re.search(r'### Evaluación Pedagógica\s*\n(.*?)(?:\n###|\n---|\n##|$)', a_content, re.DOTALL)
                    analisis = analisis_match.group(1).strip() if analisis_match else ""
                    
                    # Extraer imágenes del manuscrito
                    imagenes = re.findall(r'!\[\[(asset_.*?\.(?:jpg|jpeg|png|webp))\]\]', a_content)
                    
                    intentos.append({
                        "id": i["id"],
                        "fecha": i["fecha"],
                        "resultado": i["resultado"],
                        "tiene_error": i["tiene_error"],
                        "transcripcion": transcripcion,
                        "analisis": analisis,
                        "imagenes": imagenes
                    })
                    
        return jsonify({
            "id": id_ex,
            "asignatura": subj,
            "tema": topic,
            "conceptos": concepts,
            "estado": state,
            "proxima_reintento": proxima_reintento,
            "proxima_revision_legacy": proxima_legacy,
            # Alias de lectura para clientes antiguos; ya no expone la fecha
            # antigua como si fuera una tarea pendiente.
            "proxima_revision": proxima_reintento,
            "tiene_error": tiene_error,
            "enunciado": enunciado,
            "enunciado_asset": enunciado_asset,
            "intentos": sorted(intentos, key=lambda x: x["fecha"], reverse=True)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_vault():
    try:
        query = request.args.get("q", "")
        if not query:
            return jsonify({"results": ""})
        handoff = buscar_web.prepare_search_handoff(query)
        return jsonify({"mode": "gemini_web", **handoff})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/import', methods=['POST'])
def import_search_result():
    """Recibe y renderiza localmente la respuesta pegada desde Gemini Web."""
    try:
        payload = request.get_json(silent=True) or {}
        query = str(payload.get("query", "")).strip()
        markdown_result = str(payload.get("markdown") or payload.get("respuesta") or "").strip()
        if not markdown_result:
            return jsonify({"error": "Pega primero la respuesta Markdown de Gemini Web."}), 400
        if len(markdown_result) > 200_000:
            return jsonify({"error": "La respuesta de Gemini es demasiado grande."}), 413

        buscar_web.HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        result_path = buscar_web.HANDOFF_DIR / f"busqueda_{stamp}_resultado.md"
        result_path.write_text(markdown_result, encoding="utf-8")
        return jsonify({
            "mode": "gemini_web_result",
            "query": query,
            "markdown": buscar_web._strip_fences(markdown_result),
            "html": buscar_web.markdown_to_html(markdown_result),
            "result_path": str(result_path),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def parse_yaml_field(content: str, field_name: str) -> str:
    match = re.search(rf'^{field_name}:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else ""

def parse_yaml_list(content: str, field_name: str) -> list[str]:
    pattern = rf'^{field_name}:\s*\n((?:\s*-\s*.*?\n)+)'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        inline_match = re.search(rf'^{field_name}:\s*\[(.*?)\]', content, re.MULTILINE)
        if inline_match:
            items = [i.strip().strip('"').strip("'") for i in inline_match.group(1).split(',')]
            return [i for i in items if i]
        return []
    lines = match.group(1).strip().split('\n')
    items = []
    for line in lines:
        item = re.sub(r'^\s*-\s*', '', line).strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items

def remove_exercise_link_from_indices(exerc_id: str, asignatura: str, tema: str):
    import file_manager
    subject_slug = file_manager.slugify(asignatura)
    topic_slug = file_manager.slugify(tema)
    subject_file = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{subject_slug}.md"
    topic_file = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{topic_slug}/{topic_slug}.md"
    
    for filepath in [subject_file, topic_file]:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            new_lines = [l for l in lines if f"[[{exerc_id}]]" not in l]
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))

@app.route('/api/exercise/<exerc_id>/edit', methods=['POST'])
def edit_exercise(exerc_id):
    import shutil
    try:
        data = request.get_json()
        new_subj = data.get("asignatura")
        new_topic = data.get("tema")
        new_concepts = data.get("conceptos", [])
        new_state = data.get("estado", "nuevo")
        new_proxima = data.get("proxima_reintento")
        if new_proxima is None:
            new_proxima = data.get("proxima_revision", "")
        new_enunciado = data.get("enunciado", "")
        
        # Locate the current file
        target_path = None
        for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
            if f"{exerc_id}.md" in files:
                target_path = os.path.join(root, f"{exerc_id}.md")
                break
                
        if not target_path or not os.path.exists(target_path):
            return jsonify({"error": f"Ejercicio {exerc_id} no encontrado"}), 404
            
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        old_subj = parse_yaml_field(content, "asignatura")
        old_topic = parse_yaml_field(content, "tema")
        old_enunciado_asset = parse_yaml_field(content, "enunciado_asset")
        old_tiene_error = parse_yaml_field(content, "tiene_error") == "true"
        old_nodos = parse_yaml_list(content, "nodos")
        old_tipo_recurso = parse_yaml_field(content, "tipo_recurso") or "ejercicio"
        old_origen = parse_yaml_field(content, "origen")
        old_fecha_origen = parse_yaml_field(content, "fecha_origen")
        
        # If subject or topic changed, move the file
        if new_subj != old_subj or new_topic != old_topic:
            new_exerc_dir = file_manager.ensure_subject_topic_dirs(new_subj, new_topic)
            file_manager.ensure_topic_note(new_subj, new_topic)
            new_path = os.path.join(new_exerc_dir, f"{exerc_id}.md")
            
            # Clean links in old indices
            remove_exercise_link_from_indices(exerc_id, old_subj, old_topic)
            
            # Move the file physically
            shutil.move(target_path, new_path)
            target_path = new_path
            
            # Link to new indices
            file_manager.link_exercise_to_indices(exerc_id, new_subj, new_topic)
            
        # Extract the attempts list from the old file to preserve history
        attempts_match = re.search(r'<!-- intentos_inicio -->\s*\n(.*?)\n\s*<!-- intentos_fin -->', content, re.DOTALL)
        attempts_content = attempts_match.group(1).strip() if attempts_match else "*No se han registrado intentos aún.*"
        
        # Also, check if there was a warning callout in the body
        warning_match = re.search(r'> \[\!WARNING\]\s*\n>\s*\*\*PROBLEMA EN ESTE ARCHIVO, REVISAR:\*\*\s*(.*?)\n', content)
        warning_transcripcion = warning_match.group(1).strip() if warning_match else ""
        
        # Make sure concept notes are created
        for concept in new_concepts:
            file_manager.ensure_concept_note(concept)
            
        # Render the template
        new_markdown = templates.render_exercise_template(
            exerc_id=exerc_id,
            asignatura=new_subj,
            tema=new_topic,
            conceptos=new_concepts,
            tiene_error=old_tiene_error,
            enunciado_asset=old_enunciado_asset,
            enunciado_transcrito=new_enunciado,
            attempt_id="", # Inject attempts manually below
            estado=new_state,
            proxima_reintento=new_proxima,
            tipo_recurso=old_tipo_recurso,
            origen=old_origen,
            fecha_origen=old_fecha_origen,
            warning_transcripcion=warning_transcripcion,
            nodos=old_nodos
        )
        
        # Inject attempts back
        new_markdown = re.sub(
            r'<!-- intentos_inicio -->\s*\n.*?\n\s*<!-- intentos_fin -->',
            f'<!-- intentos_inicio -->\n{attempts_content}\n<!-- intentos_fin -->',
            new_markdown,
            flags=re.DOTALL
        )
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_markdown)
            
        generar_dashboard.run()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/exercise/<exerc_id>', methods=['DELETE'])
def delete_exercise(exerc_id):
    try:
        # Buscar el ejercicio
        target_path = None
        for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
            if f"{exerc_id}.md" in files:
                target_path = os.path.join(root, f"{exerc_id}.md")
                break
                
        if not target_path or not os.path.exists(target_path):
            return jsonify({"error": f"Ejercicio {exerc_id} no encontrado"}), 404
            
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        subj = parse_yaml_field(content, "asignatura")
        topic = parse_yaml_field(content, "tema")
        
        # Eliminar archivo físico
        os.remove(target_path)
        
        # Eliminar enlaces de los índices
        remove_exercise_link_from_indices(exerc_id, subj, topic)
        
        # Regenerar dashboard
        generar_dashboard.run()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/exercise/<exerc_id>/review', methods=['POST'])
def review_exercise(exerc_id):
    try:
        data = request.get_json(silent=True) or {}
        rating = data.get("rating") # 'facil', 'duda', 'fallo'
        try:
            calidad = repeticion.calidad_de_rating(rating)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        
        # Buscar la nota del ejercicio
        target_path = None
        for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
            if f"{exerc_id}.md" in files:
                target_path = os.path.join(root, f"{exerc_id}.md")
                break
                
        if not target_path or not os.path.exists(target_path):
            return jsonify({"error": f"Ejercicio {exerc_id} no encontrado"}), 404
            
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        current_state = parse_yaml_field(content, "estado") or "nuevo"
        new_state = repeticion.estado_ejercicio(current_state, calidad)
        next_retry = repeticion.fecha_reintento(calidad)
        
        # El estado del ejercicio y la cola de reintento son metadatos locales;
        # no son la agenda académica del sistema.
        content = re.sub(r'^estado:\s*\w+', f'estado: {new_state}', content, flags=re.MULTILINE)
        retry_line = f'proxima_reintento: {next_retry}'
        if re.search(r'^proxima_reintento:', content, flags=re.MULTILINE):
            content = re.sub(r'^proxima_reintento:.*$', retry_line, content, flags=re.MULTILINE)
        elif re.search(r'^proxima_revision:', content, flags=re.MULTILINE):
            # Migración perezosa: al tocar una nota antigua se sustituye el
            # campo ambiguo por el campo explícito de reintento local.
            content = re.sub(r'^proxima_revision:.*$', retry_line, content, flags=re.MULTILINE)
        else:
            content = re.sub(r'^(fecha_creacion:.*)$', r'\1\n' + retry_line, content,
                             flags=re.MULTILINE, count=1)
        
        # Actualizar el resumen visible de la nota.
        resumen = (
            f'- **Estado del ejercicio:** `{new_state.upper()}`\n'
            f'- **Reintento local:** `{next_retry or "no programado"}`'
        )
        content = re.sub(
            r'- \*\*(?:Estado de Repaso|Estado del ejercicio):\*\*.*(?:\n- \*\*Reintento local:\*\*.*)?',
            resumen,
            content,
        )

        mensajes_kg = []
        nodos_kg = parse_yaml_list(content, "nodos")
        if not nodos_kg:
            subj = parse_yaml_field(content, "asignatura")
            conceptos = [re.sub(r'[\[\]"]', '', c) for c in parse_yaml_list(content, "conceptos")]
            nodos_kg = kg_perfil.resolver_conceptos(subj, conceptos)
        if nodos_kg:
            mensajes_kg = kg_perfil.registrar_y_guardar(
                nodos_kg,
                calidad >= 0.5,
                origen=f'autoeval:{exerc_id}',
                calidad=calidad,
            )

        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        generar_dashboard.run()

        return jsonify({
            "success": True,
            "new_state": new_state,
            "proxima_reintento": next_retry,
            # Alias de respuesta para clientes antiguos; no es fecha
            # académica y desaparecerá cuando se retire la interfaz antigua.
            "proxima_revision": next_retry,
            "calidad": calidad,
            "nodos_actualizados": nodos_kg,
            "mensajes_kg": mensajes_kg,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================================
# KNOWLEDGE GRAPH: perfil, plan de estudio, exámenes, mapa y banco
# =====================================================================
import sys
import json as _json

KG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_graph')
if KG_DIR not in sys.path:
    sys.path.insert(0, KG_DIR)
import perfil as kg_perfil
import gamificacion as kg_gamificacion
import planificar as kg_planificar
import problemas as kg_problemas

@app.route('/kg/mapa')
def kg_mapa():
    return send_from_directory(KG_DIR, 'mapa_conocimiento.html')

@app.route('/api/kg/plan', methods=['GET'])
def kg_plan():
    try:
        fecha = request.args.get('fecha')
        minutos = request.args.get('minutos', type=int)
        energia = request.args.get('energia', type=int)
        foco = request.args.get('foco', type=int)
        materia_forzada = request.args.get('materia') or None
        hoy = datetime.strptime(fecha, '%Y-%m-%d').date() if fecha else None
        r = kg_planificar.calcular(hoy=hoy, minutos=minutos, energia=energia, foco=foco, materia_forzada=materia_forzada)
        if not fecha:
            kg_planificar.guardar_plan(r['md'])
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/study/prepare', methods=['GET'])
def study_prepare():
    """Devuelve el plan enriquecido con preview, PACER y el estado RAIL."""
    try:
        fecha = request.args.get('fecha')
        minutos = request.args.get('minutos', type=int)
        energia = request.args.get('energia', type=int)
        foco = request.args.get('foco', type=int)
        hoy = datetime.strptime(fecha, '%Y-%m-%d').date() if fecha else None
        calculo = kg_planificar.calcular(hoy=hoy, minutos=minutos, energia=energia, foco=foco)
        nodos = kg_perfil.cargar_grafos()
        perfil_d = kg_perfil.cargar_perfil()
        return jsonify({
            'plan': calculo['plan'],
            'viabilidad': calculo['viabilidad'],
            'minutos': calculo['minutos'],
            'preview': study_flow.build_preview(calculo['plan'], nodos, perfil_d),
            'skill': study_flow.rail_snapshot(),
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/walk/prepare', methods=['GET'])
def study_walk_prepare():
    """Prepara el contexto del paseo/bus, respetando la asignatura elegida."""
    try:
        mode = request.args.get('mode', 'walk_review')
        if mode not in study_flow.WALK_MODES:
            return jsonify({'error': 'Tipo de paseo no válido'}), 400
        fecha = request.args.get('fecha')
        minutos = request.args.get('minutos', type=int)
        materia_forzada = request.args.get('materia') or None
        if not materia_forzada:
            return jsonify({'error': 'Elige primero una asignatura; el paseo no selecciona una automáticamente.'}), 400
        pack = study_context.build_study_pack(
            materia=materia_forzada,
            minutos=minutos or 60,
            objetivo=(
                'cuestiones y ejercicios; teoría solo para cubrir huecos'
                if materia_forzada.strip().casefold() == 'electromagnetismo'
                else 'microteoría y ejercicios'
            ),
        )
        preview = pack.get('nodes', [])
        context = {'available_minutes': minutos or 60, 'materia': materia_forzada}
        note_context = apuntes.context_for_nodes([item.get('id') for item in preview])
        return jsonify({
            'mode': mode,
            'mode_info': study_flow.walk_mode_info(mode),
            'materia': materia_forzada,
            'preview': preview,
            'problem_ids': pack.get('problem_ids', []),
            'minutos': context['available_minutes'],
            'prompt': study_flow.build_walk_prompt(mode, context, preview, note_context=note_context),
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


def _apply_walk_report(session_id, report):
    """Cierra una vez el paseo y aplica sus valoraciones conservadoras al grafo."""
    session = study_flow.get_session(session_id)
    if session.get('status') == 'completed':
        return session, []
    session = study_flow.finish_walk_session(session_id, report)
    applied = []
    seen = set()
    for item in session.get('walk_report', {}).get('nodos', []):
        node_id = item.get('id')
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)
        quality = min(0.85, max(0.0, float(item.get('calidad', 0))))
        exito = quality >= 0.5
        mensajes = kg_perfil.registrar_y_guardar(
            [node_id], exito, origen='paseo_voz', calidad=quality
        )
        applied.append({'id': node_id, 'calidad': quality, 'exito': exito, 'mensajes': mensajes})
    try:
        graph_nodes = kg_perfil.cargar_grafos()
        note_result = apuntes.apply_walk_report(
            session, session.get('walk_report', {}), graph_nodes
        )
        # La generación es local y solo escribe los nodos recién trabajados.
        latex_files = []
        pdf_files = []
        for materia in note_result.get('subjects', []):
            generated = apuntes.generate(materia, graph_nodes)
            latex_files.extend(generated.get('files', []))
            pdf_files.extend(generated.get('pdf_files', []))
        session['apuntes'] = {**note_result, 'latex_files': latex_files, 'pdf_files': pdf_files}
        session['latex_files'] = latex_files
        session['pdf_files'] = pdf_files
    except Exception as exc:
        # Un fallo de LaTeX/apuntes nunca debe impedir cerrar el paseo ni actualizar el grafo.
        session['apuntes_error'] = str(exc)
    return session, applied


@app.route('/api/study/walks/<session_id>/remote-instructions', methods=['GET'])
def study_walk_remote_instructions(session_id):
    """Prepara el encargo del paseo para Remote o para un cierre manual."""
    try:
        session = study_flow.get_session(session_id)
        if session.get('session_type') not in study_flow.WALK_MODES:
            return jsonify({'error': 'La sesión indicada no es un paseo de voz'}), 400
        pack = study_context.build_study_pack(
            materia=session.get('materia', ''),
            minutos=session.get('context', {}).get('available_minutes', 60),
            objetivo=session.get('context', {}).get('goal', 'microteoría y ejercicios'),
            session=session,
        )
        preview = pack.get('nodes', [])
        transport = request.args.get('transport', 'remote').strip().lower()
        use_remote_file = transport != 'notebooklm'
        report_path = study_flow.walk_report_path(session_id) if use_remote_file else None
        note_context = apuntes.context_for_nodes(session.get('plan_ids', []))
        prompt = study_flow.build_walk_prompt(
            session['session_type'], session.get('context', {}), preview,
            report_path=report_path, note_context=note_context
        )
        if use_remote_file:
            study_flow.save_active_walk_context(session, prompt, report_path)
        return jsonify({'transport': transport, 'prompt': study_flow.build_walk_prompt(
            session['session_type'], session.get('context', {}), preview,
            report_path=report_path, note_context=note_context
        ), 'report_path': report_path, 'active_context_path': study_flow.ACTIVE_WALK_PATH if use_remote_file else None})
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/walks/<session_id>/status', methods=['GET'])
def study_walk_status(session_id):
    """Importa automáticamente el cierre que Work Remote deja en el proyecto."""
    try:
        session = study_flow.get_session(session_id)
        if session.get('status') == 'completed':
            return jsonify({'ready': True, 'session': session, 'applied': []})
        report_path = study_flow.walk_report_path(session_id)
        if not os.path.exists(report_path):
            return jsonify({'ready': False})
        if os.path.getsize(report_path) > 200 * 1024:
            return jsonify({'error': 'El informe remoto es demasiado grande'}), 400
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        if not isinstance(report, dict):
            return jsonify({'error': 'El informe remoto debe ser un objeto JSON'}), 400
        session, applied = _apply_walk_report(session_id, report)
        return jsonify({'ready': True, 'session': session, 'applied': applied, 'insights': study_flow.insights()})
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return jsonify({'error': f'No se pudo leer el informe remoto: {exc}'}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/sessions', methods=['POST'])
def study_start_session():
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get('plan_ids'), list) or not data['plan_ids']:
            return jsonify({'error': 'La sesión necesita al menos un nodo del plan.'}), 400
        return jsonify({'success': True, 'session': study_flow.start_session(data)})
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/sessions/<session_id>/events', methods=['POST'])
def study_session_event(session_id):
    try:
        data = request.get_json(silent=True) or {}
        return jsonify({'success': True, 'event': study_flow.record_event(session_id, data)})
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/sessions/<session_id>/finish', methods=['POST'])
def study_finish_session(session_id):
    try:
        data = request.get_json(silent=True) or {}
        return jsonify({'success': True, 'session': study_flow.finish_session(session_id, data), 'insights': study_flow.insights()})
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/walks/<session_id>/close', methods=['POST'])
def study_close_walk(session_id):
    """Recibe solo el informe final de voz y aplica sus valoraciones al grafo."""
    try:
        data = request.get_json(silent=True) or {}
        report = data.get('report', data)
        session, applied = _apply_walk_report(session_id, report)
        return jsonify({
            'success': True,
            'session': session,
            'applied': applied,
            'insights': study_flow.insights(),
        })
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/insights', methods=['GET'])
def study_insights():
    return jsonify(study_flow.insights())


@app.route('/api/apuntes', methods=['GET'])
def apuntes_estado():
    """Estado de los apuntes personales, sin exponer el contenido en la interfaz."""
    return jsonify(apuntes.summary())


@app.route('/api/apuntes/generar', methods=['POST'])
def apuntes_generar():
    """Regenera el LaTeX de una asignatura o de todo el grafo."""
    try:
        data = request.get_json(silent=True) or {}
        materia = data.get('materia') or None
        graph_nodes = kg_perfil.cargar_grafos()
        return jsonify({'success': True, **apuntes.generate(materia, graph_nodes)})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/work/start', methods=['POST'])
def study_work_start():
    """Abre una sesión desde una tarjeta de asignatura para usarla en Work."""
    try:
        data = request.get_json(silent=True) or {}
        materia = str(data.get('materia', '')).strip()
        if not materia:
            return jsonify({'error': 'Selecciona una asignatura para iniciar la sesión.'}), 400
        study_context.auto_import_ready_work_report()
        active = study_context.active_study_status()
        if active.get('active'):
            return jsonify({
                'error': f"Ya hay una sesión activa de {active.get('materia') or 'otra asignatura'}. Cierra esa sesión antes de iniciar otra."
            }), 409
        pack = study_context.build_study_pack(
            materia=materia,
            minutos=data.get('available_minutes', data.get('minutos', 60)),
            objetivo=data.get('goal', data.get('objetivo', 'aprender')),
            node_ids=data.get('node_ids'),
        )
        if not pack.get('plan_ids'):
            return jsonify({'error': 'No hay conceptos seleccionables para iniciar esta sesión todavía.'}), 400
        session = study_flow.start_session({
            'session_type': 'work_guided',
            'materia': materia,
            'plan_ids': pack['plan_ids'],
            'problem_ids': pack.get('problem_ids', []),
            'available_minutes': pack['session']['available_minutes'],
            'goal': pack['session']['goal'],
            'energy': data.get('energy', 3),
            'focus': data.get('focus', 3),
            'obstacle': data.get('obstacle', ''),
            'preview_ack': True,
        })
        pack = study_context.build_study_pack(
            materia=materia,
            minutos=pack['session']['available_minutes'],
            objetivo=pack['session']['goal'],
            session=session,
        )
        study_context.reset_active_study_report()
        study_context.save_active_study_context(pack)
        return jsonify({'success': True, 'session': session, 'pack': pack, 'prompt': pack['prompt']})
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/work/status', methods=['GET'])
def study_work_status():
    try:
        auto_import = study_context.auto_import_ready_work_report()
        status = study_context.active_study_status()
        if auto_import.get('imported'):
            status['auto_imported'] = True
            _schedule_context_snapshot()
        elif auto_import.get('error'):
            status['auto_import_error'] = auto_import['error']
        return jsonify(status)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/work/context', methods=['GET'])
def study_work_context():
    try:
        context = study_context.load_active_study_context()
        if not context:
            return jsonify({'error': 'No hay una sesión de Work preparada.'}), 404
        return jsonify(context)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/work/report', methods=['GET'])
def study_work_report():
    try:
        status = study_context.active_study_status()
        if not status.get('report_ready'):
            return jsonify({'error': 'Todavía no hay un cierre de Work listo para importar.'}), 404
        return jsonify(study_context.load_active_study_report())
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/work/finish', methods=['POST'])
def study_work_finish():
    """Importa el informe final que Work escribe en el buzón de la sesión."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = str(data.get('session_id', '')).strip()
        report = data.get('report')
        if not session_id and isinstance(report, dict):
            session_id = str(report.get('session_id', '')).strip()
        if not session_id:
            return jsonify({'error': 'Falta el identificador de la sesión.'}), 400
        if report is None:
            report = data
        return jsonify({'success': True, **study_context.finish_work_report(session_id, report)})
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


def _context_bool(value, default=True):
    """Interpreta flags de query/body sin que ``bool('false')`` dé True."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {'0', 'false', 'no', 'off'}


@app.route('/api/context/summary', methods=['GET'])
def context_summary():
    """Resumen ligero para saber qué contexto está disponible."""
    try:
        return jsonify(study_context.context_summary())
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/context', methods=['GET'])
def get_context():
    """Entrega el contexto vivo completo o una selección por asignatura/nodos.

    ``format=md`` devuelve un documento autónomo para adjuntarlo a ChatGPT o
    Gemini. La respuesta JSON conserva la misma información de forma
    estructurada y es la opción recomendada para futuras integraciones.
    """
    try:
        materia = request.args.get('materia') or None
        node_ids = [item.strip() for item in request.args.get('nodos', '').split(',') if item.strip()]
        include_documents = _context_bool(request.args.get('include_documents'), True)
        context = study_context.build_context(
            materia=materia,
            node_ids=node_ids or None,
            include_documents=include_documents,
        )
        formato = (request.args.get('format') or 'json').strip().lower()
        if formato in {'md', 'markdown'}:
            body = study_context.context_to_markdown(context)
            response = app.response_class(body, mimetype='text/markdown')
            if _context_bool(request.args.get('download'), False):
                response.headers['Content-Disposition'] = 'attachment; filename="contexto_ia.md"'
            return response

        body = json.dumps(context, ensure_ascii=False, indent=2)
        response = app.response_class(body, mimetype='application/json')
        if _context_bool(request.args.get('download'), False):
            response.headers['Content-Disposition'] = 'attachment; filename="contexto_ia.json"'
        return response
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/context/export', methods=['GET', 'POST'])
def export_context():
    """Actualiza las dos copias portables del contexto en knowledge_graph."""
    try:
        payload = request.get_json(silent=True) or {} if request.method == 'POST' else {}
        materia = payload.get('materia') or request.args.get('materia') or None
        raw_ids = payload.get('node_ids', payload.get('nodos', request.args.get('nodos', '')))
        if isinstance(raw_ids, str):
            node_ids = [item.strip() for item in raw_ids.split(',') if item.strip()]
        elif isinstance(raw_ids, list):
            node_ids = [str(item).strip() for item in raw_ids if str(item).strip()]
        else:
            node_ids = None
        include_documents = _context_bool(
            payload.get('include_documents', request.args.get('include_documents')),
            True,
        )
        return jsonify(study_context.export_context(
            materia=materia,
            node_ids=node_ids,
            include_documents=include_documents,
        ))
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/context/events', methods=['POST'])
def apply_context_event():
    """Recibe una actualización estructurada de un tutor externo."""
    try:
        event = request.get_json(silent=True) or {}
        result = study_context.apply_event(event)
        return jsonify({
            'success': True,
            'event': result,
            'context_summary': study_context.context_summary(),
        })
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    except (TypeError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/study/pacer', methods=['POST'])
def study_pacer_override():
    try:
        data = request.get_json(silent=True) or {}
        if not data.get('node_id'):
            return jsonify({'error': 'Falta node_id'}), 400
        return jsonify({'success': True, 'pacer': study_flow.set_pacer_override(data['node_id'], data.get('code'))})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/kg/examenes', methods=['GET', 'POST'])
def kg_examenes():
    ruta = os.path.join(KG_DIR, 'examenes.json')
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not isinstance(data, dict) or 'examenes' not in data:
                return jsonify({"error": "Formato inválido: falta 'examenes'"}), 400
            for ex in data['examenes']:
                oficial = datetime.strptime(ex['fecha'], '%Y-%m-%d')
                if ex.get('fecha_preparacion'):
                    preparacion = datetime.strptime(ex['fecha_preparacion'], '%Y-%m-%d')
                    if preparacion > oficial:
                        raise ValueError('La fecha de preparación no puede ser posterior al examen')
            data['examenes'] = [kg_planificar.normalizar_examen(ex) for ex in data['examenes']]
            with open(ruta, 'w', encoding='utf-8') as f:
                _json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"success": True})
        with open(ruta, 'r', encoding='utf-8') as f:
            data = _json.load(f)
        data['examenes'] = [kg_planificar.normalizar_examen(ex) for ex in data.get('examenes', [])]
        return jsonify(data)
    except ValueError as e:
        return jsonify({"error": f"Fecha inválida (usa YYYY-MM-DD): {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/cuadernos', methods=['GET', 'POST'])
def kg_cuadernos():
    ruta = os.path.join(KG_DIR, 'cuadernos_gemini.json')
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            if not isinstance(data, dict):
                return jsonify({'error': 'Formato inválido: se espera un objeto'}), 400
            with open(ruta, 'w', encoding='utf-8') as f:
                _json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True})
        if not os.path.exists(ruta):
            return jsonify({})
        with open(ruta, 'r', encoding='utf-8') as f:
            return jsonify(_json.load(f))
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/cuadernos/abrir_materiales', methods=['POST'])
def cuadernos_abrir_materiales():
    try:
        import subprocess
        data = request.get_json(silent=True) or {}
        materia = data.get('materia', '')
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CUADERNOS_GEMINI_STUDY'))
        carpeta = None
        ruta_cfg = os.path.join(KG_DIR, 'cuadernos_gemini.json')
        if os.path.exists(ruta_cfg):
            with open(ruta_cfg, 'r', encoding='utf-8') as f:
                cfg = _json.load(f)
                if materia in cfg:
                    carpeta = cfg[materia].get('carpeta_materiales')
        target = os.path.join(base_dir, carpeta) if carpeta else base_dir
        if not os.path.exists(target):
            target = base_dir
        subprocess.Popen(f'explorer "{target}"')
        return jsonify({'success': True, 'path': target})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/biblioteca/resolver', methods=['POST'])
def biblioteca_resolver():
    try:
        data = request.get_json(silent=True) or {}
        nodo_id = data.get('nodo_id')
        problema_id = data.get('problema_id')
        calidad = float(data.get('calidad', 1.0))
        exito = calidad >= 0.5
        segundos = data.get('segundos')
        comentarios = data.get('comentarios', '').strip()
        if segundos is not None:
            try:
                segundos = float(segundos)
            except (TypeError, ValueError):
                segundos = None

        if not nodo_id and not problema_id:
            return jsonify({'error': 'Falta nodo_id o problema_id'}), 400

        if problema_id:
            # El problema conoce todos sus nodos requeridos. Así una resolución
            # no actualiza solo el nodo que abrió la tarjeta, sino el conjunto
            # completo que debe quedar demostrado.
            perfil = kg_perfil.cargar_perfil()
            resultado = kg_problemas.registrar_feedback(
                perfil, kg_perfil.cargar_grafos(), kg_problemas.cargar_banco(), problema_id,
                veredicto=data.get('veredicto'), calidad=calidad,
                comentarios=comentarios, segundos=segundos,
                origen='biblioteca_silencio',
            )
            kg_perfil.guardar_perfil(perfil)
        elif nodo_id:
            kg_perfil.registrar_y_guardar([nodo_id], exito, origen='biblioteca_silencio',
                                          segundos=segundos, calidad=calidad)

        return jsonify({'success': True, 'mensaje': 'Resolución en biblioteca guardada en el grafo.'})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/kg/perfil', methods=['GET'])
def kg_perfil_estado():
    try:
        nodos = kg_perfil.cargar_grafos()
        perfil_d = kg_perfil.cargar_perfil()
        from datetime import date as _date
        hoy = _date.today()
        por_materia = {}
        for nid, n in nodos.items():
            e = por_materia.setdefault(n['materia'], {'materia': n['materia'], 'curso': n['curso'],
                                                      'total': 0, 'practicados': 0, 'suma': 0.0})
            e['total'] += 1
            d = kg_perfil.dominio_efectivo(perfil_d['nodos'].get(nid), hoy)
            e['suma'] += d
            if perfil_d['nodos'].get(nid, {}).get('dominio', 0) > 0:
                e['practicados'] += 1
        materias = []
        for e in por_materia.values():
            e['dominio_medio'] = round(e['suma'] / e['total'], 3)
            del e['suma']
            materias.append(e)
        materias.sort(key=lambda x: (x['curso'], x['materia']))
        return jsonify({
            'materias': materias,
            'vencidos': kg_perfil.vencidos(perfil_d, nodos)[:30],
            'frontera': kg_perfil.frontera(perfil_d, nodos)[:30],
            'problemas': kg_problemas.resumen_para_plan(
                perfil_d, nodos, kg_problemas.cargar_banco(), limite=12
            ),
            'retroalimentacion': kg_problemas.debilidades(perfil_d, nodos, limite=12),
            'gamificacion': kg_gamificacion.estado(perfil_d, hoy),
            'objetivo_academico': perfil_d.get('objetivo_academico', {
                'meta': 'Matrícula de Honor (10.0) en todas las asignaturas',
                'modo_evaluacion': 'maxima_exigencia_tribunal'
            })
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/gamificacion', methods=['GET', 'POST'])
def kg_gamificacion_estado():
    try:
        perfil_d = kg_perfil.cargar_perfil()
        if request.method == 'POST':
            meta = (request.get_json() or {}).get('meta_diaria')
            if meta is not None:
                kg_gamificacion._bloque(perfil_d)['meta_diaria'] = max(10, int(meta))
                kg_perfil.guardar_perfil(perfil_d)
        return jsonify(kg_gamificacion.estado(perfil_d))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/registrar', methods=['POST'])
def kg_registrar():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        exito = bool(data.get('exito', True))
        # segundos: tiempo real empleado si viene de un quiz cronometrado (mueve la
        # fluidez vs. la referencia del nodo); ausente/None si no está cronometrado.
        segundos = data.get('segundos', None)
        if segundos is not None:
            try:
                segundos = float(segundos)
            except (TypeError, ValueError):
                segundos = None
        # calidad: escala graduada 0–1 (resuelto/desliz/a_medias/bloqueado/en_blanco).
        # Si viene, el motor deriva de ella el éxito y modula ganancia/decaimiento.
        calidad = data.get('calidad', None)
        if calidad is not None:
            try:
                calidad = float(calidad)
            except (TypeError, ValueError):
                calidad = None
        if not ids:
            return jsonify({"error": "Faltan ids de nodos"}), 400
        mensajes = kg_perfil.registrar_y_guardar(ids, exito, origen='web',
                                                 segundos=segundos, calidad=calidad)
        return jsonify({"success": True, "mensajes": mensajes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/inbox', methods=['POST'])
def kg_inbox():
    try:
        f = request.files.get('file')
        if not f or not f.filename:
            return jsonify({"error": "No se recibió ningún archivo"}), 400
        nombre = os.path.basename(f.filename)
        destino = os.path.join(config.INBOX_DIR, nombre)
        f.save(destino)
        return jsonify({"success": True, "mensaje": f"'{nombre}' guardado en el Inbox. El watcher lo procesará en segundos."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/banco', methods=['GET', 'POST'])
def kg_banco():
    try:
        if request.method == 'GET':
            ruta = os.path.join(KG_DIR, 'banco_problemas.json')
            if not os.path.exists(ruta):
                return jsonify({})
            with open(ruta, 'r', encoding='utf-8') as f:
                banco = _json.load(f)
            resumen = {m: {'problemas': len(b.get('problemas', [])), 'fuente': b.get('fuente', '')}
                       for m, b in banco.items()}
            return jsonify(resumen)
        # POST: subir un MD de hojas de problemas y clasificarlo
        f = request.files.get('file')
        grafo = request.form.get('grafo', 'electromagnetismo.json')
        if not f or not f.filename:
            return jsonify({"error": "No se recibió el archivo MD"}), 400
        ruta_grafo = os.path.join(KG_DIR, os.path.basename(grafo))
        if not os.path.exists(ruta_grafo):
            return jsonify({"error": f"Grafo '{grafo}' no encontrado"}), 400
        destino = os.path.join(KG_DIR, '_subidas')
        os.makedirs(destino, exist_ok=True)
        ruta_md = os.path.join(destino, os.path.basename(f.filename))
        f.save(ruta_md)
        import clasificar_problemas as kg_clasificar
        resultado = kg_clasificar.procesar(ruta_md, ruta_grafo, con_ia=True)
        return jsonify({"success": True, **resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/correcciones', methods=['GET', 'DELETE'])
def kg_correcciones():
    """Correcciones de Gemini para verlas en la app (Obsidian queda como registro)."""
    try:
        import correcciones as kg_corr
        if request.method == 'DELETE':
            data = request.get_json(silent=True) or {}
            idx = data.get('index')
            if idx is None:
                kg_corr.guardar([])            # limpiar todas
            else:
                entradas = kg_corr.cargar()
                if 0 <= idx < len(entradas):
                    del entradas[idx]
                    kg_corr.guardar(entradas)
            return jsonify({"success": True})
        return jsonify({"correcciones": kg_corr.cargar()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/correcciones/revertir', methods=['POST'])
def kg_correcciones_revertir():
    """Marca una corrección como MAL CORREGIDA: deshace su efecto en el perfil
    (dominio/repasos/XP) y la quita de la lista. Para cuando Gemini se equivoca."""
    try:
        import correcciones as kg_corr
        data = request.get_json(silent=True) or {}
        corr_id = data.get('id')
        if not corr_id:
            return jsonify({"error": "Falta el id de la corrección"}), 400
        res = kg_corr.revertir(corr_id)
        if not res.get("encontrado"):
            return jsonify({"error": "No se encontró la corrección"}), 404
        return jsonify({"success": True, "revertido": res.get("revertido", False)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/corregir', methods=['POST'])
def corregir_lo_nuevo():
    """Lanza en segundo plano el procesado de los archivos nuevos del Inbox."""
    try:
        import subprocess
        base = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(base, "corregir.py")
        if not os.path.exists(script):
            return jsonify({"error": "No se encontró corregir.py"}), 500
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen([sys.executable, script],
                         cwd=base, creationflags=creationflags,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({"success": True, "mensaje": "Procesando lo nuevo en segundo plano. Refresca en un par de minutos."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/voz', methods=['POST'])
def recibir_grabacion_voz():
    """Guarda una grabación del navegador y lanza su análisis Feynman en segundo plano."""
    try:
        archivo = request.files.get('audio')
        if not archivo or not archivo.filename:
            return jsonify({'error': 'No se recibió ninguna grabación.'}), 400
        extension = os.path.splitext(archivo.filename)[1].lower() or '.webm'
        if extension not in VOICE_EXTENSIONS:
            return jsonify({'error': f'Formato de audio no admitido: {extension}'}), 400
        os.makedirs(VOICE_DIR, exist_ok=True)
        job_id = uuid.uuid4().hex[:12]
        nombre = secure_filename(archivo.filename) or 'grabacion.webm'
        nombre = f"sesion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{job_id}_{nombre}"
        ruta = os.path.join(VOICE_DIR, nombre)
        archivo.save(ruta)
        _voice_jobs[job_id] = {
            'id': job_id,
            'estado': 'en_cola',
            'mensaje': 'Grabación recibida. Preparando el análisis…',
            'archivo': nombre,
            'modelo_requerido': config.GEMINI_REQUIRED_MODEL,
            'creado': datetime.now().isoformat(timespec='seconds'),
        }
        threading.Thread(target=_run_voice_job, args=(job_id, ruta), daemon=True).start()
        return jsonify({'success': True, 'job_id': job_id, 'mensaje': 'Grabación recibida. Whisper la está transcribiendo; después se abrirá Gemini.'})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/voz/<job_id>', methods=['GET'])
def estado_grabacion_voz(job_id):
    with _voice_jobs_lock:
        job = _voice_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'No encuentro ese análisis de voz.'}), 404
    return jsonify(job)


@app.route('/api/voz/<job_id>/gemini', methods=['POST'])
def importar_respuesta_gemini(job_id):
    """Recibe la respuesta copiada desde Gemini Web y la integra tras validarla."""
    with _voice_jobs_lock:
        job = _voice_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'No encuentro ese análisis de voz.'}), 404
    if job.get('estado') != 'esperando_gemini':
        return jsonify({'error': 'Este análisis no está esperando una respuesta de Gemini.'}), 409

    data = request.get_json(silent=True) or {}
    respuesta = str(data.get('respuesta', '')).strip()
    if not respuesta:
        return jsonify({'error': 'Pega primero la respuesta JSON de Gemini.'}), 400

    modelo_esperado = job.get('modelo_requerido') or config.GEMINI_REQUIRED_MODEL
    modelo_recibido = str(data.get('modelo', '')).strip()
    if data.get('modelo_verificado') is not True or modelo_recibido != modelo_esperado:
        return jsonify({
            'error': 'Modelo de Gemini no verificado.',
            'detalle': f'Comprueba que Gemini Web muestra exactamente «{modelo_esperado}» y vuelve a intentarlo.',
            'modelo_requerido': modelo_esperado,
        }), 409

    resultado = job.get('resultado')
    transcript_path = job.get('transcripcion')
    if not resultado or not transcript_path:
        return jsonify({'error': 'Faltan las rutas internas de este análisis.'}), 500
    try:
        os.makedirs(os.path.dirname(resultado), exist_ok=True)
        with open(resultado, 'w', encoding='utf-8') as f:
            f.write(respuesta)
        script = os.path.join(BASE_DIR, 'corregir_voz.py')
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        proc = subprocess.run(
            [sys.executable, script, '--importar-gemini', resultado, transcript_path,
             '--modelo', modelo_recibido],
            cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8',
            errors='replace', creationflags=creationflags,
        )
        if proc.returncode:
            detalle = (proc.stdout or proc.stderr or 'JSON no válido')[-1200:]
            _set_voice_job(job_id, estado='esperando_gemini', mensaje=f'Gemini devolvió un formato no válido: {detalle}')
            return jsonify({'error': 'La respuesta no tiene el formato esperado.', 'detalle': detalle}), 422
        _set_voice_job(
            job_id, estado='completado',
            mensaje='Corrección de Gemini terminada. El feedback y el grafo ya están actualizados.',
            salida=(proc.stdout or '')[-1200:],
        )
        return jsonify({'success': True, 'mensaje': 'Respuesta de Gemini validada e integrada.'})
    except Exception as exc:
        _set_voice_job(job_id, estado='error', mensaje=str(exc))
        return jsonify({'error': str(exc)}), 500

@app.route('/api/kg/quiz', methods=['GET'])
def kg_quiz():
    try:
        n = request.args.get('n', default=6, type=int)
        modo = request.args.get('modo', default='repaso')
        materia = request.args.get('materia') or None
        seleccion = kg_perfil.seleccionar_quiz(n=n, modo=modo, materia=materia)
        return jsonify({"problemas": seleccion})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/simulacro', methods=['GET'])
def kg_simulacro():
    try:
        materia = request.args.get('materia')
        if not materia:
            return jsonify({"error": "Falta la materia"}), 400
        n = request.args.get('n', default=4, type=int)
        temas_raw = request.args.get('temas', '')
        temas = [int(t) for t in temas_raw.split(',') if t.strip() != ''] or None
        seleccion = kg_perfil.seleccionar_simulacro(materia, temas=temas, n=n)
        return jsonify({"problemas": seleccion})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/problema', methods=['POST'])
def kg_problema():
    try:
        data = request.get_json(silent=True) or {}
        pid = data.get('id')
        if not pid:
            return jsonify({"error": "Falta el id del problema"}), 400
        banco = kg_problemas.cargar_banco()
        if kg_problemas.buscar_problema(banco, pid)[1] is None:
            return jsonify({"error": f"No existe el problema {pid} en el banco"}), 404
        perfil = kg_perfil.cargar_perfil()
        nodos = kg_perfil.cargar_grafos()
        veredicto = data.get('veredicto')
        if not veredicto and 'calidad' not in data:
            veredicto = 'resuelto' if bool(data.get('exito', True)) else 'incorrecto'
        calidad = data.get('calidad')
        if calidad is not None:
            try:
                calidad = float(calidad)
            except (TypeError, ValueError):
                calidad = None
        segundos = data.get('segundos')
        if segundos is not None:
            try:
                segundos = float(segundos)
            except (TypeError, ValueError):
                segundos = None
        resultado = kg_problemas.registrar_feedback(
            perfil, nodos, banco, pid, veredicto=veredicto, calidad=calidad,
            nodos_hueco=data.get('nodos_hueco_teorico') or data.get('nodos_hueco') or [],
            nodos_error=data.get('nodos_error') or [],
            comentarios=str(data.get('comentarios', '') or ''),
            segundos=segundos, origen=str(data.get('origen', 'web')),
        )
        kg_perfil.guardar_perfil(perfil)
        return jsonify({"success": True, **resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/kg/problemas/estado', methods=['GET'])
def kg_problemas_estado():
    """Semáforo de preparación: qué problemas están desbloqueados y por qué."""
    try:
        materia = request.args.get('materia') or None
        limite = request.args.get('limite', default=100, type=int)
        estado = kg_problemas.estado_banco(
            kg_perfil.cargar_perfil(), kg_perfil.cargar_grafos(),
            kg_problemas.cargar_banco(), materia=materia, limite=max(1, min(limite, 500)),
        )
        return jsonify(estado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/kg/retroalimentacion', methods=['GET'])
def kg_retroalimentacion():
    try:
        materia = request.args.get('materia') or None
        limite = request.args.get('limite', default=12, type=int)
        return jsonify({
            "debilidades": kg_problemas.debilidades(
                kg_perfil.cargar_perfil(), kg_perfil.cargar_grafos(),
                materia=materia, limite=max(1, min(limite, 100)),
            )
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _errores_por_nodo():
    """Mapa nodo → lista de errores pasados, vía los `nodos:` de cada ejercicio."""
    nodos_de_ejercicio = {}
    for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
        for fn in files:
            if fn.startswith('ejercicio') and fn.endswith('.md'):
                with open(os.path.join(root, fn), 'r', encoding='utf-8') as f:
                    contenido = f.read()
                eid = parse_yaml_field(contenido, 'id') or os.path.splitext(fn)[0]
                nodos_de_ejercicio[eid] = parse_yaml_list(contenido, 'nodos')
    salida = {}
    if os.path.exists(config.ERRORES_DIR):
        for fn in os.listdir(config.ERRORES_DIR):
            if not fn.endswith('.md'):
                continue
            with open(os.path.join(config.ERRORES_DIR, fn), 'r', encoding='utf-8') as f:
                contenido = f.read()
            m_ex = re.search(r'ejercicio_origen:\s*"?\[\[(.*?)\]\]', contenido)
            m_tit = re.search(r'^# Error [^:]*:\s*(.*)$', contenido, re.MULTILINE)
            m_ev = re.search(r'## ¿Cómo evitarlo en el futuro\?\s*\n> \[!IMPORTANT\]\s*\n> (.*)', contenido)
            fecha = parse_yaml_field(contenido, 'fecha_deteccion')
            if not m_ex:
                continue
            for nid in nodos_de_ejercicio.get(m_ex.group(1), []):
                salida.setdefault(nid, []).append({
                    'titulo': m_tit.group(1).strip() if m_tit else 'Error',
                    'como_evitarlo': m_ev.group(1).strip() if m_ev else '',
                    'fecha': fecha, 'ejercicio': m_ex.group(1),
                })
    return salida

@app.route('/api/kg/avisos', methods=['GET'])
def kg_avisos():
    try:
        pedidos = [x for x in request.args.get('nodos', '').split(',') if x]
        mapa = _errores_por_nodo()
        # Errores típicos (de otros años/compañeros), clasificados por nodo
        ruta_tipicos = os.path.join(KG_DIR, 'errores_tipicos.json')
        if os.path.exists(ruta_tipicos):
            with open(ruta_tipicos, 'r', encoding='utf-8') as f:
                tipicos = _json.load(f)
            for nid, lista in tipicos.items():
                for e in lista:
                    mapa.setdefault(nid, []).append({**e, 'tipo': 'tipico'})
        return jsonify({nid: mapa.get(nid, []) for nid in pedidos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/leccion/<nid>', methods=['GET'])
def kg_leccion(nid):
    try:
        import lecciones as kg_lecciones
        regenerar = request.args.get('regenerar') == '1'
        md = kg_lecciones.obtener_leccion(nid, regenerar=regenerar)
        return jsonify({"id": nid, "md": md})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/grafos', methods=['GET'])
def kg_grafos():
    try:
        import glob as _glob
        salida = []
        for ruta in sorted(_glob.glob(os.path.join(KG_DIR, '*.json'))):
            base = os.path.basename(ruta)
            if base in ('perfil.json', 'banco_problemas.json', 'examenes.json'):
                continue
            with open(ruta, 'r', encoding='utf-8') as fh:
                g = _json.load(fh)
            if 'materia' in g and 'nodos' in g:
                salida.append({'archivo': base, 'materia': g['materia'],
                               'curso': g.get('curso', 0), 'nodos': len(g['nodos'])})
        return jsonify(salida)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
