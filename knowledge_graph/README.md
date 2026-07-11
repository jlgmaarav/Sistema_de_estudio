# Knowledge Graph — Sistema de Estudio

Grafos de conocimiento estilo Math Academy: nodos granulares (1 nodo ≈ 1 lección de ~10 min de teoría + problemas representativos) unidos por aristas de prerrequisito. Son la base para calcular la frontera de conocimiento, prescribir estudio y propagar crédito de repaso implícito.

## Formato

Un archivo JSON por asignatura/materia. El esquema es agnóstico al contenido (sirve para física, póker o cualquier otra cosa).

```json
{
  "esquema_version": 1,
  "materia": "Electromagnetismo",
  "codigo_uva": "45758",
  "temas": { "0": "Nombre del tema...", "1": "..." },
  "nodos": [
    {
      "id": "em.1.02",
      "tema": 1,
      "nombre": "Ley de Coulomb y superposición",
      "descripcion": "Una línea que delimita qué cubre el nodo.",
      "prerequisitos": [
        { "id": "em.1.01", "peso": 1.0 },
        { "id": "em.0.01", "peso": 0.5 }
      ],
      "fuentes": { "wangsness": "2-2, 2-3", "griffiths": "2.1.2", "problemas": "cap. 2" }
    }
  ]
}
```

## Semántica de los campos

- **id**: `<materia>.<tema>.<orden>`. Estable: no renumerar al insertar nodos (usar sufijos tipo `em.1.02b` si hace falta intercalar).
- **prerequisitos.peso**:
  - `1.0` — prerrequisito duro que además se ejercita como subskill al practicar este nodo (relación de *encompassing*: resolver problemas de este nodo cuenta como repaso implícito del prerrequisito).
  - `0.5` — prerrequisito blando: conviene conocerlo, recibe crédito de repaso parcial.
- **fuentes**: sección exacta en la bibliografía. `problemas` = "Electromagnetismo. Problemas resueltos" (el de los capítulos con problemas resueltos/propuestos), que alimentará el banco de ejercicios por nodo.
- Las aristas siempre apuntan a nodos anteriores en el orden del archivo → el grafo es acíclico por construcción. `validar_grafo.py` lo comprueba.

## Convenciones de granularidad

- Un nodo debe poder dominarse en una sesión: dosis mínima de teoría + 3–10 problemas.
- Si un epígrafe de la guía docente contiene dos técnicas evaluables distintas (p. ej. "método de las imágenes" con plano vs. esfera), se divide en dos nodos.
- El "Tema 0" recoge prerrequisitos matemáticos que la guía asume (cálculo vectorial); normalmente arrancarán ya dominados tras el diagnóstico inicial.

## Aristas entre asignaturas

Un prerrequisito puede apuntar a un nodo de otro archivo usando su id completo (p. ej. `el.1.09` requiere `em.4.01`). La validación se hace siempre sobre el grafo fusionado, pasando todos los archivos a la vez.

## Alcance y granularidad

Hay un grafo por asignatura del Grado en Física (28 archivos). Dos niveles de granularidad, marcados en el campo `granularidad`:

- **`fina`** (~1 nodo = 1 lección): asignaturas pendientes de cursar — Electromagnetismo, Gravitación y Cosmología, y todo 4º (Electrónica, Electrodinámica, Atómica, Nuclear, Estado Sólido, Mecánica Cuántica, Simetrías).
- **`gruesa`/`media`** (~1 nodo = 1 bloque de la guía docente): asignaturas ya cursadas de 1º a 3º. Sirven como ancla de prerrequisitos; se pueden refinar a granularidad fina cuando se quiera aplicar el método completo sobre ellas.

Cada archivo lleva `curso` (1–4), usado por el mapa para ordenar y colorear.

## Flujo de trabajo

1. Editar el JSON (o pedirle a la IA que lo haga).
2. `python validar_grafo.py *.json` (pasando todos los archivos) — valida ids, duplicados, ciclos (incluidas aristas cruzadas) y regenera los `REVISION_<materia>.md` para revisión humana.
3. `python generar_visor.py <archivo.json>` — visor por asignatura (listas por tema, clic → prerrequisitos).
4. `python generar_mapa.py <todos los .json>` — mapa global estilo Math Academy (`mapa_conocimiento.html`, usa `_plantilla_mapa.html`).
5. `python actualizar_taxonomia.py <todos los .json>` — regenera `../taxonomy_uva.json` para el clasificador Gemini a partir de los grafos.
6. El resto del sistema (clasificador Gemini, perfil de conocimiento, planificador) consume los JSON como fuente de verdad.

