# Physics Learning & Context Engine ⚛️🧠
### Motor de Contexto, Grafos de Conocimiento (DAGs) y Tutoría con IA para Grado en Física

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: Pytest](https://img.shields.io/badge/tests-94%20passed-brightgreen.svg)](tests/)
[![Architecture: Precision RAG](https://img.shields.io/badge/architecture-Graph--Guided%20Context%20Engine-orange.svg)](#arquitectura-del-sistema)

---

## 💡 El Cambio de Paradigma: De App Web Monolítica a Motor de Contexto para LLMs

Inicialmente concebido como una aplicación web local de estudio, la práctica real reveló un problema fundamental en la interacción entre estudiantes y Modelos de Lenguaje (LLMs):

1. **La trampa de la memoria paramétrica y la alucinación:** En física teórica avanzada (Mecánica Cuántica, Electrodinámica Clásica, Física del Estado Sólido), los modelos generalistas tienden a confundir convenios de signos, mezclar aproximaciones o inventar pasos matemáticos si dependen exclusivamente de sus pesos internos.
2. **El desbordamiento y degradación del contexto (*Token Bloat*):** Inyectar PDFs de 200 páginas o transcripciones masivas en el prompt satura la ventana de atención (*lost in the middle*), degrada la capacidad de deducción lógica del modelo y eleva los tiempos de respuesta.

**La solución:** El sistema evolucionó hacia un **Motor de Conocimiento y Contexto de Alta Precisión (Graph-Guided Precision RAG)**. Actúa como una base de datos conceptual determinista y headless que alimenta directamente al asistente de IA (Antigravity, ChatGPT mobile, Claude, etc.) con **micro-cargas de contexto ultra-acotadas (~200–400 tokens)**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ASISTENTE DE IA (CHAT / MÓVIL / VOZ)                  │
│       Interacción Socrática, Evaluación Estricta, Resolución Guiada        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                    Consulta precisa   │ Inyección de micro-contexto
                    del nodo en estudio│ (nodo + prerrequisitos + fuentes)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 KNOWLEDGE & CONTEXT ENGINE (MOTOR LOCAL PYTHON)             │
│                                                                             │
│  ├── Grafos Curriculares (DAG): 20+ asignaturas, dependencias formales     │
│  ├── Taxonomía de Bloom & Nodos Atómicos (1 sesión = 1 nodo)                │
│  ├── Algoritmo de Frontera de Conocimiento (Dominio vs Fluidez)             │
│  ├── Banco de Cuestiones Teóricas Rápidas (Modo Paseo / Oral)               │
│  ├── Generative UI: Síntesis autónoma de simulaciones interactivas (HTML5)  │
│  └── Pipeline Automático de Compilación Tipográfica (LaTeX -> PDF)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Capacidades Principales

### 1. Grafos de Conocimiento Dirigidos (DAGs)
- **Modelado Curricular Completo:** Más de 20 asignaturas del Grado en Física estructuradas como grafos dirigidos acíclicos con dependencias explícitas y pesos de prerrequisitos.
- **Granularidad Fina:** Cada nodo representa una unidad de aprendizaje atómica abordable en una única sesión de trabajo riguroso.
- **Frontera de Aprendizaje Dinámica:** Identifica automáticamente los conceptos listos para ser asimilados, garantizando que el estudiante nunca afronte un concepto sin tener asentada su base matemática previa.

### 2. Recuperación de Contexto sin Saturación (*Precision RAG*)
- En lugar de búsquedas vectoriales aproximadas que recuperan fragmentos redundantes, el motor realiza **recuperación determinista basada en el grafo**.
- Suministra al tutor de IA exactamente:
  - El identificador y alcance del nodo.
  - La condición de repaso o nuevo aprendizaje.
  - La lista exhaustiva de prerrequisitos directos.
  - El marco bibliográfico de referencia.
  - El límite de validez física y las hipótesis de partida.

### 3. Protocolo Pedagógico Estricto (Meta: Excelencia Académica)
- **Criterio de Dominio 100% Autónomo:** Un problema o deducción solo computa como superado si el alumno lo completa de principio a fin sin pistas. Si la IA interviene, se marca como *brecha de aprendizaje* a programar para revisión espaciada.
- **Anti-Spoiler Pedagógico:** En la explicación teórica previa, la IA tiene estrictamente prohibido utilizar la misma geometría o truco matemático del problema que se planteará a continuación. El estudiante debe deducir la aplicación por sí mismo.
- **Estilo Conciso (Inspirado en ASD-STE100):** Explicaciones directas, técnicas y rigurosas, eliminando rodeos conversacionales innecesarios.

### 4. Modo Conversacional y Estudio Móvil (*Modo Paseo*)
- **Entrada y Salida por Voz:** Integración con `faster-whisper` local para dictado de razonamientos y transcripción de baja latencia.
- **Batería de Flash-Questions Conceptuales:** Preguntas orales atómicas diseñadas para razonar de viva voz sin necesidad de papel ni soporte gráfico (ej. argumentar el teorema de Bloch, justificar el signo del coeficiente Hall o relacionar dispersión fonónica con calor específico).

### 5. Generative UI: Simulaciones Visuales Autónomas
- Cuando un concepto físico involucra geometría tridimensional o dinámicas complejas (precesión de espín en la **Esfera de Bloch**, apertura de gaps en **Zonas de Brillouin**, estados coherentes o transporte en junturas semiconductoras), la IA sintetiza **widgets HTML5/Canvas interactivos** que se incrustan en vivo en el chat.

### 6. Pipeline Tipográfico Automatizado en LaTeX / PDF
- Al concluir una sesión de estudio (`"cerramos sesión"`), el sistema compila los conceptos asimilados, demostraciones y recursos visuales directamente a **apuntes académicos en LaTeX** (`main.tex` → `main.pdf` mediante MiKTeX / `pdflatex`), manteniendo un archivo limpio y profesional.

---

## 🛠️ Tecnologías y Herramientas

| Componente | Tecnología | Propósito |
|---|---|---|
| **Motor Central** | Python 3.11+, Pydantic, Dataclasses | Gestión de grafos, cálculo de rutas y exportación de contexto. |
| **Modelado de Grafos** | Grafos Dirigidos (JSON), NetworkX-like | Validación de dependencias y detección de ciclos en el plan de estudios. |
| **Servicios Web & API** | Flask, AnyIO | Servidor local headless y endpoints de consulta de estado. |
| **Reconocimiento de Voz** | `faster-whisper` (CTranslate2) | Transcripción local privada y de alto rendimiento. |
| **Tipografía Académica** | LaTeX (`pdflatex`, MiKTeX, TeX Live) | Generación automática de documentos y apuntes curriculares. |
| **Visualización Interactiva**| HTML5, Canvas, Three.js, Tailwind CSS | Widgets generados proceduralmente por el agente para física visual. |
| **Pruebas Automatizadas** | Pytest (94 tests unitarios/integración) | Garantía de integridad de grafos, codificación y lógica de sesión. |

---

## 📁 Estructura del Proyecto

```text
├── knowledge_graph/               # Grafos curriculares en JSON y herramientas
│   ├── mecanica_cuantica.json     # Grafo atómico de Mecánica Cuántica
│   ├── estado_solido.json         # Grafo atómico de Física del Estado Sólido
│   ├── electrodinamica.json       # Grafo de Electrodinámica Clásica
│   ├── electromagnetismo.json     # Grafo de Electromagnetismo
│   ├── banco_problemas.example.json # Esquema de problemas de muestra
│   ├── errores_tipicos.json       # Catálogo de errores conceptuales frecuentes
│   └── validar_grafo.py           # Validador de consistencia y aciclicidad
├── study_context.py               # Generador de micro-contextos de alta precisión para LLMs
├── study_output_guidance.py       # Directrices pedagógicas y de formato estricto
├── apuntes.py                     # Compilador automatizado de apuntes a LaTeX/PDF
├── study_sessions.py              # Gestión y registro del ciclo de vida de sesiones
├── repeticion.py                  # Algoritmo de recuperación espaciada (SM-2 adaptado)
├── file_manager.py                # Gestor de archivos y sincronización
├── app.py                         # API local y servidor web
├── templates/ & static/           # Visores de grafos y panel de control
└── tests/                         # Suite de 94 pruebas unitarias con Pytest
```

---

## 🚀 Puesta en Marcha

### Requisitos Previos
- Python 3.11 o superior.
- Git.
- *(Opcional para compilación de PDFs)* Distribución de LaTeX instalada en el sistema (MiKTeX en Windows o TeX Live en Linux/macOS).

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/jlgmaarav/Sistema_de_estudio.git
cd Sistema_de_estudio

# 2. Crear y activar el entorno virtual
python -m venv .venv

# En Windows:
.venv\Scripts\activate
# En Linux / macOS:
source .venv/bin/activate

# 3. Instalar dependencias
python -m pip install -r requirements.txt

# 4. Ejecutar la suite de pruebas
python -m pytest
```

---

## 🔒 Privacidad y Ética Académica

Este repositorio de código abierto constituye un **proyecto de ingeniería de software educativo y portfolio profesional**:
- **Sin datos privados:** No contiene expedientes de alumnos, métricas de progreso personal ni calificaciones privadas (gestionadas en entornos locales cifrados o repositorios privados).
- **Propiedad intelectual respetada:** No incluye enunciados ni soluciones de exámenes propiedad del profesorado universitario, ni manuales con derechos de autor. Los ejemplos proporcionados son esquemas sintéticos de dominio público.

---

## 💼 Resumen para Currículum / Portfolio

> **Motor de Conocimiento y Contexto para LLMs (EdTech & AI Engineering — Grado en Física)**  
> Arquitectura completa de un sistema de tutoría personalizada asistido por IA basado en grafos de conocimiento dirigidos (DAGs) y recuperación de contexto de alta precisión (*Precision RAG*). Modela más de 20 asignaturas en unidades atómicas para eliminar alucinaciones y prevenir la saturación de contexto en LLMs. Incluye protocolo socrático estricto, generación autónoma de simulaciones visuales interactivas (Generative UI en HTML5/Canvas), transcripción de voz local (`faster-whisper`) y compilación automática de apuntes en LaTeX/PDF.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.
