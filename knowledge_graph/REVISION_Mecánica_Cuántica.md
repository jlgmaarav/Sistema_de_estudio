# Revisión del grafo — Mecánica Cuántica

Total: **50 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

La revisión usa como referencia directa `MECANICA CUANTICA. TEORIA.pdf`. Cada fila incluye las páginas manuscritas y el estado de cobertura: `desarrollado` cuando el concepto aparece explicado en el desarrollo y `resumen` cuando solo aparece enumerado en el resumen del Tema 6. Los identificadores se conservan para no romper las clasificaciones del banco de problemas; por eso el oscilador 2D mantiene `mc.6.07` y el decaimiento al continuo se añade como `mc.6.08`.

## Tema 1: Formalismo matemático

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.1.01 | **Traza de un operador** — Definición de traza, cálculo en una base, invariancia y propiedad cíclica; incluye la discusión de degeneración. | cu.04, al.05, m2.02 | Guia Tema 1; Libro Cohen-Tannoudji II; Apuntes pp. 25–26 [desarrollado] | |
| mc.1.02 | **Funciones de operadores** — Construcción de funciones de operadores a partir de su espectro y de las representaciones matriciales. | mc.1.01 | Guia Tema 1; Apuntes pp. 26 [desarrollado] | |
| mc.1.03 | **Diferenciación de operadores** — Derivada temporal de operadores, regla del producto y ejemplos de diferenciación de productos y funciones de operadores. | mc.1.02 | Guia Tema 1; Apuntes pp. 27–29 [desarrollado] | |
| mc.1.04 | **Operadores unitarios y operadores transformados** — Operadores unitarios, cambio de base y transformación unitaria de estados y observables. | mc.1.03, al.04 | Guia Tema 1; Apuntes pp. 30–32 [desarrollado] | |
| mc.1.05 | **Bases ortonormales y representaciones matriciales** — Bases ortonormales, componentes de kets y bras, matrices de operadores y matrices unitarias de cambio de base. | mc.1.04 | Guia Tema 1; Apuntes pp. 31–32 [desarrollado] | |
| mc.1.06 | **Autovalores, degeneración y observables** — Ecuaciones de autovalores, espectro, degeneración y lectura de los observables en una base propia. | mc.1.05, m2.04 | Guia Tema 1; Apuntes pp. 32–34 [desarrollado] | |
| mc.1.07 | **Descomposición espectral y proyectores** — Proyectores asociados a subespacios propios y descomposición espectral de operadores. | mc.1.06 | Guia Tema 1; Apuntes pp. 33–34 [desarrollado] | |
| mc.1.08 | **Operador paridad y simetría discreta** — Definición del operador paridad, autovalores ±1, subespacios par e impar y transformación de observables. | mc.1.07 | Guia Tema 1; Apuntes pp. 33–36 [desarrollado] | |
| mc.1.09 | **Reglas de selección por paridad y matrices de Pauli** — Anulación de elementos de matriz por paridad; se conserva la conexión operativa con las matrices de Pauli usadas después para espín 1/2. | mc.1.08 | Guia Tema 1; Apuntes pp. 35–36; 135–137 [desarrollado] | |

