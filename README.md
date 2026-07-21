# EstudioIA — Mastery learning con knowledge graphs e IA

Sistema personal de estudio para el Grado en Física (UVa) que implementa la metodología de
[Math Academy](https://www.mathacademy.com/) — knowledge graph + mastery learning + repetición
espaciada — usando IA generativa (Gemini y Claude) como corrector, clasificador y generador de lecciones.

**El bucle completo:** el mapa dice dónde estás → el plan dice qué estudiar hoy → resuelves a mano
(reMarkable/papel) → subes la foto → la IA transcribe tu manuscrito, lo corrige paso a paso,
clasifica tus errores y actualiza tu perfil de conocimiento → el plan de mañana ya lo sabe.

**Dos formas de entrada:** subir la **foto** del manuscrito (corrige **Gemini**), o **narrar en alto**
tu razonamiento mientras resuelves —método Feynman— y dejar que **Whisper** transcriba tu voz y
**Claude** la corrija con rigor de profesor: marca los saltos no justificados, distingue error
conceptual de matemático y etiqueta los fallos por nodo del grafo. Ambas actualizan el mismo mapa.

## Cómo se ha construido

Un proyecto complejo (motor de mastery learning, app web Flask, pipeline de visión + corrección con
IA, integración con reMarkable) desarrollado íntegramente con herramientas de IA de última generación:

- **[Claude Code](https://claude.com/claude-code)** (modelos **Fable 5** y **Opus 4.8**) — desarrollo
  principal: arquitectura, motor del knowledge graph, app web, pipeline de corrección y toda la lógica.
- **Antigravity** (**Gemini 3.1 Pro** y **Gemini 3.5 Flash**) — apoyo en diseño y prototipado.

En tiempo de ejecución hay dos correctores: los **manuscritos** (foto) los corrige **Gemini** (3.5 Flash
principal, con respaldo a un modelo más ligero); la **narración por voz** la corrige **Claude** (Opus 4.8,
con respaldo a Sonnet) a través de Claude Code, usando la suscripción y sin API de pago. Sirve como
referencia de qué se puede construir hoy combinando estas herramientas.

## Los 7 principios del método (y dónde viven)

| Principio | Implementación |
|---|---|
| 1. Identificar lo que ya sabes | Inicialización de cursadas + quiz diagnóstico por materia |
| 2. Knowledge graph → perfil personal | 28 grafos (451 nodos, 725 aristas de prerrequisito con peso), `perfil.json` por nodo, mapa con dominio sombreado |
| 3. Enseñar solo en la frontera | `frontera()`: nodos con prerrequisitos duros ≥ 0.7 de dominio efectivo |
| 4. Dosis mínima de instrucción + práctica activa | Lecciones IA cacheadas (explicación + ejemplo resuelto + reglas de oro) + banco de 229 problemas reales etiquetados por nodo |
| 5. Mastery obligatorio, caminos paralelos | ~3 éxitos para dominar; el fallo y el olvido (curva exponencial) bloquean dependientes; frontera multi-rama |
| 6. Repetición espaciada + quizzes cronometrados | Intervalos expansivos por nodo + quiz a libro cerrado con interleaving + simulacros de examen |
| 7. Repasar lo viejo aprendiendo lo nuevo | Crédito implícito a los prerrequisitos (pesos × 0.6^profundidad) al resolver con éxito |

Además: **planificación hacia atrás desde los exámenes** (carga restante ÷ días = ritmo requerido,
semáforo de viabilidad, ritmo real vs. necesario con proyección de fecha de fin).

## Arquitectura

```
Inbox/  ←– foto del manuscrito (reMarkable sync o subida web)
  │  watcher.py
  ▼
gemini_client.py ──► Gemini: transcripción LaTeX + corrección paso a paso
  │                  + taxonomía de errores + nodos del grafo ejercitados
  ▼
analizar.py ──► notas Obsidian (ejercicio/intento/error/concepto)
  │
  ▼
knowledge_graph/
  ├── 28 grafos JSON (uno por asignatura; esquema agnóstico al contenido)
  ├── perfil.py      motor: dominio, crédito implícito, olvido, frontera, quiz
  ├── planificar.py  plan diario orientado a exámenes + ritmo real
  ├── lecciones.py   lecciones mínimas IA (cacheadas)
  ├── clasificar_problemas.py  banco de problemas etiquetado por IA
  └── generar_mapa.py  mapa interactivo (canvas, fuerza dirigida)
  │
  ▼
app.py ──► app web (Flask): plan del día, sesión guiada, mapa, quizzes,
           simulacros, editor de exámenes, subidas — cero edición de código
```

### Estudio por voz (método Feynman)

```
grabaciones/  ←– audio de tu narración mientras resuelves
  │  transcribir.py ──► Whisper (faster-whisper, local y gratis): voz → texto
  ▼
corregir_voz.py ──► Claude (claude -p, tu suscripción, sin API de pago):
  │                  corrección de profesor exigente → mismo AnalysisResponse
  ▼
watcher._procesar_una_solucion ──► mismas fichas Obsidian + grafo/XP + app
                                    (idéntico al flujo del reMarkable)
```

## Estructura del proyecto

```
├── app.py  watcher.py  corregir.py  sync_remarkable.py   # puntos de entrada
├── app_biblioteca.py                                     # app aparte (estudio no-carrera)
├── gemini_client · schemas · analizar · file_manager     # pipeline de IA y notas
├── transcribir.py · corregir_voz.py                      # estudio por voz (Whisper + Claude)
├── config · templates · buscar · generar_dashboard       # utilidades y app
├── knowledge_graph/    # motor (perfil, planificar, gamificación…) + 28 grafos JSON
├── remarkable_sync/    # sincronización con el reMarkable
├── static/ · templates/   # frontend de la app web
├── tests/             # pytest (motor del knowledge graph)
├── docs/              # documentación de diseño
└── *.bat              # lanzadores para Windows (Corregir, voz, transcribir, iniciar_*)
```

## Uso

```bash
pip install -r requirements.txt
cp .env.example .env   # añade tu GEMINI_API_KEY

# Datos personales/con copyright que NO se versionan: crea los tuyos a partir del ejemplo
cp knowledge_graph/banco_problemas.example.json knowledge_graph/banco_problemas.json

iniciar_centro_estudio.bat   # servidor web (http://localhost:5000)
```

**Flujo de baja fricción con el reMarkable:** resuelve a mano cada problema escribiendo su código
(`3.1` = hoja 3, problema 1). Cuando quieras feedback, ejecuta **`Corregir.bat`** (sincroniza el
reMarkable → una sola llamada a Gemini por hoja, detecta varios problemas → corrección paso a paso).
El resultado aparece en la pestaña **Correcciones** de la app (Obsidian queda solo como registro).
La pestaña **Cómo resolver** tiene el método de Pólya a mano mientras trabajas.

**Estudio por voz (método Feynman):** graba con el móvil mientras resuelves y narras tu razonamiento
(incluidos los caminos equivocados), deja el audio en `grabaciones/` y ejecuta **`voz.bat`**. **Whisper**
transcribe tu voz en local (gratis, sin internet) y **Claude** (Opus 4.8, respaldo a Sonnet si se agota el
límite) la corrige con rigor de profesor —marca cada salto no justificado, distingue error conceptual de
matemático y etiqueta los fallos por nodo—, actualizando el mapa igual que el reMarkable. Solo transcribir:
`transcribir.bat`. No requiere API de pago: usa tu suscripción de Claude Code.

> Ejecuta **un solo** watcher a la vez (un cerrojo lo garantiza). `Corregir.bat` a demanda es lo recomendado.

CLI equivalente: `python knowledge_graph/perfil.py estado|frontera|vencidos|registrar`,
`python knowledge_graph/planificar.py [--fecha YYYY-MM-DD]`.

## Generalización a cualquier materia

El motor es agnóstico al contenido. `knowledge_graph/PROTOCOLO_NUEVA_MATERIA.md` documenta el
bootstrap "quiero aprender X" (póker, programación, IA...): 5 inputs del usuario → la IA construye
el grafo, el banco y las metas en una sesión. Incluye el diagnóstico epistémico previo
(Bernstein/Maton, ver [`docs/SKILL.md`](docs/SKILL.md)) para saber qué parte del dominio es jerárquica.

## Documentación

- [`knowledge_graph/README.md`](knowledge_graph/README.md) — esquema de grafos y herramientas
- [`knowledge_graph/VERIFICACION_MATH_ACADEMY.md`](knowledge_graph/VERIFICACION_MATH_ACADEMY.md) — auditoría de los 7 principios
- [`knowledge_graph/ARQUITECTURA_electromagnetismo.md`](knowledge_graph/ARQUITECTURA_electromagnetismo.md) — diagnóstico epistémico del itinerario
- [`knowledge_graph/PROTOCOLO_NUEVA_MATERIA.md`](knowledge_graph/PROTOCOLO_NUEVA_MATERIA.md) — cómo montar el sistema para otra materia

## Qué no se versiona (repo público)

Para respetar copyright ajeno y la privacidad, estos archivos están en `.gitignore` (crea los tuyos):

- `knowledge_graph/banco_problemas.json` — transcripciones de exámenes/hojas de profesores. Se incluye `banco_problemas.example.json` con el formato.
- `knowledge_graph/perfil.json`, `examenes.json`, `correcciones.json` — tu progreso, fechas y feedback personales.
- `.env` (tu API key), la bóveda de Obsidian, los PDFs de guías y hojas de problemas.
- `grabaciones/` — tus audios de narración por voz y sus transcripciones.

*Los grafos de conocimiento y el código son obra propia.*
