# Revisión del grafo — Electromagnetismo

Total: **94 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

## Tema 0: Fundamentos matemáticos (cálculo vectorial)

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.0.01 | **Álgebra vectorial** — Suma, componentes, vectores unitarios, producto escalar y vectorial, vector de posición y coordenadas relativas. | al.05 (0.5) | Wangsness 1-1 a 1-7, 1-20; Griffiths 1.1; Problemas cap. 1 | |
| em.0.02 | **Gradiente y derivada direccional** — Derivación respecto a un escalar, gradiente de un campo escalar, operador nabla. | em.0.01, am.06 (0.5) | Wangsness 1-8, 1-9; Griffiths 1.2.1 a 1.2.3; Problemas cap. 1 | |
| em.0.03 | **Divergencia y rotacional** — Definición e interpretación física; reglas de producto con nabla. | em.0.02 | Wangsness 1-10, 1-19; Griffiths 1.2.4 a 1.2.6; Problemas cap. 1 | |
| em.0.04 | **Laplaciano y operadores de segundo orden** — Segundas derivadas de campos, laplaciano escalar y vectorial, identidades (rot grad = 0, div rot = 0). | em.0.03 | Wangsness 1-19; Griffiths 1.2.7; Problemas cap. 1 | |
| em.0.05 | **Integrales de línea, superficie y volumen** — Circulación, elemento vectorial de superficie, flujo de un campo vectorial. | em.0.01 | Wangsness 1-11 a 1-13; Griffiths 1.3.1; Problemas cap. 1 | |
| em.0.06 | **Teorema de la divergencia** — Teorema de Gauss-Ostrogradski y teorema de Green; uso para convertir integrales. | em.0.03, em.0.05 | Wangsness 1-14; Griffiths 1.3.4; Problemas cap. 1 | |
| em.0.07 | **Teorema de Stokes** — Relación circulación-rotacional; campos irrotacionales y solenoidales. | em.0.03, em.0.05 | Wangsness 1-15; Griffiths 1.3.5; Problemas cap. 1 | |
| em.0.08 | **Coordenadas cilíndricas y esféricas** — Vectores base, elementos de línea/superficie/volumen y operadores diferenciales en curvilíneas. | em.0.01 | Wangsness 1-16, 1-17; Griffiths 1.4, Ap. A; Problemas cap. 1 | |
| em.0.09 | **Delta de Dirac** — Delta 1D y 3D, divergencia de r̂/r², representación de cargas puntuales como densidades. | em.0.05 | Griffiths 1.5 | |
| em.0.10 | **Campos conservativos, potenciales y teorema de Helmholtz** — Condiciones de campo conservativo, existencia de potenciales escalar y vector, teorema de Helmholtz. | em.0.06, em.0.07 | Wangsness 1-18; Griffiths 1.6, Ap. B; Problemas cap. 1 (1.4) | |