## Tema 2: Postulados

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.2.01 | **Postulados: estados, observables y medida** — Estado como rayo del espacio de Hilbert, observables hermíticos y regla general de medida. | mc.1.05 | Guia Tema 2; Apuntes pp. 37–40 [desarrollado] | |
| mc.2.02 | **Probabilidades y reducción del estado** — Descomposición espectral, probabilidades de resultados, espectros discreto y continuo y reducción tras la medida. | mc.2.01 | Guia Tema 2; Apuntes pp. 38–39 [desarrollado] | |
| mc.2.03 | **Incertidumbre, compatibilidad y CCOC** — Valores medios, desviaciones, relaciones de incertidumbre, medida simultánea y conjuntos completos de observables que conmutan. | mc.2.01 | Guia Tema 2; Apuntes pp. 41–43 [desarrollado] | |
| mc.2.04 | **Dinámica de Schrödinger, continuidad y corriente** — Ecuación de Schrödinger, determinismo y superposición; conservación de probabilidad, ecuación de continuidad, corriente y potencial vector. | mc.2.01, cu.02 | Guia Tema 2; Apuntes pp. 43–47 [desarrollado] | |
| mc.2.05 | **Ehrenfest, límite clásico y sistemas conservativos** — Teorema de Ehrenfest, campo de velocidades, comparación clásica-cuántica y evolución de sistemas conservativos. | mc.2.04 | Guia Tema 2; Apuntes pp. 48–50 [desarrollado] | |
| mc.2.06 | **Representación de energía y estados estacionarios** — Constantes del movimiento, base de energía, estados estacionarios, frecuencias de Bohr y evolución de fases relativas. | mc.2.05, mc.1.08 | Guia Tema 2; Apuntes pp. 50–52 [desarrollado] | |
| mc.2.07 | **Operador densidad y mezclas estadísticas** — Estados puros y mezclas, propiedades de la matriz densidad, valor medio, positividad y ensamble canónico. | mc.2.06, mc.1.07 | Guia Tema 2; Apuntes pp. 53–54; 61–69 [desarrollado] | |
| mc.2.08 | **Productos tensoriales, subsistemas y entrelazamiento** — Estados producto y estados correlacionados, observables de subsistemas, traza parcial y entrelazamiento. | mc.2.07, mc.1.07 | Guia Tema 2; Apuntes pp. 55–60; 70–73 [desarrollado] | |
| mc.2.09 | **Operador de evolución, imágenes y sistemas de dos niveles** — Evolución unitaria y operador de evolución; imágenes de Schrödinger y Heisenberg; aplicación al sistema de dos niveles y oscilaciones de Rabi. | mc.2.06, mc.1.09 | Guia Tema 2; Apuntes pp. 74–84; 90–97 [desarrollado] | |

## Tema 3: Oscilador armónico

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.3.01 | **Oscilador 1-D: variables adimensionales y operadores escalera** — Hamiltoniano adimensional, operadores creación y aniquilación, operador número y álgebra de conmutación. | mc.1.08, cu.02 | Guia Tema 3; Apuntes pp. 103–107 [desarrollado] | |
| mc.3.02 | **Espectro, estado fundamental y funciones de Hermite** — Cuantización del operador número, energía del oscilador, estado fundamental, construcción de autoestados y funciones de Hermite. | mc.3.01 | Guia Tema 3; Apuntes pp. 108–110 [desarrollado] | |
| mc.3.03 | **Valores medios, incertidumbre y evolución del oscilador** — Elementos de matriz, valores medios de X y P, incertidumbre, teorema del virial y evolución temporal. | mc.3.02 | Guia Tema 3; Apuntes pp. 109–113 [desarrollado] | |
| mc.3.04 | **Osciladores 2-D/3-D, campo eléctrico y equilibrio térmico** — Degeneración del oscilador 2-D y 3-D, oscilador cargado en campo eléctrico, desplazamiento y polarización, función de partición, límites térmicos e inversión de población. | mc.3.03, mc.1.07 | Guia Tema 3; Apuntes pp. 113–119 [desarrollado] | |

