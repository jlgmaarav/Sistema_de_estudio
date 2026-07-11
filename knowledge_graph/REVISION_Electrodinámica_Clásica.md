# Revisión del grafo — Electrodinámica Clásica

Total: **30 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

## Bloque 1: Ecuaciones del campo electromagnético

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.1.01 | **Leyes generales del electromagnetismo** — Repaso sistemático de las ecuaciones de Maxwell micro/macroscópicas y sus condiciones de frontera. | em.10.01, em.10.02 (0.5) | Jackson 6.3, 6.10; Panofsky cap. 9; Thide 1.3 | |
| ed.1.02 | **Campos y potenciales** — Potenciales electromagnéticos como variables fundamentales; ecuaciones acopladas para V y A. | ed.1.01, em.10.03 | Jackson 6.4; Thide 3.3; Griffiths 10.1.1 | |
| ed.1.03 | **Transformaciones gauge: el gauge de Lorenz** — Libertad gauge, gauges de Lorenz y Coulomb, desacoplo de las ecuaciones de los potenciales. | ed.1.02 | Jackson 6.5; Griffiths 10.1.2, 10.1.3; Thide 3.3.1 a 3.3.3 | |

## Bloque 2: Leyes de conservación

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.2.01 | **Conservación de la energía: teorema de Poynting** — Balance local de energía campo-materia, vector de Poynting, ejemplos no triviales. | ed.1.01, em.10.04 | Jackson 6.8; Thide 6.3.1; Panofsky 10-5 | |
| ed.2.02 | **Conservación del momento: tensor de tensiones de Maxwell** — Momento electromagnético, tensor de Maxwell, balance de fuerzas sobre distribuciones. | ed.2.01, em.10.05 | Jackson 6.9; Griffiths 8.2; Panofsky 10-6; Thide 6.3.2 | |

## Bloque 3: Formulación covariante

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.3.01 | **Postulados y transformaciones de Lorentz** — Base experimental, postulados de Einstein, transformación de Lorentz, contracción y dilatación. | mo.08 | Wangsness 28-1, 28-2; Jackson 11.1 a 11.4; Griffiths 12.1; Panofsky cap. 15, 16 | |
| ed.3.02 | **Cuadrivectores y tensores** — Espacio de Minkowski, métrica, cuadrivectores co/contravariantes, álgebra tensorial. | ed.3.01 | Jackson 11.7, 11.8; Wangsness 28-3; Panofsky 17-1, 17-2; Thide 4.1.2, 4.1.3 | |
| ed.3.03 | **Mecánica relativista de partículas** — Tiempo propio, cuadrivelocidad, cuadrimomento, energía-momento, fuerza de Minkowski. | ed.3.02 | Jackson 12.1; Griffiths 12.2; Panofsky 17-3 a 17-5; Thide 4.2 | |
| ed.3.04 | **Transformación de las fuentes: cuadricorriente y cuadripotencial** — J^μ y A^μ, ecuación de continuidad y gauge de Lorenz en forma covariante. | ed.3.02, ed.1.03 | Panofsky 18-1; Thide 4.3.1; Feynman II-25 | |
| ed.3.05 | **El tensor campo electromagnético** — F^μν, transformación de E y B entre sistemas de referencia, invariantes del campo. | ed.3.04 | Jackson 11.9, 11.10; Griffiths 12.3.2, 12.3.3; Panofsky 18-2, 18-6; Wangsness 28-5 | |
| ed.3.06 | **Electrodinámica en forma covariante** — Ecuaciones de Maxwell con F^μν, fuerza de Lorentz covariante, covariancia de las leyes de conservación. | ed.3.05, ed.3.03 | Jackson 11.9, 11.11; Griffiths 12.3.4, 12.3.5; Panofsky 18-3 | |

## Bloque 4: La ecuación de ondas

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.4.01 | **Ecuación de ondas no homogénea: potenciales retardados** — Función de Green de la ecuación de ondas, causalidad, potenciales retardados. | ed.1.03, em.10.06 | Jackson 6.6; Griffiths 10.2; Panofsky 14-1, 14-2; Wangsness 27-1 | |
| ed.4.02 | **Potenciales de Liénard-Wiechert** — Potenciales de una carga puntual en movimiento arbitrario; tiempo retardado. | ed.4.01, ed.3.03 (0.5) | Jackson 14.1; Griffiths 10.3; Panofsky 19-1; Thide 4.3.2 | |
| ed.4.03 | **Ecuación homogénea: campos armónicos** — Soluciones armónicas, ecuación de Helmholtz, representación espectral. | em.10.07, ed.4.01 (0.5) | Thide cap. 2; Jackson cap. 7 | |
| ed.4.04 | **Campos en una guía de ondas** — Separación de variables, modos TE/TM, frecuencia de corte, guía rectangular. | ed.4.03, em.10.09, em.4.04 (0.5) | Jackson 8.2 a 8.4; Wangsness 26-2 a 26-4; Griffiths 9.5; Panofsky 13-6 | |
| ed.4.05 | **Cavidades resonantes** — Modos propios, frecuencias de resonancia, factor de calidad. | ed.4.04 | Jackson 8.6, 8.7; Wangsness 26-6; Panofsky 13-3 a 13-5; Feynman II-23 | |

