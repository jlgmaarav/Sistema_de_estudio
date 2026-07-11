import os
import re
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from datetime import datetime

import config
import file_manager
import templates

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Ensure vault structure is initialized
config.init_vault_structure()

def parse_yaml_field(content: str, field_name: str) -> str:
    match = re.search(rf'^{field_name}:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else ""

def clean_link(link_str: str) -> str:
    """Elimina [[ y ]] de los enlaces internos de Obsidian."""
    if not link_str:
        return ""
    return link_str.replace("[[", "").replace("]]", "").strip('"').strip("'")

def get_between_markers(content: str, start_marker: str, end_marker: str) -> str:
    pattern = rf"{re.escape(start_marker)}\s*\n(.*?)\n\s*{re.escape(end_marker)}"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""

def replace_between_markers(content: str, start_marker: str, end_marker: str, new_text: str) -> str:
    pattern = rf"({re.escape(start_marker)}\s*\n)(.*?)(\n\s*{re.escape(end_marker)})"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        if start_marker not in content:
            return content + f"\n\n{start_marker}\n{new_text.strip()}\n{end_marker}\n"
        return content
    start_idx = match.start(2)
    end_idx = match.end(2)
    return content[:start_idx] + new_text.strip() + "\n" + content[end_idx:]

@app.route('/')
def index():
    return render_template('biblioteca.html')

@app.route('/assets/<path:filename>')
def serve_asset(filename):
    return send_from_directory(config.ASSETS_DIR, filename)

@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        projects = []
        if os.path.exists(config.PROYECTOS_DIR):
            for file in os.listdir(config.PROYECTOS_DIR):
                if file.endswith(".md"):
                    path = os.path.join(config.PROYECTOS_DIR, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    proj_id = parse_yaml_field(content, "id") or os.path.splitext(file)[0]
                    titulo = parse_yaml_field(content, "titulo") or proj_id
                    estado = parse_yaml_field(content, "estado") or "activo"
                    etiqueta = parse_yaml_field(content, "etiqueta") or ""
                    
                    projects.append({
                        "id": proj_id,
                        "titulo": titulo,
                        "estado": estado,
                        "etiqueta": etiqueta
                    })
        return jsonify(projects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<proj_id>', methods=['GET'])
def get_project_detail(proj_id):
    try:
        path = os.path.join(config.PROYECTOS_DIR, f"{proj_id}.md")
        if not os.path.exists(path):
            return jsonify({"error": f"Proyecto {proj_id} no encontrado"}), 404
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        titulo = parse_yaml_field(content, "titulo") or proj_id
        estado = parse_yaml_field(content, "estado") or "activo"
        etiqueta = parse_yaml_field(content, "etiqueta") or ""
        
        # Extraer descripción (todo lo que viene después de --- y antes de las secciones ##)
        body = content.split("---")[-1].strip()
        desc_match = re.match(r'^(.*?)(?:## Libros|## Tareas|##|$)', body, re.DOTALL)
        descripcion = desc_match.group(1).strip() if desc_match else ""
        # Limpiar posible título # Proyecto: xxx
        descripcion = re.sub(rf'^# Proyecto:\s*{re.escape(titulo)}\s*\n', '', descripcion, flags=re.IGNORECASE).strip()
        
        # Extraer tareas y notas
        tareas = get_between_markers(content, "<!-- tareas_inicio -->", "<!-- tareas_fin -->")
        
        # Buscar libros en Lecturas que pertenezcan a este proyecto
        books = []
        if os.path.exists(config.LECTURAS_DIR):
            for file in os.listdir(config.LECTURAS_DIR):
                if file.endswith(".md"):
                    b_path = os.path.join(config.LECTURAS_DIR, file)
                    with open(b_path, 'r', encoding='utf-8') as bf:
                        b_content = bf.read()
                    
                    b_proj = clean_link(parse_yaml_field(b_content, "proyecto"))
                    if b_proj == proj_id:
                        b_id = parse_yaml_field(b_content, "id") or os.path.splitext(file)[0]
                        b_title = parse_yaml_field(b_content, "titulo") or b_id
                        b_autor = parse_yaml_field(b_content, "autor") or "Desconocido"
                        b_cat = parse_yaml_field(b_content, "categoria") or "General"
                        b_sec = parse_yaml_field(b_content, "seccion_proyecto") or "General"
                        
                        books.append({
                            "id": b_id,
                            "titulo": b_title,
                            "autor": b_autor,
                            "categoria": b_cat,
                            "seccion": b_sec
                        })
                        
        # Agrupar libros por sección
        grouped_books = {}
        for b in books:
            sec = b["seccion"] or "General"
            if sec not in grouped_books:
                grouped_books[sec] = []
            grouped_books[sec].append(b)
            
        return jsonify({
            "id": proj_id,
            "titulo": titulo,
            "estado": estado,
            "etiqueta": etiqueta,
            "descripcion": descripcion,
            "tareas": tareas,
            "libros_agrupados": grouped_books
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<proj_id>/tareas', methods=['POST'])
def save_project_tasks(proj_id):
    try:
        data = request.json
        new_tareas = data.get("tareas", "")
        
        path = os.path.join(config.PROYECTOS_DIR, f"{proj_id}.md")
        if not os.path.exists(path):
            return jsonify({"error": f"Proyecto {proj_id} no encontrado"}), 404
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        updated_content = replace_between_markers(content, "<!-- tareas_inicio -->", "<!-- tareas_fin -->", new_tareas)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/new', methods=['POST'])
def create_project():
    try:
        data = request.json
        titulo = data.get("titulo")
        descripcion = data.get("descripcion", "")
        estado = data.get("estado", "activo")
        etiqueta = data.get("etiqueta", "")
        
        if not titulo:
            return jsonify({"error": "El título es obligatorio"}), 400
            
        proj_file = file_manager.ensure_project_note(
            titulo=titulo,
            descripcion=descripcion,
            estado=estado,
            etiqueta=etiqueta
        )
        
        proj_id = file_manager.slugify(titulo)
        return jsonify({
            "id": proj_id,
            "titulo": titulo,
            "estado": estado,
            "etiqueta": etiqueta,
            "file_path": proj_file
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        books = []
        if os.path.exists(config.LECTURAS_DIR):
            for file in os.listdir(config.LECTURAS_DIR):
                if file.endswith(".md"):
                    path = os.path.join(config.LECTURAS_DIR, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    b_id = parse_yaml_field(content, "id") or os.path.splitext(file)[0]
                    titulo = parse_yaml_field(content, "titulo") or b_id
                    autor = parse_yaml_field(content, "autor") or "Desconocido"
                    categoria = parse_yaml_field(content, "categoria") or "General"
                    proyecto = clean_link(parse_yaml_field(content, "proyecto"))
                    seccion = parse_yaml_field(content, "seccion_proyecto") or "General"
                    fecha = parse_yaml_field(content, "fecha_registro") or ""
                    
                    books.append({
                        "id": b_id,
                        "titulo": titulo,
                        "autor": autor,
                        "categoria": categoria,
                        "proyecto": proyecto,
                        "seccion": seccion,
                        "fecha_registro": fecha
                    })
        return jsonify(books)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<book_id>', methods=['GET'])
def get_book_detail(book_id):
    try:
        path = os.path.join(config.LECTURAS_DIR, f"{book_id}.md")
        if not os.path.exists(path):
            return jsonify({"error": f"Libro {book_id} no encontrado"}), 404
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        b_id = parse_yaml_field(content, "id") or book_id
        titulo = parse_yaml_field(content, "titulo") or b_id
        autor = parse_yaml_field(content, "autor") or "Desconocido"
        categoria = parse_yaml_field(content, "categoria") or "General"
        proyecto = clean_link(parse_yaml_field(content, "proyecto"))
        seccion = parse_yaml_field(content, "seccion_proyecto") or "General"
        fecha = parse_yaml_field(content, "fecha_registro") or ""
        
        notes = get_between_markers(content, "<!-- notas_inicio -->", "<!-- notas_fin -->")
        
        return jsonify({
            "id": b_id,
            "titulo": titulo,
            "autor": autor,
            "categoria": categoria,
            "proyecto": proyecto,
            "seccion": seccion,
            "fecha_registro": fecha,
            "notes": notes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<book_id>/notes', methods=['POST'])
def save_book_notes(book_id):
    try:
        data = request.json
        new_notes = data.get("notes", "")
        
        path = os.path.join(config.LECTURAS_DIR, f"{book_id}.md")
        if not os.path.exists(path):
            return jsonify({"error": f"Libro {book_id} no encontrado"}), 404
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        updated_content = replace_between_markers(content, "<!-- notas_inicio -->", "<!-- notas_fin -->", new_notes)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/new', methods=['POST'])
def create_book():
    try:
        data = request.json
        titulo = data.get("titulo")
        autor = data.get("autor")
        categoria = data.get("categoria")
        proyecto_id = data.get("proyecto_id", "")
        seccion_proyecto = data.get("seccion_proyecto", "")
        
        if not titulo or not autor or not categoria:
            return jsonify({"error": "Título, Autor y Categoría son obligatorios"}), 400
            
        book_file = file_manager.ensure_book_note(
            titulo=titulo,
            autor=autor,
            categoria=categoria,
            proyecto_id=proyecto_id,
            seccion_proyecto=seccion_proyecto
        )
        
        book_id = file_manager.slugify(titulo)
        return jsonify({
            "id": book_id,
            "titulo": titulo,
            "autor": autor,
            "categoria": categoria,
            "proyecto": proyecto_id,
            "seccion": seccion_proyecto,
            "file_path": book_file
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
