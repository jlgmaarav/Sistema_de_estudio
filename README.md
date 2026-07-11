# EstudioIA — Mastery learning con knowledge graphs e IA

Sistema personal de estudio para el Grado en Física (UVa) que implementa la metodología de
[Math Academy](https://www.mathacademy.com/) — knowledge graph + mastery learning + repetición
espaciada — usando IA generativa (Gemini) como corrector, clasificador y generador de lecciones.

**El bucle completo:** el mapa dice dónde estás → el plan dice qué estudiar hoy → resuelves a mano
(reMarkable/papel) → subes la foto → la IA transcribe tu manuscrito, lo corrige paso a paso,
clasifica tus errores y actualiza tu perfil de conocimiento → el plan de mañana ya lo sabe.

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

> Ejecuta **un solo** watcher a la vez (un cerrojo lo garantiza). `Corregir.bat` a demanda es lo recomendado.

CLI equivalente: `python knowledge_graph/perfil.py estado|frontera|vencidos|registrar`,
`python knowledge_graph/planificar.py [--fecha YYYY-MM-DD]`.

## Generalización a cualquier materia

El motor es agnóstico al contenido. `knowledge_graph/PROTOCOLO_NUEVA_MATERIA.md` documenta el
bootstrap "quiero aprender X" (póker, programación, IA...): 5 inputs del usuario → la IA construye
el grafo, el banco y las metas en una sesión. Incluye el diagnóstico epistémico previo
(Bernstein/Maton, ver `SKILL.md`) para saber qué parte del dominio es jerárquica.

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

*Los grafos de conocimiento y el código son obra propia.*
