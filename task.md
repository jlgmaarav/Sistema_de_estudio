# Lista de Tareas - Sistema de Estudio Asistido por IA para Física

## Fase 2: Auto-creación de Notas en Obsidian
- [x] Crear plantillas Markdown en `templates.py` para:
  - [x] Asignatura
  - [x] Tema
  - [x] Concepto
- [x] Implementar la creación física de notas en `file_manager.py`:
  - [x] `ensure_subject_note(asignatura)`
  - [x] `ensure_topic_note(asignatura, tema)`
  - [x] `ensure_concept_note(concepto)`
- [x] Modificar `analizar.py` para llamar a la creación de estas notas
- [x] Añadir lógica para actualizar las listas de enlaces dinámicamente en lugar de sobrescribir

## Fase 3: Ingesta de Taxonomía UVa y Auto-clasificación por IA
- [x] Crear el archivo `taxonomy_uva.json` con la lista de asignaturas y sus respectivos bloques temáticos de la UVa
- [x] Modificar `schemas.py` para añadir campos `asignatura_detectada` y `tema_detectado` a `AnalysisResponse`
- [x] Actualizar `gemini_client.py`:
  - [x] Cargar `taxonomy_uva.json` en memoria
  - [x] Incluir el temario de la UVa estructurado en el prompt del sistema
  - [x] Solicitar a Gemini la clasificación automática

## Fase 4: Transcripciones Completas en LaTeX
- [x] Modificar `schemas.py` para añadir `transcripcion_enunciado` en `AnalysisResponse`
- [x] Modificar el prompt en `gemini_client.py`:
  - [x] Instruir para transcribir el enunciado en LaTeX/Markdown completo
  - [x] Instruir para transcribir la solución del alumno de forma matemática y literal paso a paso
- [x] Actualizar `templates.py` para renderizar el enunciado transcrito en la ficha de Ejercicio
- [x] Actualizar `templates.py` para pintar la transcripción literal en la ficha de Intento

## Fase 5: Ingesta Automática mediante Watcher
- [x] Crear el script de fondo `watcher.py`:
  - [x] Bucle de escaneo de `Inbox/` (frecuencia de 3 segundos)
  - [x] Control de bloqueo del archivo (esperar a que termine de escribirse antes de procesar)
  - [x] Ingesta en un solo archivo (tratando el PDF único como enunciado + solución)
  - [x] Llamar a `analizar.py` con auto-clasificación
  - [x] Mover el archivo original a `Inbox/Procesados/`
  - [x] Guardar log de ejecuciones automáticas en `Inbox/watcher.log`
- [x] Actualizar `config.py` para definir y crear directorios de `Inbox/` y `Inbox/Procesados/`
- [x] Crear un archivo ejecutable/script de ayuda en Windows (por ejemplo, `iniciar_watcher.bat`) para que el usuario pueda levantar el watcher con doble clic

## Fase 6: Spaced Repetition (Repetición Espaciada)
- [x] Modificar `templates.py` para que la plantilla de ejercicio contenga metadatos `estado` y `proxima_revision`
- [x] Implementar el algoritmo de espaciado en `file_manager.py`:
  - [x] Función para recalcular y actualizar la fecha de revisión y el estado según los resultados del intento
- [x] Adaptar `analizar.py` para invocar el recalculo del espaciado tras cada intento

## Fase 7: Dashboard de Errores y Conceptos Débiles
- [x] Crear el script `generar_dashboard.py`:
  - [x] Parsea todos los ficheros `.md` de la bóveda
  - [x] Calcula el porcentaje de tipos de errores y causas comunes
  - [x] Genera un ranking de los 5 conceptos más débiles del estudiante
  - [x] Lista los ejercicios pendientes de repetir hoy
- [x] Diseñar en `templates.py` la plantilla Markdown para el `Dashboard.md`
- [x] Hacer que `analizar.py` y `watcher.py` ejecuten automáticamente `generar_dashboard.py` al finalizar cada análisis