## Perfil de conocimiento (`perfil.py` + `perfil.json`)

Estado por nodo: `dominio` (0–1), `reps`, `intervalo` de repaso, `ultima`, `proxima` e historial. Se actualiza por dos vías:

- **Automática**: cada intento corregido por el pipeline (`analizar.py`) registra los `nodos_detectados` que devuelve Gemini (elegidos del catálogo de nodos que va en el prompt; si vienen vacíos, se mapean los conceptos por similitud). Éxito = resultado "correcto" sin errores.
- **Manual**: `python perfil.py registrar em.1.07 [--fallo]` o `registrar-conceptos`.

Mecánica del motor:
- Éxito directo: dominio += (1−d)·0.35, intervalo progresa por [1,3,7,14,30,60,120,240] días. Fallo: dominio ×0.55, repaso mañana.
- **Crédito implícito** (la pieza Math Academy): al resolver un nodo con éxito, sus ancestros reciben crédito = producto de pesos × 0.6^profundidad (mínimo 0.1), que sube su dominio y pospone su repaso — repasas lo viejo aprendiendo lo nuevo.
- **Curva de olvido**: el dominio efectivo decae exponencialmente cuando pasa la fecha de revisión.
- **Frontera** (`perfil.py frontera`): nodos no dominados con todos los prerrequisitos duros (peso 1.0) por encima de 0.7 de dominio efectivo.
- `perfil.py marcar-cursadas` inicializa las asignaturas ya aprobadas (granularidad no fina) a dominio 0.75 con repaso a 180 días.
- Tras cada registro se regenera `mapa_conocimiento.html`: relleno = dominio, hueco = sin practicar.

## Banco de problemas (`clasificar_problemas.py` + `banco_problemas.json`)

`python clasificar_problemas.py <transcripcion.md> <grafo.json>` parsea un MD de hojas de problemas (`# Tema` / `## Hoja` / `### N.- título`) y etiqueta cada problema con los nodos que ejercita (Gemini en lotes; respaldo por tema si falla). Electromagnetismo: 229 problemas de las hojas de los profesores, 79/94 nodos con problemas específicos. Para añadir otra asignatura: transcribe sus hojas al mismo formato y ejecuta el script.

## Planificador orientado a exámenes (`planificar.py` + `examenes.json`)

**EDITA `examenes.json`** con tus fechas reales (y borra asignaturas que no curses; `temas` acota qué temas entran en un parcial). Después:

- `python planificar.py` — plan de hoy, guardado también como `Plan de Estudio.md` en el vault.
- `python planificar.py --fecha 2026-12-01` — simula el plan de otro día (para decidir cuándo empezar).
- `python planificar.py --minutos 90` — otro presupuesto diario.

Diseño (planificación hacia atrás desde el examen):
1. **Viabilidad**: por examen, nodos con dominio efectivo < 0.7 × (40 min lección + 1.5 repasos × 15 min) ÷ días restantes (menos 3 de buffer) = ritmo requerido en min/día. La suma se compara con tu presupuesto → HOLGADO / AJUSTADO / INSUFICIENTE.
2. **Plan diario**: primero repasos vencidos (máx. 40% del tiempo), luego lecciones nuevas de la frontera priorizando la asignatura con más presión de examen y los nodos que repasan implícitamente prerrequisitos vencidos (menos repaso explícito). Cada nodo sale con su teoría (secciones de libro) y sus problemas del banco (rotan a diario).

## Documentos

- `ARQUITECTURA_electromagnetismo.md` — diagnóstico epistémico del itinerario (skill `curriculum-knowledge-architecture-designer`): qué parte es jerárquica (el grafo), cuál horizontal (elección de método → interleaving) y cuál disposicional (rigor/modelización → reflexión + dashboard, nunca nota automática).
- `VERIFICACION_MATH_ACADEMY.md` — auditoría de los 7 principios del método contra la implementación.
- `PROTOCOLO_NUEVA_MATERIA.md` — **cómo montar todo esto para aprender cualquier otra cosa** (póker, programación, IA...): checklist de 5 inputs del usuario + 7 pasos que ejecuta la IA. El motor es agnóstico al contenido.
