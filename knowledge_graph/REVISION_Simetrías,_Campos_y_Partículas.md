# Revisión del grafo — Simetrías, Campos y Partículas

Total: **23 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

## Bloque 1: Teoría clásica de campos

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| sc.1.01 | **De sistemas discretos a continuos** — Paso al continuo, densidad lagrangiana, el campo como sistema dinámico. | mt.04 | Guia Bloque 1 | |
| sc.1.02 | **Euler-Lagrange para campos** — Ecuaciones de campo desde un principio variacional; ejemplos (cuerda, campo escalar). | sc.1.01 | Guia Bloque 1 | |
| sc.1.03 | **Formalismo hamiltoniano de campos** — Momentos conjugados, densidad hamiltoniana, corchetes. | sc.1.02, mt.02 | Guia Bloque 1 | |
| sc.1.04 | **Grupos de Lie: generadores y álgebras** — Grupos continuos, generadores infinitesimales, álgebra de Lie, exponenciación. | al.04, gc.1.02 (0.5) | Guia Bloque 1 | |
| sc.1.05 | **SO(3) y SU(2): representaciones** — Rotaciones y espín como representaciones, relación 2 a 1. | sc.1.04, mc.4.05 | Guia Bloque 1 | |
| sc.1.06 | **Grupos de Lorentz y de Poincaré** — Estructura, generadores (boosts, rotaciones, traslaciones), representaciones. | sc.1.05, gc.1.05 | Guia Bloque 1 | |
| sc.1.07 | **Teorema de Noether para campos** — Simetrías continuas y corrientes conservadas; tensor energía-momento canónico. | sc.1.02, sc.1.04 | Guia Bloque 1 | |
| sc.1.08 | **Noether aplicado al campo electromagnético** — Lagrangiano de Maxwell, simetrías y corrientes del campo EM. | sc.1.07, ed.1.03, gc.1.11 (0.5) | Guia Bloque 1 | |

## Bloque 2: Ecuación de Klein-Gordon

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| sc.2.01 | **De Schrödinger a Klein-Gordon** — Motivación relativista, construcción de la ecuación KG. | mc.2.04, gc.1.06 | Guia Bloque 2 | |
| sc.2.02 | **KG: soluciones libres** — Soluciones de partícula libre, espacio de momentos, energías negativas. | sc.2.01 | Guia Bloque 2 | |
| sc.2.03 | **KG: problemas de interpretación** — Densidad no definida positiva, límites como ecuación de una partícula. | sc.2.02 | Guia Bloque 2 | |
| sc.2.04 | **KG con campo electromagnético** — Acoplamiento mínimo, espectro del potencial coulombiano (átomos piónicos). | sc.2.02, gc.1.11 (0.5) | Guia Bloque 2 | |
| sc.2.05 | **La paradoja de Klein** — Escalón de potencial relativista y su interpretación. | sc.2.03, sc.2.04 (0.5) | Guia Bloque 2 | |

## Bloque 3: Ecuación de Dirac

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| sc.3.01 | **Construcción de la ecuación de Dirac** — Linealización, matrices gamma y su álgebra. | sc.2.03, mc.1.09 | Guia Bloque 3 | |
| sc.3.02 | **Covariancia y corriente de Dirac** — Formalismo covariante, corriente conservada definida positiva, espín intrínseco. | sc.3.01, sc.1.06 | Guia Bloque 3 | |
| sc.3.03 | **Dirac: soluciones libres** — Espinores de partícula libre, espacio de momentos, helicidad. | sc.3.02 | Guia Bloque 3 | |
| sc.3.04 | **Zitterbewegung** — Interferencia de energías positivas y negativas, movimiento tembloroso. | sc.3.03 | Guia Bloque 3 | |
| sc.3.05 | **Mar de Dirac y antipartículas** — Interpretación de las energías negativas, predicción del positrón. | sc.3.03 | Guia Bloque 3 | |
| sc.3.06 | **Dirac con campo EM: momento magnético** — Acoplamiento mínimo, límite no relativista (Pauli), factor g=2. | sc.3.03, mc.4.04 | Guia Bloque 3 | |
| sc.3.07 | **Correcciones relativistas al espectro coulombiano** — Estructura fina desde Dirac, comparación con el tratamiento perturbativo. | sc.3.06, fa.1.06 (0.5) | Guia Bloque 3 | |

## Bloque 4: Introducción a la QFT

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| sc.4.01 | **Cuantización del campo electromagnético** — Modos del campo, osciladores, fotones. | sc.1.08, mc.3.02 | Guia Bloque 4 | |
| sc.4.02 | **De la mecánica cuántica relativista a la QFT** — Por qué campos cuantizados: creación/destrucción de partículas, panorama de la QFT. | sc.4.01, sc.3.05 | Guia Bloque 4 | |
| sc.4.03 | **Conexión con la física de partículas** — Campos y partículas del modelo estándar como representaciones de simetrías. | sc.4.02, np.2.05 (0.5) | Guia Bloque 4 | |

## Estadísticas

- Nodos raíz (sin prerrequisitos): —
- Nodos sin dependientes en todo el sistema: sc.1.03, sc.2.05, sc.3.04, sc.3.07, sc.4.03
- Aristas: 40 (16 hacia otras asignaturas)
