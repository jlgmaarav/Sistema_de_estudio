import os
import re
import sys
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from datetime import datetime
from google import genai
from google.genai import types

import config
import file_manager
import gemini_client
import templates
import generar_dashboard
import buscar

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Ensure folders exist
config.init_vault_structure()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assets/<path:filename>')
def serve_asset(filename):
    return send_from_directory(config.ASSETS_DIR, filename)

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
        
        # Agenda de repaso para hoy o retrasados
        hoy = datetime.now().date()
        agenda = []
        for ex in data["ejercicios"]:
            try:
                ex_date = datetime.strptime(ex["proxima_revision"], "%d/%m/%Y").date()
            except ValueError:
                ex_date = hoy
            if ex_date <= hoy:
                agenda.append(ex)
                
        def get_date_key(x):
            try:
                return datetime.strptime(x["proxima_revision"], "%d/%m/%Y")
            except ValueError:
                return datetime.now()
        agenda.sort(key=get_date_key)
        
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
        proxima = parse_yaml_field(content, "proxima_revision")
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
            "proxima_revision": proxima,
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
            
        # Ejecutar la búsqueda en memoria de forma similar a buscar.py
        catalog_text = buscar.build_lightweight_catalog()
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        prompt = (
            "Eres un buscador inteligente y asistente de estudio de Física.\n\n"
            "Se te proporciona:\n"
            "1. La base de datos (catálogo) de los apuntes y ejercicios de Física del estudiante:\n"
            f"{catalog_text}\n\n"
            "2. La consulta de búsqueda del estudiante en lenguaje natural:\n"
            f"'{query}'\n\n"
            "Tu tarea es:\n"
            "- Identificar los ejercicios, intentos, conceptos y errores que sean más relevantes para la consulta.\n"
            "- Devolver una nota formateada en Markdown titulada '# Resultados de Búsqueda: {query}' con la lista de resultados.\n"
            "- Para cada resultado, proporciona un enlace interno de Obsidian (ej: [[ejercicio_001]], [[intento_002]], [[error_001]], [[Concepto]]) y una brevísima explicación (1 o 2 líneas) de su relevancia.\n"
            "- Agrupa los resultados por categorías (ej: Ejercicios recomendados, Errores relacionados, Conceptos clave).\n\n"
            "Devuelve únicamente la nota Markdown completa. No agregues introducciones ni explicaciones fuera del bloque de Markdown."
        )
        
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(temperature=0.2),
        )
        
        markdown_result = response.text
        markdown_result = re.sub(r'^```markdown\s*\n', '', markdown_result)
        markdown_result = re.sub(r'\n```$', '', markdown_result)
        
        # Reemplazar enlaces dobles [[algo]] por enlaces interactivos o etiquetas con estilo
        # E.g., [[ejercicio_001]] -> <a href="#/exercise/ejercicio_001" class="obsidian-link">ejercicio_001</a>
        def link_repl(match):
            name = match.group(1)
            if name.startswith("ejercicio_"):
                return f'<a href="#" onclick="viewExercise(\'{name}\'); return false;" class="obsidian-link">{name}</a>'
            elif name.startswith("intento_"):
                return f'<span class="obsidian-badge attempt">{name}</span>'
            elif name.startswith("error_"):
                return f'<span class="obsidian-badge error">{name}</span>'
            else:
                # Es una asignatura o concepto
                return f'<span class="obsidian-badge concept">{name}</span>'
                
        html_result = re.sub(r'\[\[(.*?)\]\]', link_repl, markdown_result)
        
        return jsonify({"markdown": markdown_result, "html": html_result})
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
        new_proxima = data.get("proxima_revision")
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
            proxima_revision=new_proxima,
            tipo_recurso=old_tipo_recurso,
            origen=old_origen,
            fecha_origen=old_fecha_origen,
            warning_transcripcion=warning_transcripcion
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
    from datetime import timedelta
    try:
        data = request.get_json()
        rating = data.get("rating") # 'facil', 'duda', 'fallo'
        
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
        
        hoy = datetime.now()
        if rating == 'facil':
            if current_state == "nuevo":
                new_state = "revisado"
                delta_days = 3
            elif current_state == "revisado":
                new_state = "dominado"
                delta_days = 10
            else: # dominado
                new_state = "dominado"
                delta_days = 30
        elif rating == 'duda':
            new_state = "revisado"
            delta_days = 2
        else: # fallo
            new_state = "nuevo"
            delta_days = 1
            
        next_revision = (hoy + timedelta(days=delta_days)).strftime("%d/%m/%Y")
        
        # Modificar archivo de ejercicio en el vault
        content = re.sub(r'^estado:\s*\w+', f'estado: {new_state}', content, flags=re.MULTILINE)
        content = re.sub(r'^proxima_revision:\s*[\d/]+', f'proxima_revision: {next_revision}', content, flags=re.MULTILINE)
        
        # Actualizar la línea de estado en el cuerpo del markdown
        content = re.sub(
            r'- \*\*Estado de Repaso:\*\* `\w+` \(Próxima revisión: [\d/]+\)',
            f'- **Estado de Repaso:** `{new_state.upper()}` (Próxima revisión: {next_revision})',
            content
        )
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        generar_dashboard.run()

        # Unificación con el knowledge graph: la autoevaluación también
        # alimenta el perfil (fácil = éxito; duda/fallo = fallo).
        try:
            nodos_kg = parse_yaml_list(content, "nodos")
            if not nodos_kg:
                subj = parse_yaml_field(content, "asignatura")
                conceptos = [re.sub(r'[\[\]"]', '', c) for c in parse_yaml_list(content, "conceptos")]
                nodos_kg = kg_perfil.resolver_conceptos(subj, conceptos)
            if nodos_kg:
                kg_perfil.registrar_y_guardar(nodos_kg, rating == 'facil', origen=f'autoeval:{exerc_id}')
        except Exception as e_kg:
            print(f"Aviso: no se pudo actualizar el perfil desde el autoevaluador: {e_kg}")

        return jsonify({
            "success": True,
            "new_state": new_state,
            "proxima_revision": next_revision
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

@app.route('/kg/mapa')
def kg_mapa():
    return send_from_directory(KG_DIR, 'mapa_conocimiento.html')

@app.route('/api/kg/plan', methods=['GET'])
def kg_plan():
    try:
        fecha = request.args.get('fecha')
        minutos = request.args.get('minutos', type=int)
        hoy = datetime.strptime(fecha, '%Y-%m-%d').date() if fecha else None
        r = kg_planificar.calcular(hoy=hoy, minutos=minutos)
        if not fecha:
            kg_planificar.guardar_plan(r['md'])
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kg/examenes', methods=['GET', 'POST'])
def kg_examenes():
    ruta = os.path.join(KG_DIR, 'examenes.json')
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not isinstance(data, dict) or 'examenes' not in data:
                return jsonify({"error": "Formato inválido: falta 'examenes'"}), 400
            for ex in data['examenes']:
                datetime.strptime(ex['fecha'], '%Y-%m-%d')  # valida fechas
            with open(ruta, 'w', encoding='utf-8') as f:
                _json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"success": True})
        with open(ruta, 'r', encoding='utf-8') as f:
            return jsonify(_json.load(f))
    except ValueError as e:
        return jsonify({"error": f"Fecha inválida (usa YYYY-MM-DD): {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            'gamificacion': kg_gamificacion.estado(perfil_d, hoy),
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
    """Lanza en segundo plano la sincronización del reMarkable + el procesado de
    lo nuevo (sync -> watcher). No bloquea: el usuario refresca las correcciones
    cuando termine."""
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
        return jsonify({"success": True, "mensaje": "Sincronizando y corrigiendo en segundo plano. Refresca en un par de minutos."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        data = request.get_json()
        pid = data.get('id')
        if not pid:
            return jsonify({"error": "Falta el id del problema"}), 400
        kg_perfil.marcar_problema_y_guardar(pid, bool(data.get('exito', True)))
        return jsonify({"success": True})
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
