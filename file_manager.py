import os
import shutil
import re
import io
from datetime import datetime, timedelta
import fitz  # PyMuPDF
from PIL import Image
import config
import templates

def slugify(text: str) -> str:
    """Convierte texto en un formato limpio para nombres de archivos de Windows."""
    text = text.lower()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9_\-]', '_', text)
    text = re.sub(r'_+', '_', text)
    return text.strip('_')

def copy_to_assets(src_path: str, asignatura: str, label: str) -> str:
    """
    Copia el archivo al directorio de Assets de Obsidian.
    Le asigna un nombre único con timestamp.
    """
    if not src_path or not os.path.exists(src_path):
        return ""
        
    ext = os.path.splitext(src_path)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subject_slug = slugify(asignatura)
    label_slug = slugify(label)
    
    dest_filename = f"asset_{subject_slug}_{timestamp}_{label_slug}{ext}"
    dest_path = os.path.join(config.ASSETS_DIR, dest_filename)
    
    try:
        shutil.copy2(src_path, dest_path)
        print(f"Archivo original guardado en Assets: {dest_path}")
        return dest_filename
    except Exception as e:
        print(f"Error al copiar archivo a Assets: {e}")
        return os.path.basename(src_path)

def get_next_sequential_id(directory: str, prefix: str, ext: str = ".md") -> str:
    """Escanea un directorio y devuelve el siguiente identificador secuencial."""
    if not os.path.exists(directory):
        return f"{prefix}_001"
        
    pattern = re.compile(rf"^{prefix}_(\d+){re.escape(ext)}$")
    max_num = 0
    
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
                
    next_num = max_num + 1
    return f"{prefix}_{next_num:03d}"

def get_next_error_id() -> str:
    """Devuelve el siguiente ID de error disponible."""
    return get_next_sequential_id(config.ERRORES_DIR, "error")

def get_next_attempt_id() -> str:
    """Devuelve el siguiente ID de intento disponible."""
    return get_next_sequential_id(config.INTENTOS_DIR, "intento")

def get_next_exercise_id(asignatura: str, tema: str) -> str:
    """Devuelve el siguiente ID de ejercicio para un tema concreto."""
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)
    exerc_dir = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{topic_slug}/ejercicios"
    return get_next_sequential_id(exerc_dir, "ejercicio")

def get_unique_exercise_id(directory: str, base_id: str) -> str:
    """Asegura que el ID de ejercicio sea único en el directorio, añadiendo sufijos si hay colisiones."""
    clean_base = slugify(base_id)
    exerc_id = clean_base
    counter = 1
    while os.path.exists(os.path.join(directory, f"{exerc_id}.md")):
        exerc_id = f"{clean_base}_{counter}"
        counter += 1
    return exerc_id

def ensure_subject_topic_dirs(asignatura: str, tema: str) -> str:
    """Asegura la creación física de las carpetas de asignaturas y temas."""
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)
    exerc_dir = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{topic_slug}/ejercicios"
    os.makedirs(exerc_dir, exist_ok=True)
    return exerc_dir

def insert_between_markers(content: str, marker_start: str, marker_end: str, new_line: str) -> str:
    """Inserta una línea de texto entre dos comentarios marcadores, evitando duplicados."""
    pattern = rf"({re.escape(marker_start)}\s*\n)(.*?)(\n\s*{re.escape(marker_end)})"
    
    def repl(match):
        start = match.group(1)
        middle = match.group(2)
        end = match.group(3)
        if new_line in middle:
            return match.group(0)
        if middle.strip():
            # Limpiar saltos de línea al final para evitar espacios duplicados
            clean_middle = middle.rstrip()
            return f"{start}{clean_middle}\n{new_line}{end}"
        else:
            return f"{start}{new_line}{end}"
            
    # Si los marcadores no existen, devolver el contenido intacto
    if marker_start not in content or marker_end not in content:
        return content
        
    return re.sub(pattern, repl, content, flags=re.DOTALL)

def append_line_between_markers(file_path: str, marker_start: str, marker_end: str, new_line: str):
    """Abre un archivo, inserta una línea entre marcadores y guarda los cambios."""
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated = insert_between_markers(content, marker_start, marker_end, new_line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated)