## Tema 1: Electrostática en el vacío

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.1.01 | **Carga eléctrica** — Propiedades de la carga: cuantización, conservación, invariancia; fenomenología básica. | — | Wangsness 2-1; Griffiths 2.1.1; Problemas cap. 2 (2.1) | |
| em.1.02 | **Ley de Coulomb y superposición** — Fuerza entre cargas puntuales, principio de superposición, sistemas de cargas puntuales. | em.1.01, em.0.01, fco.01 (0.5) | Wangsness 2-2, 2-3; Griffiths 2.1.2; Problemas cap. 2 (2.2) | |
| em.1.03 | **Distribuciones continuas de carga** — Densidades lineal, superficial y volumétrica; fuerza y campo por integración sobre la distribución. | em.1.02, em.0.05, em.0.08 (0.5) | Wangsness 2-4, 2-5; Griffiths 2.1.4; Problemas cap. 2 | |
| em.1.04 | **El campo eléctrico y las líneas de fuerza** — Definición de E, interpretación, representación mediante líneas de campo. | em.1.02 | Wangsness 3-1, 3-4; Griffiths 2.1.3; Problemas cap. 2 (2.3) | |
| em.1.05 | **Cálculo de E por integración directa** — Campo de hilo infinito, anillo, disco, plano infinito y otras geometrías canónicas. | em.1.03, em.1.04, em.0.08 | Wangsness 3-2, 3-3; Griffiths 2.1.4; Problemas cap. 2 | |
| em.1.06 | **Flujo de E y ley de Gauss (forma integral)** — Concepto de flujo, deducción de la ley de Gauss, ángulo sólido. | em.1.04, em.0.05 | Wangsness 4-1; Griffiths 2.2.1; Problemas cap. 2 (2.5.1) | |
| em.1.07 | **Aplicaciones de la ley de Gauss** — Cálculo de E con simetría esférica, cilíndrica y plana; elección de superficie gaussiana. | em.1.06, em.0.08 (0.5) | Wangsness 4-2; Griffiths 2.2.3; Problemas cap. 2 | |
| em.1.08 | **Ecuaciones diferenciales de la electrostática** — div E = ρ/ε₀ y rot E = 0; paso entre formas integral y diferencial. | em.1.06, em.0.06, em.0.07 (0.5), em.0.09 (0.5) | Wangsness 4-3; Griffiths 2.2.2, 2.2.4; Problemas cap. 2 (2.5.2) | |
| em.1.09 | **El potencial electrostático** — Definición, relación E = -grad V, cálculo para distribuciones, superficies equipotenciales. | em.1.04, em.0.02, em.0.10 (0.5) | Wangsness 5-1 a 5-3; Griffiths 2.3; Problemas cap. 2 (2.4) | |
| em.1.10 | **Energía de una distribución de cargas** — Trabajo para ensamblar cargas puntuales y distribuciones continuas; energía y potencial. | em.1.09 | Wangsness 5-4, 7-1; Griffiths 2.4.1, 2.4.2; Problemas cap. 3 (3.3) | |
| em.1.11 | **Energía en función del campo** — Densidad de energía ε₀E²/2, energía total del campo, comentarios sobre autoenergía. | em.1.10, em.0.06 (0.5) | Wangsness 7-3; Griffiths 2.4.3, 2.4.4; Problemas cap. 3 (3.3) | |
| em.1.12 | **El dipolo eléctrico** — Potencial y campo del dipolo, momento dipolar, fuerza y par en campo externo. | em.1.09 | Wangsness 8-2; Griffiths 3.4.4; Problemas cap. 2 | |
| em.1.13 | **Desarrollo multipolar** — Expansión del potencial a grandes distancias: monopolo, dipolo, cuadrupolo; energía en campo externo. | em.1.12, em.1.09 | Wangsness 8-1, 8-3, 8-4; Griffiths 3.4; Jackson 4.1, 4.2 | |
| em.1.14 | **Condiciones de frontera del campo electrostático** — Discontinuidad de la componente normal de E y continuidad de la tangencial y del potencial en superficies cargadas. | em.1.08 | Wangsness 9-1 a 9-5; Griffiths 2.3.5; Problemas cap. 3 | |

