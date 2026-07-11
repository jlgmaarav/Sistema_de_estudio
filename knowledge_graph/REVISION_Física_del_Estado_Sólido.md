# Revisión del grafo — Física del Estado Sólido

Total: **41 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

## Estructura cristalina y difracción

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.1.01 | **Red, base y redes de Bravais** — Concepto de estructura cristalina, celdilla primitiva y unidad, representación matricial. | fm.01 | Guia 2.1-2.2; Libro Hook-Hall / Ashcroft-Mermin | |
| es.1.02 | **Índices de Miller** — Notaciones cristalográficas de planos y direcciones. | es.1.01 | Guia 2.3 | |
| es.1.03 | **Red recíproca y zonas de Brillouin** — Propiedades de la red recíproca, construcción de zonas de Brillouin. | es.1.02 | Guia 2.4 | |
| es.1.04 | **Difracción de rayos X en cristales** — Condiciones de Laue, ley de Bragg, factor de estructura. | es.1.03 | Guia 2.5 | |

## Teoría de bandas

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.2.01 | **Modelo de Sommerfeld** — Gas de electrones libres, esfera de Fermi, densidad de estados, calor específico electrónico. | cu.08, fe.05 | Guia 3.1 | |
| es.2.02 | **Fallos del modelo de electrones libres** — Limitaciones de Sommerfeld; necesidad del potencial periódico. | es.2.01 | Guia 3.1 | |
| es.2.03 | **Teorema de Bloch** — Funciones de onda monoelectrónicas en potencial periódico, forma de Bloch. | es.1.03, es.2.02, mc.1.06 (0.5) | Guia 3.2-3.3 | |
| es.2.04 | **Zona reducida y recuento de estados** — Reducción a la primera zona de Brillouin, condiciones de contorno de Born-von Karman. | es.2.03 | Guia 3.3.1-3.3.2 | |
| es.2.05 | **Electrones casi libres** — Potencial periódico débil, apertura de gaps en los bordes de zona. | es.2.04, mc.6.02 (0.5) | Guia 3.4 | |
| es.2.06 | **Método de ligaduras fuertes** — Tight-binding, bandas a partir de orbitales atómicos. | es.2.04 | Guia 3.5 | |
| es.2.07 | **Metales, aislantes y semiconductores** — Carácter según el llenado de bandas. | es.2.05, es.2.06 | Guia 3.6 | |

## Dinámica semiclásica

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.3.01 | **Ecuaciones semiclásicas** — Movimiento de electrones de conducción bajo campos externos. | es.2.07 | Guia 4.1 | |
| es.3.02 | **Velocidad y masa efectiva** — Velocidad de grupo, tensor de masa efectiva. | es.3.01 | Guia 4.2 | |
| es.3.03 | **Huecos** — Concepto y utilidad del hueco como cuasipartícula. | es.3.02 | Guia 4.4 | |
| es.3.04 | **Movimiento semiclásico en campo magnético** — Órbitas en el espacio k, superficies de Fermi. | es.3.02, em.6.05 (0.5) | Guia 4.5 | |

## Semiconductores (se imparte en Electrónica)

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.4.01 | **Dopado y niveles de impurezas** — Impurezas donadoras/aceptadoras y sus niveles (contenido impartido en Electrónica). | es.3.03 | Guia 5.1-5.2 (→ Electrónica) | |
| es.4.02 | **Portadores y nivel de Fermi en semiconductores** — Densidad de estados, concentraciones intrínsecas/extrínsecas (contenido impartido en Electrónica). | es.4.01 | Guia 5.3-5.4 (→ Electrónica) | |

## Propiedades de transporte

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.5.01 | **Ecuación de Boltzmann** — Teoría semiclásica del transporte, aproximación de tiempo de relajación. | es.3.02, fe.02 (0.5) | Guia 6.1 | |
| es.5.02 | **Conductividad eléctrica de metales** — Conductividad a partir de Boltzmann, comparación con Drude. | es.5.01 | Guia 6.2 | |
| es.5.03 | **Conductividad térmica: Wiedemann-Franz** — Transporte de calor electrónico, ley de Wiedemann-Franz. | es.5.02 | Guia 6.3 | |
| es.5.04 | **Efectos termoeléctricos** — Seebeck, Peltier, Thomson. | es.5.03 | Guia 6.4 | |
| es.5.05 | **Efecto Hall** — Efectos termomagnetoeléctricos, medida de portadores. | es.5.02, es.3.04 | Guia 6.5 | |