# =====================================================================
# Auto-creación de Notas Físicas en Obsidian
# =====================================================================

def ensure_subject_note(asignatura: str) -> str:
    """Crea la nota física de la asignatura si no existe."""
    subject_slug = slugify(asignatura)
    subject_dir = f"{config.ASIGNATURAS_DIR}/{subject_slug}"
    os.makedirs(subject_dir, exist_ok=True)
    
    file_path = f"{subject_dir}/{subject_slug}.md"
    if not os.path.exists(file_path):
        content = templates.render_subject_template(asignatura)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creada nota de Asignatura: {file_path}")
    return file_path

def ensure_topic_note(asignatura: str, tema: str) -> str:
    """Crea la nota física del tema y la enlaza en la asignatura."""
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)
    topic_dir = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{topic_slug}"
    os.makedirs(topic_dir, exist_ok=True)
    
    # 1. Asegurar nota de asignatura primero
    subject_file = ensure_subject_note(asignatura)
    
    # 2. Crear nota de tema si no existe
    file_path = f"{topic_dir}/{topic_slug}.md"
    if not os.path.exists(file_path):
        content = templates.render_topic_template(tema, asignatura)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creada nota de Tema: {file_path}")
        
    # 3. Enlazar tema en la nota de asignatura
    link_line = f"- [[{topic_slug}|{tema}]]"
    append_line_between_markers(subject_file, "<!-- temas_inicio -->", "<!-- temas_fin -->", link_line)
    
    return file_path

def ensure_concept_note(concepto: str, dominio: float = 0.0) -> str:
    """Crea la nota física del concepto en la carpeta Conceptos."""
    clean_concept = concepto.replace("[[", "").replace("]]", "").strip()
    file_path = f"{config.CONCEPTOS_DIR}/{clean_concept}.md"
    if not os.path.exists(file_path):
        content = templates.render_concept_template(clean_concept, dominio)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creada nota de Concepto: {file_path}")
    return file_path

def link_exercise_to_indices(exerc_id: str, asignatura: str, tema: str):
    """Enlaza el ejercicio en las fichas correspondientes de Asignatura y Tema."""
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)
    
    subject_file = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{subject_slug}.md"
    topic_file = f"{config.ASIGNATURAS_DIR}/{subject_slug}/{topic_slug}/{topic_slug}.md"
    
    link_line = f"- [[{exerc_id}]] - {tema}"
    
    if os.path.exists(subject_file):
        append_line_between_markers(subject_file, "<!-- ejercicios_inicio -->", "<!-- ejercicios_fin -->", link_line)
        
    link_line_topic = f"- [[{exerc_id}]]"
    if os.path.exists(topic_file):
        append_line_between_markers(topic_file, "<!-- ejercicios_inicio -->", "<!-- ejercicios_fin -->", link_line_topic)