## Tema 2: Electrostática en presencia de conductores

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.2.01 | **Conductores en equilibrio electrostático** — E interno nulo, carga en la superficie, conductor como volumen equipotencial; campo en la superficie. | em.1.07, em.1.09 | Wangsness 6-1; Griffiths 2.5.1; Problemas cap. 3 (3.1) | |
| em.2.02 | **Cargas inducidas, cavidades y apantallamiento** — Inducción electrostática, cavidades con y sin carga, jaula de Faraday. | em.2.01, em.1.06 | Wangsness 6-1; Griffiths 2.5.2; Feynman II-5; Problemas cap. 3 | |
| em.2.03 | **Fuerza y presión electrostática sobre conductores** — Fuerza por unidad de superficie σ²/2ε₀ sobre la superficie de un conductor. | em.2.01, em.1.14 (0.5) | Wangsness 7-4; Griffiths 2.5.3; Problemas cap. 3 | |
| em.2.04 | **Condiciones de contorno en presencia de conductores** — Formulación de problemas con conductores: potencial dado o carga dada; planteamiento de unicidad. | em.2.01, em.1.14 | Wangsness 9-4, 11-1; Griffiths 3.1.5; Problemas cap. 3 | |
| em.2.05 | **Capacidad y condensadores** — Definición de capacidad; condensador plano, esférico y cilíndrico; asociaciones serie/paralelo. | em.2.01, em.1.09, em.2.04 (0.5) | Wangsness 6-3; Griffiths 2.5.4; Problemas cap. 3 (3.4.2) | |
| em.2.06 | **Sistemas de conductores: coeficientes de potencial y capacidad** — Matrices de coeficientes p_ij y c_ij, propiedades y su relación con la capacidad. | em.2.05, em.1.09 | Wangsness 6-2; Problemas cap. 3 (3.4.1); Panofsky cap. 3 | |
| em.2.07 | **Energía de sistemas de conductores** — Energía almacenada en condensadores y sistemas de conductores cargados. | em.2.05, em.1.10 | Wangsness 7-2; Griffiths 2.5.4; Problemas cap. 3 | |
| em.2.08 | **Fuerzas electrostáticas en sistemas de conductores** — Fuerzas a carga constante y a potencial constante; método de la energía. | em.2.07 | Wangsness 7-4; Problemas cap. 3; Panofsky 6-4 | |

## Tema 3: Electrostática en presencia de medios dieléctricos

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.3.01 | **Polarización y sus mecanismos** — Dieléctricos, polarización electrónica/iónica/orientacional, vector polarización P. | em.1.12 | Wangsness 10-1; Griffiths 4.1; Problemas cap. 3 (3.2.1) | |
| em.3.02 | **Cargas de polarización** — Densidades de carga ligada ρ_b = -div P y σ_b = P·n; interpretación física. | em.3.01, em.0.03 (0.5) | Wangsness 10-2; Griffiths 4.2.1, 4.2.2; Problemas cap. 3 (3.2.2) | |
| em.3.03 | **Campo dentro de un dieléctrico; esfera polarizada** — Campo creado por objetos polarizados; el ejemplo canónico de la esfera uniformemente polarizada. | em.3.02, em.1.09 | Wangsness 10-3, 10-4; Griffiths 4.2.3; Problemas cap. 3 | |
| em.3.04 | **El vector desplazamiento D y la ley de Gauss generalizada** — Definición de D, ley de Gauss con cargas libres, precauciones (paralelo engañoso con E). | em.3.02, em.1.08 | Wangsness 10-5; Griffiths 4.3; Problemas cap. 3 (3.2.4) | |
| em.3.05 | **Relaciones constitutivas: susceptibilidad y permitividad** — Medios lineales, isótropos y homogéneos; χ_e, ε y constante dieléctrica. | em.3.04 | Wangsness 10-7; Griffiths 4.4.1; Problemas cap. 3 (3.2.3) | |
| em.3.06 | **Clasificación de los medios dieléctricos** — Lineales/no lineales, isótropos/anisótropos, homogéneos/inhomogéneos; polarizabilidad molecular, Clausius-Mossotti. | em.3.05 | Wangsness 10-6, B-1; Griffiths 4.4.1; Feynman II-11 | |
| em.3.07 | **Condiciones de contorno con dieléctricos** — Continuidad de D_n (sin carga libre) y E_t; refracción de líneas de campo; problemas de frontera con dieléctricos. | em.3.04, em.1.14 | Wangsness 10-7; Griffiths 4.3.3, 4.4.2; Problemas cap. 3 (3.2.5) | |
| em.3.08 | **Condensadores con dieléctricos** — Capacidad con dieléctricos totales o parciales, en serie/paralelo dentro del condensador. | em.3.05, em.3.07, em.2.05 | Wangsness 10-7; Griffiths 4.4.2; Problemas cap. 3 | |
| em.3.09 | **Energía y fuerzas en presencia de dieléctricos** — Densidad de energía D·E/2, fuerzas sobre dieléctricos, succión de láminas en condensadores. | em.3.05, em.1.11, em.2.08 (0.5) | Wangsness 10-8, 10-9; Griffiths 4.4.3, 4.4.4; Problemas cap. 3 | |

