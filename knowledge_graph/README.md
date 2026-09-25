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
5. `python actualizar_taxonomia.py <todos los .json>` — regenera `../taxonomy_uva.json` a partir de los grafos.
6. El resto del sistema (perfil de conocimiento, planificador y corrección manual en Gemini Web) consume los JSON como fuente de verdad.

## Perfil de conocimiento (`perfil.py` + `perfil.json`)

Estado por nodo: `dominio` (0–1), `reps`, `intervalo` de repaso, `ultima`, `proxima` e historial. Se actualiza por dos vías:

- **Automática**: cada intento de voz validado localmente tras Gemini Web registra los `nodos_detectados` devueltos por el análisis. Éxito = resultado "correcto" sin errores.
- **Manual**: `python perfil.py registrar em.1.07 [--fallo]` o `registrar-conceptos`.

Mecánica del motor:
- Éxito directo: dominio += (1−d)·0.35, intervalo progresa por [1,3,7,14,30,60,120,240] días. Fallo: dominio ×0.55, repaso mañana.
- **Crédito implícito** (la pieza Math Academy): al resolver un nodo con éxito, sus ancestros reciben crédito = producto de pesos × 0.6^profundidad (mínimo 0.1), que sube su dominio y pospone su repaso — repasas lo viejo aprendiendo lo nuevo.
- **Curva de olvido**: el dominio efectivo decae exponencialmente cuando pasa la fecha de revisión.
- **Frontera** (`perfil.py frontera`): nodos no dominados con todos los prerrequisitos duros (peso 1.0) por encima de 0.7 de dominio efectivo.
- `perfil.py marcar-cursadas` inicializa las asignaturas ya aprobadas (granularidad no fina) a dominio 0.75 con repaso a 180 días.
- Tras cada registro se regenera `mapa_conocimiento.html`: relleno = dominio, hueco = sin practicar.

Este perfil es la única fuente de verdad del calendario académico. Las notas
de ejercicios en la bóveda pueden tener `estado` y `proxima_reintento`, pero
esa fecha solo sirve para repetir localmente un problema fallado o incompleto;
no compite con `proxima` del nodo ni aparece como repaso académico duplicado.

## Banco de problemas (`clasificar_problemas.py` + `banco_problemas.json`)

`python clasificar_problemas.py <transcripcion.md> <grafo.json>` parsea un MD de hojas de problemas (`# Tema` / `## Hoja` / `### N.- título`) y etiqueta cada problema con los nodos locales de su tema. No hace llamadas de red. Electromagnetismo: 229 problemas de las hojas de los profesores; además, el importador reproducible `importar_examenes_electromagnetismo.py` incorpora las recopilaciones maestras de exámenes. Para añadir otra asignatura: transcribe sus hojas al mismo formato y ejecuta el script.

### Preparación y retroalimentación de problemas

`problemas.py` aplica el criterio de preparación: un problema solo aparece como
desbloqueado cuando **todos** sus `nodos_requeridos` tienen dominio efectivo ≥
0.7. Si uno de esos nodos se olvida y cae por debajo del umbral, el problema
vuelve a quedar bloqueado automáticamente.

Cada resolución puede registrarse como:

- `resuelto`: problema, explicación y justificaciones correctas.
- `hueco_teorico`: el problema sale, pero hay una explicación o justificación que revisar; el nodo señalado vuelve a repaso.
- `incorrecto`: la resolución no sale; los requisitos bajan y se analizan como posibles puntos débiles.

El historial `perfil.json > retroalimentacion` cuenta errores y huecos por nodo.
La API ofrece
`/api/kg/problemas/estado` y `/api/kg/retroalimentacion` para la interfaz.

Electrónica quedó auditada con 46 nodos y 160 problemas clasificados. La
clasificación reproducible está en `auditar_electronica.py`; no se debe
renumerar ni borrar los nodos antiguos porque el perfil personal conserva sus
identificadores.

Electromagnetismo quedó auditado con 94 nodos y 409 problemas clasificados
(229 de clase y 180 de examen: 134 cuestiones y 46 problemas). La conversión
reproducible está en `auditar_electromagnetismo.py` y
`importar_examenes_electromagnetismo.py`; cada entrada conserva el enunciado existente,
sus `nodos_requeridos`, una fuente local, su familia (`calculo`, `conceptual`,
`grafico`, `circuito` o `mixto`) y el momento de desbloqueo.

