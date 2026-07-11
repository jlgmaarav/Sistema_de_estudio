import os
import sys
import re
from datetime import datetime
from google import genai
from google.genai import types

import config
import file_manager
import gemini_client

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

def build_lightweight_catalog() -> str:
    """Escanea la bóveda y devuelve un texto descriptivo compacto de su catálogo de contenidos."""
    catalog = []
    
    # 1. Ejercicios
    catalog.append("=== EJERCICIOS REGISTRADOS ===")
    if os.path.exists(config.ASIGNATURAS_DIR):
        for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
            for file in files:
                if file.endswith(".md") and file.startswith("ejercicio_"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    ex_id = parse_yaml_field(content, "id")
                    subj = parse_yaml_field(content, "asignatura")
                    topic = parse_yaml_field(content, "tema")
                    state = parse_yaml_field(content, "estado")
                    has_err = parse_yaml_field(content, "tiene_error")
                    concepts = parse_yaml_list(content, "conceptos")
                    
                    # Leer fragmento del enunciado
                    body = content.split("---")[-1].strip()
                    enunciado_snippet = body[:250].replace("\n", " ").strip()
                    
                    catalog.append(
                        f"- Ejercicio: [[{ex_id}]] | Asignatura: {subj} | Tema: {topic} | Estado: {state} | "
                        f"Tiene Error: {has_err} | Conceptos: {', '.join(concepts)} | Enunciado: {enunciado_snippet}..."
                    )
                    
    # 2. Intentos
    catalog.append("\n=== HISTORIAL DE INTENTOS ===")
    if os.path.exists(config.INTENTOS_DIR):
        for file in os.listdir(config.INTENTOS_DIR):
            if file.endswith(".md") and file.startswith("intento_"):
                path = os.path.join(config.INTENTOS_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                att_id = parse_yaml_field(content, "id")
                ex_origin = parse_yaml_field(content, "ejercicio_origen").replace("[[", "").replace("]]", "")
                result = parse_yaml_field(content, "resultado")
                date = parse_yaml_field(content, "fecha_intento")
                
                catalog.append(
                    f"- Intento: [[{att_id}]] del Ejercicio [[{ex_origin}]] | Resultado: {result} | Fecha: {date}"
                )
                
    # 3. Errores
    catalog.append("\n=== ERRORES HISTÓRICOS ===")
    if os.path.exists(config.ERRORES_DIR):
        for file in os.listdir(config.ERRORES_DIR):
            if file.endswith(".md") and file.startswith("error_"):
                path = os.path.join(config.ERRORES_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                err_id = parse_yaml_field(content, "id")
                subj = parse_yaml_field(content, "asignatura")
                topic = parse_yaml_field(content, "tema")
                err_types = parse_yaml_list(content, "tipo_error")
                ex_origin = parse_yaml_field(content, "ejercicio_origen").replace("[[", "").replace("]]", "")
                
                # Snippet de descripción
                body = content.split("---")[-1].strip()
                desc_snippet = body[:200].replace("\n", " ").strip()
                
                catalog.append(
                    f"- Error: [[{err_id}]] originado en Ejercicio [[{ex_origin}]] | Asignatura: {subj} | Tema: {topic} | "
                    f"Tipos de Error: {', '.join(err_types)} | Detalles: {desc_snippet}..."
                )
                
    # 4. Conceptos
    catalog.append("\n=== CONCEPTOS FÍSICOS ===")
    if os.path.exists(config.CONCEPTOS_DIR):
        for file in os.listdir(config.CONCEPTOS_DIR):
            if file.endswith(".md"):
                path = os.path.join(config.CONCEPTOS_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                concept_id = parse_yaml_field(content, "id") or os.path.splitext(file)[0]
                domain = parse_yaml_field(content, "dominio_actual")
                
                catalog.append(
                    f"- Concepto: [[{concept_id}]] | Dominio actual: {domain}"
                )
                
    return "\n".join(catalog)

def main():
    if len(sys.argv) < 2:
        print("Uso: python buscar.py \"<tu consulta en lenguaje natural>\"")
        print("Ejemplo: python buscar.py \"ejercicios de cuántica donde cometí errores algebraicos\"")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    print(f"Iniciando búsqueda semántica para: '{query}'...")
    
    # 1. Generar catálogo ligero de la bóveda
    print("Compilando catálogo de la bóveda...")
    catalog_text = build_lightweight_catalog()
    
    # 2. Configurar cliente de Gemini
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
        "- Agrupa los resultados por categorías (ej: Ejercicios recomendados, Errores relacionados, Conceptos clave).\n"
        "- Si no hay resultados relevantes, explícalo con amabilidad y sugiere conceptos o temas similares de la taxonomía.\n\n"
        "Devuelve únicamente la nota Markdown completa. No agregues introducciones ni explicaciones fuera del bloque de Markdown."
    )
    
    print("Consultando a Gemini...")
    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.2, # Baja temperatura para evitar alucinaciones en enlaces
            ),
        )
        
        markdown_result = response.text
        
        # Quitar delimitadores de markdown si Gemini los puso al principio/fin
        markdown_result = re.sub(r'^```markdown\s*\n', '', markdown_result)
        markdown_result = re.sub(r'\n```$', '', markdown_result)
        
        # Ruta del archivo final en Obsidian
        search_results_path = os.path.join(config.VAULT_PATH, "Resultados de Búsqueda.md")
        
        with open(search_results_path, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
            
        print("\n========================================================")
        print("¡BÚSQUEDA SEMÁNTICA COMPLETADA CON ÉXITO!")
        print(f"Resultados guardados en Obsidian: Resultados de Búsqueda.md")
        print("========================================================")
        
    except Exception as e:
        print(f"Error al ejecutar la búsqueda semántica: {e}")

if __name__ == "__main__":
    main()