## Tema 4: Teoría del potencial

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.4.01 | **Ecuaciones de Poisson y Laplace; unicidad** — Deducción, propiedades de las soluciones armónicas y teoremas de unicidad. | em.1.08, em.1.09, em.0.04 | Wangsness 11-1; Griffiths 3.1; Panofsky 3-1 | |
| em.4.02 | **Método de las imágenes: plano conductor** — Carga frente a plano a tierra: potencial, carga inducida, fuerza y energía. | em.4.01, em.2.04 | Wangsness 11-2; Griffiths 3.2.1 a 3.2.3; Panofsky 3-5 | |
| em.4.03 | **Método de las imágenes: esfera y otras geometrías** — Carga frente a esfera conductora (a tierra y aislada), imágenes con dieléctricos. | em.4.02 | Wangsness 11-2, 11-3; Griffiths 3.2.4; Jackson cap. 2 | |
| em.4.04 | **Separación de variables en coordenadas cartesianas** — Soluciones producto de Laplace en 2D/3D rectangular, series de Fourier para condiciones de contorno. | em.4.01, m4.03 (0.5) | Wangsness 11-4; Griffiths 3.3.1; Jackson 2.9, 2.10 | |
| em.4.05 | **Separación de variables en coordenadas esféricas** — Polinomios de Legendre, problemas con simetría azimutal (esfera en campo uniforme, etc.). | em.4.01, em.0.08, m2.08 (0.5) | Wangsness 11-5; Griffiths 3.3.2; Jackson 3.1 a 3.3 | |
| em.4.06 | **Separación de variables en coordenadas cilíndricas** — Soluciones armónicas cilíndricas 2D; nociones de funciones de Bessel. | em.4.01, em.4.05 (0.5) | Jackson 3.6, 3.7; Panofsky 5-8, 5-9 | |

## Tema 5: Corriente eléctrica

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.5.01 | **Densidad e intensidad de corriente** — Naturaleza de la corriente, J y su relación con I, velocidad de arrastre, tipos de corriente. | em.1.01 | Wangsness 12-1; Griffiths 5.1.3; Problemas cap. 4 (4.1, 4.2) | |
| em.5.02 | **La ecuación de continuidad** — Conservación local de la carga, forma integral y diferencial, corrientes estacionarias (div J = 0). | em.5.01, em.0.06 | Wangsness 12-2; Problemas cap. 4 (4.3); Thide 1.3.1 | |
| em.5.03 | **Ley de Ohm, conductividad y resistencia** — J = σE, modelo microscópico, resistencia de conductores filiformes y geometrías sencillas. | em.5.01, em.1.09 (0.5) | Wangsness 12-3, 12-5; Griffiths 7.1.1; Problemas cap. 4 (4.4, 4.5) | |
| em.5.04 | **Problemas de corrientes estacionarias y condiciones de contorno** — Resolución de problemas de conducción con la ecuación de Laplace; condiciones de contorno para J. | em.5.02, em.5.03, em.4.01 (0.5) | Panofsky 7-3; Problemas cap. 4 | |
| em.5.05 | **Relajación de la carga** — Tiempo de relajación τ = ε/σ, evolución de la carga libre en un conductor. | em.5.02, em.5.03, em.3.05 (0.5) | Wangsness 12-6; Panofsky 7-4 | |
| em.5.06 | **Ley de Joule, generadores y fuerza electromotriz** — Disipación de energía, fem de un generador, potencia suministrada, motores. | em.5.03 | Wangsness 12-4; Griffiths 7.1.2; Problemas cap. 4 (4.6 a 4.8) | |
| em.5.07 | **Leyes de Kirchhoff y circuitos de corriente continua** — Nudos y mallas, método de corrientes de malla, equivalentes Thévenin/Norton. | em.5.06, em.5.03 | Problemas cap. 4 (4.9 a 4.13) | |

