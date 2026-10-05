# Sistema de Estudio Asistido por IA (Physics Learning Engine)

Aplicación y motor de aprendizaje adaptativo diseñado para optimizar el estudio intensivo en el **Grado en Física**. Combina grafos de conocimiento dirigidos (DAGs), algoritmos de recuperación espaciada, tutoría pedagógica contextualizada con modelos de lenguaje (LLMs), generación automatizada de apuntes en LaTeX/PDF y simulaciones interactivas.

---

## 🚀 Arquitectura del Sistema

El sistema opera bajo una **arquitectura desacoplada en dos capas**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA 1: PROTOCOLO DE TUTORÍA Y AGENTES              │
│  - Detección de entorno (Paseo / Biblioteca / Casa)                    │
│  - Criterio de dominio estricto 10/10 (Anti-Spoiler Pedagógico)        │
│  - Inyección de contexto estructurado (TUTOR_WORK.md / docs/)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    CAPA 2: MOTOR LOCAL (PYTHON / FLASK)                │
│  - Grafos de Conocimiento (Álgebra, Electromagnetismo, Cuántica...)   │
│  - Algoritmo de Frontera de Conocimiento y Repetición Espaciada       │
│  - Compilador de Apuntes Vivos (LaTeX -> PDF automático)               │
│  - Servicios Locales de Voz (Faster-Whisper STT)                       │
│  - Respaldo Distribuido Dual (Portfolio Público vs Datos Privados)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Características Principales

### 1. Grafos de Conocimiento Curriculares (Knowledge Graphs)
- Cada asignatura se modela como un grafo dirigido acíclico (DAG) de conceptos con dependencias y prerrequisitos explícitos.
- Cálculo automático de la **frontera de aprendizaje**: identifica los nodos óptimos para estudiar hoy sin lagunas previas.
- Seguimiento diferenciado de **comprensión conceptual**, **fluidez operativa** y registro recurrente de **errores típicos**.

### 2. Entornos de Estudio Adaptativos
El tutor ajusta su metodología y formato de respuesta según la situación del estudiante:
- **🚶 Paseo (Modo Audio / Diálogo):** Enfocado 100% en debate conceptual de alto nivel, preguntas socráticas y analogías físicas (método Feynman), optimizado para entrada y salida por voz.
- **📚 Biblioteca (Modo Texto Breve / Silencioso):** Interacción puramente escrita con máxima concisión. El tutor evalúa respuestas esquemáticas manteniendo el rigor analítico.
- **🏠 Casa (Modo Análisis Profundo):** Explicación y resolución exhaustiva de problemas, deducciones matemáticas paso a paso y demostraciones completas.

### 3. Criterio de Dominio Estricto (Objetivo: Matrícula de Honor)
- **Cero pistas regaladas:** Un problema solo se computa como *dominado* si el estudiante lo resuelve de manera 100% autónoma.
- Si la IA proporciona pistas intermedias o desatasca el ejercicio, el concepto se registra como **brecha a reforzar** para futuras sesiones.
- **Anti-Spoiler Pedagógico:** En las explicaciones teóricas previas, el sistema tiene prohibido utilizar la misma geometría o truco matemático del problema que se planteará a continuación.

### 4. Apuntes Personales Vivos en LaTeX y PDF (`apuntes.py`)
- Al finalizar cada sesión (`"cerramos sesión"`), el sistema recopila los conceptos trabajados, justificaciones teóricas, dudas resueltas y errores corregidos.
- Genera automáticamente un documento formal en LaTeX (`main.tex`) y lo compila a **PDF** mediante integración con MiKTeX/TeX Live.
- Redacción precisa con estilo técnico inspirado en especificaciones aeronáuticas (ASD-STE100) para máxima claridad y cero relleno superfluo.

### 5. Recursos Visuales e Interactivos
- Soporte para generar simulaciones web autónomas (HTML5/JS con Canvas o Plotly) en tiempo real.
- Permite al estudiante manipular parámetros físicos mediante controles deslizantes (ej. barreras de potencial cuántico, curvas $I$-$V$ de MOSFETs o reflexión de ondas electromagnéticas).

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3.11+, Flask, AnyIO.
- **Frontend:** HTML5, CSS3 moderno, JavaScript (ES6+), KaTeX para renderizado matemático.
- **Procesamiento de Voz:** `faster-whisper` para transcripción local de audio de baja latencia.
- **Tipografía y Documentos:** LaTeX (`pdflatex`, MiKTeX, TeX Live) con compilación desatendida.
- **Estructura de Datos:** Grafos en JSON, esquemas Pydantic / dataclasses para validación estricta de reportes.
- **Control de Versiones y Sincronización:** Git, GitHub API, scripts de respaldo asíncrono.

---

## 📁 Estructura del Repositorio

| Ruta | Descripción |
| --- | --- |
| `app.py` | Servidor web Flask y endpoints del centro de estudio. |
| `study_context.py` | Motor de construcción y exportación de contexto para LLMs. |
| `study_sessions.py` | Gestión del ciclo de vida de sesiones y persistencia. |
| `study_output_guidance.py` | Esquemas y directrices pedagógicas estructuradas. |
| `apuntes.py` | Motor de generación y compilación de apuntes en LaTeX (`.tex` y `.pdf`). |
| `TUTOR_WORK.md` | Protocolo de tutoría personalizada y reglas pedagógicas activas. |
| `docs/protocolo_de_tutoria.md` | Especificación del protocolo de interacción con la IA. |
| `knowledge_graph/` | Definiciones JSON de los grafos curriculares por materia y visores interactivos. |
| `templates/`, `static/` | Interfaz web de usuario y visores de grafos. |
| `tests/` | Suite completa de pruebas unitarias y de integración (`pytest`). |

---

## 🔒 Privacidad y Política de Datos

Este repositorio público contiene exclusivamente el **código fuente**, la **arquitectura del sistema**, los **grafos curriculares generales** y **datos de ejemplo**.

- Los expedientes y métricas de progreso personal (`perfil.json`), los enunciados de exámenes universitarios sujetos a derechos docentes y las grabaciones de audio se gestionan en un **repositorio privado independiente** o almacenamiento seguro cifrado.
- Se implementan reglas estrictas de `.gitignore` para garantizar el cumplimiento normativo y la propiedad intelectual.

---

## 💼 Resumen para Currículum / Portfolio

> **Sistema de Estudio y Aprendizaje Acelerado con IA (Proyecto Personal — Física UVa)**  
> Diseño e implementación completa de una plataforma local de tutoría y seguimiento pedagógico basada en Python/Flask y JavaScript. Implementé modelado del plan de estudios como Grafos de Conocimiento Dirigidos (DAGs) para cálculo de frontera de aprendizaje y recuperación espaciada. Diseñé un protocolo de tutoría adaptativa multi-entorno para LLMs con detección de brechas conceptuales, compilación automatizada de apuntes en LaTeX/PDF tras cada sesión y transcripción local de voz con Whisper.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [`LICENSE`](LICENSE) para más información.
