# Verificación del método Math Academy (los 7 principios)

Estado a 2026-07-09. Cada principio, dónde está implementado y qué queda.

## 1. Identificar lo que el estudiante ya sabe — 🟡 PARCIAL

- `perfil.py marcar-cursadas` inicializa las 19 asignaturas aprobadas (90 nodos) a dominio 0.75.
- **Limitación**: es un 0.75 plano, no un diagnóstico real. **Refinamiento previsto**: el quiz cronometrado corrige esto con evidencia real en cuanto haya bancos de problemas de las cursadas (cada fallo baja el nodo y lo devuelve a la frontera); y a mano, `perfil.py registrar <id> [--fallo]` o los botones ✓/✗ de la app.

## 2. Superponer sobre el grafo → perfil personal — ✅

- 28 grafos, 451 nodos, 725 aristas de prerrequisito con pesos (1.0 duro/encompassing, 0.5 blando).
- `perfil.json`: dominio, repeticiones, intervalo, próxima revisión e historial por nodo.
- Visualización: mapa con relleno proporcional al dominio, hueco = sin practicar.

## 3. Enseñar solo en la frontera de conocimiento — ✅

- `perfil.frontera()`: nodos no dominados cuyos prerrequisitos **duros** tienen dominio efectivo ≥ 0.7.
- El planificador (`planificar.py`) solo prescribe lecciones nuevas de la frontera. No hay forma de que el plan te ponga un tema sin base.

## 4. Lección = dosis mínima de instrucción guiada + práctica activa — ✅

- Botón "📖 Lección" en cada nodo del plan: lección mínima generada por IA y cacheada (`lecciones.py`): idea central + explicación 300-500 palabras asumiendo los prerrequisitos dominados + UN ejemplo resuelto + 3 reglas de oro (esto último cubre el gap de "enseñar el pensamiento crítico explícitamente" detectado en ARQUITECTURA).
- Práctica activa inmediata: 3 problemas reales de las hojas de los profesores por nodo (banco de 229, rotan a diario).

## 5. Mastery obligatorio + caminos paralelos — ✅

- Un solo éxito NO domina un nodo: dominio 0→0.35→0.58→0.72 (hacen falta ~3 éxitos para cruzar el umbral 0.7). Un fallo multiplica por 0.55 y programa repaso inmediato: los dependientes se bloquean solos.
- El olvido también bloquea: el dominio efectivo decae exponencialmente pasada la fecha de revisión, y puede sacar un prerrequisito de la zona dominada → sus dependientes salen de la frontera hasta repasarlo.
- Caminos paralelos: la frontera es multi-asignatura y multi-rama; si una rama se bloquea, el plan sigue por las demás y vuelve cuando toque.

## 6. Repetición espaciada + quizzes frecuentes cronometrados a libro cerrado — ✅

- SR por nodo: intervalos expansivos [1,3,7,14,30,60,120,240] días, fallo → reinicio a 1 día.
- Quiz cronometrado (pestaña Autoevaluador): cobertura amplia sobre lo aprendido, interleaving (máx. 2 problemas por materia-tema), prioriza nodos "fríos", temporizador, autocalificación → actualiza el perfil.
- **Unificado**: los tres canales de práctica (Inbox/watcher, botones ✓/✗ del plan, autoevaluación de flashcards) alimentan TODOS el mismo perfil. La ficha de ejercicio guarda ahora sus `nodos:` del grafo.

## 7. Repasar lo viejo aprendiendo lo nuevo — ✅

- Crédito implícito: cada éxito propaga crédito = producto de pesos × 0.6^profundidad a todos los ancestros (sube su dominio y pospone su revisión).
- El planificador prioriza los nodos nuevos que cubren más repasos vencidos, y marca esos repasos como "cubiertos implícitamente" en el plan del día.

---

## Compresión temporal (la promesa del método)

`planificar.py` planifica hacia atrás desde `examenes.json`: carga restante ÷ días = ritmo requerido, con semáforo HOLGADO/AJUSTADO/INSUFICIENTE y simulación de fechas de inicio (`--fecha`). Editable desde la app (pestaña Plan de Estudio).

## Pendiente conocido

1. Fechas reales de exámenes (placeholders en `examenes.json` — editar desde la app).
2. Bancos de problemas del resto de asignaturas (la app ya acepta subir MDs).
3. Diagnóstico fino de cursadas (mejorará solo con el uso del quiz; opcional: sesión dedicada).
4. Deuda menor: `app_biblioteca.py` como app separada; SR viejo por-ejercicio convive (inofensivo, ya sincronizado con el perfil).
