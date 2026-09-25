from datetime import datetime
from typing import List
import re

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

# Caracteres que Windows PROHÍBE en un nombre de archivo. El peligroso de verdad es
# la barra invertida: la IA devuelve conceptos con LaTeX ("$dV=4\pi r^2dr$") y Windows
# la interpreta como separador de carpetas -> FileNotFoundError al crear la nota.
# Pasó el 29/07/2026 con la primera narración de voz real y abortó la actualización
# del knowledge graph entera.
_CARACTERES_PROHIBIDOS = r'[\\/:*?"<>|]'


def nombre_concepto_seguro(concepto: str) -> str:
    """Nombre canónico de un concepto: legible, y válido como archivo en Windows.

    Se usa a la vez para el NOMBRE DEL ARCHIVO y para el enlace `[[...]]` de Obsidian.
    Tienen que salir de la misma función o los enlaces apuntarían a notas inexistentes.
    """
    nombre = concepto.replace("[[", "").replace("]]", "").strip()
    nombre = nombre.replace("\\", "")            # \pi -> pi (no ensucia con guiones)
    nombre = re.sub(_CARACTERES_PROHIBIDOS, "-", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    nombre = nombre.rstrip(". ")                 # Windows no admite punto/espacio final
    if len(nombre) > 120:                        # margen de sobra bajo el límite de ruta
        nombre = nombre[:120].rstrip(". ")
    return nombre or "concepto sin nombre"


def format_concept_links(conceptos: List[str]) -> str:
    """Formatos de lista de conceptos como enlaces de Obsidian entrecomillados para evitar fallos de YAML."""
    if not conceptos:
        return " []"
    lines = []
    for c in conceptos:
        lines.append(f'  - "[[{nombre_concepto_seguro(c)}]]"')
    return "\n" + "\n".join(lines)

def format_links_list(items: List[str]) -> str:
    """Formatos de lista de enlaces como enlaces de Obsidian entrecomillados para evitar fallos de YAML."""
    if not items:
        return " []"
    lines = []
    for i in items:
        clean_i = i.replace("[[", "").replace("]]", "")
        lines.append(f'  - "[[{clean_i}]]"')
    return "\n" + "\n".join(lines)

def render_subject_template(asignatura: str) -> str:
    """Genera la nota de Asignatura."""
    return f"""---
id: "{asignatura}"
tipo: asignatura
---

# Asignatura: {asignatura}

## Temas de la Asignatura
<!-- temas_inicio -->
<!-- temas_fin -->

## Todos los Ejercicios
<!-- ejercicios_inicio -->
<!-- ejercicios_fin -->
"""

def render_topic_template(tema: str, asignatura: str) -> str:
    """Genera la nota de Tema."""
    subject_slug = slugify(asignatura)
    return f"""---
id: "{tema}"
asignatura: "[[{subject_slug}]]"
tipo: tema
---

# Tema: {tema}

- **Asignatura de Origen:** [[{subject_slug}|{asignatura}]]

## Ejercicios del Tema
<!-- ejercicios_inicio -->
<!-- ejercicios_fin -->
"""

def render_concept_template(concepto: str, dominio: float = 0.0) -> str:
    """Genera la nota de Concepto."""
    return f"""---
id: "{concepto}"
tipo: concepto
dominio_actual: {dominio:.2f}
---

# Concepto: {concepto}

## Historial de Evaluación de Dominio
<!-- intentos_inicio -->
| Fecha | Ejercicio | Intento | Dominio Estimado |
| :--- | :--- | :--- | :---: |
| {datetime.now().strftime("%d/%m/%Y")} | - | - | {dominio:.2f} |
<!-- intentos_fin -->
"""

def render_exercise_template(
    exerc_id: str,
    asignatura: str,
    tema: str,
    conceptos: List[str],
    tiene_error: bool,
    enunciado_asset: str,
    enunciado_transcrito: str,
    attempt_id: str,
    estado: str = "nuevo",
    proxima_reintento: str | None = None,
    tipo_recurso: str = "ejercicio",
    origen: str = "",
    fecha_origen: str = "",
    warning_transcripcion: str = "",
    nodos: List[str] | None = None,
    # Compatibilidad con llamadas antiguas: el nombre anterior describía
    # ambiguamente una fecha que ya no controla el calendario académico.
    proxima_revision: str | None = None,
) -> str:
    """Genera la nota de ejercicio.

    ``proxima_reintento`` es únicamente una cola local para repetir un
    ejercicio fallado o incompleto. El repaso académico de conceptos lo
    gobierna ``knowledge_graph/perfil.json``.
    """
    concept_links = format_concept_links(conceptos)
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    if proxima_reintento is None:
        proxima_reintento = proxima_revision or ""
        
    enunciado_render = ""
    if enunciado_asset:
        if enunciado_asset.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')):
            enunciado_render = f"![[{enunciado_asset}]]"
        else:
            enunciado_render = f"[[{enunciado_asset}|Ver Enunciado (PDF/Archivo)]]"
            
    origen_line = f"- **Origen:** {origen} (Fecha: {fecha_origen})" if origen else ""
    
    warning_callout = ""
    if warning_transcripcion:
        warning_callout = f"\n> [!WARNING]\n> **PROBLEMA EN ESTE ARCHIVO, REVISAR:** {warning_transcripcion}\n"
            
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)

    return f"""---
id: "{exerc_id}"
asignatura: "{asignatura}"
tema: "{tema}"
conceptos:{concept_links}
estado: {estado}
fecha_creacion: {fecha_hoy}
proxima_reintento: {proxima_reintento}
tiene_error: {str(tiene_error).lower()}
nodos: [{", ".join(nodos or [])}]
errores_asociados: []
tipo_recurso: "{tipo_recurso}"
origen: "{origen}"
fecha_origen: "{fecha_origen}"
duda_transcripcion: {str(bool(warning_transcripcion)).lower()}
enunciado_asset: "{enunciado_asset}"
---

# Ejercicio: {exerc_id} - {tema}
{warning_callout}
- **Asignatura:** [[{subject_slug}|{asignatura}]]
- **Tema:** [[{topic_slug}|{tema}]]
- **Estado del ejercicio:** `{estado.upper()}`
- **Reintento local:** `{proxima_reintento or 'no programado'}`
{origen_line}

## Enunciado del Problema
{enunciado_transcrito}

---

## Recurso de Enunciado Original
{enunciado_render}

---

## Historial de Intentos
<!-- intentos_inicio -->
""" + (f"* [[{attempt_id}]] - {fecha_hoy} ({'Con errores' if tiene_error else 'Correcto'})" if attempt_id else "*No se han registrado intentos aún.*") + """
<!-- intentos_fin -->
"""

