import os
import sys
import json
import shutil
import re
import io
import tempfile
from dotenv import load_dotenv
from rmrl import render

# Load environment variables
load_dotenv()


def render_annotated(doc_source_path):
    """Renderiza un documento del reMarkable a PDF.

    Usa `rmc` (soporta el formato de trazos nuevo, v6, del reMarkable) en vez de
    `rmrl` (que con los dispositivos actuales apelotona la letra ilegible). El
    resultado combina las páginas del PDF base (los enunciados impresos) con las
    páginas anotadas a mano (la solución), bien renderizadas. Si algo falla, se
    lanza excepción y el llamador puede caer a `rmrl`.

    Devuelve un stream (BytesIO) con el PDF, como hacía `rmrl.render`.
    """
    import fitz  # PyMuPDF
    from rmc.exporters.svg import rm_to_svg

    base = doc_source_path  # .../<uuid> (sin extensión); .content/.pdf son hermanos
    with open(base + ".content", "r", encoding="utf-8") as f:
        content = json.load(f)

    cpages = content.get("cPages", {}).get("pages") or []
    page_ids = [p["id"] for p in cpages] if cpages else content.get("pages", [])
    filetype = content.get("fileType", "notebook")

    salida = fitz.open()
    # 1) Páginas del enunciado (PDF/EPUB base), tal cual
    base_pdf_path = base + ".pdf"
    if filetype in ("pdf", "epub") and os.path.exists(base_pdf_path):
        with fitz.open(base_pdf_path) as base_pdf:
            salida.insert_pdf(base_pdf)

    # 2) Páginas anotadas a mano (rmc → SVG → PDF), en el orden del documento
    if not page_ids:
        page_ids = sorted(f[:-3] for f in os.listdir(base)) if os.path.isdir(base) else []
    anotadas = 0
    for pid in page_ids:
        rm_file = os.path.join(base, pid + ".rm")
        if not os.path.exists(rm_file) or os.path.getsize(rm_file) < 2000:
            continue  # sin trazos reales
        svg_path = tempfile.mktemp(suffix=".svg")
        try:
            rm_to_svg(rm_file, svg_path)
            with fitz.open(svg_path) as svg_doc:
                pdf_bytes = svg_doc.convert_to_pdf()
            with fitz.open("pdf", pdf_bytes) as annot:
                salida.insert_pdf(annot)
            anotadas += 1
        except Exception as e:
            print(f"    [aviso] no se pudo renderizar una página anotada ({pid[:8]}): {e}")
        finally:
            if os.path.exists(svg_path):
                os.remove(svg_path)

    if salida.page_count == 0:
        raise RuntimeError("rmc no produjo ninguna página")
    stream = io.BytesIO(salida.tobytes())
    salida.close()
    stream.seek(0)
    return stream

# Helper to load state
def load_state(state_path):
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[reMarkable Sync] Advertencia: No se pudo leer el archivo de estado ({e}). Se creará uno nuevo.")
    return {"documents": {}}

# Helper to save state
def save_state(state_path, state):
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[reMarkable Sync] Error al guardar el archivo de estado: {e}")

# Helper to slugify filenames to avoid Windows path issues
def clean_filename(name: str) -> str:
    # Remove characters that Windows does not allow in file names
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', name)
    return cleaned.strip()

# Helper to normalize names for robust matching (e.g. "4º Física" -> "4fisica", "4 Física" -> "4fisica")
def normalize_name(name: str) -> str:
    n = name.lower()
    # Replace accented letters
    n = n.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
    # Keep only alphanumeric characters
    n = re.sub(r'[^a-z0-9]', '', n)
    return n

# Helper to check if a document has any page stroke files
def has_strokes(cache_dir: str, uuid: str) -> bool:
    doc_dir = os.path.join(cache_dir, uuid)
    if not os.path.exists(doc_dir) or not os.path.isdir(doc_dir):
        return False
    # Check if there is at least one .rm file with size > 0
    for f in os.listdir(doc_dir):
        if f.endswith(".rm"):
            try:
                if os.path.getsize(os.path.join(doc_dir, f)) > 0:
                    return True
            except Exception:
                pass
    return False

