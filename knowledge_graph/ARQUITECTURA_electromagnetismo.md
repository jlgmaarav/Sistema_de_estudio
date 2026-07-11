# Análisis de Arquitectura del Conocimiento: Itinerario de Electromagnetismo (UVa)

*Generado aplicando el skill `curriculum-knowledge-architecture-designer` (Bernstein 1999/2000; Muller 2009; Maton 2009–2014).*

**Tipo de input:** scope-and-sequence — tres asignaturas encadenadas: Electromagnetismo (45758, 3º), Electrónica (45772, 4º), Electrodinámica Clásica (45769, 4º).
**Etapa del estudiante:** 20–23 años (3º–4º del Grado en Física, UVa).
**Objetivos de aprendizaje (derivados de las guías docentes):** dominar la teoría clásica del campo electromagnético en vacío y en medios materiales hasta las ecuaciones de Maxwell y las ondas; resolver problemas de contorno y de circuitos; comprender la física de los dispositivos semiconductores (unión PN, BJT, MOSFET) desde el modelo de bandas; reformular la electrodinámica en forma covariante y dominar la radiación de cargas y sistemas. *(Nota: derivados de los bloques de contenidos; si se aportan las secciones oficiales de competencias de las guías, se refina el diagnóstico disposicional.)*

---

## 1. Diagnóstico epistémico

**Tipo de arquitectura:** Predominantemente jerárquica, con elementos horizontales y disposicionales menores.
**Proporciones:** ~85% jerárquica, ~8% horizontal, ~7% disposicional.

**Razonamiento:**

**Jerárquica (85%).** La física teórica es el caso paradigmático de estructura jerárquica de Bernstein: cada concepto subsume los anteriores (Coulomb → Gauss → Poisson → métodos de potencial; Biot-Savart → Ampère → Maxwell → ondas → radiación). Se cumplen todos los indicadores: existen cadenas de prerrequisitos estrictas, los errores en niveles bajos se propagan hacia arriba (quien no domina condiciones de contorno falla en dieléctricos, guías de ondas y uniones PN por igual), y la secuenciación canónica es casi inamovible (coherencia conceptual de Muller). Las tres asignaturas forman una sola jerarquía: Electrodinámica es literalmente la continuación de Electromagnetismo con formalismo covariante, y Electrónica cuelga de la electrostática (Poisson, capacidad) y la corriente (continuidad, deriva/difusión), más una base de estado sólido.

**Horizontal (8%).** Dentro del dominio hay "lentes" alternativas que no se ordenan jerárquicamente entre sí: formulación integral vs. diferencial; campos vs. potenciales; formulación 3-vectorial vs. covariante; SI vs. gaussiano; y sobre todo la **elección de método** ante un problema de potencial (Gauss directo, imágenes, separación de variables, desarrollo multipolar). Saber *cuál* usar es conocimiento horizontal: se desarrolla por acumulación de perspectivas y práctica mezclada, no por prerrequisito.

**Disposicional (7%).** El "oficio del físico": modelizar (idealizar la geometría, elegir aproximación y validar sus límites) y el rigor operativo (análisis dimensional, comprobación de casos límite, estimación de órdenes de magnitud). Existe solo en la ejecución — no se puede aprobar un test de "sentido físico" — y progresa por bandas cualitativas.

## 2. Mapa de arquitectura del conocimiento

### Elementos jerárquicos

El mapa completo son los tres grafos JSON de esta carpeta (156 nodos, 274 aristas; peso 1.0 = prerrequisito duro, 0.5 = blando), visualizables en `mapa_conocimiento.html`. Estructura macro:

```
Cálculo vectorial (em.0)
   ↓ [duro]
Electrostática vacío (em.1) → Conductores (em.2) → Dieléctricos (em.3) → T. potencial (em.4)
   ↓                                                        ↓
Corriente (em.5) → Magnetostática (em.6) → Inducción (em.7) → Circuitos AC (em.8)
   ↓                       ↓                       ↓
Medios magnéticos (em.9) → Maxwell y ondas (em.10)
   ↓                            ↓
   ↓                     Electrodinámica (ed.1–ed.7)  [+ relatividad, raíz propia en ed.3.01]
   ↓
Electrónica (el.1–el.5)  [+ bandas/Fermi de FES, cubierto en el.1]
```

Convergencias críticas: `em.4.01` (Poisson) y `em.5.02` (continuidad) alimentan `el.1.09` (ecuaciones de los dispositivos), del que cuelga toda la unión PN; `em.10.*` alimenta todo `ed.*`.

### Elementos horizontales

**Hub conceptual: "el problema de potencial"** — lentes que lo orbitan: Gauss por simetría / imágenes / separación de variables (cartesianas, esféricas, cilíndricas) / multipolar. **Hub: "la misma física, varios lenguajes"** — integral↔diferencial, campos↔potenciales, 3-vectorial↔covariante, SI↔gaussiano.

Progresión de sofisticación analítica:

| Etapa | Qué hace el estudiante |
|---|---|
| Método único | Aplica el método que le indica el enunciado o el tema en que aparece el problema. |
| Selección | Ante un problema sin etiqueta, elige el método adecuado y justifica por qué. |
| Traducción | Cambia de formulación a mitad de problema cuando conviene (p. ej. pasa a potenciales, o a covariante). |
| Integración | Reconoce el mismo contenido físico entre asignaturas (esfera polarizada ↔ esfera magnetizada ↔ ZCE de la unión PN). |

