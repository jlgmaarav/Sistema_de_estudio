# Revisión del grafo — Electrónica

Total: **32 nodos**. Para cada nodo revisa: ¿se dio en clase?, ¿la granularidad es correcta (1 sesión)?, ¿faltan o sobran prerrequisitos?

Marca en la columna final: `ok` / `quitar` / `dividir` / comentario libre.
Los prerrequisitos de otra asignatura aparecen con su id completo (ej. `em.4.01`).

## Tema 1: Propiedades electrónicas de los materiales semiconductores

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| el.1.01 | **Materiales semiconductores** — Semiconductores vs conductores/aislantes; intrínsecos vs extrínsecos; elementos y compuestos. | — | Apuntes 1.1 | |
| el.1.02 | **Modelo de bandas y portadores** — Estructura cristalina, banda de valencia/conducción, gap; electrones y huecos como portadores. (Apoya en bandas de FES.) | el.1.01, es.2.07 (0.5) | Apuntes 1.2.1, 1.2.2 | |
| el.1.03 | **Concentración intrínseca de portadores** — n_i, dependencia con temperatura y gap. | el.1.02 | Apuntes 1.2.3 | |
| el.1.04 | **Dopado: semiconductores tipo N y tipo P** — Impurezas donadoras y aceptadoras, niveles en el gap, centros profundos. | el.1.02 | Apuntes 1.3, 1.4.1 | |
| el.1.05 | **Estadística de Fermi-Dirac y nivel de Fermi** — Concentraciones de equilibrio, producto np = n_i², cálculo del nivel de Fermi con dopado. | el.1.03, el.1.04 | Apuntes 1.4.2, 1.5 | |
| el.1.06 | **Transporte por arrastre: movilidad y conducción** — Masa efectiva, movilidad, densidad de corriente de conducción J_C. | el.1.02, em.5.01 (0.5), em.5.03 (0.5) | Apuntes 1.6.1 a 1.6.3 | |
| el.1.07 | **Difusión de portadores** — Corriente de difusión, relación de Einstein. | el.1.06 | Apuntes 1.6.4 | |
| el.1.08 | **Generación, recombinación y cuasi-niveles de Fermi** — Semiconductor fuera del equilibrio, tiempos de vida, cuasi-niveles de Fermi. | el.1.05 | Apuntes 1.7, 1.8 | |
| el.1.09 | **Ecuaciones fundamentales de los dispositivos** — Ecuación de continuidad para portadores y ecuación de Poisson aplicadas a semiconductores. | el.1.06, el.1.07, el.1.08, em.5.02, em.4.01 | Apuntes 1.9 | |

## Tema 2: El diodo de unión PN

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| el.2.01 | **La unión PN en equilibrio: la ZCE** — Formación de la zona de carga espacial; distribución de carga, campo y potencial electrostático. | el.1.09, em.1.09 (0.5) | Apuntes 2.1 | |
| el.2.02 | **Diagrama de bandas de la unión PN** — Nivel de Fermi constante en equilibrio, curvatura de bandas, potencial de difusión. | el.2.01, el.1.05 | Apuntes 2.2 | |
| el.2.03 | **Campo eléctrico y anchura de la ZCE** — Resolución de Poisson en la unión abrupta; E_max y anchura en función del dopado y la tensión. | el.2.01 | Apuntes 2.3 | |
| el.2.04 | **Polarización directa: bandas y flujo de portadores** — Reducción de la barrera, inyección de minoritarios, cuasi-niveles de Fermi en la unión. | el.2.02, el.1.08 | Apuntes 2.4.1 a 2.4.4 | |
| el.2.05 | **Polarización directa: concentraciones y corriente** — Perfil de minoritarios inyectados, cálculo de la corriente directa, diagrama de corrientes. | el.2.04, el.1.07 | Apuntes 2.4.5 a 2.4.8 | |
| el.2.06 | **Polarización inversa** — Aumento de barrera y ZCE, extracción de minoritarios, corriente de saturación inversa. | el.2.04, el.2.03 | Apuntes 2.5 | |
| el.2.07 | **Característica I-V y ruptura de la unión** — Ecuación del diodo, desviaciones reales, ruptura Zener y por avalancha. | el.2.05, el.2.06 | Apuntes 2.6 | |