## Fase 8: Extractor Automático de Exámenes
- [x] Añadir en `schemas.py` el modelo de datos `ExamExtractionResponse` para los problemas del examen
- [x] Diseñar el prompt en `gemini_client.py` para dividir exámenes en ejercicios independientes
- [x] Implementar en `watcher.py` la lógica de bifurcación: si el nombre tiene "examen", llama al extractor de exámenes
- [x] Crear los ejercicios individuales a partir de la respuesta del extractor de exámenes

## Fase 9: Búsqueda Semántica Asistida por IA
- [x] Crear el script `buscar.py`:
  - [x] Leer resúmenes de la bóveda para enviárselos a Gemini junto a la consulta del usuario
  - [x] Generar la nota interactiva `Resultados de Búsqueda.md` con enlaces directos

## Fase 10: Backend y API Flask (`app.py`)
- [x] Instalar `flask` y `flask-cors` e incluirlos en `requirements.txt`
- [x] Implementar la API REST en `app.py` expeliendo JSON del vault en tiempo real
- [x] Servir la carpeta `/Assets` como archivos estáticos
- [x] Integrar el endpoint de búsqueda semántica y de nuevos intentos

## Fase 11: Frontend de Alta Estética (`index.html` y estáticos)
- [x] Crear la estructura HTML con layout responsivo de pestañas (Dashboard, Asignaturas, Libros, Buscar)
- [x] Implementar KaTeX en el frontend para renderizar ecuaciones LaTeX
- [x] Añadir estilos CSS premium oscuros con efectos de glassmorphism y transiciones fluidas
- [x] Escribir la lógica JS (`app.js`) para cargar la API, alternar pantallas, buscar y filtrar elementos

## Fase 12: Módulo de Lecturas de No Ficción
- [x] Actualizar `config.py` para añadir y crear `LECTURAS_DIR`
- [x] Crear la plantilla `render_book_template` en `templates.py`
- [x] Añadir lógica de escaneo e ingesta de libros en `file_manager.py`
- [x] Exponer los libros en el backend (`/api/books`) y diseñar la sección visual en el frontend

## Fase 13: Watcher Integrado y Scripts de Windows
- [x] Crear el script de arranque dual `iniciar_centro_estudio.bat` para levantar el watcher y el servidor en paralelo
- [x] Realizar pruebas integrales y verificar que la comunicación en tiempo real funciona

## Fase 14: Gestión de Proyectos y Separación de Bóveda
- [ ] Actualizar `config.py` para definir y auto-crear `PROYECTOS_DIR`
- [ ] Crear la plantilla `render_project_template` en `templates.py` y actualizar `render_book_template` para aceptar proyectos
- [ ] Añadir funciones `ensure_project_note(...)` y linking de libros en `file_manager.py`
- [ ] Modificar `generar_dashboard.py` para separar agendas (académica y personal) e indexar proyectos
- [ ] Implementar endpoints en `app.py` para `/api/projects`, `/api/projects/<id>` y `/api/projects/new`
- [ ] Adaptar el frontend (`templates/index.html` y `static/app.js`) para dividir la UI en Áreas y agrupar libros por proyecto/sección

## Fase 15: Semillero (Seeding) de Proyectos y Libros Iniciales
- [ ] Crear el script `seed_data.py` con los 3 proyectos y los 14 libros iniciales clasificados
- [ ] Ejecutar el script y validar la creación de todas las notas físicas en Obsidian

## Integración de Tablet reMarkable (Local & Offline)
- [x] Instalar librería de renderizado `rmrl` en el `venv`
- [x] Resolver conflictos de dependencias (`setuptools`, `reportlab>=5.0.0`)
- [x] Crear el módulo `remarkable_sync` con script de escaneo y conversión local (`sync.py`)
- [x] Añadir el script de entrada `sync_remarkable.py`
- [x] Crear el lanzador directo `iniciar_sync_remarkable.bat`
- [x] Modificar `iniciar_centro_estudio.bat` para sincronizar automáticamente al arranque
- [x] Actualizar `requirements.txt`