## Bloque 5: Desarrollo multipolar de la radiación

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.5.01 | **Campos de una fuente localizada oscilante** — Zonas cercana, intermedia y de radiación; campos de radiación. | ed.4.01, ed.4.03 | Jackson 9.1; Panofsky 14-3; Thide cap. 7 | |
| ed.5.02 | **Radiación dipolar eléctrica** — Aproximación de primer orden, patrón de radiación, potencia radiada. | ed.5.01, em.1.12 (0.5) | Jackson 9.2; Griffiths 11.1.2; Thide 8.2.2; Panofsky 14-7 | |
| ed.5.03 | **Radiación dipolar magnética y cuadrupolar** — Aproximación de segundo orden: dipolo magnético y cuadrupolo eléctrico; potencias radiadas. | ed.5.02, em.6.09 (0.5) | Jackson 9.3; Griffiths 11.1.3; Thide 8.2.3, 8.2.4; Panofsky 14-8 | |
| ed.5.04 | **Antenas** — Antena lineal alimentada en el centro, resistencia de radiación, patrones. | ed.5.02 | Jackson 9.4; Wangsness 27-6; Thide 8.1 | |

## Bloque 6: Radiación de partículas cargadas

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.6.01 | **Campos de una carga acelerada** — Campos de velocidad y de aceleración a partir de Liénard-Wiechert. | ed.4.02 | Jackson 14.1; Griffiths 10.3.2; Panofsky 20-1 | |
| ed.6.02 | **Potencia radiada: Larmor y su generalización relativista** — Fórmula de Larmor, generalización de Liénard, dependencia con γ. | ed.6.01, ed.3.03 | Jackson 14.2; Griffiths 11.2.1; Panofsky 20-2, 20-3 | |
| ed.6.03 | **Distribución angular de la radiación** — Patrones angulares para aceleración paralela y perpendicular a la velocidad; colimación relativista. | ed.6.02 | Jackson 14.3, 14.4; Panofsky 20-3, 20-4; Thide 8.3.2 | |
| ed.6.04 | **Bremsstrahlung y radiación de Cherenkov** — Radiación de frenado en movimiento rectilíneo; radiación de cargas en medios (Cherenkov). | ed.6.03 | Jackson 14.9, cap. 15; Panofsky 20-6, 20-7; Thide 8.3.3, 8.3.5 | |
| ed.6.05 | **Radiación sincrotrónica** — Movimiento circular relativista: espectro y distribución angular de la radiación sincrotrón. | ed.6.03 | Jackson 14.6; Panofsky 20-4; Thide 8.3.4 | |
| ed.6.06 | **Reacción de radiación** — Fuerza de Abraham-Lorentz, autoenergía, límites del modelo clásico. | ed.6.02 | Jackson cap. 17; Griffiths 11.2.2, 11.2.3; Panofsky cap. 21 | |
| ed.6.07 | **Aceleradores y fuentes de radiación** — Aplicaciones: aceleradores de partículas, fuentes de luz sincrotrón, pérdidas radiativas. | ed.6.04, ed.6.05 | Jackson cap. 15; Panofsky cap. 20 | |

## Bloque 7: Dinámica de partículas cargadas

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| ed.7.01 | **Movimiento en campos estáticos y uniformes** — Tratamiento relativista del movimiento en E y B uniformes; deriva E×B. | ed.3.06, em.6.05 | Jackson 12.7, 12.8; Panofsky cap. 23; Wangsness Ap. A | |
| ed.7.02 | **Movimiento en campos estáticos no uniformes** — Derivas de gradiente y curvatura, espejos magnéticos, invariantes adiabáticos. | ed.7.01 | Jackson 12.9, 12.10; Panofsky 23-4 | |
| ed.7.03 | **Movimiento en campos variables con el tiempo** — Aceleración por campos inducidos, betatrón, calentamiento de partículas. | ed.7.02 | Wangsness A-4; Panofsky cap. 23 | |

## Estadísticas

- Nodos raíz (sin prerrequisitos): —
- Nodos sin dependientes en todo el sistema: ed.2.02, ed.4.05, ed.5.04, ed.6.06, ed.6.07, ed.7.03
- Aristas: 47 (13 hacia otras asignaturas)