def render_attempt_template(
    attempt_id: str,
    exerc_id: str,
    asignatura: str,
    tema: str,
    resultado: str,
    tiene_error: bool,
    confianza: float,
    motivo_baja_confianza: str,
    transcripcion: str,
    analisis: str,
    conceptos_dominio: list,
    sol_assets: List[str],
    off_assets: List[str],
    contexto: str,
    intento_mental: str,
    errors_ids: List[str]
) -> str:
    """Genera el contenido Markdown para la nota de Intento."""
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    conceptos = [c.concepto for c in conceptos_dominio]
    concept_links = format_concept_links(conceptos)
    errors_links = format_links_list(errors_ids)
    
    # Enlaces a los assets de solución
    soluciones_render = "\n".join([f"![[{asset}]]" if asset.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')) else f"[[{asset}|Solución Manuscrita (Original)]]" for asset in sol_assets])
    
    # Enlaces a los assets de solución oficial
    oficiales_render = "\n".join([f"![[{asset}]]" if asset.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')) else f"[[{asset}|Solución Oficial]]" for asset in off_assets]) if off_assets else "*No se proporcionó solución oficial.*"
    
    # Formatear la tabla de dominio de conceptos
    dominio_rows = []
    for item in conceptos_dominio:
        dominio_rows.append(f"| [[{item.concepto}]] | {item.dominio:.2f} |")
    dominio_table = "\n".join(dominio_rows)
    
    # Formatear lista de errores asociados
    errores_asociados_render = ""
    if errors_ids:
        errores_asociados_render = "\n".join([f"* [[{eid}]]" for eid in errors_ids])
    else:
        errores_asociados_render = "*Ningún error detectado en este intento.*"
        
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)

    return f"""---
id: "{attempt_id}"
ejercicio_origen: "[[{exerc_id}]]"
fecha_intento: {fecha_hoy}
resultado: {resultado}
tiene_error: {str(tiene_error).lower()}
confianza_analisis: {confianza:.2f}
conceptos:{concept_links}
errores_asociados:{errors_links}
---

# Intento: {exerc_id} ({attempt_id})

- **Ejercicio de Origen:** [[{exerc_id}]]
- **Asignatura:** [[{subject_slug}|{asignatura}]]
- **Tema:** [[{topic_slug}|{tema}]]
- **Resultado del Intento:** `{resultado.upper()}`

## Datos del Intento
* **Contexto del Intento:** {contexto if contexto else "*No aportado.*"}
* **Intento Mental (Dudas/Objetivo):** {intento_mental if intento_mental else "*No aportado.*"}

---

## Solución Manuscrita Presentada (Imágenes)
{soluciones_render}

## Solución Oficial de Referencia
{oficiales_render}

---

## Transcripción Literal de la Solución (por la IA)
```latex
{transcripcion}
```

---

## Análisis de la Resolución
* **Confianza de Lectura:** {confianza * 100:.1f}% {f'(Baja por: {motivo_baja_confianza})' if confianza < 0.8 else ''}

### Evaluación Pedagógica
{analisis}

### Estimación de Dominio de Conceptos
| Concepto | Nivel de Dominio |
| :--- | :---: |
{dominio_table}

---

## Errores Registrados en este Intento
{errores_asociados_render}
"""

def render_error_template(
    error_id: str,
    title: str,
    tipo_error: List[str],
    descripcion: str,
    razon: str,
    como_evitarlo: str,
    ejemplo_incorrecto: str,
    ejemplo_correcto: str,
    asignatura: str,
    tema: str,
    conceptos: List[str],
    exerc_id: str,
    attempt_id: str
) -> str:
    """Genera el contenido Markdown para la nota de Error."""
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    concept_links = format_concept_links(conceptos)
    tipo_links = "\n" + "\n".join([f'  - "{t}"' for t in tipo_error]) if tipo_error else "[]"
    
    subject_slug = slugify(asignatura)
    topic_slug = slugify(tema)

    return f"""---
id: "{error_id}"
asignatura: "{asignatura}"
tema: "{tema}"
conceptos:{concept_links}
tipo_error:{tipo_links}
estado: nuevo
fecha_deteccion: {fecha_hoy}
veces_fallado: 1
resuelto: false
ultima_revision: null
ejercicio_origen: "[[{exerc_id}]]"
intento_origen: "[[{attempt_id}]]"
---

# Error {error_id.split('_')[-1]}: {title}

- **Asignatura:** [[{subject_slug}|{asignatura}]]
- **Tema:** [[{topic_slug}|{tema}]]
- **Ejercicio de Origen:** [[{exerc_id}]]
- **Intento de Origen:** [[{attempt_id}]]

## Descripción del Error
{descripcion}

## ¿Por qué ocurrió?
{razon}

## ¿Cómo evitarlo en el futuro?
> [!IMPORTANT]
> {como_evitarlo}

## Ejemplo Corregido

### Paso incorrecto:
$$
{ejemplo_incorrecto}
$$

### Paso corregido:
$$
{ejemplo_correcto}
$$
"""


def render_book_template(
    libro_id: str,
    titulo: str,
    autor: str,
    categoria: str,
    proyecto_id: str = "",
    seccion_proyecto: str = ""
) -> str:
    """Genera la plantilla de notas para libros de no ficción."""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    proyecto_link = f'"[[{proyecto_id}]]"' if proyecto_id else '""'
        
    return f"""---
id: "{libro_id}"
titulo: "{titulo}"
autor: "{autor}"
categoria: "{categoria}"
proyecto: {proyecto_link}
seccion_proyecto: "{seccion_proyecto}"
fecha_registro: {fecha_hoy}
---

# Libro: {titulo}

- **Autor:** {autor}
- **Categoría:** {categoria}
- **Proyecto Asociado:** [[{proyecto_id}]]
- **Sección en Proyecto:** {seccion_proyecto if seccion_proyecto else "General"}

## Notas y Resumen de Lectura
<!-- notas_inicio -->
*Escribe tus notas de lectura aquí.*
<!-- notas_fin -->
"""


def render_project_template(
    proyecto_id: str,
    titulo: str,
    descripcion: str,
    estado: str = "activo",
    etiqueta: str = ""
) -> str:
    """Genera la nota de Proyecto."""
    return f"""---
id: "{proyecto_id}"
titulo: "{titulo}"
estado: {estado}
etiqueta: "{etiqueta}"
---

# Proyecto: {titulo}

{descripcion if descripcion else "*No se ha provisto descripción para este proyecto.*"}

## Libros y Lecturas del Proyecto
<!-- libros_inicio -->
<!-- libros_fin -->

## Tareas y Notas
<!-- tareas_inicio -->
<!-- tareas_fin -->
"""