## Tema 4: Momento angular, espín y rotaciones

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.4.01 | **Álgebra del momento angular** — Relaciones de conmutación, operadores escalera, espectro de J² y Jz y bases estándar del momento angular. | mc.1.05, cu.05 | Guia Tema 4; Apuntes pp. 121–123 [desarrollado] | |
| mc.4.02 | **Momento angular orbital y grupo de rotaciones** — Partícula sin espín, armónicos esféricos, representación unitaria de rotaciones, generadores y rotaciones finitas. | mc.4.01, m2.08 (0.5) | Guia Tema 4; Apuntes pp. 124–131 [desarrollado] | |
| mc.4.03 | **Espín 1/2, espacios de espín y espinores** — Espacio de estados de espín 1/2, representación en bases de espín y coordenadas, espinores, operadores de Pauli y medidas parciales. | mc.4.02, mc.1.09 | Guia Tema 4; Apuntes pp. 132–140 [desarrollado] | |
| mc.4.04 | **Momento magnético, precesión de Larmor y dos niveles** — Acoplamiento del espín a un campo magnético, momento magnético, precesión de Larmor, dinámica de dos niveles y transición entre niveles. | mc.4.03, em.6.05 (0.5) | Guia Tema 4; Apuntes pp. 85–102 [desarrollado] | |
| mc.4.05 | **Rotaciones y transformación de observables** — Rotaciones globales y del espacio completo, transformación de operadores y observables escalares y vectoriales. | mc.4.03 | Guia Tema 4; Apuntes pp. 123–131; 140–142 [desarrollado] | |
| mc.4.06 | **Suma de dos momentos angulares** — Producto tensorial y base acoplada; estados singlete y triplete como caso de dos espines 1/2. | mc.4.03, mc.1.07 | Guia Tema 4; Apuntes pp. 143–149 [desarrollado] | |
| mc.4.07 | **Acoplamiento general y coeficientes de Clebsch–Gordan** — Valores permitidos de J, degeneraciones, construcción de multipletes y coeficientes de Clebsch–Gordan para momentos angulares acoplados. | mc.4.06 | Guia Tema 4; Apuntes pp. 145–149 [desarrollado] | |
| mc.4.08 | **Wigner–Eckart, reglas de selección y Landé** — Componentes esféricas de operadores vectoriales, teorema de Wigner–Eckart, reglas de selección, proyección/factor de Landé y aplicación al acoplamiento LS de átomos multielectrónicos. | mc.4.07 | Guia Tema 4; Apuntes pp. 150–157 [desarrollado] | |

## Tema 5: Dispersión y colisiones

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.5.01 | **Scattering: sección eficaz, amplitud y estados asintóticos** — Dispersión elástica, dispositivo experimental, sección eficaz diferencial, estados estacionarios y forma asintótica de la amplitud. | mc.2.05, mo.03 | Guia Tema 5; Apuntes pp. 159–165 [desarrollado] | |
| mc.5.02 | **Flujo, interferencia y teorema óptico** — Flujo de probabilidad, término de interferencia entre onda incidente y dispersada, paquetes de onda y teorema óptico. | mc.5.01 | Guia Tema 5; Apuntes pp. 166–168 [desarrollado] | |
| mc.5.03 | **Ecuación integral y funciones de Green** — Funciones de Green entrante y saliente, condición asintótica y ecuación integral para la función y la amplitud de scattering. | mc.5.01, m2.02 (0.5) | Guia Tema 5; Apuntes pp. 168–170 [desarrollado] | |
| mc.5.04 | **Aproximación de Born y rango de validez** — Primera aproximación y serie de Born, criterio de validez y aplicación a potenciales de Yukawa y Coulomb apantallado. | mc.5.03, m2.04 (0.5) | Guia Tema 5; Apuntes pp. 167–172; 184 [desarrollado] | |
| mc.5.05 | **Ondas parciales, parámetro de impacto y desfasajes** — Expansión en ondas parciales, cambio entre ondas planas y esféricas, parámetro de impacto, comportamiento asintótico y desplazamientos de fase. | mc.5.01, mc.4.02 | Guia Tema 5; Apuntes pp. 173–180 [desarrollado] | |
| mc.5.06 | **Aplicaciones de ondas parciales y resonancias** — Scattering por esfera impenetrable y pozos, resonancias de baja energía y aplicaciones a Yukawa y Rutherford. | mc.5.05 | Guia Tema 5; Apuntes pp. 181–187 [desarrollado] | |
| mc.5.07 | **Scattering inelástico y absorción** — Canales elásticos e inelásticos, absorción como pérdida de flujo del canal incidente y efecto sobre amplitudes y secciones eficaces. | mc.5.01 | Guia Tema 5, dispersión con absorción; Libro Cohen-Tannoudji II, VIII; Apuntes pp. 160 [desarrollado] | |