## Fonones y propiedades térmicas

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.6.01 | **Límites del modelo de red estática** — Fallos en equilibrio, transporte e interacción radiación-materia que motivan la dinámica de red. | es.5.02 | Guia 7 | |
| es.6.02 | **Aproximación armónica** — Teoría clásica de la dinámica de redes. | es.6.01, mo.02 | Guia 8.2 | |
| es.6.03 | **Cadenas monoatómica y diatómica** — Vibraciones en modelos unidimensionales, relaciones de dispersión. | es.6.02 | Guia 8.3 | |
| es.6.04 | **Modos acústicos y ópticos en 3D** — Ramas de vibración en redes tridimensionales. | es.6.03 | Guia 8.4 | |
| es.6.05 | **Espectro de la red y densidad de estados** — Densidad de modos vibracionales. | es.6.04 | Guia 8.5 | |
| es.6.06 | **Propiedades ópticas IR de cristales iónicos** — Acoplamiento fotón-fonón óptico, reflectividad infrarroja. | es.6.04, em.10.08 (0.5) | Guia 8.6 | |
| es.6.07 | **El fonón** — Cuantización de la cadena monoatómica, el fonón como cuasipartícula. | es.6.03, mc.3.02 | Guia 8.7 | |
| es.6.08 | **Medida de relaciones de dispersión** — Dispersión inelástica de neutrones y otras técnicas. | es.6.07 | Guia 8.8 | |
| es.6.09 | **Calor específico reticular: Einstein y Debye** — Modelos aproximados del calor específico de la red. | es.6.05, es.6.07, fe.05 | Guia 9.1-9.2 | |
| es.6.10 | **Fusión: criterio de Lindemann** — Amplitudes vibracionales y fusión de sólidos. | es.6.09 | Guia 9.3 | |
| es.6.11 | **Anarmonicidad: dilatación térmica** — Parámetro de Grüneisen, dilatación. | es.6.09 | Guia 9.4 | |
| es.6.12 | **Interacción fonón-fonón y conductividad térmica** — Procesos normales y umklapp, conductividad de aislantes. | es.6.11 | Guia 9.5-9.6 | |

## Fenómenos cooperativos

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.7.01 | **Dia- y paramagnetismo en sólidos** — Respuesta magnética de electrones localizados e itinerantes. | es.2.01, em.9.04 | Guia 10.1 | |
| es.7.02 | **Orden magnético: ferro, antiferro y ferri** — Descripción clásica de los fenómenos cooperativos, materiales magnéticos. | es.7.01 | Guia 10.2 | |
| es.7.03 | **Superconductividad: fenomenología** — Temperatura crítica, corrientes persistentes, efecto Meissner, calor específico, efecto isotópico. | es.5.02 | Guia 10.3 | |
| es.7.04 | **Teoría de London y par de Cooper** — Ecuaciones de London, longitud de penetración, noción del par de Cooper, nuevos materiales. | es.7.03, em.9.06 (0.5) | Guia 10.3 | |

## Sistemas de baja dimensión

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| es.8.01 | **Cristales y electrones en dos dimensiones** — Estructuras 2D, propiedades electrónicas en baja dimensión. | es.2.07 | Guia 11.1-11.2 | |
| es.8.02 | **Efecto Hall cuántico** — Cuantización de la conductancia Hall en 2D. | es.8.01, es.5.05 | Guia 11.2 | |
| es.8.03 | **Magnetismo en una dimensión** — Cadenas de espines y orden magnético en 1D. | es.8.01, es.7.02 | Guia 11.3 | |

## Estadísticas

- Nodos raíz (sin prerrequisitos): —
- Nodos sin dependientes en todo el sistema: es.1.04, es.4.02, es.5.04, es.6.06, es.6.08, es.6.10, es.6.12, es.7.04, es.8.02, es.8.03
- Aristas: 58 (13 hacia otras asignaturas)