## Tema 6: Magnetostática en el vacío

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.6.01 | **Interacción entre corrientes: ley de fuerzas de Ampère** — Experiencia de Oersted, fuerza entre circuitos completos y entre corrientes paralelas. | em.5.01, em.0.01 | Wangsness 13-1 a 13-3; Problemas cap. 5 | |
| em.6.02 | **El campo B: ley de Biot y Savart** — Definición del campo de inducción magnética y su cálculo a partir de corrientes. | em.6.01, em.0.05 | Wangsness 14-1; Griffiths 5.2; Problemas cap. 5 (5.4) | |
| em.6.03 | **Cálculo de B por Biot-Savart** — Hilo recto (finito e infinito), espira circular, solenoide, plano de corriente. | em.6.02, em.0.08 | Wangsness 14-2 a 14-4; Griffiths 5.2.2; Problemas cap. 5 | |
| em.6.04 | **Fuerza de Lorentz y fuerza sobre corrientes** — F = q(E + v×B), fuerza sobre elementos de corriente, par sobre una espira. | em.6.02, em.1.04 (0.5) | Wangsness 14-5; Griffiths 5.1; Problemas cap. 5 (5.5, 5.6) y cap. 9 (9.1) | |
| em.6.05 | **Movimiento de partículas cargadas en campos E y B** — Movimiento ciclotrónico, campos cruzados, ciclotrón y betatrón. | em.6.04 | Wangsness Ap. A; Problemas cap. 9; Feynman II-29 | |
| em.6.06 | **Ecuaciones de la magnetostática: div B = 0 y teorema de Ampère** — Forma integral y diferencial; aplicaciones del teorema de Ampère a simetrías (hilo, solenoide, toroide). | em.6.02, em.0.06, em.0.07 | Wangsness 15-1 a 15-3, 16-1; Griffiths 5.3; Problemas cap. 5 (5.1, 5.2) | |
| em.6.07 | **El potencial vector** — Definición B = rot A, elección de gauge, cálculo para corrientes sencillas. | em.6.06, em.0.10 | Wangsness 16-2 a 16-5; Griffiths 5.4.1; Problemas cap. 5 (5.3) | |
| em.6.08 | **El potencial escalar magnético** — Regiones sin corriente: B = -grad φ_m; analogías con electrostática y limitaciones. | em.6.06, em.1.09 (0.5) | Panofsky 7-7; Jackson 5.9 | |
| em.6.09 | **El dipolo magnético y el desarrollo multipolar** — Desarrollo multipolar de A, momento magnético, campo dipolar, fuerza y par en campo externo. | em.6.07, em.6.04 (0.5), em.1.13 (0.5) | Wangsness 19-1 a 19-4; Griffiths 5.4.3; Problemas cap. 5 (5.7) | |
| em.6.10 | **Condiciones de contorno del campo magnetostático** — Continuidad de B_n y salto de B_t a través de láminas de corriente. | em.6.06, em.1.14 (0.5) | Griffiths 5.4.2; Jackson 5.8 | |

## Tema 7: Inducción electromagnética

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.7.01 | **Ley de Faraday y ley de Lenz** — fem inducida por variación de flujo, signo (Lenz), forma integral y diferencial. | em.6.03, em.5.06 | Wangsness 17-1, 17-2; Griffiths 7.2.1; Problemas cap. 7 (7.1) | |
| em.7.02 | **fem de movimiento: medios en movimiento** — Circuitos móviles en campos estáticos, regla del flujo y sus excepciones, generador de alterna. | em.7.01, em.6.04 | Wangsness 17-3; Griffiths 7.1.3; Feynman II-17; Problemas cap. 7 | |
| em.7.03 | **El campo eléctrico inducido** — E no conservativo con rot E = -∂B/∂t; cálculo de E inducido en simetrías. | em.7.01, em.1.08 (0.5) | Wangsness 17-2; Griffiths 7.2.2; Problemas cap. 7 | |
| em.7.04 | **Autoinducción e inducción mutua** — Coeficientes L y M, fórmula de Neumann, cálculo para solenoides, toroides y líneas. | em.7.01, em.6.07 (0.5) | Wangsness 17-4; Griffiths 7.2.3; Problemas cap. 7 (7.2) | |
| em.7.05 | **Aplicaciones de la ley de inducción** — Generadores, transformadores, corrientes de Foucault, betatrón. | em.7.02, em.7.04 (0.5) | Feynman II-16, II-17; Problemas cap. 7 | |
| em.7.06 | **Energía magnética** — Energía de sistemas de corrientes estacionarias, densidad B²/2μ₀, energía en inductores. | em.7.04, em.1.11 (0.5) | Wangsness 18-1, 18-2; Griffiths 7.2.4; Problemas cap. 7 (7.3.1) | |
| em.7.07 | **Fuerzas magnéticas entre circuitos** — Fuerzas a flujo constante y a corriente constante mediante la energía magnética. | em.7.06, em.6.04 (0.5) | Wangsness 18-3; Problemas cap. 7 (7.3.2) | |