## Tema 6: Métodos aproximados

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.6.01 | **Perturbaciones estacionarias no degeneradas** — Expansión en potencias, correcciones de energía y estado, condiciones de normalización y validez para niveles no degenerados. | mc.2.05 | Guia Tema 6; Apuntes pp. 189–194 [desarrollado] | |
| mc.6.02 | **Perturbaciones estacionarias degeneradas** — Selección de la base adecuada, diagonalización de la perturbación en el subespacio degenerado y desdoblamiento de niveles. | mc.6.01 | Guia Tema 6; Apuntes pp. 195–202 [desarrollado] | |
| mc.6.03 | **Método variacional (incluido en el resumen del tema)** — Principio variacional, funciones de prueba y cota superior a la energía fundamental; figura en el resumen del Tema 6, sin desarrollo manuscrito identificable en el escaneo. | mc.6.01 | Guia Tema 6; Apuntes pp. 19 [resumen] | |
| mc.6.04 | **Aproximación WKB (incluida en el resumen del tema)** — Aproximación semiclásica, reglas de conexión y efecto túnel; figura en el resumen del Tema 6, sin desarrollo manuscrito identificable en el escaneo. | mc.6.01, cu.02 | Guia Tema 6; Apuntes pp. 19 [resumen] | |
| mc.6.05 | **Perturbaciones dependientes del tiempo** — Amplitudes y probabilidades de transición, aproximación a primer orden, reglas de selección y perturbación monocromática/armónica. | mc.6.01, mc.2.08 | Guia Tema 6; Apuntes pp. 203–209 [desarrollado] | |
| mc.6.06 | **Regla de oro de Fermi y transiciones al continuo** — Continuo de estados finales, densidad de estados, emisión espontánea, aproximación resonante y tasa de transición. | mc.6.05 | Guia Tema 6; Apuntes pp. 205–216 [desarrollado] | |
| mc.6.07 | **Perturbaciones al oscilador armónico bidimensional** — Aplicación de la perturbación estacionaria al espectro degenerado del oscilador armónico bidimensional; nodo operativo conservado para los problemas asociados. | mc.6.02, mc.3.04 | Guia Tema 6, aplicación al oscilador armónico bidimensional; Apuntes_manuscritos MECANICA CUANTICA. TEORIA.pdf, pp. 113–119; Libro Cohen-Tannoudji II, XI; Apuntes pp. 113–119 [desarrollado] | |
| mc.6.08 | **Decaimiento de un estado discreto acoplado al continuo** — Evolución de un estado discreto acoplado a un continuo, decaimiento exponencial, anchura de Breit–Wigner y desplazamiento de Lamb. | mc.6.06, mc.2.06 | Guia Tema 6, continuo y decaimiento; Apuntes_manuscritos MECANICA CUANTICA. TEORIA.pdf, pp. 217–221; Apuntes pp. 217–221 [desarrollado] | |