# Helper to get the file type of the document
def get_file_type(cache_dir: str, uuid: str) -> str:
    content_path = os.path.join(cache_dir, f"{uuid}.content")
    if os.path.exists(content_path):
        try:
            with open(content_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("fileType", "")
        except Exception:
            pass
    return ""

def sync():
    # 1. Configuración de carpetas y variables
    target_folders = ["4º Física", "Extra"]
    
    # Directorio de caché local de la aplicación de escritorio reMarkable
    cache_dir = os.path.join(os.environ.get('APPDATA', ''), 'remarkable', 'desktop').replace("\\", "/")
    if not os.path.exists(cache_dir):
        print(f"[ERROR] No se encontró el directorio de la aplicación de reMarkable en: {cache_dir}")
        print("Asegúrate de que la aplicación oficial de reMarkable esté instalada y sincronizada.")
        sys.exit(1)
        
    # Cargar config.py local para obtener las rutas del Vault
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import config
    except ImportError:
        print("[ERROR] No se pudo cargar el archivo config.py del sistema de estudio.")
        sys.exit(1)
        
    inbox_dir = os.path.abspath(config.INBOX_DIR).replace("\\", "/")
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Archivo de estado local
    state_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "remarkable_sync_state.json"))
    state = load_state(state_path)
    
    print("========================================================")
    print("   Sincronización Local Inteligente de reMarkable")
    print(f"   Carpetas origen a escanear: {target_folders}")
    print(f"   Destino (Inbox/Vault): {config.VAULT_PATH}")
    print("========================================================")
    
    # 2. Leer metadatos locales de la aplicación
    metadata_files = [f for f in os.listdir(cache_dir) if f.endswith(".metadata")]
    item_map = {}
    for f in metadata_files:
        uuid = f[:-9]
        path = os.path.join(cache_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            item_map[uuid] = {
                "id": uuid,
                "parent": data.get("parent", ""),
                "type": data.get("type", ""),
                "name": data.get("visibleName", ""),
                "last_modified": int(data.get("lastModified", 0))
            }
        except Exception:
            pass
            
    # 3. Encontrar los IDs de las carpetas principales buscadas (usando normalización de texto)
    target_folder_ids_map = {}
    normalized_targets = {normalize_name(f): f for f in target_folders}
    
    for item in item_map.values():
        if item["type"] == "CollectionType":
            norm_name = normalize_name(item["name"])
            if norm_name in normalized_targets:
                target_folder_ids_map[item["id"]] = normalized_targets[norm_name]
                
    # Helper para determinar a cuál de las carpetas principales pertenece un ítem
    def get_root_target_folder(item):
        curr = item
        visited = set()
        while curr["parent"] and curr["parent"] not in visited:
            visited.add(curr["parent"])
            if curr["parent"] in target_folder_ids_map:
                return target_folder_ids_map[curr["parent"]]
            if curr["parent"] in item_map:
                curr = item_map[curr["parent"]]
            else:
                break
        return None

    # 4. Filtrar y clasificar los documentos a sincronizar
    docs_to_sync = []
    
    for item in item_map.values():
        if item["type"] == "DocumentType" and item["parent"] != "trash":
            root_folder = get_root_target_folder(item)
            if root_folder:
                doc_id = item["id"]
                last_modified = item["last_modified"]
                name = item["name"]
                
                # Regla de Trazos: Ignorar libros/PDFs limpios
                file_type = get_file_type(cache_dir, doc_id)
                is_notebook = (file_type == "notebook")
                has_any_strokes = has_strokes(cache_dir, doc_id)
                
                # Solo procesar si es un cuaderno o si es un PDF/EPUB con notas reales
                if is_notebook or has_any_strokes:
                    last_synced_time = state["documents"].get(doc_id, 0)
                    if last_synced_time < last_modified:
                        docs_to_sync.append((item, last_modified, name, root_folder))
                    
    if not docs_to_sync:
        print("No hay apuntes o cuadernos nuevos o modificados en las carpetas. Todo al día.")
        sys.exit(0)
        
    print(f"Se detectaron {len(docs_to_sync)} documentos nuevos o modificados para procesar:")
    for _, _, name, root_folder in docs_to_sync:
        print(f" - {name} (Carpeta: {root_folder})")
        
    # 5. Exportar y enrutar
    success_count = 0
    for item, last_modified, name, root_folder in docs_to_sync:
        print(f"\nProcesando: '{name}' ({root_folder})...")
        try:
            # 5.1 Determinar si requiere IA (Gemini)
            has_ia_prefix = False
            cleaned_name = name
            
            # Detectar prefijo [IA] o IA_ (sin importar mayúsculas)
            match = re.match(r'^\[?IA\]?[\s_-]*(.*)$', name, re.IGNORECASE)
            if match:
                has_ia_prefix = True
                cleaned_name = match.group(1).strip()
                
            # Regla de enrutamiento y análisis IA
            process_with_ai = False
            if root_folder == "4º Física":
                # La carrera siempre pasa por IA (Inbox)
                dest_dir = inbox_dir
                process_with_ai = True
                output_filename = clean_filename(name) + ".pdf"
            else: # "Extra"
                if has_ia_prefix:
                    # Solo con prefijo va a IA (Inbox)
                    dest_dir = inbox_dir
                    process_with_ai = True
                    output_filename = clean_filename(cleaned_name) + ".pdf"
                else:
                    # Va directo a Obsidian sin pasar por IA
                    process_with_ai = False
                    dest_dir = os.path.abspath(os.path.join(config.VAULT_PATH, "Extra")).replace("\\", "/")
                    output_filename = clean_filename(name) + ".pdf"
                    
            os.makedirs(dest_dir, exist_ok=True)
            output_pdf_path = os.path.join(dest_dir, output_filename).replace("\\", "/")
            
            # 5.2 Renderizar a PDF. Preferimos rmc (soporta el formato nuevo del
            #     reMarkable y deja la letra legible); si falla, caemos a rmrl.
            doc_source_path = os.path.join(cache_dir, item["id"]).replace("\\", "/")
            print(" -> Renderizando anotaciones a PDF (rmc)...")
            try:
                pdf_stream = render_annotated(doc_source_path)
            except Exception as e_rmc:
                print(f"    [aviso] rmc falló ({e_rmc}); usando rmrl como respaldo...")
                pdf_stream = render(doc_source_path)
            with open(output_pdf_path, "wb") as f_out:
                shutil.copyfileobj(pdf_stream, f_out)
                
            # 5.3 Crear nota markdown de acompañamiento si no pasa por la IA
            if not process_with_ai:
                note_filename = clean_filename(cleaned_name) + ".md"
                note_path = os.path.join(dest_dir, note_filename).replace("\\", "/")
                
                # Crear contenido de la nota incrustando el PDF renderizado
                note_content = f"# {cleaned_name}\n\n![[{output_filename}]]\n"
                with open(note_path, "w", encoding="utf-8") as f_note:
                    f_note.write(note_content)
                print(f" -> Guardado directo en Obsidian (Sin IA): {output_filename} y {note_filename}")
            else:
                print(f" -> Enviado a Inbox para análisis IA: {output_filename}")
                
            state["documents"][item["id"]] = last_modified
            save_state(state_path, state)
            success_count += 1
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f" [ERROR] Falló el procesamiento de '{name}': {e}")

            
    print("\nSincronización local e inteligente completada.")
    print(f"Resultado: {success_count} de {len(docs_to_sync)} exportados correctamente.")

if __name__ == "__main__":
    sync()