## Tema 8: Corrientes lentamente variables

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.8.01 | **Aproximación cuasiestacionaria y leyes de Kirchhoff** — Validez de la teoría de circuitos para corrientes lentamente variables. | em.5.07, em.7.04 | Problemas cap. 8 (8.1) | |
| em.8.02 | **Componentes ideales: R, L, C, M y generador** — Relaciones tensión-corriente de cada elemento ideal. | em.8.01, em.2.05 (0.5) | Problemas cap. 8 (8.2) | |
| em.8.03 | **Régimen transitorio** — Carga/descarga RC, establecimiento RL, oscilaciones RLC; constantes de tiempo. | em.8.02, m2.06 (0.5) | Problemas cap. 8 (8.3) | |
| em.8.04 | **Notación fasorial e impedancia** — Magnitudes complejas, impedancia de R, L, C y asociaciones. | em.8.02 | Problemas cap. 8 (8.4.1 a 8.4.3) | |
| em.8.05 | **Circuitos de alterna en régimen permanente** — Kirchhoff con fasores, análisis de mallas en AC, transformadores en circuitos. | em.8.04, em.5.07 | Problemas cap. 8 (8.4.4) | |
| em.8.06 | **Potencia en corriente alterna** — Potencia instantánea, activa, reactiva y aparente; factor de potencia; valores eficaces. | em.8.05 | Problemas cap. 8 (8.4.5) | |
| em.8.07 | **Resonancia** — Resonancia serie y paralelo, factor de calidad Q, ancho de banda. | em.8.05 | Problemas cap. 8 (8.4.6) | |

## Tema 9: Magnetostática en presencia de medios materiales

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.9.01 | **Magnetización y corrientes de magnetización** — Vector M, corrientes ligadas J_m = rot M y K_m = M×n; densidad de cargas magnéticas equivalentes. | em.6.09, em.3.01 (0.5) | Wangsness 20-1, 20-2; Griffiths 6.1, 6.2; Problemas cap. 6 (6.1, 6.2) | |
| em.9.02 | **La esfera uniformemente magnetizada** — Campo de objetos magnetizados; el ejemplo canónico de la esfera y su paralelo con la esfera polarizada. | em.9.01, em.3.03 (0.5) | Wangsness 20-3; Jackson 5.10; Problemas cap. 6 | |
| em.9.03 | **El campo H y la ley de Ampère generalizada** — Definición de H, teorema de Ampère con corrientes libres, paralelo engañoso con B. | em.9.01, em.6.06 | Wangsness 20-4; Griffiths 6.3; Problemas cap. 6 (6.3, 6.4) | |
| em.9.04 | **Susceptibilidad, permeabilidad y clasificación de medios magnéticos** — Medios l.i.h., χ_m y μ; diamagnetismo, paramagnetismo, ferromagnetismo. | em.9.03, em.3.05 (0.5) | Wangsness 20-5, B-2; Griffiths 6.4.1; Problemas cap. 6 (6.5) | |
| em.9.05 | **Ferromagnetismo, histéresis y circuitos magnéticos** — Curva de magnetización, ciclo de histéresis, imanes permanentes, circuitos magnéticos. | em.9.04 | Wangsness 20-7, 20-8; Griffiths 6.4.2; Problemas cap. 6 (6.6); Feynman II-36, II-37 | |
| em.9.06 | **Condiciones de contorno con medios magnéticos** — Continuidad de B_n y de H_t (sin corriente libre); problemas de frontera magnéticos. | em.9.03, em.6.10 | Griffiths 6.3.3; Panofsky 8-3; Problemas cap. 6 | |
| em.9.07 | **Energía y fuerzas con medios magnéticos** — Densidad de energía B·H/2 en medios lineales, fuerzas sobre materiales magnéticos. | em.9.03, em.7.06 | Wangsness 20-6; Problemas cap. 6 | |

