# Sistema de estudio asistido por IA

Aplicación local para organizar y practicar el estudio universitario con grafos de conocimiento, recuperación espaciada y apoyo de inteligencia artificial. Se creó para el Grado en Física y combina una interfaz web, herramientas de voz y seguimiento del aprendizaje.

## Qué permite hacer

- Representar asignaturas, conceptos y prerrequisitos como grafos de conocimiento.
- Seguir por separado el dominio conceptual y la fluidez, y registrar errores y avances por sesión.
- Practicar con preguntas y problemas vinculados a conceptos concretos.
- Mantener continuidad entre sesiones sin delegar en la IA la elección del contenido ni la actualización directa del estado académico.
- Dictar razonamientos, transcribir audio localmente y recibir retroalimentación estructurada con ayuda de un tutor de IA.
- Exportar contexto legible y estructurado para trabajar con distintos asistentes.
- Guardar apuntes en una bóveda de Obsidian configurable.

## Cómo funciona

```text
Estudiante
   ↓ texto o voz
Centro de Estudio (Python + Flask)
   ├── grafos de conocimiento y estado de aprendizaje
   ├── práctica, sesiones y apuntes
   └── contexto estructurado para el tutor de IA
            ↓
       respuesta revisada
            ↓
La aplicación valida y registra los cambios
```

La aplicación y los datos de estudio se ejecutan localmente. La transcripción de voz usa Whisper local; la interacción con el tutor de IA se realiza mediante el flujo configurado por el usuario. Las respuestas se revisan y pasan por la aplicación antes de actualizar el seguimiento.

## Tecnologías

- Python y Flask para la aplicación y sus servicios locales.
- JavaScript, HTML y CSS para la interfaz web.
- JSON para los grafos, el perfil de aprendizaje y los formatos de intercambio.
- faster-whisper para transcripción local de voz.
- Obsidian como destino configurable para notas y materiales personales.

## Puesta en marcha

Se requiere Python y las dependencias indicadas en `requirements.txt`.

```bash
python -m venv .venv
```

Activa el entorno virtual y luego instala las dependencias:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS o Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Copia `.env.example` a `.env` y configura `VAULT_PATH` si quieres guardar las notas en una bóveda de Obsidian. Inicia el servidor con `python app.py`; en Windows también puedes usar `iniciar_centro_estudio.bat`. La aplicación se abre en `http://localhost:5000`.

## Estructura del proyecto

| Ruta | Contenido |
| --- | --- |
| `app.py` | Aplicación web y API local. |
| `knowledge_graph/` | Grafos de asignaturas, herramientas del motor y visualizaciones. |
| `study_sessions.py` | Flujo y registro de sesiones de estudio. |
| `study_context.py` | Construcción y exportación del contexto para tutores de IA. |
| `apuntes.py` | Gestión y generación de apuntes por concepto. |
| `buscar_web.py` | Preparación de búsquedas asistidas por IA y recepción de resultados. |
| `templates/`, `static/` | Interfaz web. |
| `tests/` | Pruebas automatizadas del proyecto. |

## Privacidad y datos

El repositorio contiene el código y los datos de ejemplo necesarios para entender el sistema. El perfil personal, el historial de sesiones, el banco privado de problemas, las credenciales, las grabaciones, los materiales de clase y los apuntes generados deben permanecer en el equipo local y están excluidos mediante `.gitignore`. No se incluyen PDFs de libros ni materiales docentes.

## Resumen para el currículum

**Sistema de estudio asistido por IA — proyecto personal.** Diseño y desarrollo de una aplicación web local en Python/Flask y JavaScript para apoyar el estudio universitario mediante grafos de conocimiento, práctica espaciada, seguimiento de sesiones, transcripción local de voz e integración con tutores de inteligencia artificial.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [`LICENSE`](LICENSE).
