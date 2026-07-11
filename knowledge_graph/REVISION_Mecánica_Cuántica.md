# Revisión del grafo — Mecánica Cuántica

Total: **44 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

## Tema 1: Formalismo matemático

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.1.01 | **Espacio de funciones de onda y bases** — Espacio vectorial de funciones de onda, bases discretas, ondas planas y deltas de Dirac. | cu.04, al.05, m2.02 | Guia Tema 1; Libro Cohen-Tannoudji II | |
| mc.1.02 | **Espacio de estados y notación de Dirac** — Kets, bras y operadores lineales; el espacio de estados abstracto. | mc.1.01 | Guia Tema 1 | |
| mc.1.03 | **Conjugación hermítica y representaciones** — Adjunto, representación matricial de kets, bras y operadores en una base. | mc.1.02 | Guia Tema 1 | |
| mc.1.04 | **Ecuaciones de autovalores y observables** — Espectro de operadores hermíticos, observables, degeneración. | mc.1.03, al.04 | Guia Tema 1 | |
| mc.1.05 | **Observables que conmutan y CCOC** — Teoremas de compatibilidad, conjunto completo de observables que conmutan. | mc.1.04 | Guia Tema 1 | |
| mc.1.06 | **Representaciones de posición y momento** — Observables X y P, cambio entre representaciones, relación con la transformada de Fourier. | mc.1.04, m2.04 | Guia Tema 1 | |
| mc.1.07 | **Producto tensorial de espacios de estados** — Espacios compuestos, separación de variables. | mc.1.05 | Guia Tema 1 | |
| mc.1.08 | **Álgebra de operadores** — Traza, conmutadores, funciones y derivación de operadores, operadores unitarios. | mc.1.04 | Guia Tema 1 | |
| mc.1.09 | **Paridad, descomposición espectral y matrices de Pauli** — Operador paridad, proyectores espectrales, álgebra de Pauli. | mc.1.08 | Guia Tema 1 | |

## Tema 2: Postulados

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.2.01 | **Postulados de la medida** — Postulados fundamentales, principio de descomposición espectral, probabilidades. | mc.1.05 | Guia Tema 2 | |
| mc.2.02 | **Reducción del paquete y reglas de cuantificación** — Colapso en espectros discretos y continuos, construcción de observables. | mc.2.01 | Guia Tema 2 | |
| mc.2.03 | **Valores medios e incompatibilidad** — Valor medio, desviación cuadrática, medida de observables compatibles e incompatibles. | mc.2.01 | Guia Tema 2 | |
| mc.2.04 | **Análisis de la ecuación de Schrödinger** — Determinismo, superposición, conservación de la probabilidad, ecuación de continuidad. | mc.2.01, cu.02 | Guia Tema 2 | |
| mc.2.05 | **Ehrenfest y sistemas conservativos** — Evolución de valores medios, límite clásico, estados estacionarios, frecuencias de Bohr, relación energía-tiempo. | mc.2.04 | Guia Tema 2 | |
| mc.2.06 | **Operador de evolución** — Evolución unitaria, propiedades del propagador. | mc.2.05, mc.1.08 | Guia Tema 2 | |
| mc.2.07 | **Operador densidad** — Estados puros y mezcla, trazas parciales, medidas sobre subsistemas, correlaciones. | mc.2.06, mc.1.07 | Guia Tema 2 | |
| mc.2.08 | **Imágenes de Schrödinger y Heisenberg** — Descripciones equivalentes de la evolución temporal. | mc.2.06 | Guia Tema 2 | |
| mc.2.09 | **Sistemas de dos niveles: fórmula de Rabi** — Ruptura de degeneración por acoplamiento, oscilaciones de Rabi. | mc.2.06, mc.1.09 | Guia Tema 2 | |

## Tema 3: Oscilador armónico

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.3.01 | **Oscilador armónico: operadores escalera** — Aproximación armónica, operadores creación/aniquilación/número, hamiltoniano. | mc.1.08, cu.02 | Guia Tema 3 | |
| mc.3.02 | **Espectro y estados propios del oscilador** — Autovalores, funciones de onda estacionarias, interpretación de a y a†. | mc.3.01 | Guia Tema 3 | |
| mc.3.03 | **Elementos de matriz y evolución en el oscilador** — Valores medios de X, P, energías; evolución temporal de valores medios. | mc.3.02 | Guia Tema 3 | |
| mc.3.04 | **Oscilador 3D y oscilador cargado** — Oscilador isótropo tridimensional; oscilador cargado en campo eléctrico uniforme. | mc.3.03, mc.1.07 | Guia Tema 3 | |