def update_concept_domain_score(concepto: str, dominio: float, exerc_id: str, attempt_id: str):
    """Actualiza la nota de concepto con una nueva evaluación de dominio e historial."""
    clean_concept = concepto.replace("[[", "").replace("]]", "").strip()
    concept_file = ensure_concept_note(clean_concept, dominio)
    
    with open(concept_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Actualizar el valor dominio_actual en el YAML header
    content = re.sub(r'dominio_actual:\s*[\d\.]+', f'dominio_actual: {dominio:.2f}', content)
    
    with open(concept_file, 'w', encoding='utf-8') as f:
        f.write(content)
        
    # 2. Agregar fila de historial
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    history_row = f"| {fecha_hoy} | [[{exerc_id}]] | [[{attempt_id}]] | {dominio:.2f} |"
    append_line_between_markers(concept_file, "<!-- intentos_inicio -->", "<!-- intentos_fin -->", history_row)

# =====================================================================
# Repetición Espaciada (Spaced Repetition)
# =====================================================================

def get_exercise_repetition_state(exerc_path: str) -> tuple[str, str]:
    """Extrae el estado actual y la fecha de próxima revisión del ejercicio."""
    if not os.path.exists(exerc_path):
        return "nuevo", datetime.now().strftime("%d/%m/%Y")
        
    with open(exerc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    estado_match = re.search(r'^estado:\s*(\w+)', content, re.MULTILINE)
    proxima_match = re.search(r'^proxima_revision:\s*([\d/]+)', content, re.MULTILINE)
    
    estado = estado_match.group(1) if estado_match else "nuevo"
    proxima = proxima_match.group(1) if proxima_match else datetime.now().strftime("%d/%m/%Y")
    
    return estado, proxima

def calculate_next_review(current_state: str, tiene_error: bool) -> tuple[str, str]:
    """Algoritmo de repetición espaciada básico."""
    hoy = datetime.now()
    
    if tiene_error:
        # Intento incorrecto o incompleto
        if current_state == "dominado":
            new_state = "revisado"
        else:
            new_state = "nuevo"
        next_date = hoy + timedelta(days=1)
    else:
        # Intento correcto (sin errores)
        if current_state == "nuevo":
            new_state = "revisado"
            next_date = hoy + timedelta(days=3)
        elif current_state == "revisado":
            new_state = "dominado"
            next_date = hoy + timedelta(days=10)
        else:
            new_state = "dominado"
            next_date = hoy + timedelta(days=30)
            
    return new_state, next_date.strftime("%d/%m/%Y")

# =====================================================================
# Procesamiento de PDFs
# =====================================================================

def process_and_copy_solution(sol_path: str, asignatura: str) -> list[str]:
    """Copia el archivo y extrae páginas de PDFs a JPEGs para Obsidian."""
    if not sol_path or not os.path.exists(sol_path):
        return []
        
    ext = os.path.splitext(sol_path)[1].lower()
    
    # 1. Copiar archivo original
    original_asset = copy_to_assets(sol_path, asignatura, "solucion")
    assets_list = [original_asset]
    
    # 2. Si es PDF, extraer páginas como JPEGs
    if ext == '.pdf':
        print(f"Extrayendo páginas del PDF a Assets para renderizado en Obsidian...")
        doc = fitz.open(sol_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subject_slug = slugify(asignatura)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("jpeg")
            img = Image.open(io.BytesIO(img_data))
            
            max_width = 1200
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
            page_filename = f"asset_{subject_slug}_{timestamp}_solucion_pag_{i+1}.jpg"
            page_path = os.path.join(config.ASSETS_DIR, page_filename)
            
            img.save(page_path, "JPEG", quality=60)
            img.close()
            
            assets_list.append(page_filename)
            print(f"  -> Guardada página {i+1} en Assets: {page_filename}")
            
    return assets_list

def ensure_book_note(
    titulo: str,
    autor: str,
    categoria: str,
    proyecto_id: str = "",
    seccion_proyecto: str = ""
) -> str:
    """Crea la nota física del libro de no ficción si no existe y lo enlaza al proyecto."""
    libro_id = slugify(titulo)
    file_path = f"{config.LECTURAS_DIR}/{libro_id}.md"
    if not os.path.exists(file_path):
        content = templates.render_book_template(
            libro_id=libro_id,
            titulo=titulo,
            autor=autor,
            categoria=categoria,
            proyecto_id=proyecto_id,
            seccion_proyecto=seccion_proyecto
        )
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creada ficha de libro: {file_path}")
        
    # Enlazar libro en la ficha de proyecto si aplica
    if proyecto_id:
        proyecto_file = f"{config.PROYECTOS_DIR}/{proyecto_id}.md"
        if os.path.exists(proyecto_file):
            link_line = f"- [[{libro_id}]] - {titulo} ({seccion_proyecto if seccion_proyecto else 'General'})"
            append_line_between_markers(proyecto_file, "<!-- libros_inicio -->", "<!-- libros_fin -->", link_line)
            
    return file_path

def ensure_project_note(
    titulo: str,
    descripcion: str = "",
    estado: str = "activo",
    etiqueta: str = ""
) -> str:
    """Crea la nota física de un Proyecto si no existe."""
    proyecto_id = slugify(titulo)
    file_path = f"{config.PROYECTOS_DIR}/{proyecto_id}.md"
    if not os.path.exists(file_path):
        content = templates.render_project_template(
            proyecto_id=proyecto_id,
            titulo=titulo,
            descripcion=descripcion,
            estado=estado,
            etiqueta=etiqueta
        )
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creada nota de Proyecto: {file_path}")
    return file_path
