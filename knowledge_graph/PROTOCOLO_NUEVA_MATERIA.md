# Protocolo: montar el sistema para aprender cualquier cosa

Cómo pasar de "quiero aprender X desde cero hasta nivel experto" a tener el sistema completo
(grafo + perfil + plan + banco + lecciones + quizzes) funcionando. Este protocolo lo ejecuta
la IA (Claude) en una sesión; el usuario solo aporta los 5 inputs del checklist.

Todo el motor es agnóstico al contenido: los grafos JSON, `perfil.py`, `planificar.py`,
`clasificar_problemas.py`, `lecciones.py`, el mapa y la app funcionan igual para
Electromagnetismo que para póker, programación o IA.

---

## Paso 0 — Diagnóstico epistémico (antes de nada)

Aplicar el skill `curriculum-knowledge-architecture-designer` (SKILL.md de la raíz) a la materia:

- **¿Cuánto hay de jerárquico?** El método Math Academy aplica de lleno a esa parte (grafo + frontera + mastery). Física ≈ 85% jerárquico; póker ≈ 60%; programación ≈ 70%.
- **Parte horizontal** (lentes/estilos/situaciones sin orden fijo) → se entrena con interleaving y quizzes mezclados, no con cadenas de prerrequisitos.
- **Parte disposicional** (solo existe en la ejecución: disciplina de bankroll, control del tilt, hábitos de debugging...) → el sistema cubre la teoría y los drills; la práctica real (mesas, proyectos) es el laboratorio, y el postmortem de errores es el instrumento de mejora.

Resultado: `ARQUITECTURA_<materia>.md`. Si la materia es <40% jerárquica, este método no es el vehículo principal — decirlo honestamente.

## Checklist — lo que el usuario debe aportar

1. **Fuentes canónicas** (2–4): índices/temarios de libros o cursos de referencia, como los "guiones" de las asignaturas. Basta el índice detallado (foto/transcripción), no el libro entero.
2. **Alcance y meta**: desde dónde hasta dónde ("de cero a NL50 en cash 6-max", "hasta leer papers de deep learning"). Sin meta no hay grafo acotado.
3. **Fechas objetivo** (opcional pero recomendado): deadlines o hitos → van a `examenes.json` y activan el semáforo de ritmo.
4. **Qué sabe ya**: lista honesta de lo dominado (equivale a `marcar-cursadas`) o "desde cero".
5. **Banco de práctica**: hojas de ejercicios/drills en el formato MD (`# Tema / ## Hoja / ### N.- título`). Si no existen, decidir por nodo si la IA genera drills (viable cuando hay respuesta verificable: cálculos de odds, ejercicios de código, rangos GTO; no viable para juicio abierto).

## Pasos que ejecuta la IA

1. **Diagnóstico** (paso 0) → `ARQUITECTURA_<materia>.md`.
2. **Grafo**: `<materia>.json` con prefijo de id nuevo (p. ej. `pk.` para póker), `curso` = nivel 1–4 (principiante→experto), granularidad fina (1 nodo ≈ 1 sesión: teoría mínima + 3–10 ejercicios), prerrequisitos con peso (1.0 duro/encompassing, 0.5 blando), fuentes por nodo. Aristas cruzadas a grafos existentes si aplica (póker → probabilidad de m3.03).
3. **Validar y revisar**: `validar_grafo.py` (todos los JSON) → `REVISION_<materia>.md` para el visto bueno del usuario. Ajustar.
4. **Integrar**: `generar_mapa.py` (el mapa lo incorpora solo), `actualizar_taxonomia.py` (el clasificador de subidas lo conoce).
5. **Metas**: añadir los hitos a `examenes.json` (desde la app: pestaña Plan → Exámenes). El "examen" puede ser "empezar a jugar NL10".
6. **Banco**: `clasificar_problemas.py <hojas.md> <materia>.json` (o subida desde la app). Si no hay fuente, generar drills con IA nodo a nodo y revisarlos.
7. **Perfil inicial**: registrar lo ya sabido (`perfil.py registrar <ids>` o botones ✓ de la app). El resto arranca en frontera.

Desde ese momento el plan diario, las lecciones mínimas, el crédito implícito, los quizzes y el mapa funcionan exactamente igual que con Física. Tiempo estimado del montaje: **una sesión** (el grafo es lo laborioso; el resto es automático).

## Convenciones

- Prefijo de id corto y único por materia (revisar los ocupados: am al fmt fco fce fc qm m1-m4 mo td fm em cu fe fl gc mt op ed el fa np es mc sc).
- `curso`: en materias no académicas = nivel (1 fundamentos, 2 intermedio, 3 avanzado, 4 experto). Ordena y colorea el mapa.
- La corrección por foto (Inbox/watcher) funciona para cualquier cosa escrita a mano; para materias digitales (código) el canal natural son los botones ✓/✗ y el quiz.

---

## Ejemplo pre-rellenado: PÓKER (pendiente de inputs del usuario)

**Diagnóstico previo (resumen):** mixto. Jerárquico (~60%): probabilidad y combinatoria → equity y pot odds → rangos preflop por posición → c-bet y texturas → barrel/bluff ratios → teoría GTO básica → explotación. Horizontal (~20%): tipos de rival, lecturas, dinámicas de mesa (interleaving). Disposicional (~20%): bankroll, tilt, volumen (no se aprende con flashcards: se registra y audita, como el rigor en física).

**Checklist para el usuario:**
1. Fuentes: índices de 2–3 de estos (elegir según formato de juego): *Modern Poker Theory* (Acevedo), *The Grinder's Manual* (Carroters, cash 6-max), *Applications of NLHE* (Janda), o el temario de un curso (Upswing, Raise Your Edge).
2. Meta: formato (cash/torneos, online/vivo), stakes de partida y objetivo, horizonte temporal.
3. Hitos con fecha si los hay ("jugar NL10 en octubre").
4. Qué sabe ya (reglas, posiciones, ¿algo de rangos?).
5. Banco: los drills de póker (odds, outs, EV, rangos por posición) tienen respuesta verificable → la IA puede generar el banco entero, con revisión del usuario. Prerrequisito matemático ya cubierto: probabilidad (`m3.03`).