## Tema 7: Partículas idénticas (Tema 8 en el desarrollo manuscrito)

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| mc.7.01 | **Indistinguibilidad, permutaciones y simetrización** — Partículas idénticas frente a distinguibles, degeneración de intercambio, operador permutación, subespacios simétrico y antisimétrico, bosones y fermiones. | mc.2.01, mc.1.07, cu.06 | Guia Tema 7; Apuntes pp. 223–233 [desarrollado] | |
| mc.7.02 | **Postulado de simetrización y determinantes de Slater** — Proyectores de simetrización y antisimetrización, conexión espín–estadística, construcción de estados físicos y determinantes de Slater. | mc.7.01 | Guia Tema 7; Apuntes pp. 223–234 [desarrollado] | |
| mc.7.03 | **Átomos multielectrónicos y aproximación de campo central** — Aplicación del acoplamiento de momentos angulares y de la simetrización a configuraciones electrónicas, repulsión electrostática y término de intercambio. | mc.7.02, mc.4.08 | Guia Tema 7, átomos multielectrónicos; Libro Cohen-Tannoudji II, XIV y complemento AXIV/BXIV; Apuntes pp. 156–157 [desarrollado] | |
| mc.7.04 | **Colisión y scattering de partículas idénticas** — Suma o diferencia de amplitudes de intercambio según la simetría, interferencia y secciones eficaces en la colisión de partículas idénticas. | mc.7.01, mc.5.01 | Guia Tema 7, colisión entre dos partículas idénticas; Libro Cohen-Tannoudji II, complemento DXIV; Apuntes pp. 227–240 [desarrollado] | |
| mc.7.05 | **Números de ocupación y gases cuánticos ideales** — Bases de números de ocupación, partículas idénticas independientes, condensación de Bose–Einstein y nivel de Fermi. | mc.7.01, mc.7.02 | Guia Tema 7; Apuntes_manuscritos MECANICA CUANTICA. TEORIA.pdf, pp. 234–238; Apuntes pp. 234–238 [desarrollado] | |

## Cuadernos manuscritos de problemas resueltos (UVa)

Además de los apuntes de teoría (`MECANICA CUANTICA. TEORIA.pdf`), se dispone de los dos cuadernos de problemas resueltos a mano por un compañero de la UVa:

1. **`MECANICA CUANTICA. PROBLEMAS1.pdf` (144 páginas):**
   - **Tema 1: Formalismo matemático** (pp. 1–12): ejercicios clave del Cohen Tema 2 resueltos (2.6, 2.9, funciones de operadores, proyectores, matrices de Pauli).
   - **Tema 2: Postulados y evolución** (pp. 13–48): ejercicios del Cohen Tema 3 resueltos (postulados de medida, matrices densidad, entrelazamiento, dinámica unitaria).
   - **Exámenes 1º Parcial UVa resueltos** (pp. 49–104): exámenes de 2017 a 2022 resueltos al completo paso a paso con criterios de corrección de clase.
   - **Exámenes 2º Parcial UVa resueltos** (pp. 105–138): problemas de momento angular, adición de momentos y espín.
   - **Tema 6: Métodos aproximados** (pp. 139–144): teoría de perturbaciones estacionarias y dependientes del tiempo.

2. **`MECANICA CUANTICA. PROBLEMAS2.pdf` (110 páginas):**
   - **Tema 7 / Tema 8 manuscrito: Partículas idénticas** (pp. 1–4): problemas de indistinguibilidad, simetrización/antisimetrización, orbitales espaciales y de espín para fermiones y bosones.
   - **Exámenes oficiales completos resueltos (cuestiones + problemas UVa)** (pp. 5–110):
     - Examen ordinario 09/02/2022 (cuestiones y problemas, pp. 5–27).
     - Examen 22/01/2021 (problemas y cuestiones, pp. 28–43).
     - Cuestiones 24/01/2023 (pp. 44–52).
     - Cuestiones 27/01/2022 (pp. 53–68).
     - Problemas extraordinaria 13/09/2021 (pp. 69–78).
     - Problemas 04/02/2021 (pp. 79–94).
     - Cuestiones ordinaria 23/01/2024 (pp. 95–104).
     - Examen 17/01/2019 con resolución optimizada de espinores (pp. 105–110).

## Estadísticas

- Nodos raíz (sin prerrequisitos): —
- Nodos sin dependientes en todo el sistema: mc.2.02, mc.2.03, mc.2.09, mc.5.02, mc.5.04, mc.5.06, mc.5.07, mc.6.04, mc.6.07, mc.6.08, mc.7.03, mc.7.04, mc.7.05
- Aristas: 79 (15 hacia otras asignaturas)