### Auditoría de asignaturas prioritarias

La auditoría local del 2026-09-15 contrastó los grafos con las guías docentes
oficiales y con el material disponible en las carpetas de 4.º Física. El
resultado operativo es:

| Asignatura | Nodos | Problemas clasificados | Procedencia adicional |
|---|---:|---:|---|
| Electrónica | 46 | 160 | 143 exámenes + 17 de hojas de clase |
| Electrodinámica Clásica | 30 | 113 | 103 exámenes + 10 de la Hoja 01 |
| Mecánica Cuántica | 50 | 144 | 41 exámenes + 103 ejercicios indexados de Cohen |
| Física del Estado Sólido | 49 | 151 | 100 exámenes + 51 de las hojas locales |
| Electromagnetismo | 94 | 409 | 229 de clase + 180 de examen |

Cada problema tiene `nodos_requeridos` y solo se desbloquea cuando todos sus
nodos alcanzan dominio efectivo ≥ 0.7. Los ejercicios de Cohen conservan el
enunciado en los dos PDF de `Descargas` y el banco guarda su volumen, capítulo
y página de inicio para localizarlo sin duplicar el libro.

En Electromagnetismo, los 409 problemas se distribuyen entre las hojas locales
y las dos recopilaciones maestras: `cuestiones.pdf` (134) y `Lista de Problemas
Completo Electromagnetismo.pdf` (46). Se han clasificado 207 como cálculo, 33
conceptuales, 12 gráficos, 29 de circuitos y 14 mixtos. El banco usa 83 de los
94 nodos directamente; los restantes son nodos teóricos del grafo que siguen
disponibles para cuestiones y futuras ampliaciones.

La revisión se hizo con material local; no se ha borrado ni modificado ningún
archivo de Drive. Si en una fase posterior aparece un hueco documental
concreto, solo se descargará el archivo necesario.

La ampliación reproducible está en `auditar_asignaturas_4.py` y los informes
por asignatura en `REVISION_*.md`. El resultado del problema alimenta
`perfil.json > retroalimentacion`: `resuelto`, `hueco_teorico` o `incorrecto`.
Así, los huecos y errores se acumulan por nodo. La tutoría usa esa información
para corregir el ejercicio actual, pero no la convierte en una agenda automática.

## Planificador histórico (`planificar.py` + `examenes.json`)

Este módulo se conserva para consultas manuales y compatibilidad con datos
antiguos, pero no participa en la elección del contenido de las sesiones. La
aplicación no usa sus resultados como recomendaciones automáticas.

**EDITA `examenes.json`** con tus fechas reales (y borra asignaturas que no curses; `temas` acota qué temas entran en un parcial). Las cuatro referencias con fecha provisional llevan `planificar=false` y no entran en la carga hasta confirmarlas. El valor `minutos_dia` es solo un valor inicial para una sesión; puedes cambiar el tiempo real al empezar cada sesión.

- `python planificar.py` — consulta manual del estado académico y exámenes.
- `python planificar.py --fecha 2026-12-01` — consulta manual simulando otra fecha.
- `python planificar.py --minutos 90` — conserva compatibilidad con sesiones antiguas.

Diseño histórico (planificación hacia atrás desde el examen):
1. **Viabilidad**: por examen, combina nodos pendientes, dominio, prerrequisitos, importancia y proximidad de la fecha para estimar el contexto de riesgo. Las estimaciones internas no se muestran como una cuota ni como un objetivo de tiempo.
2. **Uso actual**: estas estimaciones quedan fuera del flujo normal de tutoría. La sesión se basa en el último punto trabajado o en la elección explícita del estudiante y usa problemas reales vinculados a los nodos.

## Documentos

- `ARQUITECTURA_electromagnetismo.md` — diagnóstico epistémico del itinerario (skill `curriculum-knowledge-architecture-designer`): qué parte es jerárquica (el grafo), cuál horizontal (elección de método → interleaving) y cuál disposicional (rigor/modelización → reflexión + dashboard, nunca nota automática).
- `VERIFICACION_MATH_ACADEMY.md` — auditoría de los 7 principios del método contra la implementación.
- `PROTOCOLO_NUEVA_MATERIA.md` — **cómo montar todo esto para aprender cualquier otra cosa** (póker, programación, IA...): checklist de 5 inputs del usuario + 7 pasos que ejecuta la IA. El motor es agnóstico al contenido.