### Elementos disposicionales

**Competencia 1: Modelización física**

| Nivel | Indicadores observables |
|---|---|
| Emergente | Reproduce el modelo dado en clase; no distingue qué idealizaciones lo sostienen. |
| En desarrollo | Identifica las aproximaciones usadas ("hilo infinito", "cuasiestacionario") y cuándo dejan de valer. |
| Competente | Elige idealizaciones propias ante problemas nuevos y estima el error cometido. |
| Avanzado | Construye el modelo mínimo que captura la física y anticipa qué términos despreciados dominarían en otros regímenes. |

**Competencia 2: Rigor operativo**

| Nivel | Indicadores observables |
|---|---|
| Emergente | Entrega el resultado sin comprobarlo; errores de unidades frecuentes. |
| En desarrollo | Comprueba dimensiones al final; detecta signos absurdos al releer. |
| Competente | Verifica sistemáticamente casos límite (r→0, r→∞, v≪c) y simetrías antes de dar por buena la solución. |
| Avanzado | Usa las comprobaciones para *encontrar* el error: localiza el paso fallido razonando qué límite se rompe. |

## 3. Notas de arquitectura mixta

- **Horizontal ⇄ jerárquico:** la lente "elección de método" es inoperable hasta dominar cada método por separado (nodos `em.4.02`–`em.4.06`). La selección de método debe entrenarse *después*, con práctica deliberadamente mezclada — nunca en bloques por método.
- **Disposicional contingente al conocimiento:** el rigor operativo y la modelización son disposiciones knowledge-contingent — no pueden desarrollarse auténticamente sin la base jerárquica (no se puede "comprobar el límite" de una fórmula que no se sabe derivar). No deben ocupar tiempo de instrucción temprana como contenido separado; deben nombrarse y exigirse en cada problema desde el principio.
- **Tensión de evaluación:** los exámenes puntúan el resultado (jerárquico), pero la causa raíz de los fallos suele ser disposicional (no comprobar límites, no dimensionar). El sistema ya captura esto: la taxonomía de errores del pipeline (`tipo_error`, `razon`, `como_evitarlo`) es exactamente el registro longitudinal que la evaluación disposicional necesita.

## 4. Implicaciones para secuenciación

- La secuencia jerárquica está fijada por el grafo: la frontera de conocimiento (nodos con prerrequisitos dominados) es el único orden válido. Electrónica y Electrodinámica pueden avanzar **en paralelo** una vez cubiertos sus puntos de entrada (`em.4.01`/`em.5.02` y `em.10.*` respectivamente) — son ramas casi independientes entre sí.
- Los elementos horizontales se secuencian como *interleaving*: cuadernos de problemas mezclados sin etiqueta de método, introducidos al cerrar el Tema 4 y mantenidos como repaso permanente.
- Lo disposicional corre como hilo continuo: cada intento incluye el ritual de comprobación (dimensiones + un caso límite), y el dashboard lo audita.

## 5. Implicaciones para evaluación

**Auto-evaluable (IA/automatizable):** todo el eje jerárquico — problemas con resultado y desarrollo verificables. Es lo que ya hace el pipeline Gemini: corrección paso a paso, clasificación contra el grafo, estimación de dominio por nodo.

**Juicio humano/mixto:** calidad de la *elección* de método y de la modelización (varias soluciones válidas; la IA puede señalar la elección subóptima pero la valoración fina es interpretativa); nivel disposicional (requiere observación longitudinal — el dashboard de patrones de error es el instrumento, no un test puntual).

**Gap de diseño detectado (Bailin et al. 1999; Willingham 2007):** el itinerario asume que el "pensar como físico" emerge solo de resolver problemas. No es cierto en general — debe enseñarse explícitamente. Acción concreta: incluir en cada lección del sistema una "regla de oro" de rigor (qué comprobar en este tipo de problema) y pedir en el postmortem de cada fallo la reflexión que ya recoge el campo `como_evitarlo`.

## 6. Implicaciones para el diseño del tutor IA (nuestro sistema)

- **Jerárquico → el motor central (Fases 2–3):** gating por prerrequisitos (no prescribir un nodo sin dominar sus prerrequisitos duros), umbral de mastery por evidencia real (problemas resueltos, no exposición), crédito implícito hacia ancestros con peso 1.0, repaso espaciado por nodo, diagnóstico inicial adaptativo.
- **Horizontal → generador de sesiones mezcladas:** el planificador debe crear sets interleaved de "elige el método" cuando varios nodos-método estén dominados, y proponer el mismo problema en dos formulaciones en Electrodinámica.
- **Disposicional → prompts de reflexión + dashboard, NUNCA nota automática:** el sistema pide la comprobación de límites/dimensiones en cada intento, rastrea su presencia en la transcripción, y muestra la tendencia temporal; no la puntúa como correcto/incorrecto.
- **Transiciones de modo:** el tutor es directivo y correctivo en lo jerárquico, propositivo en lo horizontal ("¿qué otro método valdría aquí?") y reflexivo no evaluativo en lo disposicional.

---

*Limitaciones: las proporciones son juicios interpretativos; el análisis se basa en los contenidos declarados de las guías, no en la docencia real; las bandas disposicionales describen desarrollo típico, no etapas universales.*