## Tema 3: Aplicaciones de la unión PN

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| el.3.01 | **El diodo como componente de circuito** — Rectificación, recorte, modelos del diodo en circuitos. | el.2.07 | Apuntes 3.1 | |
| el.3.02 | **Diodos especiales: varactor, túnel, PIN, IMPATT** — Principio físico y aplicación de cada variante de la unión PN. | el.2.07, em.2.05 (0.5) | Apuntes 3.2 | |
| el.3.03 | **Optoelectrónica: LED, láser y fotodetectores** — Emisión y absorción en la unión PN, materiales de gap directo. | el.2.07 | Apuntes 3.3 | |

## Tema 4: El transistor bipolar de unión (BJT)

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| el.4.01 | **El transistor NPN en activa: bandas y minoritarios** — Dos uniones acopladas, diagrama de bandas en activa, perfil de minoritarios en la base. | el.2.04, el.1.08 | Apuntes 4.1 | |
| el.4.02 | **Configuraciones y ganancias del BJT** — Base/emisor/colector común; eficacia de emisor γ, factor de transporte B, multiplicación M; α y β. | el.4.01 | Apuntes 4.2, 4.3 | |
| el.4.03 | **Diagrama y ecuaciones de corrientes del BJT** — Relaciones entre corrientes en activa, ecuaciones fundamentales del transistor. | el.4.02 | Apuntes 4.4 | |
| el.4.04 | **Características estáticas y efecto Early** — Curvas en base común y emisor común, modulación de la anchura de base. | el.4.03 | Apuntes 4.5 | |
| el.4.05 | **Regímenes de funcionamiento del BJT** — Activa directa/inversa, saturación, corte; lectura de las características estáticas. | el.4.03 | Apuntes 4.6 | |
| el.4.06 | **Modelos del BJT: Ebers-Moll y Giacoletto** — Modelo de gran señal y modelo de pequeña señal del transistor bipolar. | el.4.05 | Apuntes 4.7 | |
| el.4.07 | **El transistor bipolar real** — Estructura tecnológica y efectos de segundo orden. | el.4.05, el.4.06 (0.5) | Apuntes 4.8 | |

## Tema 5: La estructura MIS y el transistor MOSFET

| Id | Nodo | Prerrequisitos (peso) | Fuentes | Revisión |
|---|---|---|---|---|
| el.5.01 | **La estructura MIS ideal** — Metal-aislante-semiconductor: componentes, materiales, diagrama de bandas en equilibrio. | el.1.05, el.2.02 (0.5) | Apuntes 5.1 | |
| el.5.02 | **Regímenes de la estructura MIS** — Acumulación, vaciamiento e inversión según la polarización de puerta. | el.5.01 | Apuntes 5.2 | |
| el.5.03 | **Característica capacidad-tensión de la MIS** — Comportamiento capacitivo en cada régimen, curvas C-V para tipo P y N. | el.5.02, em.2.05 (0.5) | Apuntes 5.3 | |
| el.5.04 | **La estructura MIS real** — Cargas en el óxido, diferencia de funciones de trabajo, tensión de banda plana. | el.5.03 | Apuntes 5.4 | |
| el.5.05 | **El transistor MOSFET** — Formación del canal, tensión umbral, regímenes óhmico y saturación, corriente de canal. | el.5.02, el.1.06 | Apuntes 5.5 | |
| el.5.06 | **Tipos de MOSFET y tecnología CMOS** — Acumulación vs vaciamiento, canal N vs P, símbolos, inversor CMOS. | el.5.05 | Apuntes 5.6 | |

## Estadísticas

- Nodos raíz (sin prerrequisitos): el.1.01
- Nodos sin dependientes en todo el sistema: el.3.01, el.3.02, el.3.03, el.4.04, el.4.07, el.5.04, el.5.06
- Aristas: 51 (8 hacia otras asignaturas)
