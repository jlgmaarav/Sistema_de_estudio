import os
import re
from datetime import datetime
import config
import repeticion

def slugify(text: str) -> str:
    """Convierte texto en un formato limpio para nombres de archivos de Windows."""
    if not text:
        return ""
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

def parse_yaml_field(content: str, field_name: str) -> str:
    match = re.search(rf'^{field_name}:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else ""

def parse_yaml_list(content: str, field_name: str) -> list[str]:
    # Buscar lista indentada
    pattern = rf'^{field_name}:\s*\n((?:\s*-\s*.*?\n)+)'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        # Buscar lista en línea ej: [error_001, error_002]
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

def scan_vault():
    stats = {
        "ejercicios": [],
        "intentos": [],
        "errores": [],
        "conceptos": []
    }
    
    # 1. Escanear Ejercicios (recursivamente en Estudios/Asignaturas)
    if os.path.exists(config.ASIGNATURAS_DIR):
        for root, dirs, files in os.walk(config.ASIGNATURAS_DIR):
            for file in files:
                if file.endswith(".md") and "/ejercicios" in root.replace("\\", "/").lower():
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    exerc_id = parse_yaml_field(content, "id")
                    if not exerc_id:
                        exerc_id = os.path.splitext(file)[0]
                    asignatura = parse_yaml_field(content, "asignatura")
                    tema = parse_yaml_field(content, "tema")
                    estado = parse_yaml_field(content, "estado")
                    # ``proxima_revision`` es el nombre antiguo. Se conserva
                    # como dato histórico para migración, pero ya no alimenta
                    # ninguna cola: la agenda académica pertenece al perfil
                    # de nodos del knowledge graph.
                    proxima_reintento = parse_yaml_field(content, "proxima_reintento")
                    proxima_legacy = parse_yaml_field(content, "proxima_revision")
                    tiene_error = parse_yaml_field(content, "tiene_error") == "true"
                    
                    stats["ejercicios"].append({
                        "id": exerc_id,
                        "asignatura": asignatura,
                        "tema": tema,
                        "estado": estado if estado else "nuevo",
                        "proxima_reintento": proxima_reintento,
                        "proxima_revision_legacy": proxima_legacy,
                        # Compatibilidad de lectura: solo el campo nuevo se
                        # expone como fecha operativa.
                        "proxima_revision": proxima_reintento,
                        "tiene_error": tiene_error,
                        "path": path
                    })
                    
    # 2. Escanear Intentos
    if os.path.exists(config.INTENTOS_DIR):
        for file in os.listdir(config.INTENTOS_DIR):
            if file.endswith(".md") and file.startswith("intento_"):
                path = os.path.join(config.INTENTOS_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                attempt_id = parse_yaml_field(content, "id")
                ejercicio = parse_yaml_field(content, "ejercicio_origen").replace("[[", "").replace("]]", "")
                resultado = parse_yaml_field(content, "resultado")
                tiene_error = parse_yaml_field(content, "tiene_error") == "true"
                fecha = parse_yaml_field(content, "fecha_intento")
                
                stats["intentos"].append({
                    "id": attempt_id,
                    "ejercicio": ejercicio,
                    "resultado": resultado,
                    "tiene_error": tiene_error,
                    "fecha": fecha
                })
                
    # 3. Escanear Errores
    if os.path.exists(config.ERRORES_DIR):
        for file in os.listdir(config.ERRORES_DIR):
            if file.endswith(".md") and file.startswith("error_"):
                path = os.path.join(config.ERRORES_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                err_id = parse_yaml_field(content, "id")
                asignatura = parse_yaml_field(content, "asignatura")
                tema = parse_yaml_field(content, "tema")
                tipos = parse_yaml_list(content, "tipo_error")
                resuelto = parse_yaml_field(content, "resuelto") == "true"
                
                stats["errores"].append({
                    "id": err_id,
                    "asignatura": asignatura,
                    "tema": tema,
                    "tipos": tipos,
                    "resuelto": resuelto
                })
                
    # 4. Escanear Conceptos
    if os.path.exists(config.CONCEPTOS_DIR):
        for file in os.listdir(config.CONCEPTOS_DIR):
            if file.endswith(".md"):
                path = os.path.join(config.CONCEPTOS_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                concept_id = parse_yaml_field(content, "id")
                # Si no hay campo id, usar el nombre del archivo sin extensión
                if not concept_id:
                    concept_id = os.path.splitext(file)[0]
                
                dominio_str = parse_yaml_field(content, "dominio_actual")
                try:
                    dominio = float(dominio_str)
                except ValueError:
                    dominio = 0.0
                    
                stats["conceptos"].append({
                    "concepto": concept_id,
                    "dominio": dominio
                })
                
    return stats

def run():
    print("Escaneando bóveda de Obsidian...")
    data = scan_vault()
    
    total_ejercicios = len(data["ejercicios"])
    total_intentos = len(data["intentos"])
    total_errores = len(data["errores"])
    
    correctos = sum(1 for i in data["intentos"] if i["resultado"] == "correcto")
    incorrectos = total_intentos - correctos
    tasa_exito = (correctos / total_intentos * 100) if total_intentos > 0 else 0.0
    
    # 1. Agenda académica: única y basada en el perfil de nodos.
    hoy = datetime.now().date()
    agenda = []
    try:
        import sys
        kg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_graph")
        if kg_dir not in sys.path:
            sys.path.insert(0, kg_dir)
        import perfil as kg_perfil
        nodos = kg_perfil.cargar_grafos()
        perfil_d = kg_perfil.cargar_perfil()
        agenda = kg_perfil.pendientes_repaso(perfil_d, nodos, hoy)
    except Exception as exc:
        print(f"Aviso: no se pudo cargar la agenda académica del grafo: {exc}")

    # Cola local, separada del calendario conceptual.
    reintentos = [ex for ex in data["ejercicios"] if repeticion.reintento_pendiente(ex, hoy)]
    reintentos.sort(key=lambda x: repeticion.fecha_reintento_de_ejercicio(x) or hoy)
    
    # 2. Análisis Transversal de Errores
    error_counts = {}
    for err in data["errores"]:
        for t in err["tipos"]:
            error_counts[t] = error_counts.get(t, 0) + 1
            
    total_tipos = sum(error_counts.values())
    error_table_rows = []
    for t, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_tipos * 100) if total_tipos > 0 else 0.0
        error_table_rows.append(f"| `{t}` | {count} | {pct:.1f}% |")
    error_table = "\n".join(error_table_rows) if error_table_rows else "| *Ningún error registrado* | - | - |"
    
    # 3. Conceptos Débiles (Top 5 con menor dominio)
    conceptos_debiles = sorted(data["conceptos"], key=lambda x: x["dominio"])[:5]
    concept_rows = []
    for c in conceptos_debiles:
        # Determinar estado cualitativo
        if c["dominio"] >= 0.85:
            estado_c = "Dominado 🟢"
        elif c["dominio"] >= 0.60:
            estado_c = "En proceso 🟡"
        else:
            estado_c = "Crítico 🔴"
        concept_rows.append(f"| [[{c['concepto']}]] | {c['dominio']:.2f} | {estado_c} |")
    concept_table = "\n".join(concept_rows) if concept_rows else "| *Ningún concepto evaluado* | - | - |"
    
    # 4. Distribución por Asignaturas
    subject_stats = {}
    for ex in data["ejercicios"]:
        subj = ex["asignatura"]
        if subj not in subject_stats:
            subject_stats[subj] = {"ejercicios": 0, "intentos": 0, "correctos": 0}
        subject_stats[subj]["ejercicios"] += 1
        
    for i in data["intentos"]:
        # Buscar la asignatura del ejercicio origen
        ex_origin = next((ex for ex in data["ejercicios"] if ex["id"] == i["ejercicio"]), None)
        if ex_origin:
            subj = ex_origin["asignatura"]
            if subj not in subject_stats:
                subject_stats[subj] = {"ejercicios": 0, "intentos": 0, "correctos": 0}
            subject_stats[subj]["intentos"] += 1
            if i["resultado"] == "correcto":
                subject_stats[subj]["correctos"] += 1
                
    subject_rows = []
    for subj, s in sorted(subject_stats.items(), key=lambda x: x[0]):
        tasa = (s["correctos"] / s["intentos"] * 100) if s["intentos"] > 0 else 0.0
        subject_rows.append(f"| [[{slugify(subj)}|{subj}]] | {s['ejercicios']} | {s['intentos']} | {tasa:.1f}% de éxito |")
    subject_table = "\n".join(subject_rows) if subject_rows else "| *Ninguna asignatura registrada* | - | - | - |"
    
    agenda_rows = []
    for item in agenda:
        fecha = datetime.strptime(item["proxima"], "%Y-%m-%d").strftime("%d/%m/%Y")
        estado = f"{item['retraso']} d de retraso" if item["retraso"] else "hoy"
        agenda_rows.append(f"| `{item['id']}` | {item['materia']} | {item['nombre']} | {estado} | {fecha} |")
    agenda_table = "\n".join(agenda_rows) if agenda_rows else "| *No hay conceptos pendientes de repaso académico hoy.* | - | - | - | - |"

    retry_rows = []
    for ex in reintentos:
        fecha = ex.get("proxima_reintento") or "—"
        retry_rows.append(f"| [[{ex['id']}]] | [[{slugify(ex['asignatura'])}|{ex['asignatura']}]] | [[{slugify(ex['tema'])}|{ex['tema']}]] | {fecha} |")
    retry_table = "\n".join(retry_rows) if retry_rows else "| *No hay reintentos locales pendientes.* | - | - | - |"
    
    # Renderizar plantilla completa
    dashboard_content = f"""# 📊 Panel de Control (Dashboard de Estudio)

*Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

---

## 📅 Agenda de Repaso Académica (Física)
| Nodo | Asignatura | Concepto | Estado | Próxima Revisión |
| :--- | :--- | :--- | :---: | :---: |
{agenda_table}

## 🔁 Reintentos locales de ejercicios
| Ejercicio | Asignatura | Tema | Próximo reintento |
| :--- | :--- | :--- | :---: |
{retry_table}

---

## 📈 Resumen de Progreso
* **Total de Ejercicios:** `{total_ejercicios}`
* **Intentos Realizados:** `{total_intentos}` (✅ `{correctos}` Correctos / ❌ `{incorrectos}` Erróneos o Incompletos)
* **Tasa de Aprobación Global:** `{tasa_exito:.1f}%`
* **Errores Históricos Detectados:** `{total_errores}`

---

## 🧠 Conceptos Físicos con Mayor Dificultad (Top 5 Debilidades)
| Concepto | Nivel de Dominio (0.0 - 1.0) | Estado de Alerta |
| :--- | :---: | :---: |
{concept_table}

---

## ⚠️ Análisis Transversal de Errores (Frecuencia)
| Tipo de Error | Frecuencia | Porcentaje |
| :--- | :---: | :---: |
{error_table}

---

## 📚 Progreso por Asignatura
| Asignatura | Nº Ejercicios | Nº Intentos | Rendimiento |
| :--- | :--- | :---: | :---: |
{subject_table}
"""

    with open(config.DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(dashboard_content)
    print(f"Dashboard actualizado correctamente en: {config.DASHBOARD_PATH}")

if __name__ == "__main__":
    run()