## Tema 4: Momento cinético

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.4.01 | **Álgebra del momento angular** — Relaciones de conmutación, operadores escalera J±, espectro de J² y Jz. | mc.1.05, cu.05 | Guia Tema 4 | |
| mc.4.02 | **Base estándar y momento angular orbital** — Construcción de la base |j,m⟩, armónicos esféricos como caso orbital. | mc.4.01, m2.08 (0.5) | Guia Tema 4 | |
| mc.4.03 | **Espín 1/2: postulados de Pauli y espinores** — Espacio de estados con espín, espinores, ejemplos. | mc.4.02, mc.1.09 | Guia Tema 4 | |
| mc.4.04 | **Partículas con espín en campos magnéticos** — Precesión de espín, acoplamiento magnético. | mc.4.03, em.6.05 (0.5) | Guia Tema 4 | |
| mc.4.05 | **Momento angular y rotaciones** — Operadores de rotación, relación con el grupo de rotaciones, caso espín 1/2. | mc.4.03 | Guia Tema 4 | |
| mc.4.06 | **Composición de dos espines 1/2** — Singlete y triplete como caso modelo de composición. | mc.4.03, mc.1.07 | Guia Tema 4 | |
| mc.4.07 | **Composición general: Clebsch-Gordan** — Autovalores y autovectores del momento total, coeficientes de Clebsch-Gordan, l⊕s, tres momentos. | mc.4.06 | Guia Tema 4 | |
| mc.4.08 | **Operadores tensoriales: Wigner-Eckart** — Operadores vectoriales y tensoriales irreducibles, teorema de Wigner-Eckart. | mc.4.07 | Guia Tema 4 | |

## Tema 5: Dispersión y colisiones

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.5.01 | **Sección eficaz y amplitud de dispersión** — Dispersión elástica, estados estacionarios de dispersión, amplitud. | mc.2.05, mo.03 | Guia Tema 5 | |
| mc.5.02 | **Teorema óptico y paquetes de onda** — Formulación con paquetes, dispersión por sistemas de partículas, teorema óptico. | mc.5.01 | Guia Tema 5 | |
| mc.5.03 | **Ecuación integral de dispersión** — Funciones de Green entrante y saliente, expresión integral de la amplitud. | mc.5.01, m2.02 (0.5) | Guia Tema 5 | |
| mc.5.04 | **Aproximación de Born** — Serie de Born, validez, ejemplos (Yukawa, coulombiano apantallado). | mc.5.03, m2.04 (0.5) | Guia Tema 5 | |
| mc.5.05 | **Método de ondas parciales: desfasajes** — Ondas esféricas vs planas, parámetro de impacto, desfasajes. | mc.5.01, mc.4.02 | Guia Tema 5 | |
| mc.5.06 | **Ondas parciales: aplicaciones y resonancias** — Esfera dura, pozos, resonancias de baja energía. | mc.5.05 | Guia Tema 5 | |

## Tema 6: Métodos aproximados

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.6.01 | **Perturbaciones estacionarias no degeneradas** — Series perturbativas de energías y estados, validez. | mc.2.05 | Guia Tema 6 | |
| mc.6.02 | **Perturbaciones degeneradas** — Diagonalización en el subespacio degenerado, rupturas de degeneración. | mc.6.01 | Guia Tema 6 | |
| mc.6.03 | **Método variacional** — Principio variacional, funciones de prueba, cotas a la energía del fundamental. | mc.6.01 | Guia Tema 6 | |
| mc.6.04 | **Aproximación WKB** — Aproximación semiclásica, reglas de conexión, efecto túnel. | mc.6.01, cu.02 | Guia Tema 6 | |
| mc.6.05 | **Perturbaciones dependientes del tiempo** — Probabilidades de transición a primer orden, perturbación armónica. | mc.6.01, mc.2.08 | Guia Tema 6 | |
| mc.6.06 | **Regla de oro de Fermi** — Transiciones a un continuo, densidad de estados finales. | mc.6.05 | Guia Tema 6 | |

## Tema 7: Partículas idénticas

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.7.01 | **Postulado de simetrización** — Indistinguibilidad, fermiones y bosones, degeneración de intercambio. | mc.2.01, mc.1.07, cu.06 | Guia Tema 7 | |
| mc.7.02 | **Determinantes de Slater y aplicaciones** — Construcción de estados antisimétricos, consecuencias físicas del intercambio. | mc.7.01 | Guia Tema 7 | |

## Estadísticas

- Nodos raíz (sin prerrequisitos): —
- Nodos sin dependientes en todo el sistema: mc.2.02, mc.2.03, mc.2.07, mc.2.09, mc.3.04, mc.5.02, mc.5.04, mc.5.06, mc.6.04
- Aristas: 67 (15 hacia otras asignaturas)