## Tema 10: Las ecuaciones del campo electromagnético

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| em.10.01 | **Corriente de desplazamiento y ecuaciones de Maxwell** — Crítica de la ley de Ampère, término de Maxwell, sistema completo de ecuaciones en vacío y en medios. | em.1.08, em.6.06, em.7.01, em.5.02 | Wangsness 21-1 a 21-3; Griffiths 7.3; Problemas cap. 10 (10.1 a 10.3) | |
| em.10.02 | **Condiciones de frontera generales del campo electromagnético** — Las cuatro condiciones de salto para E, D, B, H en superficies de discontinuidad. | em.10.01, em.1.14, em.3.07 (0.5), em.9.06 (0.5) | Griffiths 7.3.6; Problemas cap. 10 (10.4) | |
| em.10.03 | **Potenciales electromagnéticos y transformaciones gauge** — Potenciales V y A dependientes del tiempo, libertad gauge, gauges de Coulomb y Lorenz. | em.10.01, em.6.07, em.1.09 | Wangsness 22-1 a 22-3; Griffiths 10.1; Thide cap. 3 | |
| em.10.04 | **Energía del campo electromagnético: teorema de Poynting** — Vector de Poynting, balance de energía, ejemplos de flujo de energía. | em.10.01, em.1.11, em.7.06 | Wangsness 21-4; Griffiths 8.1.2; Feynman II-27 | |
| em.10.05 | **Momento del campo electromagnético** — Densidad de momento, presión de radiación; noción del tensor de tensiones de Maxwell. | em.10.04 | Wangsness 21-5; Griffiths 8.2; Panofsky 10-6 | |
| em.10.06 | **La ecuación de ondas y las ondas planas** — Deducción de la ecuación de ondas para E y B en el vacío, velocidad de la luz, estructura transversal. | em.10.01, em.0.04 | Wangsness 24-1, 24-2; Griffiths 9.2; Problemas cap. 10 (10.6) | |
| em.10.07 | **Ondas planas armónicas: Helmholtz y polarización** — Solución armónica, ecuación de Helmholtz, notación compleja, estados de polarización, promedios temporales. | em.10.06 | Wangsness 24-5 a 24-7; Griffiths 9.1.2, 9.2.2, 9.2.3; Thide cap. 2 | |
| em.10.08 | **Propagación en medios dieléctricos** — Índice de refracción, velocidad e impedancia en medios lineales; energía transportada. | em.10.07, em.3.05 | Wangsness 24-2; Griffiths 9.3.1; Problemas cap. 10 | |
| em.10.09 | **Propagación en medios conductores** — Vector de onda complejo, atenuación, profundidad de penetración (efecto pelicular), buen/mal conductor. | em.10.07, em.5.03, em.5.05 (0.5) | Wangsness 24-3; Griffiths 9.4.1; Thide 2.2.2 | |

## Estadísticas

- Nodos raíz (sin prerrequisitos): em.1.01
- Nodos sin dependientes en todo el sistema: em.1.05, em.2.02, em.2.03, em.2.06, em.3.06, em.3.08, em.3.09, em.4.03, em.4.06, em.5.04, em.6.08, em.7.03, em.7.05, em.7.07, em.8.03, em.8.06, em.8.07, em.9.02, em.9.05, em.9.07
- Aristas: 184 (6 hacia otras asignaturas)
