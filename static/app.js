// Active view state
let currentTab = 'dashboard';
let errorChartInstance = null;
let currentSubjectData = null;
let activeTopicFilter = null;
let currentExerciseDetail = null;

let quizExercises = [];
let quizCurrentIndex = 0;
let voiceRecorder = null;
let voiceStream = null;
let voiceChunks = [];
let voiceTimerInterval = null;
let voiceStartedAt = null;
let voiceJobPoll = null;
let waitingGeminiJobId = null;
let studyRailStage = 'relevance';
let workSessionId = null;
let workSessionStatusPoll = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchDashboardData();
    fetchSubjectsData();
    fetchHubStatus();
    fetchCuadernosConfig();
    loadStudySubjectCards();
    loadActiveWorkSession();
});

// =====================================================================
// CENTRO DE ESTUDIO: acciones rápidas y flujo unificado
// =====================================================================
function loadStudySubjectCards() {
    const container = document.getElementById('study-subjects-grid');
    if (!container) return Promise.resolve();
    container.innerHTML = '<div class="loading-spinner">Leyendo el estado de tus asignaturas…</div>';
    return fetch('/api/study/subjects')
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            const subjects = data.subjects || [];
            if (!subjects.length) {
                container.innerHTML = '<div class="no-tasks">Todavía no hay asignaturas activas en el sistema.</div>';
                return;
            }
            container.innerHTML = subjects.map(subject => {
                const materiaJson = JSON.stringify(subject.materia).replace(/'/g, '\\u0027');
                const progress = Math.max(0, Math.min(100, Number(subject.dominio_porcentaje || 0)));
                const examDate = subject.examen?.fecha || subject.examen?.fecha_examen || '';
                return `
                    <article style="background:#11141d; border:1px solid #2d3748; border-radius:10px; padding:14px; display:flex; flex-direction:column; gap:10px; min-height:190px;">
                        <div style="display:flex; justify-content:space-between; gap:8px; align-items:flex-start;">
                            <div>
                                <h3 style="margin:0 0 4px; color:#f3f4f6; font-size:16px;">${escapeSearchHtml(subject.materia)}</h3>
                                <span style="color:#93c5fd; font-size:12px;">${escapeSearchHtml(subject.estado || 'Lista para estudiar')}</span>
                            </div>
                            <span style="color:#60a5fa; font-weight:700; font-size:18px;">${progress}%</span>
                        </div>
                        <div style="height:6px; background:#1e293b; border-radius:99px; overflow:hidden;"><div style="height:100%; width:${progress}%; background:${progress < 60 ? '#f59e0b' : '#34d399'}; border-radius:99px;"></div></div>
                        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:6px; color:#9ca3af; font-size:11px;">
                            <span><strong style="display:block; color:#e2e8f0; font-size:14px;">${subject.repasos_pendientes ?? 0}</strong>repasos</span>
                            <span><strong style="display:block; color:#e2e8f0; font-size:14px;">${subject.nodos_debiles ?? 0}</strong>débiles</span>
                            <span><strong style="display:block; color:#e2e8f0; font-size:14px;">${subject.problemas ?? 0}</strong>problemas</span>
                        </div>
                        <div style="color:#6b7280; font-size:11px; line-height:1.35; min-height:30px;">${examDate ? `Examen configurado: ${escapeSearchHtml(examDate)}` : 'Sin examen configurado'}</div>
                        <div style="display:flex; gap:7px; margin-top:auto;">
                            <button class="btn btn-primary" onclick='startWorkStudySession(${materiaJson})' style="flex:1; padding:7px 9px; font-size:12px; display:inline-flex; justify-content:center; align-items:center; gap:5px;"><i data-lucide="play" style="width:14px;height:14px;"></i> Estudiar con Work</button>
                            <button class="btn" onclick='viewSubjectDetail(${materiaJson})' style="background:#374151; color:white; padding:7px 9px; font-size:12px;" title="Ver ficha de la asignatura"><i data-lucide="arrow-up-right" style="width:14px;height:14px;"></i></button>
                        </div>
                    </article>`;
            }).join('');
            lucide.createIcons();
        })
        .catch(error => {
            container.innerHTML = `<div class="no-tasks">No se pudieron cargar las asignaturas: ${escapeSearchHtml(error.message)}</div>`;
        });
}

function renderActiveWorkSession(status) {
    const target = document.getElementById('study-active-session');
    if (!target) return;
    if (!status?.active && !status?.report_ready) {
        target.innerHTML = '';
        return;
    }
    const session = status.session || {};
    const materia = status.materia || session.materia || 'asignatura';
    if (status.report_ready) {
        target.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; background:rgba(52,211,153,0.10); border:1px solid rgba(52,211,153,0.45); border-radius:8px; padding:10px 12px;"><span style="color:#a7f3d0; font-size:13px;">✓ Work ha dejado listo el cierre de <strong>${escapeSearchHtml(materia)}</strong>.</span><button class="btn btn-primary" onclick="openActiveWorkSession()" style="padding:6px 10px; font-size:12px;">Revisar e importar</button></div>`;
        return;
    }
    target.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; background:rgba(96,165,250,0.10); border:1px solid rgba(96,165,250,0.35); border-radius:8px; padding:10px 12px;"><span style="color:#bfdbfe; font-size:13px;">Sesión de <strong>${escapeSearchHtml(materia)}</strong> en marcha. El cierre se importa al dashboard cuando Work escriba el informe.</span><button class="btn" onclick="openActiveWorkSession()" style="background:#2563eb; color:white; padding:6px 10px; font-size:12px;">Ver sesión</button></div>`;
}

function loadActiveWorkSession() {
    return fetch('/api/study/work/status')
        .then(r => r.json())
        .then(status => {
            workSessionId = status.session?.id || null;
            renderActiveWorkSession(status);
            if (status.auto_imported) {
                const statusLabel = document.getElementById('work-session-status');
                if (statusLabel) statusLabel.textContent = '✓ Cierre importado automáticamente. Perfil, problemas y apuntes actualizados.';
                mostrarToast('✓ Cierre de Work importado automáticamente.');
            }
            if (status.active && !workSessionStatusPoll) {
                workSessionStatusPoll = setInterval(loadActiveWorkSession, 5000);
            }
            if (!status.active && workSessionStatusPoll) {
                clearInterval(workSessionStatusPoll);
                workSessionStatusPoll = null;
            }
            return status;
        })
        .catch(() => {});
}

function populateWorkSessionModal(pack, session) {
    workSessionId = session?.id || pack?.session?.id || null;
    const title = document.getElementById('work-session-title');
    const prompt = document.getElementById('work-session-prompt');
    const status = document.getElementById('work-session-status');
    const summary = document.getElementById('work-session-summary');
    if (title) title.textContent = `Sesión de ${pack?.session?.materia || session?.materia || 'estudio'}`;
    if (prompt) prompt.value = pack?.prompt || '';
    if (status) status.textContent = '✓ Contexto listo. En Work, escribe «empieza la sesión activa» y estudiad desde allí.';
    if (summary) {
        const state = pack?.state?.resumen_dominio || {};
        summary.innerHTML = `<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:8px;"><div style="background:#11141d;border:1px solid #2d3748;border-radius:7px;padding:9px;"><span style="display:block;color:#9ca3af;font-size:11px;">Dominio medio</span><strong style="color:#60a5fa;font-size:18px;">${Math.round((state.media || 0) * 100)}%</strong></div><div style="background:#11141d;border:1px solid #2d3748;border-radius:7px;padding:9px;"><span style="display:block;color:#9ca3af;font-size:11px;">Nodos de sesión</span><strong style="color:#e2e8f0;font-size:18px;">${pack?.plan_ids?.length || 0}</strong></div><div style="background:#11141d;border:1px solid #2d3748;border-radius:7px;padding:9px;"><span style="display:block;color:#9ca3af;font-size:11px;">Problemas del banco</span><strong style="color:#e2e8f0;font-size:18px;">${pack?.problem_ids?.length || 0}</strong></div></div>`;
    }
    document.getElementById('work-session-close-area').style.display = 'none';
    document.getElementById('work-session-modal').classList.add('active');
    lucide.createIcons();
}

function startWorkStudySession(materia) {
    const modal = document.getElementById('work-session-modal');
    const status = document.getElementById('work-session-status');
    if (modal) modal.classList.add('active');
    if (status) status.textContent = 'Preparando el contexto vivo de esta asignatura…';
    return fetch('/api/study/work/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({materia, available_minutes: 60, goal: 'aprender y consolidar'}),
    }).then(r => r.json().then(data => ({ok: r.ok, data}))).then(({ok, data}) => {
        if (!ok || data.error) throw new Error(data.error || 'No se pudo iniciar la sesión.');
        populateWorkSessionModal(data.pack, data.session);
        setHubPipeline('study');
        renderActiveWorkSession({active: true, session: data.session, materia});
        if (!workSessionStatusPoll) workSessionStatusPoll = setInterval(loadActiveWorkSession, 5000);
        return data;
    }).catch(error => {
        if (status) status.textContent = `No se pudo iniciar: ${error.message}`;
        else alert(`No se pudo iniciar la sesión: ${error.message}`);
    });
}

function openActiveWorkSession() {
    fetch('/api/study/work/context').then(r => r.json()).then(pack => {
        if (pack.error) throw new Error(pack.error);
        populateWorkSessionModal(pack, pack.session);
        if (pack.session?.id) workSessionId = pack.session.id;
        return checkWorkSessionReport();
    }).catch(error => mostrarToast(`No se pudo abrir la sesión: ${error.message}`));
}

function copyWorkSessionPrompt() {
    const prompt = document.getElementById('work-session-prompt')?.value || '';
    const status = document.getElementById('work-session-status');
    if (!prompt) { if (status) status.textContent = 'Todavía no hay ningún encargo preparado.'; return; }
    const copied = navigator.clipboard?.writeText ? navigator.clipboard.writeText(prompt) : Promise.reject(new Error('clipboard'));
    copied.then(() => {
        if (status) status.textContent = '✓ Encargo copiado. Pégalo en la conversación de Work.';
    }).catch(() => {
        const area = document.getElementById('work-session-prompt');
        area?.focus(); area?.select();
        if (status) status.textContent = 'Selecciona y copia el encargo manualmente.';
    });
}

function checkWorkSessionReport() {
    const status = document.getElementById('work-session-status');
    return fetch('/api/study/work/status').then(r => r.json()).then(current => {
        renderActiveWorkSession(current);
        if (current.auto_imported) {
            if (status) status.textContent = '✓ Cierre importado automáticamente. Perfil, problemas y apuntes actualizados.';
            return current;
        }
        if (current.auto_import_error) {
            if (status) status.textContent = `No se pudo importar automáticamente: ${current.auto_import_error}`;
            return current;
        }
        if (!current.report_ready) {
            if (status) status.textContent = 'Todavía no hay cierre. Cuando termines, pide a Work que escriba el informe en la carpeta del sistema.';
            return current;
        }
        return fetch('/api/study/work/report').then(r => r.json()).then(report => {
            document.getElementById('work-session-report').value = JSON.stringify(report, null, 2);
            document.getElementById('work-session-close-area').style.display = 'block';
            if (status) status.textContent = 'Cierre detectado. Revísalo antes de importarlo.';
            return report;
        });
    }).catch(error => {
        if (status) status.textContent = `No se pudo comprobar el cierre: ${error.message}`;
    });
}

function importWorkSessionReport() {
    const status = document.getElementById('work-session-status');
    const raw = document.getElementById('work-session-report')?.value.trim() || '';
    if (!raw) { if (status) status.textContent = 'Pega o espera primero el informe de cierre.'; return; }
    let report;
    try { report = JSON.parse(raw); } catch (error) { if (status) status.textContent = 'El cierre no es JSON válido.'; return; }
    if (status) status.textContent = 'Validando el cierre y actualizando el sistema…';
    return fetch('/api/study/work/finish', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: workSessionId || report.session_id, report}),
    }).then(r => r.json().then(data => ({ok: r.ok, data}))).then(({ok, data}) => {
        if (!ok || data.error) throw new Error(data.error || 'No se pudo importar el cierre.');
        if (status) status.textContent = '✓ Cierre importado. Perfil, problemas y apuntes actualizados.';
        workSessionId = null;
        if (workSessionStatusPoll) { clearInterval(workSessionStatusPoll); workSessionStatusPoll = null; }
        setHubPipeline('map');
        fetchDashboardData(); fetchHubStatus(); loadStudySubjectCards();
        renderActiveWorkSession({active: false, report_ready: false});
        return data;
    }).catch(error => {
        if (status) status.textContent = `No se pudo importar: ${error.message}`;
    });
}

function closeWorkSessionModal() {
    document.getElementById('work-session-modal')?.classList.remove('active');
}

function fetchHubStatus() {
    fetch('/api/hub')
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            const pendientes = data.correcciones_pendientes || 0;
            const inbox = data.inbox_pendientes || 0;
            const label = document.getElementById('hub-corrections-label');
            if (label) label.textContent = pendientes ? `${pendientes} ${pendientes === 1 ? 'corrección' : 'correcciones'} por revisar` : 'Revisar tus últimas correcciones';
            const next = document.getElementById('hub-next-step');
            if (next) {
                if (inbox) {
                    next.innerHTML = '<span class="hub-next-label">SIGUIENTE PASO</span><strong>Tienes material esperando</strong><span>La IA está preparando tu feedback. Puedes seguir con una sesión mientras tanto.</span>';
                } else if (pendientes) {
                    next.innerHTML = `<span class="hub-next-label">SIGUIENTE PASO</span><strong>Revisa tu feedback reciente</strong><span>Hay ${pendientes} ${pendientes === 1 ? 'corrección lista' : 'correcciones listas'} para convertir en aprendizaje.</span>`;
                } else {
                    next.innerHTML = '<span class="hub-next-label">TU ELECCIÓN</span><strong>Elige una asignatura</strong><span>La sesión continuará desde el historial disponible, sin prioridades automáticas.</span>';
                }
            }
            const trabajos = (data.trabajos_voz || []).filter(j => j.estado === 'procesando' || j.estado === 'en_cola');
            const background = document.getElementById('hub-background-status');
            if (background && trabajos.length) {
                background.innerHTML = `<i data-lucide="loader-circle" class="spin"></i> La IA está procesando ${trabajos.length} grabación${trabajos.length === 1 ? '' : 'es'} en segundo plano.`;
                lucide.createIcons();
            }
            if (data.estudio?.skill) renderRailHint(data.estudio.skill);
        })
        .catch(() => {});
}

function renderRailHint(skill) {
    const target = document.getElementById('session-rail-hint') || document.getElementById('hub-skill-insight');
    if (!target || !skill) return;
    studyRailStage = skill.stage || 'relevance';
    target.dataset.stage = skill.stage || 'relevance';
    const action = skill.acciones?.[0] || 'reflexionar';
    target.innerHTML = `<span class="rail-badge">RAIL · ${skill.nombre}</span><strong>Esta sesión entrena tu forma de estudiar</strong><span>${skill.descripcion} Próximo movimiento: <b>${action}</b>.</span>`;
}

function setHubPipeline(stage) {
    const order = ['study', 'capture', 'feedback', 'map'];
    order.forEach((name, index) => {
        const el = document.getElementById('hub-step-' + name);
        if (!el) return;
        el.classList.toggle('active', index <= order.indexOf(stage));
        el.classList.toggle('current', name === stage);
    });
    const labels = { study: 'Sesión en marcha', capture: 'Esperando tu trabajo', feedback: 'IA analizando', map: 'Grafo actualizado' };
    const status = document.getElementById('hub-pipeline-status');
    if (status) status.textContent = labels[stage] || 'Listo para empezar';
}

function startCentralSession() {
    setHubPipeline('study');
    switchTab('subjects');
}

function openCorrectionsFromHub() {
    closeVoiceRecorder();
    closeUploadModal();
    switchTab('correcciones');
    fetchCorrecciones();
}

function openQuizFromHub() {
    switchTab('quiz');
    const panel = document.getElementById('kgquiz-panel');
    if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function openWalkFromHome() {
    switchTab('subjects');
}

function openGraphFromHub() {
    switchTab('mapa');
}

function openVoiceRecorder() {
    const modal = document.getElementById('voice-modal');
    if (!modal) return;
    modal.classList.add('active');
    resetVoiceRecorder();
    lucide.createIcons();
}

function closeVoiceRecorder() {
    if (voiceRecorder && voiceRecorder.state === 'recording') voiceRecorder.stop();
    if (voiceStream) voiceStream.getTracks().forEach(track => track.stop());
    clearInterval(voiceTimerInterval);
    document.getElementById('voice-modal')?.classList.remove('active');
}

function resetVoiceRecorder() {
    clearInterval(voiceTimerInterval);
    if (voiceStream) voiceStream.getTracks().forEach(track => track.stop());
    voiceRecorder = null;
    voiceStream = null;
    voiceChunks = [];
    document.getElementById('voice-idle').style.display = 'block';
    document.getElementById('voice-recording').style.display = 'none';
    document.getElementById('voice-review').style.display = 'none';
    const geminiBridge = document.getElementById('voice-gemini-bridge');
    if (geminiBridge) geminiBridge.style.display = 'none';
    const geminiResult = document.getElementById('voice-gemini-result');
    if (geminiResult) geminiResult.value = '';
    const geminiModelOk = document.getElementById('voice-gemini-model-ok');
    if (geminiModelOk) geminiModelOk.checked = false;
    waitingGeminiJobId = null;
    document.getElementById('voice-timer').textContent = '00:00';
    if (voiceJobPoll) clearInterval(voiceJobPoll);
}

async function startVoiceRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
        alert('Este navegador no permite grabar audio desde la aplicación. Puedes usar la opción de subir un archivo de audio.');
        return;
    }
    try {
        voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const options = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? { mimeType: 'audio/webm;codecs=opus' } : {};
        voiceRecorder = new MediaRecorder(voiceStream, options);
        voiceChunks = [];
        voiceRecorder.ondataavailable = event => { if (event.data.size) voiceChunks.push(event.data); };
        voiceRecorder.onstop = finishVoiceRecording;
        voiceRecorder.start(250);
        voiceStartedAt = Date.now();
        document.getElementById('voice-idle').style.display = 'none';
        document.getElementById('voice-recording').style.display = 'block';
        document.getElementById('voice-review').style.display = 'none';
        clearInterval(voiceTimerInterval);
        voiceTimerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - voiceStartedAt) / 1000);
            document.getElementById('voice-timer').textContent = `${String(Math.floor(elapsed / 60)).padStart(2, '0')}:${String(elapsed % 60).padStart(2, '0')}`;
        }, 500);
        setHubPipeline('capture');
    } catch (error) {
        alert('No se pudo acceder al micrófono: ' + error.message);
    }
}

function stopVoiceRecording() {
    if (voiceRecorder && voiceRecorder.state === 'recording') voiceRecorder.stop();
}

function finishVoiceRecording() {
    clearInterval(voiceTimerInterval);
    if (voiceStream) voiceStream.getTracks().forEach(track => track.stop());
    const blob = new Blob(voiceChunks, { type: voiceRecorder?.mimeType || 'audio/webm' });
    const preview = document.getElementById('voice-preview');
    if (preview) preview.src = URL.createObjectURL(blob);
    document.getElementById('voice-recording').style.display = 'none';
    document.getElementById('voice-review').style.display = 'block';
    document.getElementById('voice-job-status').textContent = 'Enviando la grabación a Whisper…';
    uploadVoiceRecording(blob);
}

function uploadVoiceRecording(blob) {
    const form = new FormData();
    form.append('audio', blob, 'explicacion.webm');
    setHubPipeline('feedback');
    fetch('/api/voz', { method: 'POST', body: form })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            document.getElementById('voice-job-status').textContent = data.mensaje || 'La IA está analizando tu razonamiento…';
            pollVoiceJob(data.job_id);
        })
        .catch(error => { document.getElementById('voice-job-status').textContent = 'No se pudo enviar: ' + error.message; });
}

function pollVoiceJob(jobId) {
    if (voiceJobPoll) clearInterval(voiceJobPoll);
    const check = () => fetch('/api/voz/' + encodeURIComponent(jobId)).then(r => r.json()).then(job => {
        const status = document.getElementById('voice-job-status');
        if (status && job.mensaje) status.textContent = job.mensaje;
        if (job.estado === 'esperando_gemini') {
            waitingGeminiJobId = jobId;
            const bridge = document.getElementById('voice-gemini-bridge');
            if (bridge) bridge.style.display = 'block';
            const modelLabel = document.getElementById('voice-gemini-model-label');
            if (modelLabel && job.modelo_requerido) modelLabel.textContent = job.modelo_requerido;
        } else if (job.estado === 'completado') {
            clearInterval(voiceJobPoll);
            waitingGeminiJobId = null;
            const bridge = document.getElementById('voice-gemini-bridge');
            if (bridge) bridge.style.display = 'none';
            setHubPipeline('map');
            fetchHubStatus();
            fetchDashboardData();
            document.getElementById('voice-job-status').innerHTML = '✓ Listo. Puedes abrir el feedback y ver qué ha aprendido el sistema de este intento.';
        } else if (job.estado === 'error') {
            clearInterval(voiceJobPoll);
            document.getElementById('voice-job-status').textContent = 'No se pudo completar: ' + job.mensaje;
        }
    }).catch(() => {});
    check();
    voiceJobPoll = setInterval(check, 2500);
}

function submitGeminiVoiceResult() {
    const resultBox = document.getElementById('voice-gemini-result');
    const modelOk = document.getElementById('voice-gemini-model-ok');
    const status = document.getElementById('voice-job-status');
    const respuesta = resultBox?.value.trim() || '';
    if (!waitingGeminiJobId) { if (status) status.textContent = 'No hay ningún análisis esperando a Gemini.'; return; }
    if (!respuesta) { if (status) status.textContent = 'Pega primero la respuesta JSON de Gemini.'; return; }
    const expectedModel = document.getElementById('voice-gemini-model-label')?.textContent.trim() || '';
    if (!modelOk?.checked) {
        if (status) status.textContent = `Comprueba que el selector de Gemini muestra exactamente «${expectedModel || 'el modelo indicado'}» y marca la casilla.`;
        return;
    }
    if (status) status.textContent = 'Validando la respuesta de Gemini e integrándola…';
    fetch('/api/voz/' + encodeURIComponent(waitingGeminiJobId) + '/gemini', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ respuesta, modelo_verificado: true, modelo: expectedModel }),
    }).then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.detalle || data.error);
        if (status) status.textContent = data.mensaje || 'Corrección integrada.';
    }).catch(error => {
        if (status) status.textContent = 'No se pudo integrar la respuesta: ' + error.message;
    });
}

function openUploadModal() {
    document.getElementById('upload-modal')?.classList.add('active');
    const status = document.getElementById('hub-upload-status');
    if (status) status.textContent = '';
    lucide.createIcons();
}

function closeUploadModal() {
    document.getElementById('upload-modal')?.classList.remove('active');
}

// Switch Main Tabs
function switchTab(tabId) {
    const clickEvent = (typeof event !== 'undefined') ? event : null;
    // Update active tab buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    if (clickEvent && clickEvent.currentTarget) {
        clickEvent.currentTarget.classList.add('active');
    }
    
    // Update active sections
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(`view-dashboard`).classList.remove('active'); // force reset
    document.getElementById(`view-${tabId}`).classList.add('active');
    
    // Close detail panels
    closeSubjectDetail();
    
    currentTab = tabId;
    
    // Trigger tab-specific refresh if needed
    let tabPromise = Promise.resolve();
    if (tabId === 'dashboard') {
        fetchDashboardData();
    } else if (tabId === 'subjects') {
        fetchSubjectsData();
    } else if (tabId === 'quiz') {
        document.getElementById('quiz-setup-panel').style.display = 'block';
        document.getElementById('quiz-play-panel').style.display = 'none';
        fetchSubjectsData();
    } else if (tabId === 'plan') {
        tabPromise = loadPlanTab();
    } else if (tabId === 'mapa') {
        loadMapaFrame();
    } else if (tabId === 'correcciones') {
        fetchCorrecciones();
    } else if (tabId === 'context') {
        tabPromise = loadContextSummary();
    }

    // Update icons
    lucide.createIcons();
    return tabPromise;
}

// =====================================================================
// CONTEXTO VIVO PARA CUALQUIER IA
// =====================================================================
function loadContextSummary() {
    const target = document.getElementById('context-summary');
    if (!target) return Promise.resolve();
    target.innerHTML = '<div class="loading-spinner">Comprobando el contexto…</div>';
    return fetch('/api/context/summary').then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.error);
        const stats = data.stats || {};
        const derived = data.derived || {};
        const weak = (derived.nodos_debiles || []).slice(0, 5);
        const weakHtml = weak.length
            ? weak.map(node => `<span style="display:inline-block; margin:3px 5px 3px 0; padding:4px 8px; border-radius:6px; background:#1f2937; color:#d1d5db;">${escapeSearchHtml(node.id)} · ${Math.round((node.dominio_efectivo || 0) * 100)}%</span>`).join('')
            : '<span style="color:#9ca3af;">Todavía no hay nodos débiles calculados.</span>';
        target.innerHTML = `
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:18px;">
                ${contextMetric('Asignaturas', stats.asignaturas)}
                ${contextMetric('Nodos del grafo', stats.nodos_grafo)}
                ${contextMetric('Problemas', stats.problemas_banco)}
                ${contextMetric('Nodos con perfil', stats.nodos_con_perfil)}
                ${contextMetric('Sesiones', stats.sesiones)}
                ${contextMetric('Documentos', stats.documentos)}
            </div>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:18px;">
                <div>
                    <h3 style="margin:0 0 8px; color:#e2e8f0; font-size:15px;">Señales que recibe la IA</h3>
                    <p style="margin:0 0 8px; color:#9ca3af; font-size:13px;">${derived.repasos_pendientes?.length || 0} repasos pendientes · ${derived.frontera_aprendizaje?.length || 0} nodos en la frontera · ${derived.problemas?.total_listos || 0} problemas listos</p>
                    <div>${weakHtml}</div>
                </div>
                <div>
                    <h3 style="margin:0 0 8px; color:#e2e8f0; font-size:15px;">Archivos portables</h3>
                    <p style="margin:0; color:#9ca3af; font-size:13px; line-height:1.6;"><code>knowledge_graph/contexto_ia.md</code><br><code>knowledge_graph/contexto_ia.json</code></p>
                    <p style="margin:8px 0 0; color:#6b7280; font-size:12px;">Última comprobación: ${escapeSearchHtml(data.generated_at || '—')}</p>
                </div>
            </div>`;
    }).catch(error => {
        target.innerHTML = `<div class="no-tasks">No se pudo leer el contexto: ${escapeSearchHtml(error.message)}</div>`;
    });
}

function contextMetric(label, value) {
    return `<div style="background:#11141d; border:1px solid #2d3748; border-radius:8px; padding:12px;"><span style="display:block; color:#9ca3af; font-size:12px;">${label}</span><strong style="display:block; color:#60a5fa; font-size:22px; margin-top:4px;">${value ?? '—'}</strong></div>`;
}

function exportStudyContext() {
    const status = document.getElementById('context-export-status');
    if (status) status.textContent = 'Reuniendo grafos, perfil, problemas, sesiones y documentos…';
    fetch('/api/context/export', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({include_documents: true}),
    }).then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.error);
        if (status) status.textContent = `✓ Contexto actualizado: ${data.stats?.documentos || 0} documentos, ${data.stats?.problemas_banco || 0} problemas y ${data.stats?.nodos_grafo || 0} nodos.`;
        return loadContextSummary();
    }).catch(error => {
        if (status) status.textContent = 'No se pudo actualizar: ' + error.message;
    });
}

function downloadStudyContext(format) {
    const suffix = format === 'md' ? 'md' : 'json';
    window.open(`/api/context?format=${suffix}&download=1`, '_blank');
}

// =====================================================================
// 1. DASHBOARD DATA LOADER
// =====================================================================
function fetchDashboardData() {
    fetch('/api/dashboard')
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            // Set stats
            document.getElementById('stat-banco').innerText = data.stats.total_banco ?? '—';
            const sub = document.getElementById('stat-exercises-sub');
            if (sub) sub.innerText = `${data.stats.total_ejercicios} intentados en el vault`;
            document.getElementById('stat-attempts').innerText = data.stats.total_intentos;
            document.getElementById('stat-errors').innerText = data.stats.total_errores;
            
            // Render Agenda
            renderAgenda(data.agenda);
            
            // Render Concepts
            renderConceptsWeakness(data.conceptos_debiles);
            
            // Render Error Chart
            renderErrorChart(data.error_counts);
        })
        .catch(err => {
            console.error('Error fetching dashboard data:', err);
            document.getElementById('dashboard-agenda').innerHTML = '<div class="no-tasks">Error al cargar datos del panel.</div>';
        });
}

function renderAgenda(agenda) {
    const container = document.getElementById('dashboard-agenda');
    if (!agenda || agenda.length === 0) {
        container.innerHTML = '<div class="no-tasks">¡Felicidades! No tienes tareas pendientes de repaso para hoy.</div>';
        return;
    }
    
    container.innerHTML = agenda.map(item => {
        const esConcepto = item.tipo === 'concepto';
        const titulo = esConcepto ? `${item.id} — ${item.nombre}` : `${item.id} — ${item.tema}`;
        const estado = item.retraso > 0 ? `${item.retraso} d de retraso` : 'hoy';
        const clase = esConcepto ? 'concepto' : 'ejercicio';
        const onclick = esConcepto ? '' : `onclick="viewExercise('${item.id}')"`;
        return `
        <div class="agenda-item ${clase}" ${onclick}>
            <div class="agenda-item-left">
                <span class="agenda-item-title">${titulo}</span>
                <span class="agenda-item-meta">${item.asignatura}</span>
            </div>
            <div class="agenda-item-right">
                <span class="badge ${item.estado}">${esConcepto ? 'concepto' : item.estado}</span>
                <span class="agenda-date"><i data-lucide="clock" style="width:12px;height:12px;display:inline;"></i> ${estado} · ${item.proxima_revision}</span>
            </div>
        </div>
    `;
    }).join('');
    
    lucide.createIcons();
}

function renderConceptsWeakness(concepts) {
    const container = document.getElementById('dashboard-concepts');
    if (!concepts || concepts.length === 0) {
        container.innerHTML = '<div class="no-tasks">Aún no se ha evaluado ningún concepto físico.</div>';
        return;
    }
    
    container.innerHTML = concepts.map(c => {
        let scoreClass = 'green';
        let statusText = 'Dominado';
        if (c.dominio < 0.60) {
            scoreClass = 'red';
            statusText = 'Crítico';
        } else if (c.dominio < 0.85) {
            scoreClass = 'yellow';
            statusText = 'En repaso';
        }
        
        return `
            <div class="concept-weakness-item">
                <span class="concept-weakness-name">${c.concepto}</span>
                <div class="concept-weakness-bar-container">
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fg ${scoreClass}" style="width: ${c.dominio * 100}%"></div>
                    </div>
                    <span class="concept-weakness-score">${Math.round(c.dominio * 100)}%</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderErrorChart(errorCounts) {
    const ctx = document.getElementById('errorChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (errorChartInstance) {
        errorChartInstance.destroy();
    }
    
    const labels = Object.keys(errorCounts);
    const counts = Object.values(errorCounts);
    
    if (labels.length === 0) {
        ctx.font = "italic 14px Outfit";
        ctx.fillStyle = "#6b7280";
        ctx.textAlign = "center";
        ctx.fillText("No hay suficientes errores registrados", 150, 100);
        return;
    }
    
    errorChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#3b82f6', // blue
                    '#ef4444', // red
                    '#8b5cf6', // purple
                    '#f59e0b', // orange
                    '#10b981', // green
                    '#6b7280'  // gray
                ],
                borderColor: '#11141d',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#9ca3af',
                        font: {
                            family: 'Outfit',
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

// =====================================================================
// 2. SUBJECTS CONTROLLER
// =====================================================================
function fetchSubjectsData() {
    fetch('/api/subjects')
        .then(res => res.json())
        .then(subjects => {
            // Populate quiz subject dropdown
            const selectEl = document.getElementById('quiz-subject-select');
            if (selectEl) {
                selectEl.innerHTML = '<option value="all">Todas las Asignaturas</option>' + 
                    subjects.map(s => `<option value="${s.nombre}">${s.nombre}</option>`).join('');
            }

            const container = document.getElementById('subjects-container');
            if (!container) return;
            if (subjects.length === 0) {
                container.innerHTML = '<div class="no-tasks">No se han registrado asignaturas en la bóveda.</div>';
                return;
            }
            
            container.innerHTML = subjects.map(s => {
                // Asignar clase de estilo según nombre
                let styleClass = '';
                const name = s.nombre.toLowerCase();
                if (name.includes('cuántica') || name.includes('cuantica')) styleClass = 's-cuantica';
                else if (name.includes('sólido') || name.includes('solido')) styleClass = 's-solido';
                else if (name.includes('electrodinámica') || name.includes('electrodinamica')) styleClass = 's-electrodinamica';
                else if (name.includes('electrónica') || name.includes('electronica')) styleClass = 's-electronica';
                else if (name.includes('nuclear')) styleClass = 's-nuclear';
                
                return `
                    <div class="subject-card ${styleClass}" onclick="viewSubjectDetail('${s.nombre}')">
                        <h3 class="subject-title">${s.nombre}</h3>
                        <div class="subject-stats-row">
                            <div class="subject-stat-item">
                                <span class="subject-stat-label">Temas</span>
                                <span class="subject-stat-value">${s.temas}</span>
                            </div>
                            <div class="subject-stat-item">
                                <span class="subject-stat-label">Ejercicios</span>
                                <span class="subject-stat-value">${s.ejercicios}</span>
                            </div>
                            <div class="subject-stat-item">
                                <span class="subject-stat-label">Errores</span>
                                <span class="subject-stat-value text-red" style="${s.errores > 0 ? 'color:#f87171;' : ''}">${s.errores}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        })
        .catch(err => {
            console.error('Error fetching subjects:', err);
            const container = document.getElementById('subjects-container');
            if (container) {
                container.innerHTML = '<div class="no-tasks">Error al cargar asignaturas.</div>';
            }
        });
}

// View Subject Detail Page
function viewSubjectDetail(subjectName) {
    fetch(`/api/subjects/${encodeURIComponent(subjectName)}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            currentSubjectData = data;
            activeTopicFilter = null;
            
            document.getElementById('subject-detail-name').innerText = data.nombre;
            
            // Exámenes fecha
            const examBadge = document.getElementById('subject-detail-exam');
            if (data.fecha_examen) {
                examBadge.style.display = 'inline-block';
                examBadge.innerHTML = `<i data-lucide="calendar-range" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> Examen: ${data.fecha_examen}`;
            } else {
                examBadge.style.display = 'none';
            }
            
            // Temario
            const topicsContainer = document.getElementById('subject-topics');
            if (data.temas.length === 0) {
                topicsContainer.innerHTML = '<li>*No hay temas cargados en la taxonomía para esta asignatura.*</li>';
            } else {
                topicsContainer.innerHTML = data.temas.map(t => `
                    <li class="topic-item-clickable" onclick="filterExercisesByTopic('${t}')" style="cursor:pointer; display:flex; align-items:center; gap:8px; padding:10px; margin-bottom:6px; background:#1e293b; border-radius:6px; transition:background 0.2s;">
                        <i data-lucide="folder" style="width:16px;height:16px;color:#3b82f6;"></i>
                        <span>${t}</span>
                    </li>
                `).join('');
            }
            
            // Render Exercises
            renderSubjectExercisesFiltered();
            
            // Errores
            const errorsContainer = document.getElementById('subject-errors');
            if (data.errores.length === 0) {
                errorsContainer.innerHTML = '<div class="no-tasks" style="grid-column:1/-1;">¡Felicidades! No tienes errores registrados en esta materia.</div>';
            } else {
                errorsContainer.innerHTML = data.errores.map(err => `
                    <div class="web-error-card">
                        <div class="web-error-card-title">${err.id.toUpperCase()}: ${err.id.split('_')[-1]}</div>
                        <div class="web-error-card-meta">
                            <strong>Tema:</strong> ${err.tema}<br>
                            <strong>Tipos:</strong> ${err.tipos.join(', ')}
                        </div>
                    </div>
                `).join('');
            }
            
            // Anotaciones y teoría
            const notesContainer = document.getElementById('subject-notes-body');
            notesContainer.innerHTML = data.anotaciones ? parseMarkdown(data.anotaciones) : '<p class="no-tasks">No hay anotaciones teóricas guardadas para esta asignatura.</p>';
            
            // Open panel
            document.getElementById('subject-detail-panel').style.display = 'block';
            switchSubjectSubTab('temas'); // reset active subtab
            lucide.createIcons();
            
            // Render Math inside annotations
            renderMath(notesContainer);
        })
        .catch(err => console.error('Error fetching subject detail:', err));
}

function topicsMatch(topicA, topicB) {
    if (!topicA || !topicB) return false;
    const clean = (str) => {
        return str.toLowerCase()
            .replace(/^tema\s*\d+\s*:\s*/, "")
            .replace(/[áàäâ]/g, "a")
            .replace(/[éèëê]/g, "e")
            .replace(/[íìïî]/g, "i")
            .replace(/[óòöô]/g, "o")
            .replace(/[úùüû]/g, "u")
            .replace(/[ñ]/g, "n")
            .replace(/[^a-z0-9]/g, " ")
            .split(/\s+/)
            .filter(w => w.length > 2);
    };
    const wordsA = clean(topicA);
    const wordsB = clean(topicB);
    if (wordsA.length === 0 || wordsB.length === 0) {
        const cleanStrA = topicA.toLowerCase().replace(/^tema\s*\d+\s*:\s*/, "").trim();
        const cleanStrB = topicB.toLowerCase().replace(/^tema\s*\d+\s*:\s*/, "").trim();
        return cleanStrA.includes(cleanStrB) || cleanStrB.includes(cleanStrA);
    }
    const common = wordsA.filter(w => wordsB.includes(w));
    const minWords = Math.min(wordsA.length, wordsB.length);
    if (minWords <= 2) {
        return common.length >= 1;
    }
    return common.length >= 2;
}

function renderSubjectExercisesFiltered() {
    const container = document.getElementById('subject-exercises');
    if (!container) return;
    if (!currentSubjectData || currentSubjectData.ejercicios.length === 0) {
        container.innerHTML = '<div class="no-tasks" style="grid-column:1/-1;">Ningún ejercicio registrado en esta asignatura.</div>';
        return;
    }
    
    let exercisesToRender = currentSubjectData.ejercicios;
    let filterBanner = '';
    if (activeTopicFilter) {
        exercisesToRender = currentSubjectData.ejercicios.filter(ex => topicsMatch(ex.tema, activeTopicFilter));
        filterBanner = `
            <div class="filter-banner" style="grid-column:1/-1; display:flex; justify-content:space-between; align-items:center; background:#1e293b; padding:8px 12px; border-radius:6px; margin-bottom:15px; border-left:4px solid #3b82f6; width: 100%;">
                <span style="font-size:14px;">Filtrado por tema: <strong>${activeTopicFilter}</strong></span>
                <button class="btn btn-sm" onclick="clearTopicFilter()" style="padding:4px 10px; font-size:12px; background:#ef4444; border:none; color:white; border-radius:4px; cursor:pointer;">Quitar filtro</button>
            </div>
        `;
    }
    
    if (exercisesToRender.length === 0) {
        container.innerHTML = filterBanner + '<div class="no-tasks" style="grid-column:1/-1;">Ningún ejercicio registrado bajo este tema.</div>';
    } else {
        container.innerHTML = filterBanner + exercisesToRender.map(ex => `
            <div class="web-exercise-card" onclick="viewExercise('${ex.id}')" style="cursor:pointer;">
                <div class="web-exercise-card-header">
                    <span class="web-exercise-card-id">${ex.id}</span>
                    <span class="badge ${ex.estado}">${ex.estado}</span>
                </div>
                <span class="web-exercise-card-topic">${ex.tema}</span>
        <span class="web-exercise-card-date">Reintento local: ${ex.proxima_reintento || '—'}</span>
            </div>
        `).join('');
    }
}

function filterExercisesByTopic(topicName) {
    activeTopicFilter = topicName;
    switchSubjectSubTab('ejercicios');
    renderSubjectExercisesFiltered();
}

function clearTopicFilter() {
    activeTopicFilter = null;
    renderSubjectExercisesFiltered();
}

function closeSubjectDetail() {
    document.getElementById('subject-detail-panel').style.display = 'none';
}

function switchSubjectSubTab(tabName) {
    document.querySelectorAll('.sub-tab').forEach(btn => btn.classList.remove('active'));
    // Set active tab button based on tabName
    document.querySelectorAll('.sub-tab').forEach(btn => {
        if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabName)) {
            btn.classList.add('active');
        }
    });
    
    document.querySelectorAll('.subject-subtab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`subject-subtab-${tabName}`).classList.add('active');
}



// =====================================================================
// 4. EXERCISE DETAILS MODAL & LATEX
// =====================================================================
// 4. EXERCISE DETAILS MODAL & LATEX
// =====================================================================
function viewExercise(exercId) {
    fetch(`/api/exercise/${exercId}`)
        .then(res => res.json())
        .then(ex => {
            if (ex.error) throw new Error(ex.error);
            
            currentExerciseDetail = ex;
            
            // Reset modal layout
            document.getElementById('modal-view-panel').style.display = 'block';
            document.getElementById('modal-edit-panel').style.display = 'none';
            
            document.getElementById('modal-exercise-id').innerText = ex.id;
            document.getElementById('modal-exercise-subject').innerText = ex.asignatura;
            document.getElementById('modal-exercise-topic').innerText = ex.tema;
            
            const stateBadge = document.getElementById('modal-exercise-state');
            stateBadge.className = `badge ${ex.estado}`;
            stateBadge.innerText = ex.estado;
            
            // Enunciado
            const enunciadoContainer = document.getElementById('modal-enunciado-body');
            enunciadoContainer.innerHTML = parseMarkdown(ex.enunciado);
            
            // Enunciado Asset (Image/PDF Drawing)
            const assetContainer = document.getElementById('modal-enunciado-asset-container');
            const assetContent = document.getElementById('modal-enunciado-asset-content');
            if (ex.enunciado_asset) {
                assetContainer.style.display = 'block';
                const lowerAsset = ex.enunciado_asset.toLowerCase();
                if (lowerAsset.endsWith('.png') || lowerAsset.endsWith('.jpg') || lowerAsset.endsWith('.jpeg') || lowerAsset.endsWith('.webp') || lowerAsset.endsWith('.gif') || lowerAsset.endsWith('.bmp')) {
                    assetContent.innerHTML = `<img src="/assets/${ex.enunciado_asset}" alt="Enunciado Original" style="max-width:100%; border-radius: 8px; border: 1px solid #2d3748; cursor:pointer;" onclick="window.open('/assets/${ex.enunciado_asset}', '_blank')">`;
                } else {
                    assetContent.innerHTML = `<a href="/assets/${ex.enunciado_asset}" target="_blank" class="obsidian-link" style="display:flex; align-items:center; gap:6px;"><i data-lucide="file-text" style="width:16px;height:16px;"></i> Ver Enunciado (PDF/Archivo)</a>`;
                }
            } else {
                assetContainer.style.display = 'none';
                assetContent.innerHTML = '';
            }
            
            // Intentos
            const attemptsContainer = document.getElementById('modal-attempts-container');
            if (ex.intentos.length === 0) {
                attemptsContainer.innerHTML = '<p class="no-tasks">No se ha registrado ningún intento para este ejercicio aún.</p>';
            } else {
                attemptsContainer.innerHTML = ex.intentos.map(i => {
                    const statusClass = i.resultado === 'correcto' ? 'correcto' : 'incorrecto';
                    
                    // Render images
                    const imgsHtml = i.imagenes.map(img => `
                        <img src="/assets/${img}" alt="Página de manuscrito" onclick="window.open('/assets/${img}', '_blank')" style="cursor:pointer; max-height:200px; border-radius:4px; border:1px solid #2d3748;">
                    `).join('');
                    
                    return `
                        <div class="timeline-item">
                            <span class="timeline-dot ${statusClass}"></span>
                            <div class="timeline-header">
                                <span class="timeline-title">${i.id.toUpperCase()} — Resultado: <strong style="${i.resultado === 'correcto' ? 'color:#34d399' : 'color:#f87171'}">${i.resultado.toUpperCase()}</strong></span>
                                <span class="timeline-date">${i.fecha}</span>
                            </div>
                            <div class="timeline-body">
                                <div class="timeline-field">
                                    <div class="timeline-field-title">Transcripción del estudiante (LaTeX)</div>
                                    <div class="math-content" style="background:#0a0b0e;max-height:200px;overflow-y:auto;padding:12px;border-radius:6px;border:1px solid #1e293b;">
                                        $$ ${i.transcripcion} $$
                                    </div>
                                </div>
                                <div class="timeline-field">
                                    <div class="timeline-field-title">Evaluación Pedagógica</div>
                                    <div style="line-height:1.5;color:#d1d5db;">${parseMarkdown(i.analisis)}</div>
                                </div>
                                ${imgsHtml ? `
                                <div class="timeline-field">
                                    <div class="timeline-field-title">Manuscrito Escaneado</div>
                                    <div class="timeline-images" style="display:flex; gap:10px; overflow-x:auto; padding-bottom:6px;">${imgsHtml}</div>
                                </div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            // Open Modal
            document.getElementById('exercise-modal').classList.add('active');
            
            // Render Math inside Enunciation and Attempts
            renderMath(enunciadoContainer);
            document.querySelectorAll('#modal-attempts-container .math-content').forEach(el => renderMath(el));
            document.querySelectorAll('#modal-attempts-container div').forEach(el => renderMath(el));
            lucide.createIcons();
        })
        .catch(err => console.error('Error fetching exercise detail:', err));
}

// EDIT & DELETE ACTIONS FOR EXERCISE MODAL
function showEditExerciseForm() {
    if (!currentExerciseDetail) return;
    
    document.getElementById('edit-subject').value = currentExerciseDetail.asignatura;
    document.getElementById('edit-topic').value = currentExerciseDetail.tema;
    document.getElementById('edit-concepts').value = currentExerciseDetail.conceptos.join(', ');
    document.getElementById('edit-state').value = currentExerciseDetail.estado;
    document.getElementById('edit-proxima').value = currentExerciseDetail.proxima_reintento || '';
    document.getElementById('edit-enunciado').value = currentExerciseDetail.enunciado;
    
    document.getElementById('modal-view-panel').style.display = 'none';
    document.getElementById('modal-edit-panel').style.display = 'block';
}

function cancelEditExercise() {
    document.getElementById('modal-view-panel').style.display = 'block';
    document.getElementById('modal-edit-panel').style.display = 'none';
}

function saveExerciseEdit() {
    if (!currentExerciseDetail) return;
    
    const updatedData = {
        asignatura: document.getElementById('edit-subject').value.trim(),
        tema: document.getElementById('edit-topic').value.trim(),
        conceptos: document.getElementById('edit-concepts').value.split(',').map(c => c.trim()).filter(c => c),
        estado: document.getElementById('edit-state').value,
        proxima_reintento: document.getElementById('edit-proxima').value.trim(),
        enunciado: document.getElementById('edit-enunciado').value.trim()
    };
    
    // Validar fecha en formato DD/MM/YYYY
    const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
    if (updatedData.proxima_reintento && !dateRegex.test(updatedData.proxima_reintento)) {
        alert('La fecha de reintento debe tener el formato DD/MM/YYYY o dejarse vacía.');
        return;
    }
    
    fetch(`/api/exercise/${currentExerciseDetail.id}/edit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        alert('Ejercicio actualizado correctamente.');
        
        // Refresh detail view
        viewExercise(currentExerciseDetail.id);
        
        // Refresh dashboard and lists in background
        fetchDashboardData();
        if (currentTab === 'subjects') {
            fetchSubjectsData();
        }
    })
    .catch(err => {
        console.error('Error saving exercise edit:', err);
        alert('Error al guardar los cambios: ' + err.message);
    });
}

function deleteCurrentExercise() {
    if (!currentExerciseDetail) return;
    
    if (confirm(`¿Estás seguro de que deseas eliminar el ejercicio "${currentExerciseDetail.id}"? Esta acción eliminará el archivo de Obsidian y no se puede deshacer.`)) {
        fetch(`/api/exercise/${currentExerciseDetail.id}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            alert('Ejercicio eliminado correctamente.');
            closeExerciseModal();
            
            // Refresh views
            fetchDashboardData();
            fetchSubjectsData();
        })
        .catch(err => {
            console.error('Error deleting exercise:', err);
            alert('Error al eliminar el ejercicio: ' + err.message);
        });
    }
}

// =====================================================================
// AUTOEVALUADOR (QUIZ FLASHCARDS) ACTIONS
// =====================================================================
function startQuizSession() {
    const subject = document.getElementById('quiz-subject-select').value;
    const filter = document.getElementById('quiz-filter-select').value;
    
    const setupPanel = document.getElementById('quiz-setup-panel');
    const playPanel = document.getElementById('quiz-play-panel');
    
    let fetchPromise;
    
    if (subject === 'all') {
        if (filter === 'today') {
            fetchPromise = fetch('/api/dashboard')
                .then(res => res.json())
                .then(data => data.reintentos_ejercicios || []);
        } else {
            fetchPromise = fetch('/api/subjects')
                .then(res => res.json())
                .then(subjects => {
                    const promises = subjects.map(s => fetch(`/api/subjects/${encodeURIComponent(s.nombre)}`).then(r => r.json()));
                    return Promise.all(promises).then(details => {
                        let allEx = [];
                        details.forEach(d => allEx = allEx.concat(d.ejercicios));
                        return allEx;
                    });
                });
        }
    } else {
        fetchPromise = fetch(`/api/subjects/${encodeURIComponent(subject)}`)
            .then(res => res.json())
            .then(data => {
                if (filter === 'today') {
                    const hoyDate = new Date();
                    hoyDate.setHours(0,0,0,0);
                    return data.ejercicios.filter(ex => {
                        const fecha = ex.proxima_reintento;
                        if (!fecha) return false;
                        const exDate = parseDateDMY(fecha);
                        return exDate && exDate <= hoyDate;
                    });
                } else {
                    return data.ejercicios;
                }
            });
    }
    
    fetchPromise.then(exercises => {
        // Mezclar aleatoriamente
        quizExercises = exercises.sort(() => Math.random() - 0.5);
        quizCurrentIndex = 0;
        
        if (quizExercises.length === 0) {
            alert('No hay ejercicios pendientes de repaso que coincidan con la selección.');
            return;
        }
        
        setupPanel.style.display = 'none';
        playPanel.style.display = 'block';
        loadQuizCard();
    }).catch(err => {
        console.error('Error starting quiz:', err);
        alert('Error al iniciar la sesión de repaso.');
    });
}

function exitQuizSession() {
    document.getElementById('quiz-setup-panel').style.display = 'block';
    document.getElementById('quiz-play-panel').style.display = 'none';
    fetchDashboardData();
}

function loadQuizCard() {
    if (quizCurrentIndex >= quizExercises.length) {
        alert('¡Enhorabuena! Has completado todas las tarjetas de repaso de esta sesión.');
        exitQuizSession();
        return;
    }
    
    const ex = quizExercises[quizCurrentIndex];
    
    // Ocultar la solución
    document.getElementById('quiz-solution-area').style.display = 'none';
    document.getElementById('quiz-action-show-solution').style.display = 'block';
    
    document.getElementById('quiz-progress-text').innerText = `Tarjeta ${quizCurrentIndex + 1} de ${quizExercises.length}`;
    document.getElementById('quiz-card-id').innerText = ex.id;
    document.getElementById('quiz-card-subject').innerText = ex.asignatura;
    document.getElementById('quiz-card-topic').innerText = ex.tema;
    
    fetch(`/api/exercise/${ex.id}`)
        .then(res => res.json())
        .then(detail => {
            document.getElementById('quiz-card-enunciado').innerHTML = parseMarkdown(detail.enunciado);
            
            // Enunciado Asset
            const assetContainer = document.getElementById('quiz-card-enunciado-asset');
            if (detail.enunciado_asset) {
                assetContainer.style.display = 'block';
                const lowerAsset = detail.enunciado_asset.toLowerCase();
                if (lowerAsset.endsWith('.png') || lowerAsset.endsWith('.jpg') || lowerAsset.endsWith('.jpeg') || lowerAsset.endsWith('.webp') || lowerAsset.endsWith('.gif') || lowerAsset.endsWith('.bmp')) {
                    assetContainer.innerHTML = `<img src="/assets/${detail.enunciado_asset}" alt="Dibujo del Enunciado" style="max-width:100%; border-radius:8px; border:1px solid #2d3748; cursor:pointer;" onclick="window.open('/assets/${detail.enunciado_asset}', '_blank')">`;
                } else {
                    assetContainer.innerHTML = `<a href="/assets/${detail.enunciado_asset}" target="_blank" class="obsidian-link" style="display:flex; align-items:center; gap:6px; justify-content:center;"><i data-lucide="file-text" style="width:16px;height:16px;"></i> Ver Enunciado Original (PDF/Archivo)</a>`;
                }
            } else {
                assetContainer.style.display = 'none';
                assetContainer.innerHTML = '';
            }
            
            // Cargar intentos y crítica
            const solImagesContainer = document.getElementById('quiz-card-sol-images');
            const solTranscripcion = document.getElementById('quiz-card-sol-transcripcion');
            const criticaContainer = document.getElementById('quiz-card-critica');
            
            if (detail.intentos.length === 0) {
                solImagesContainer.innerHTML = '<p class="no-tasks">No hay intentos de resolución previos para este ejercicio.</p>';
                solTranscripcion.innerText = 'N/A';
                criticaContainer.innerHTML = '<p class="no-tasks">N/A</p>';
            } else {
                const latest = detail.intentos[0];
                
                if (latest.imagenes && latest.imagenes.length > 0) {
                    solImagesContainer.innerHTML = latest.imagenes.map(img => `
                        <img src="/assets/${img}" alt="Resolución Manuscrita" style="max-height:250px; border-radius:6px; border:1px solid #2d3748; cursor:pointer;" onclick="window.open('/assets/${img}', '_blank')">
                    `).join('');
                } else {
                    solImagesContainer.innerHTML = '<p class="no-tasks">No hay imágenes escaneadas en el último intento.</p>';
                }
                
                solTranscripcion.innerText = latest.transcripcion ? `$$ ${latest.transcripcion} $$` : 'Sin transcripción LaTeX.';
                criticaContainer.innerHTML = parseMarkdown(latest.analisis);
            }
            
            renderMath(document.getElementById('quiz-card-enunciado'));
            renderMath(solTranscripcion);
            renderMath(criticaContainer);
            lucide.createIcons();
        })
        .catch(err => {
            console.error('Error loading quiz card:', err);
            alert('Error al cargar la tarjeta de repaso.');
        });
}

function showQuizSolution() {
    document.getElementById('quiz-action-show-solution').style.display = 'none';
    document.getElementById('quiz-solution-area').style.display = 'block';
    
    // Trigger Math Jax compilation inside evaluation areas
    renderMath(document.getElementById('quiz-card-sol-transcripcion'));
    renderMath(document.getElementById('quiz-card-critica'));
    lucide.createIcons();
}

function submitQuizRating(rating) {
    const ex = quizExercises[quizCurrentIndex];
    
    fetch(`/api/exercise/${ex.id}/review`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating: rating })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        
        // Avanzar a la siguiente tarjeta
        quizCurrentIndex++;
        loadQuizCard();
    })
    .catch(err => {
        console.error('Error submitting quiz rating:', err);
        alert('Error al guardar la calificación de repaso: ' + err.message);
    });
}

// DATE UTILITY FUNCTIONS FOR JS
function parseDateDMY(dateStr) {
    if (!dateStr) return new Date();
    const parts = dateStr.split('/');
    if (parts.length === 3) {
        return new Date(parts[2], parts[1] - 1, parts[0]);
    }
    const partsIso = dateStr.split('-');
    if (partsIso.length === 3) {
        return new Date(partsIso[0], partsIso[1] - 1, partsIso[2]);
    }
    return new Date(dateStr);
}

function closeExerciseModal() {
    document.getElementById('exercise-modal').classList.remove('active');
}

// =====================================================================
// 5. SEARCH ENGINE (SEMANTIC SEARCH)
// =====================================================================
function handleSearchKey(event) {
    if (event.key === 'Enter') {
        executeSearch();
    }
}

function escapeSearchHtml(value) {
    return String(value || '').replace(/[&<>"']/g, function (char) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[char];
    });
}

function executeSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<div class="loading-spinner"><i data-lucide="sparkles" class="logo-icon spinning"></i> Preparando el encargo para Gemini Web...</div>';
    lucide.createIcons();
    
    fetch('/api/search?q=' + encodeURIComponent(query))
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            if (data.mode === 'gemini_web') {
                const copiedMessage = data.copied
                    ? 'El prompt se ha copiado al portapapeles.'
                    : 'No se pudo copiar automáticamente: abre el archivo de encargo indicado y copia su contenido.';
                const openedMessage = data.opened
                    ? 'Gemini Web se ha abierto en el navegador.'
                    : 'No se pudo abrir Gemini Web automáticamente; ábrelo manualmente.';
                const promptPath = escapeSearchHtml(data.prompt_path || '');
                resultsContainer.innerHTML =
                    '<div class="search-handoff">' +
                        '<span class="hub-eyebrow"><i data-lucide="globe-2"></i> GEMINI WEB</span>' +
                        '<h2>Encargo preparado</h2>' +
                        '<p>' + copiedMessage + '</p>' +
                        '<p>' + openedMessage + '</p>' +
                        '<p class="handoff-meta">Encargo guardado en: <code>' + promptPath + '</code></p>' +
                        '<p class="handoff-meta">Modelo que debes comprobar: <strong>' +
                            escapeSearchHtml(data.model || 'el modelo configurado') + '</strong></p>' +
                        '<label for="search-gemini-response">Pega aquí la respuesta Markdown de Gemini Web</label>' +
                        '<textarea id="search-gemini-response" placeholder="Pega aquí la respuesta completa de Gemini..."></textarea>' +
                        '<button class="btn btn-primary" onclick="importSearchResult()">' +
                            '<i data-lucide="download"></i> Importar resultados</button>' +
                    '</div>';
                lucide.createIcons();
                return;
            }

            resultsContainer.innerHTML =
                '<div class="markdown-body">' + (data.html || '') + '</div>';
            renderMath(resultsContainer);
        })
        .catch(err => {
            console.error('Error running search:', err);
            resultsContainer.innerHTML = '<div class="no-tasks">No se pudo preparar la búsqueda para Gemini Web: ' +
                escapeSearchHtml(err.message) + '</div>';
        });
}

function importSearchResult() {
    const query = document.getElementById('search-input').value.trim();
    const responseBox = document.getElementById('search-gemini-response');
    const markdown = responseBox ? responseBox.value.trim() : '';
    const resultsContainer = document.getElementById('search-results');

    if (!markdown) {
        resultsContainer.insertAdjacentHTML('afterbegin',
            '<div class="no-tasks">Pega primero la respuesta completa de Gemini Web.</div>');
        return;
    }

    resultsContainer.innerHTML =
        '<div class="loading-spinner"><i data-lucide="loader-circle" class="logo-icon spinning"></i> Importando resultados...</div>';
    lucide.createIcons();

    fetch('/api/search/import', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: query, markdown: markdown})
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            resultsContainer.innerHTML =
                '<div class="markdown-body">' + (data.html || '') + '</div>';
            renderMath(resultsContainer);
        })
        .catch(err => {
            console.error('Error importing search result:', err);
            resultsContainer.innerHTML = '<div class="no-tasks">No se pudo importar la respuesta: ' +
                escapeSearchHtml(err.message) + '</div>';
        });
}

// =====================================================================
// 6. GENERAL UTILITY FUNCTIONS
// =====================================================================

// LaTeX & Markdown compiling support inside element
function renderMath(element) {
    if (typeof renderMathInElement === 'function') {
        renderMathInElement(element, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\(', right: '\\)', display: false},
                {left: '\\[', right: '\\]', display: true}
            ],
            throwOnError: false
        });
    }
}

// Lightweight Markdown to HTML parser (renders titles, tables, bold, list, blockquotes)
function parseMarkdown(markdown) {
    if (!markdown) return '';
    let html = markdown
        // Headers
        .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Inline code / badge
        .replace(/`(.*?)`/g, '<code>$1</code>')
        // Blockquotes
        .replace(/^>\s*\[\!IMPORTANT\]\s*\n(.*?)$/gm, '<blockquote><strong>Importante:</strong> $1')
        .replace(/^>\s*(.*?)$/gm, '<blockquote>$1</blockquote>')
        // Unordered lists
        .replace(/^\s*[\-\*]\s+(.*?)$/gm, '<li>$1</li>')
        // Wrap lists
        .replace(/(<li>.*?<\/li>)/s, '<ul>$1</ul>')
        // Tables
        .replace(/\|(.+)\|/g, (match, content) => {
            const cols = content.split('|').map(c => c.trim());
            if (cols[0].includes('---')) return ''; // skip divider line
            return '<tr>' + cols.map(c => `<td>${c}</td>`).join('') + '</tr>';
        });
        
    // Wrap tables
    html = html.replace(/(<tr>.*?<\/tr>)/s, '<table class="table"><tbody>$1</tbody></table>');
    
    // Fix paragraphs
    html = html.split('\n\n').map(p => {
        if (p.trim().startsWith('<h') || p.trim().startsWith('<ul') || p.trim().startsWith('<table') || p.trim().startsWith('<block')) {
            return p;
        }
        return `<p>${p}</p>`;
    }).join('\n');

    return html;
}

// =====================================================================
// KNOWLEDGE GRAPH: Plan de Estudio, Exámenes, Mapa, Subidas
// =====================================================================
let examConfig = null;

function loadPlanTab() {
    fetchExamConfig();
    fetchGrafosSelect();
    fetchGamificacion();
    return Promise.resolve();
}

function fetchGamificacion() {
    fetch('/api/kg/gamificacion')
        .then(r => r.json())
        .then(g => { if (!g.error) renderGamificacion(g); })
        .catch(() => {});
}

function renderGamificacion(g) {
    const cont = document.getElementById('kg-gamificacion');
    if (!cont) return;
    const pct = g.xp_para_siguiente ? Math.min(100, Math.round(100 * g.xp_en_nivel / g.xp_para_siguiente)) : 0;
    const metaPct = g.meta_diaria ? Math.min(100, Math.round(100 * g.xp_hoy / g.meta_diaria)) : 0;
    const conseguidas = g.insignias.filter(i => i.conseguida);
    const pendientes = g.insignias.filter(i => !i.conseguida);
    const chip = (i, on) =>
        `<span title="${i.desc}${i.fecha ? ' — ' + i.fecha : ''}" style="display:inline-block; padding:4px 10px; margin:3px; border-radius:14px; font-size:12px; border:1px solid ${on ? '#f59e0b' : '#374151'}; background:${on ? 'rgba(245,158,11,.15)' : 'transparent'}; color:${on ? '#fbbf24' : '#6b7280'};">${on ? '★' : '☆'} ${i.nombre}</span>`;
    cont.innerHTML = `
      <div style="display:flex; gap:24px; flex-wrap:wrap; align-items:center; justify-content:space-between;">
        <div style="display:flex; gap:24px; flex-wrap:wrap; align-items:center;">
          <div style="text-align:center;">
            <div style="font-size:34px; font-weight:800; color:#a78bfa; line-height:1;">${g.nivel}</div>
            <div style="font-size:11px; color:#9ca3af; text-transform:uppercase; letter-spacing:.5px;">Nivel</div>
          </div>
          <div style="min-width:180px;">
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#9ca3af;">
              <span>${g.xp_total} XP totales</span><span>${g.xp_en_nivel}/${g.xp_para_siguiente}</span>
            </div>
            <div style="height:8px; background:#1f2430; border-radius:4px; overflow:hidden; margin-top:4px;">
              <div style="height:100%; width:${pct}%; background:linear-gradient(90deg,#8b5cf6,#a78bfa);"></div>
            </div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:28px; font-weight:800; color:#fb923c; line-height:1;">🔥 ${g.racha}</div>
            <div style="font-size:11px; color:#9ca3af;">racha (máx ${g.racha_max})</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:20px; font-weight:700; color:#34d399; line-height:1.2;">${g.dominados}<span style="color:#6b7280; font-size:14px;"> dom · ${g.consolidados} cons</span></div>
            <div style="font-size:11px; color:#9ca3af;">nodos</div>
          </div>
        </div>
        <div style="min-width:200px;">
          <div style="display:flex; justify-content:space-between; font-size:12px; color:#9ca3af;">
            <span>Meta de hoy</span><span>${g.xp_hoy}/${g.meta_diaria} XP ${g.meta_cumplida ? '✅' : ''}</span>
          </div>
          <div style="height:8px; background:#1f2430; border-radius:4px; overflow:hidden; margin-top:4px;">
            <div style="height:100%; width:${metaPct}%; background:${g.meta_cumplida ? '#34d399' : 'linear-gradient(90deg,#059669,#34d399)'};"></div>
          </div>
        </div>
      </div>
      <div style="margin-top:12px; border-top:1px solid #1f2430; padding-top:10px;">
        ${conseguidas.map(i => chip(i, true)).join('')}
        ${pendientes.map(i => chip(i, false)).join('')}
      </div>`;
}

function loadMapaFrame() {
    const frame = document.getElementById('mapa-frame');
    // Recargar siempre para reflejar el perfil más reciente
    frame.src = '/kg/mapa?t=' + Date.now();
}

function reloadMapa() {
    loadMapaFrame();
}

function toggleMapaFullscreen() {
    const wrap = document.getElementById('mapa-wrap');
    if (!document.fullscreenElement) {
        (wrap.requestFullscreen ? wrap.requestFullscreen() : (wrap.webkitRequestFullscreen && wrap.webkitRequestFullscreen()));
    } else {
        document.exitFullscreen ? document.exitFullscreen() : (document.webkitExitFullscreen && document.webkitExitFullscreen());
    }
}

// En pantalla completa, el contenedor y el iframe deben ocupar toda la pantalla.
document.addEventListener('fullscreenchange', () => {
    const wrap = document.getElementById('mapa-wrap');
    if (!wrap) return;
    const full = document.fullscreenElement === wrap;
    wrap.style.height = full ? '100vh' : 'calc(100vh - 170px)';
    // Poke al mapa (dentro del iframe, mismo origen) para que recalcule su tamaño.
    const frame = document.getElementById('mapa-frame');
    setTimeout(() => {
        try { frame.contentWindow.dispatchEvent(new Event('resize')); } catch (e) {}
    }, 80);
});

// ---- Correcciones (feedback de Gemini, fuera de Obsidian) ----
function _veredicto(c) {
    if (c.resultado === 'correcto' && !c.tiene_error) return { txt: '✓ Resuelto', color: '#059669' };
    if (c.resultado === 'correcto' && c.tiene_error) return { txt: '≈ Con un desliz', color: '#16a34a' };
    if (c.resultado === 'incompleto') return { txt: '~ A medias', color: '#ca8a04' };
    return { txt: '✗ Con errores', color: '#dc2626' };
}

function fetchCorrecciones() {
    const cont = document.getElementById('correcciones-list');
    cont.innerHTML = '<div class="loading-spinner" style="color:#9ca3af;">Cargando correcciones...</div>';
    fetch('/api/kg/correcciones')
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            renderCorrecciones(data.correcciones || []);
        })
        .catch(e => { cont.innerHTML = `<div class="no-tasks">Error al cargar: ${e.message}</div>`; });
}

// Envuelve una expresión LaTeX "pelada" (sin $ ) en delimitadores para que KaTeX
// la renderice. Gemini devuelve incorrecto/correcto como LaTeX sin delimitar.
function mathWrap(expr) {
    if (!expr) return '';
    const s = String(expr).trim();
    if (/\$|\\\(|\\\[|\\begin\{/.test(s)) return s;   // ya trae delimitadores
    return `$$${s}$$`;
}

function renderCorrecciones(lista) {
    const cont = document.getElementById('correcciones-list');
    if (!lista.length) {
        cont.innerHTML = `<div class="no-tasks">Aún no hay correcciones. Sube un ejercicio o déjalo en el Inbox y pulsa <b>Corregir lo nuevo</b>: el feedback aparecerá aquí.</div>`;
        return;
    }
    cont.innerHTML = lista.map((c, i) => {
        const v = _veredicto(c);
        const fecha = (c.fecha || '').replace('T', ' ').slice(0, 16);
        const codigo = c.codigo ? `<span class="badge" style="background:#1e3a8a; color:#bfdbfe; white-space:nowrap;">${c.codigo}</span>` : '';
        const confPct = (typeof c.confianza === 'number') ? Math.round(c.confianza * 100) : null;
        const bajaConf = (confPct !== null && confPct < 80);
        const modeloBadge = c.modelo ? `<span class="badge" style="background:${c.es_fallback ? '#7c2d12' : '#1f2937'}; color:${c.es_fallback ? '#fdba74' : '#9ca3af'}; white-space:nowrap; font-size:11px;" title="Modelo de IA que hizo esta corrección">${c.es_fallback ? '⚠ ' : ''}${c.modelo}</span>` : '';
        const errores = (c.errores || []).map(e => `
            <div style="background:#1a1114; border:1px solid #7f1d1d; border-radius:8px; padding:12px 14px; margin-top:10px;">
                <div style="color:#fca5a5; font-weight:600; margin-bottom:6px;">✗ ${e.titulo || 'Error'}${(e.tipo && e.tipo.length) ? ` <span style="color:#9ca3af; font-weight:400; font-size:12px;">(${e.tipo.join(', ')})</span>` : ''}</div>
                <div class="math-content" style="color:#e5e7eb; line-height:1.5; margin-bottom:8px;">${(e.descripcion || '')}</div>
                ${e.incorrecto ? `<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:6px;"><span style="color:#f87171; min-width:80px;">Incorrecto:</span><span class="math-content" style="flex:1; min-width:0;">${mathWrap(e.incorrecto)}</span></div>` : ''}
                ${e.correcto ? `<div style="display:flex; gap:10px; flex-wrap:wrap;"><span style="color:#34d399; min-width:80px;">Correcto:</span><span class="math-content" style="flex:1; min-width:0;">${mathWrap(e.correcto)}</span></div>` : ''}
                ${e.como_evitarlo ? `<div style="color:#9ca3af; font-size:13px; margin-top:8px;">💡 ${e.como_evitarlo}</div>` : ''}
            </div>`).join('');
        const checkpoints = (c.checkpoints || []).map((cp, ci) => `
            <div style="display:flex; gap:8px; align-items:flex-start; padding:6px 0; ${cp.correcto ? '' : 'background:#1a1114; border-radius:6px; padding:8px 10px;'}">
                <span>${cp.correcto ? '✅' : '❌'}</span>
                <div style="min-width:0; flex:1;">
                    <span style="color:#e5e7eb;">${ci + 1}. ${cp.descripcion || ''}</span>
                    <span class="math-content" style="color:#9ca3af;"> → ${cp.resultado_dicho || ''}</span>
                    ${(!cp.correcto && cp.nota) ? `<div style="color:#fca5a5; font-size:13px; margin-top:2px;">${cp.nota}</div>` : ''}
                </div>
            </div>`).join('');
        return `
        <div class="details-card" style="padding:16px 18px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;">
                <div style="min-width:0;">
                    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                        ${codigo}
                        <span style="font-weight:700; font-size:1.05rem; overflow-wrap:anywhere;">${c.titulo || 'Ejercicio'}</span>
                    </div>
                    <div style="color:#9ca3af; font-size:13px; margin-top:3px;">${c.asignatura || ''}${c.tema ? ' · ' + c.tema : ''} · ${fecha}</div>
                </div>
                <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap; justify-content:flex-end;">
                    ${modeloBadge}
                    <span class="badge" style="background:${v.color}22; color:${v.color}; border:1px solid ${v.color}55; white-space:nowrap;">${v.txt}</span>
                </div>
            </div>
            ${c.es_fallback ? `<div style="background:#3a1a0e; border:1px solid #9a3412; color:#fdba74; border-radius:8px; padding:8px 12px; margin-top:10px; font-size:13px;">⚠ Corregido por el modelo de <b>respaldo</b> (${c.modelo || 'flash-lite'}), bastante menos fiable — el principal estaba ocupado. Verifica esta corrección o vuelve a lanzarla más tarde.</div>` : ''}
            ${bajaConf ? `<div style="background:#3a2e12; border:1px solid #a16207; color:#fde68a; border-radius:8px; padding:8px 12px; margin-top:10px; font-size:13px;">⚠ Confianza de lectura ${confPct}%: puede que Gemini haya leído mal tu letra${c.motivo_baja_confianza ? ' — ' + c.motivo_baja_confianza : ''}. Revisa la transcripción antes de fiarte de la corrección.</div>` : ''}
            ${c.dudas ? `<div style="background:#3a2e12; border:1px solid #a16207; color:#fde68a; border-radius:8px; padding:8px 12px; margin-top:10px; font-size:13px;">⚠ Gemini tuvo dudas al leer: ${c.mensaje_duda || 'revisa la transcripción'}</div>` : ''}
            ${c.resumen ? `<div class="math-content" style="margin-top:12px; line-height:1.55; font-size:15px;">${c.resumen}</div>` : ''}
            ${checkpoints ? `<div style="margin-top:12px;"><div style="color:#9ca3af; font-size:13px; margin-bottom:4px;">Checkpoints:</div>${checkpoints}</div>` : ''}
            ${errores || (c.tiene_error ? '' : '<div style="color:#34d399; margin-top:10px;">Sin errores detectados. 👍</div>')}
            ${c.manuscrito ? `<details style="margin-top:12px;">
                <summary style="cursor:pointer; color:#93c5fd; font-size:14px;">📝 Lo que Gemini leyó de tu letra (verifícalo)</summary>
                <div class="math-content" style="margin-top:8px; background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:10px 12px; line-height:1.55;">${c.manuscrito}</div>
            </details>` : ''}
            <details style="margin-top:12px;">
                <summary style="cursor:pointer; color:#60a5fa; font-size:14px;">Ver análisis completo y enunciado</summary>
                <div style="margin-top:10px;">
                    <div style="color:#9ca3af; font-size:13px; margin-bottom:4px;">Enunciado (${c.codigo || 's/código'}):</div>
                    <div class="math-content" style="background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:10px 12px; line-height:1.5;">${(c.enunciado || '—')}</div>
                    <div style="color:#9ca3af; font-size:13px; margin:12px 0 4px;">Análisis paso a paso:</div>
                    <div class="math-content" style="line-height:1.55;">${parseMarkdown(c.analisis || '—')}</div>
                    ${c.exerc_id ? `<div style="color:#6b7280; font-size:12px; margin-top:10px;">Registro en Obsidian: <code>${c.exerc_id}</code></div>` : ''}
                </div>
            </details>
            <div style="margin-top:10px; display:flex; gap:10px; justify-content:flex-end; flex-wrap:wrap;">
                ${(c.reverso && c.id) ? `<button class="btn btn-sm" onclick="revertirCorreccion('${c.id}')" title="Deshace el efecto en tu perfil: usa esto si Gemini se equivocó al corregir" style="background:#7f1d1d; color:#fecaca; cursor:pointer; padding:4px 10px; font-size:12px;">✗ Mal corregido</button>` : ''}
                <button class="btn btn-sm" onclick="descartarCorreccion(${i})" style="background:#374151; color:#9ca3af; cursor:pointer; padding:4px 10px; font-size:12px;">Quitar de la lista</button>
            </div>
        </div>`;
    }).join('');
    cont.querySelectorAll('.math-content').forEach(el => renderMath(el));
    lucide.createIcons();
}

function descartarCorreccion(index) {
    fetch('/api/kg/correcciones', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index })
    }).then(() => fetchCorrecciones());
}

function revertirCorreccion(id) {
    if (!confirm('¿Marcar como MAL corregido? Se deshará el efecto en tu perfil (dominio y repasos) y se quitará de la lista.')) return;
    fetch('/api/kg/correcciones/revertir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
        .then(r => r.json())
        .then(res => {
            if (res.error) { alert('No se pudo revertir: ' + res.error); return; }
            fetchCorrecciones();
        })
        .catch(e => alert('Error: ' + e.message));
}

function limpiarCorrecciones() {
    if (!confirm('¿Vaciar la lista de correcciones? (No borra el registro de Obsidian)')) return;
    fetch('/api/kg/correcciones', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: '{}' })
        .then(() => fetchCorrecciones());
}

function fetchPlan() {
    // Compatibilidad con controles antiguos: el planificador ya no decide
    // el contenido de las sesiones ni se consulta desde la interfaz.
    lastPlan = null;
    return Promise.resolve(null);
}

function renderViabilidad(data) {
    document.getElementById('plan-semaforo').innerHTML =
        `<span style="color:#93c5fd;">ℹ️ RECOMENDACIONES ABIERTAS</span>
         <span style="color:#9ca3af; font-weight:400; font-size:14px;"> — elige una, varias, otra cosa o ninguna; no hay una cuota que cumplir</span>`;

    window.lastPlanViability = data.viabilidad || [];
    renderPlanRecommendation(data.recomendacion);
    const filas = data.viabilidad.sort((a, b) => a.fecha.localeCompare(b.fecha));
    let html = `<tr style="color:#9ca3af; text-align:left; border-bottom:1px solid #2d3748;">
        <th style="padding:8px;">Examen</th><th>Fecha / preparación</th><th>Fase</th><th>Riesgo</th><th>Pendientes</th><th>Estado</th></tr>`;
    filas.forEach(f => {
        html += `<tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:8px;">${f.materia} <span style="color:#6b7280;">${f.desc}</span></td>
                        <td>${f.fecha}<br><small>Prep: ${f.fecha_preparacion || "—"}</small></td>
            <td>${f.fase || "—"}</td>
            <td>${Math.round((f.riesgo || 0) * 100)}%<br><small>${f.preparado ? "preparado" : "en progreso"}</small></td>
            <td>${f.pendientes}/${f.total}</td>
            <td>${f.preparado ? "Preparado" : "En progreso"}</td></tr>`;
    });
    document.getElementById('plan-viabilidad').innerHTML = html;
}

function renderPlanRecommendation(rec) {
    const target = document.getElementById('plan-recomendacion');
    if (!target || !rec) return;
    const main = rec.principal;
    if (!main) { target.textContent = rec.justificacion || 'No hay recomendación disponible.'; return; }
    window.currentRecommendedMateria = main.materia;
    const materias = (window.lastPlanViability || []).map(x => x.materia).filter((v, i, a) => a.indexOf(v) === i);
    const options = materias.map(m => `<option value="${m}" ${m === main.materia ? 'selected' : ''}>${m}</option>`).join('');
    const simulacro = rec.simulacro ? `<button class="btn btn-primary" onclick='startRecommendedSimulation(${JSON.stringify(rec.simulacro)})'>Explorar ${rec.simulacro.problemas} problemas (sin cronómetro)</button>` : '';
    target.innerHTML = `<strong>Sugerencia destacada: ${main.materia}</strong> · ${rec.accion}<br><small>${rec.justificacion} ${rec.por_que || ''}</small><div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">${simulacro}<label>Ver sugerencias de otra asignatura:</label><select id="plan-priority-select" style="background:#0a0b0e;color:white;border:1px solid #334155;padding:5px;">${options}</select><button class="btn" onclick="applyPlanPriority()" style="background:#374151;color:white;padding:5px 10px;">Actualizar opciones</button></div>`;
}

function startRecommendedSimulation(config) {
    const temas = config.temas?.length ? '&temas=' + config.temas.join(',') : '';
    fetch(`/api/kg/simulacro?materia=${encodeURIComponent(config.materia)}&n=${config.problemas}${temas}`)
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            kgQuizData = (data.problemas || []).map(p => ({ ...p, resultado: null }));
            if (!kgQuizData.length) throw new Error('No hay problemas de examen disponibles para esta selección.');
            switchTab('quiz');
            document.getElementById('kgquiz-setup').style.display = 'none';
            document.getElementById('kgquiz-area').style.display = 'block';
            kgQuizSecuencial = true;
            kgQuizIdx = 0;
            kgQuizInicio = Date.now();
            renderKgQuizSecuencial();
            clearInterval(kgQuizInterval);
            const timer = document.getElementById('kgquiz-timer');
            if (timer) { timer.textContent = 'Sin cronómetro'; timer.style.color = '#93c5fd'; }
        }).catch(e => alert('No se pudo preparar el simulacro: ' + e.message));
}

function applyPlanPriority() {
    const materia = document.getElementById('plan-priority-select')?.value || '';
    const query = materia ? `?materia=${encodeURIComponent(materia)}` : '';
    fetch('/api/kg/plan' + query).then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.error);
        renderViabilidad(data); renderPlanHoy(data.plan);
    }).catch(e => alert('No se pudieron actualizar las sugerencias: ' + e.message));
}
let lastPlan = null;

function renderPlanHoy(plan) {
    lastPlan = plan;
    let html = '<p style="color:#9ca3af; margin-top:0;">Son sugerencias, no una lista de tareas. Puedes profundizar en una sola, combinar varias, elegir otra cosa o cerrar cuando quieras.</p>';
    const listos = plan.problemas_listos || [];
    if (listos.length) {
        html += `<div style="background:rgba(52,211,153,0.10); border:1px solid rgba(52,211,153,0.45); border-radius:8px; padding:14px 16px; margin:12px 0 18px;">
            <h3 style="color:#6ee7b7; margin:0 0 6px;">🚦 Toca practicar (${listos.length} desbloqueados)</h3>
            <p style="color:#d1d5db; margin:0 0 10px;">${escapeSearchHtml(plan.practica?.mensaje || 'Ya has superado todos los nodos necesarios de estos problemas.')}</p>
            <p style="color:#9ca3af; font-size:12px; margin:0 0 10px;">${escapeSearchHtml(plan.practica?.criterio || 'Todos los nodos requeridos tienen dominio efectivo ≥ 0.7.')}</p>`;
        listos.forEach(p => {
            const req = (p.nodos_requeridos || []).map(n => `<code style="color:#93c5fd;">${escapeSearchHtml(n)}</code>`).join(', ');
            html += `<div style="background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:10px 12px; margin:8px 0;">
                <div style="color:#d1d5db;"><strong>${escapeSearchHtml(p.id)}</strong> · ${escapeSearchHtml(p.titulo || 'Problema sin título')} <span style="color:#6b7280;">[${escapeSearchHtml(p.materia || '')}]</span></div>
                <div style="color:#6b7280; font-size:12px; margin:5px 0;">Nodos superados: ${req}</div>
                <div style="display:flex; gap:6px; flex-wrap:wrap;">
                    <button class="btn btn-sm" onclick="openMode2_Whisper('${p.id}')" style="background:#1d4ed8; color:white; padding:5px 10px; font-size:11px;">🎙 Resolver con voz</button>
                    <button class="btn btn-sm" onclick="openMode3_Library('${p.id}')" style="background:#059669; color:white; padding:5px 10px; font-size:11px;">📖 Resolver en silencio</button>
                </div>
            </div>`;
        });
        html += '</div>';
    }
    if (plan.repasos && plan.repasos.length) {
        html += `<h3 style="color:#fbbf24; margin-bottom:10px;">Opciones de repaso (${plan.repasos.length})</h3>`;
        plan.repasos.forEach(r => { html += planItemHtml(r, true); });
    } else {
        html += '<p style="color:#6b7280;">No hay repasos vencidos entre las opciones actuales.</p>';
    }
    html += `<h3 style="color:#60a5fa; margin: 15px 0 10px;">Opciones de exploración (${plan.nuevos.length})</h3>`;
    if (!plan.nuevos.length) html += '<p style="color:#9ca3af;">No hay conceptos nuevos recomendados ahora.</p>';
    plan.nuevos.forEach(n => { html += planItemHtml(n, false); });
    if (plan.implicitos && plan.implicitos.length) {
        html += `<p style="color:#6b7280; font-size:13px; margin-top:12px;">Al explorar algunas opciones también puedes repasar: ${plan.implicitos.join(', ')}</p>`;
    }
    if (plan.repasos_omitidos || plan.nuevos_omitidos) {
        const total = (plan.repasos_omitidos || 0) + (plan.nuevos_omitidos || 0);
        html += `<p style="color:#6b7280; font-size:12px; margin-top:12px;">Hay ${total} opciones adicionales ocultas para no saturar la vista. No se han descartado por tiempo.</p>`;
    }
    document.getElementById('plan-hoy').innerHTML = html;
    document.querySelectorAll('#plan-hoy .math-content').forEach(el => renderMath(el));
    lucide.createIcons();
    cargarAvisos(plan);
}

function cargarAvisos(plan) {
    // Tus errores pasados en los nodos de hoy, mostrados antes de practicar
    const ids = [...(plan.repasos || []), ...(plan.nuevos || [])].map(x => x.id);
    if (!ids.length) return;
    fetch('/api/kg/avisos?nodos=' + ids.join(','))
        .then(r => r.json())
        .then(avisos => {
            ids.forEach(id => {
                const lista = avisos[id];
                if (!lista || !lista.length) return;
                const objetivo = document.getElementById('leccion-' + id.replace(/\./g, '-'));
                if (!objetivo) return;
                const div = document.createElement('div');
                div.style.cssText = 'background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.35); border-radius:6px; padding:10px 14px; margin:8px 0; font-size:13px;';
                div.innerHTML = `<strong style="color:#fbbf24;">⚠ Errores conocidos en este nodo:</strong><ul style="margin:6px 0 0 18px; color:#d1d5db;">` +
                    lista.slice(0, 4).map(e => {
                        const etiqueta = e.tipo === 'tipico'
                            ? `<span style="color:#9ca3af; font-size:11px;">[${e.fuente || 'otros años'}]</span> `
                            : '<span style="color:#f87171; font-size:11px;">[tuyo]</span> ';
                        return `<li>${etiqueta}<strong>${e.titulo}</strong>${e.como_evitarlo ? ' — ' + e.como_evitarlo : ''}</li>`;
                    }).join('') + '</ul>';
                objetivo.parentNode.insertBefore(div, objetivo);
            });
        })
        .catch(() => {});
}

function planItemHtml(item, esRepaso) {
    const borde = esRepaso ? '#fbbf24' : '#60a5fa';
    let extra = '';
    if (item.fuentes) extra += `<div style="color:#9ca3af; font-size:13px; margin:4px 0;">📖 ${item.fuentes}</div>`;
    if (esRepaso && item.retraso) extra += `<div style="color:#9ca3af; font-size:13px;">${item.retraso} días de retraso</div>`;
    if (item.cubre && item.cubre.length) extra += `<div style="color:#6b7280; font-size:12px;">Repasa implícitamente: ${item.cubre.join(', ')}</div>`;

    const nombreEsc = (item.nombre || '').replace(/'/g, "\\'");
    const materiaEsc = (item.materia || '').replace(/'/g, "\\'");

    let probs = '';
    (item.problemas || []).forEach(p => {
        const tag = p.hecho ? ' <span style="color:#34d399; font-size:11px;">(ya hecho)</span>' : '';
        const pIdEsc = p.id;
        const nIdEsc = item.id;
        probs += `<details style="margin:8px 0; background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:10px 14px;">
            <summary style="cursor:pointer; color:#d1d5db; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <span>Problema ${p.numero} — ${p.titulo} <span style="color:#6b7280;">(${p.hoja})</span>${tag}</span>
                <span style="display:inline-flex; gap:6px;" onclick="event.stopPropagation()">
                    <button class="btn btn-sm" onclick="openMode2_Whisper('${pIdEsc}', '${nIdEsc}')" title="Resolver narrando en voz alta con Whisper" style="background:#1d4ed8; color:white; padding:4px 9px; font-size:11px; display:inline-flex; align-items:center; gap:4px; border-radius:4px;"><i data-lucide="mic" style="width:12px;height:12px;"></i> Whisper</button>
                    <button class="btn btn-sm" onclick="openMode3_Library('${pIdEsc}', '${nIdEsc}')" title="Resolver en silencio en la biblioteca" style="background:#059669; color:white; padding:4px 9px; font-size:11px; display:inline-flex; align-items:center; gap:4px; border-radius:4px;"><i data-lucide="book-open" style="width:12px;height:12px;"></i> Biblioteca</button>
                </span>
            </summary>
            <div class="math-content" style="margin-top:8px; line-height:1.6; color:#d1d5db;">${p.enunciado.replace(/\n/g, '<br>')}</div>
        </details>`;
    });
    if (!(item.problemas || []).length) {
        probs = '<div style="color:#6b7280; font-size:13px; margin:6px 0;">Sin problemas en el banco: estudia la teoría y usa uno del tema.</div>';
    }

    return `<div style="background:#11141d; border-left:3px solid ${borde}; border-radius:8px; padding:14px 16px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <code style="color:${borde};">${item.id}</code> <strong>${item.nombre}</strong>
                <span style="color:#6b7280; font-size:13px;">[${item.materia || ''}]</span>
            </div>
            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                <button class="btn btn-primary" onclick="abrirCuadernoLeccion('${materiaEsc}', '${item.id}', '${nombreEsc}')" title="Abrir el Cuaderno Gemini de esta materia con el prompt socrático copiado" style="cursor:pointer; padding:6px 12px; display:inline-flex; align-items:center; gap:6px;">
                    <i data-lucide="book-open" style="width:14px;height:14px;"></i> Cuaderno Gemini
                </button>
                <button class="btn" onclick="verLeccion('${item.id}')" title="Ver resumen offline" style="background:#374151; color:white; cursor:pointer; padding:6px 10px;">Resumen</button>
                <button class="btn" onclick="registrarNodo('${item.id}', true)" style="background:#059669; color:white; cursor:pointer; padding:6px 10px;">✓ Sólido</button>
                <button class="btn" onclick="registrarNodo('${item.id}', false)" style="background:#dc2626; color:white; cursor:pointer; padding:6px 10px;">✗ Necesita refuerzo</button>
            </div>
        </div>
        ${extra}
        <div id="leccion-${item.id.replace(/\./g, '-')}" style="display:none; margin:10px 0; background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:14px; line-height:1.6;"></div>
        ${probs}
    </div>`;
}

function verLeccion(id) {
    const div = document.getElementById('leccion-' + id.replace(/\./g, '-'));
    if (div.style.display === 'block') { div.style.display = 'none'; return; }
    div.style.display = 'block';
    if (div.dataset.cargada) return;
    div.innerHTML = '<span style="color:#9ca3af;">Generando lección mínima (primera vez tarda ~20 s, luego queda cacheada)...</span>';
    fetch('/api/kg/leccion/' + id)
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            div.innerHTML = parseMarkdown(data.md);
            div.dataset.cargada = '1';
            renderMath(div);
        })
        .catch(e => { div.innerHTML = `<span style="color:#f87171;">Error: ${e.message}</span>`; });
}

// ---- Quiz cronometrado del knowledge graph ----
let kgQuizData = [];
let kgQuizInterval = null;
let kgQuizMaterias = null;
let kgQuizExamenes = null;
let kgQuizInicio = null;
let kgQuizSecuencial = true;
let kgQuizIdx = 0;
let kgQuizProblemStart = null;

// Escala de calidad graduada (0–1) compartida por el quiz y la sesión de estudio.
const CALIDAD_NIVELES = [
    { k: 'resuelto',  etiqueta: '✓ Resuelto',  calidad: 1.0,  exito: true,  color: '#059669', ayuda: 'Bien, camino correcto y terminado' },
    { k: 'desliz',    etiqueta: '≈ Desliz',    calidad: 0.75, exito: true,  color: '#16a34a', ayuda: 'Terminado pero mal por un desliz (concepto entendido)' },
    { k: 'a_medias',  etiqueta: '~ A medias',  calidad: 0.5,  exito: true,  color: '#ca8a04', ayuda: 'Ibas bien pero no llegaste al final' },
    { k: 'bloqueado', etiqueta: '✗ Bloqueado', calidad: 0.25, exito: false, color: '#ea580c', ayuda: 'Bloqueado o a medias equivocado (empuja prerrequisitos a repaso)' },
    { k: 'blanco',    etiqueta: '∅ En blanco', calidad: 0.0,  exito: false, color: '#dc2626', ayuda: 'En blanco' },
];

function onKgQuizModo() {
    const modo = document.getElementById('kgquiz-modo').value;
    const sel = document.getElementById('kgquiz-materia');
    if (modo === 'repaso') { sel.style.display = 'none'; return; }
    sel.style.display = 'inline-block';
    if (modo === 'diagnostico') {
        const pinta = () => {
            sel.innerHTML = '<option value="">Todas las materias</option>' +
                kgQuizMaterias.map(g => `<option value="${g.materia}">${g.curso}º · ${g.materia}</option>`).join('');
        };
        if (kgQuizMaterias) pinta();
        else fetch('/api/kg/grafos').then(r => r.json()).then(gs => { kgQuizMaterias = gs; pinta(); });
    } else { // simulacro
        const pinta = () => {
            sel.innerHTML = kgQuizExamenes.map((ex, i) =>
                `<option value="${i}">${ex.materia} — ${ex.descripcion || ex.fecha}</option>`).join('');
        };
        if (kgQuizExamenes) pinta();
        else fetch('/api/kg/examenes').then(r => r.json()).then(cfg => { kgQuizExamenes = (cfg.examenes || []).filter(ex => ex.planificar !== false); pinta(); });
    }
}

function startKgQuiz() {
    const modo = document.getElementById('kgquiz-modo').value;
    const n = document.getElementById('kgquiz-n').value;
    let url;
    if (modo === 'simulacro') {
        const ex = kgQuizExamenes ? kgQuizExamenes[parseInt(document.getElementById('kgquiz-materia').value)] : null;
        if (!ex) { alert('Selecciona un examen (configúralos en Plan de Estudio).'); return; }
        const temas = ex.temas ? '&temas=' + ex.temas.join(',') : '';
        url = `/api/kg/simulacro?materia=${encodeURIComponent(ex.materia)}&n=${n}${temas}`;
    } else {
        const materia = document.getElementById('kgquiz-materia').value;
        url = `/api/kg/quiz?n=${n}&modo=${modo}` + (modo === 'diagnostico' && materia ? '&materia=' + encodeURIComponent(materia) : '');
    }
    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            kgQuizData = (data.problemas || []).map(p => ({ ...p, resultado: null }));
            if (!kgQuizData.length) {
                alert(modo === 'repaso'
                    ? 'Aún no hay nodos aprendidos con problemas en el banco. Estudia algunas lecciones primero.'
                    : 'No hay problemas disponibles para esa selección (¿hay banco de esa materia?).');
                return;
            }
            kgQuizSecuencial = document.getElementById('kgquiz-secuencial').checked;
            document.getElementById('kgquiz-setup').style.display = 'none';
            document.getElementById('kgquiz-area').style.display = 'block';
            kgQuizInicio = Date.now();
            if (kgQuizSecuencial) { kgQuizIdx = 0; renderKgQuizSecuencial(); }
            else renderKgQuiz();
            startKgTimer(parseInt(document.getElementById('kgquiz-min').value) * 60);
        })
        .catch(e => alert('Error: ' + e.message));
}

// Botones de calidad (5 niveles) para un problema. `onclickBase` recibe el índice del nivel.
function botonesCalidad(onclickExpr, extra = '') {
    return CALIDAD_NIVELES.map((n, ni) =>
        `<button class="btn ${extra}" data-ni="${ni}" onclick="${onclickExpr(ni)}" title="${n.ayuda}"
            style="background:#374151; color:white; cursor:pointer; padding:6px 12px; font-size:13px;">${n.etiqueta}</button>`
    ).join('');
}

// --- Modo "todos a la vez" (cobertura rápida; el tiempo por problema se aproxima) ---
function renderKgQuiz() {
    let html = '';
    kgQuizData.forEach((q, i) => {
        html += `<div style="background:#11141d; border:1px solid #2d3748; border-radius:8px; padding:14px 16px; margin-bottom:12px;">
            <div style="color:#6b7280; font-size:12px; margin-bottom:6px;">${i + 1}. <code>${q.id}</code> ${q.nombre} [${q.materia}]</div>
            <div class="math-content" style="line-height:1.6;">${q.problema.enunciado.replace(/\n/g, '<br>')}</div>
            <div class="kgq-grades-${i}" style="display:flex; gap:8px; margin-top:10px; flex-wrap:wrap;">
                ${botonesCalidad(ni => `gradeKgQuiz(${i}, ${ni})`, `kgq-btn-${i}`)}
            </div>
        </div>`;
    });
    const cont = document.getElementById('kgquiz-problems');
    cont.innerHTML = html;
    cont.querySelectorAll('.math-content').forEach(el => renderMath(el));
}

function gradeKgQuiz(i, ni) {
    const n = CALIDAD_NIVELES[ni];
    kgQuizData[i].resultado = n.exito;
    kgQuizData[i].calidad = n.calidad;
    kgQuizData[i].calificadoEn = Date.now();
    document.querySelectorAll(`.kgq-btn-${i}`).forEach(b => b.style.background = '#374151');
    const btn = document.querySelector(`.kgq-btn-${i}[data-ni="${ni}"]`);
    if (btn) btn.style.background = n.color;
}

// --- Modo "un problema a la vez" (mide el tiempo limpio de cada problema) ---
function renderKgQuizSecuencial() {
    const i = kgQuizIdx;
    const cont = document.getElementById('kgquiz-problems');
    if (i >= kgQuizData.length) { finishKgQuiz(); return; }
    const q = kgQuizData[i];
    cont.innerHTML = `
        <div style="color:#6b7280; font-size:13px; margin-bottom:8px;">Problema ${i + 1} de ${kgQuizData.length}</div>
        <div style="background:#11141d; border:1px solid #2d3748; border-radius:8px; padding:14px 16px;">
            <div style="color:#6b7280; font-size:12px; margin-bottom:6px;"><code>${q.id}</code> ${q.nombre} [${q.materia}]</div>
            <div class="math-content" style="line-height:1.6;">${q.problema.enunciado.replace(/\n/g, '<br>')}</div>
        </div>
        <p style="color:#9ca3af; font-size:13px; margin:14px 0 6px;">Resuélvelo en papel, sin apuntes, y califícate:</p>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">${botonesCalidad(ni => `gradeKgQuizSeq(${ni})`)}</div>`;
    cont.querySelectorAll('.math-content').forEach(el => renderMath(el));
    kgQuizProblemStart = Date.now();
    window.scrollTo(0, 0);
}

function gradeKgQuizSeq(ni) {
    const n = CALIDAD_NIVELES[ni];
    const q = kgQuizData[kgQuizIdx];
    q.resultado = n.exito;
    q.calidad = n.calidad;
    q.segundos = Math.max(1, Math.round((Date.now() - kgQuizProblemStart) / 1000));
    kgQuizIdx++;
    renderKgQuizSecuencial();
}

function startKgTimer(segundos) {
    clearInterval(kgQuizInterval);
    let restante = segundos;
    const pinta = () => {
        const m = Math.floor(Math.abs(restante) / 60), s = Math.abs(restante) % 60;
        const el = document.getElementById('kgquiz-timer');
        el.textContent = (restante < 0 ? '-' : '') + `${m}:${s.toString().padStart(2, '0')}`;
        el.style.color = restante < 0 ? '#f87171' : (restante < 300 ? '#fbbf24' : '#34d399');
    };
    pinta();
    kgQuizInterval = setInterval(() => { restante--; pinta(); }, 1000);
}

function finishKgQuiz() {
    const calificado = q => q.calidad !== undefined && q.calidad !== null;
    if (!kgQuizSecuencial) {
        const sinCalificar = kgQuizData.filter(q => !calificado(q)).length;
        if (sinCalificar && !confirm(`Hay ${sinCalificar} problemas sin calificar (se ignorarán). ¿Terminar?`)) return;
    }
    clearInterval(kgQuizInterval);
    const calificados = kgQuizData.filter(calificado);
    if (!kgQuizSecuencial) {
        // Modo "todos a la vez": el tiempo por problema se aproxima por el intervalo
        // entre calificaciones sucesivas (en orden de calificación). En modo secuencial
        // ya viene el tiempo limpio medido problema a problema.
        const enOrden = calificados.filter(q => q.calificadoEn).slice().sort((a, b) => a.calificadoEn - b.calificadoEn);
        let prev = kgQuizInicio || (enOrden[0] && enOrden[0].calificadoEn);
        enOrden.forEach(q => { q.segundos = Math.max(1, Math.round((q.calificadoEn - prev) / 1000)); prev = q.calificadoEn; });
    }
    const registros = [];
    calificados.forEach(q => {
        if (q.problema && q.problema.id) {
            registros.push(fetch('/api/kg/problema', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: q.problema.id, exito: q.resultado, calidad: q.calidad,
                    segundos: q.segundos,
                    veredicto: q.calidad >= 0.9 ? 'resuelto' : (q.calidad >= 0.5 ? 'hueco_teorico' : 'incorrecto'),
                })
            }));
        } else {
            registros.push(fetch('/api/kg/registrar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: [q.id], exito: q.resultado, calidad: q.calidad, segundos: q.segundos })
            }));
        }
    });
    Promise.all(registros).then(() => {
        const bien = calificados.filter(q => q.resultado).length;
        alert(`Quiz registrado: ${bien}/${calificados.length} resueltos. Tu perfil y tus repasos se han actualizado.`);
        document.getElementById('kgquiz-area').style.display = 'none';
        document.getElementById('kgquiz-setup').style.display = 'flex';
        kgQuizData = [];
        fetchGamificacion();
    });
}

// ---- Sesión de estudio guiada ----
let sesionItems = [];
let sesionIdx = 0;
let sesionStats = { bien: 0, mal: 0, saltados: 0 };
let sesionPreview = [];
let sesionContext = { energy: 3, focus: 3, available_minutes: 60, goal: 'aprender', obstacle: '' };
let sesionSessionId = null;
let sesionProblemResults = {};
let sesionCompleted = false;

let paseoSessionId = null;
let paseoMode = 'walk_review';

function startWalkSession() {
    if (!lastPlan) { alert('Espera a que carguen las sugerencias.'); return; }
    const items = [...(lastPlan.repasos || []), ...(lastPlan.nuevos || [])];
    if (!items.length) { alert('No hay sugerencias disponibles.'); return; }
    paseoSessionId = null;
    document.getElementById('sesion-overlay').style.display = 'block';
    document.getElementById('sesion-fase').textContent = 'Preparación del paseo o bus';
    document.getElementById('sesion-progreso').textContent = 'Opciones abiertas';
    document.getElementById('sesion-barra').style.width = '0%';
    renderWalkPreparation();
}

function renderWalkPreparation() {
    const cont = document.getElementById('sesion-contenido');
    cont.innerHTML = `<div class="session-prep">
        <div class="session-prep-intro"><span class="hub-eyebrow">🎧📱 PASEO / BUS DE ESTUDIO</span><h2>Estudiar teoría con la IA</h2><p>La aplicación preparará un encargo completo para NotebookLM. En un paseo puedes hablar; en el bus puedes leer y responder por texto. En ambos casos, empieza por la teoría y cierra con el informe estructurado.</p></div>
        <div class="session-prep-field"><label for="walk-mode-select">Tipo de conversación</label><select id="walk-mode-select" style="width:100%; padding:10px; background:#11141d; color:white; border:1px solid #2d3748; border-radius:6px;" onchange="loadWalkPreparation(this.value)"><option value="walk_introduction" selected>Teoría guiada (paseo o bus)</option><option value="walk_rescue">Rescate conceptual</option><option value="walk_review">Repaso general</option><option value="walk_oral_exam">Examen oral</option></select></div>
        <div id="walk-prep-content" style="margin-top:16px;"><div class="loading-spinner">Preparando el paseo…</div></div>
    </div>`;
    lucide.createIcons();
    loadWalkPreparation('walk_introduction');
}

function loadWalkPreparation(mode) {
    paseoMode = mode;
    const target = document.getElementById('walk-prep-content');
    if (!target) return;
    target.innerHTML = '<div class="loading-spinner">Preparando el contexto…</div>';
    const materia = window.currentRecommendedMateria || '';
    const materiaQuery = materia ? `&materia=${encodeURIComponent(materia)}` : '';
    fetch(`/api/study/walk/prepare?mode=${encodeURIComponent(mode)}${materiaQuery}`)
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            target.innerHTML = `<div class="details-card" style="padding:16px;"><h3>${data.mode_info.nombre}</h3><p>${data.mode_info.descripcion}</p><p style="color:#9ca3af;">${data.mode_info.reparto}</p><div style="display:flex; gap:8px; flex-wrap:wrap; margin:12px 0;"><button class="btn" onclick="copyWalkPrompt()" style="background:#374151;color:white;">📋 Copiar prompt</button><button class="btn btn-primary" onclick="beginWalkSession()">Preparar para el móvil</button></div><textarea id="walk-prompt" rows="12" readonly style="width:100%; box-sizing:border-box; background:#0a0b0e; color:#d1d5db; border:1px solid #1e293b; border-radius:6px; padding:12px; font-family:monospace; font-size:12px;"></textarea><p style="color:#fbbf24; font-size:13px; margin-bottom:0;">Al terminar, escribe exactamente: «CIERRE ESTRUCTURADO DEL PASEO». Después copia el JSON y pégalo en la aplicación.</p></div>`;
            document.getElementById('walk-prompt').value = data.prompt || '';
            window.walkPrepared = data;
        }).catch(error => { target.innerHTML = `<p style="color:#f87171;">No se pudo preparar el paseo: ${error.message}</p>`; });
}

function copyWalkPrompt() {
    const prompt = document.getElementById('walk-prompt')?.value || '';
    if (!prompt) { alert('Todavía no hay ningún prompt preparado.'); return; }
    if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(prompt)
            .then(() => alert('Prompt copiado. Ya puedes pegarlo en NotebookLM.'))
            .catch(() => alert('Selecciona y copia el prompt manualmente.'));
        return;
    }
    const area = document.getElementById('walk-prompt');
    area?.select();
    try { document.execCommand('copy'); alert('Prompt copiado. Ya puedes pegarlo en NotebookLM.'); }
    catch (error) { alert('Selecciona y copia el prompt manualmente.'); }
}

function problemaListoEnPlan(problemId) {
    return (lastPlan?.problemas_listos || []).find(p => p.id === problemId) || null;
}

async function shareWalkPrompt() {
    const prompt = document.getElementById('walk-prompt')?.value || '';
    if (!prompt) { alert('Todavía no hay ningún prompt preparado.'); return; }
    if (navigator.share) {
        try {
            await navigator.share({ title: 'Paseo de estudio', text: prompt });
            return;
        } catch (error) {
            if (error?.name === 'AbortError') return;
        }
    }
    copyWalkPrompt();
}

function beginWalkSession() {
    const prepared = window.walkPrepared;
    if (!prepared) return;
    const ids = (prepared.preview || []).map(x => x.id);
    fetch('/api/study/sessions', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
        materia: prepared.materia || '', plan_ids: ids, problem_ids: prepared.problem_ids || [], session_type: paseoMode,
        available_minutes: prepared.minutos || 60, goal: 'consolidar', preview_ack: true
    })}).then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.error);
        paseoSessionId = data.session.id;
        return fetch(`/api/study/walks/${paseoSessionId}/remote-instructions?transport=notebooklm`).then(r => r.json());
    }).then(data => {
        if (data.error) throw new Error(data.error);
        renderWalkClosing(data.prompt || '');
    }).catch(error => alert('No se pudo iniciar el paseo: ' + error.message));
}

function renderWalkClosing(remotePrompt) {
    const cont = document.getElementById('sesion-contenido');
    document.getElementById('sesion-fase').textContent = 'Paseo en marcha';
    document.getElementById('sesion-progreso').textContent = 'Prompt listo para el móvil';
    document.getElementById('sesion-barra').style.width = '50%';
    cont.innerHTML = `<div class="session-close-card"><div class="session-close-intro"><span class="hub-eyebrow">PASEO PREPARADO</span><h2>Prompt listo para NotebookLM</h2><p>Comparte este prompt con el móvil o cópialo y pégalo en tu NotebookLM. Al terminar, escribe exactamente <strong>«CIERRE ESTRUCTURADO DEL PASEO»</strong>. Después copia únicamente el JSON final y pégalo abajo.</p></div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;"><button class="btn btn-primary" onclick="shareWalkPrompt()">📱 Enviar al móvil</button><button class="btn" onclick="copyWalkPrompt()" style="background:#374151;color:white;">📋 Copiar prompt</button></div><textarea id="walk-prompt" rows="14" readonly style="width:100%; box-sizing:border-box; margin-top:14px; background:#0a0b0e; color:#d1d5db; border:1px solid #1e293b; border-radius:6px; padding:12px; font-family:monospace; font-size:12px;"></textarea><details open style="margin-top:18px;"><summary style="cursor:pointer;color:#9ca3af;">Pegar el cierre de NotebookLM</summary><div class="session-reflection-block" style="margin-top:10px;"><label for="walk-report-json">Informe JSON final</label><textarea id="walk-report-json" rows="10" placeholder="Pega aquí únicamente el JSON final, sin texto alrededor."></textarea></div><button class="btn session-finish-btn" onclick="closeWalkSession()" style="background:#374151;color:white;">Guardar paseo y generar apuntes LaTeX</button></details></div>`;
    document.getElementById('walk-prompt').value = remotePrompt || window.walkPrepared?.prompt || '';
}

function copyRemoteWalkPrompt() {
    const prompt = document.getElementById('walk-remote-prompt')?.value || '';
    navigator.clipboard?.writeText(prompt).then(() => alert('Instrucciones copiadas.')).catch(() => alert('Selecciona y copia las instrucciones manualmente.'));
}

function pollRemoteWalkClose() {
    if (!paseoSessionId || !document.getElementById('sesion-overlay') || document.getElementById('sesion-overlay').style.display === 'none') return;
    fetch(`/api/study/walks/${paseoSessionId}/status`).then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.error);
        if (data.ready) {
            finishRemoteWalkUi(data);
            return;
        }
        window.setTimeout(pollRemoteWalkClose, 4000);
    }).catch(error => {
        const status = document.getElementById('walk-remote-status');
        if (status) status.textContent = `Esperando el cierre remoto (${error.message})`;
        window.setTimeout(pollRemoteWalkClose, 8000);
    });
}

function finishRemoteWalkUi(data) {
    document.getElementById('sesion-fase').textContent = 'Paseo guardado';
    document.getElementById('sesion-progreso').textContent = data.session?.apuntes_error ? 'Grafo actualizado; revisar apuntes' : 'Grafo y apuntes actualizados';
    document.getElementById('sesion-barra').style.width = '100%';
    const files = data.session?.latex_files || data.session?.apuntes?.latex_files || [];
    const noteText = data.session?.apuntes_error
        ? `<p style="color:#fbbf24;">El grafo se actualizó, pero no se pudieron generar los apuntes LaTeX: ${data.session.apuntes_error}</p>`
        : `<p>También se actualizaron los apuntes personales LaTeX${files.length ? ` (${files.length} archivo${files.length === 1 ? '' : 's'} generado${files.length === 1 ? '' : 's'}).` : '.'}</p>`;
    document.getElementById('sesion-contenido').innerHTML = `<div class="session-saved"><h2>✅ Paseo guardado</h2><p>${data.applied?.length || 0} conceptos incorporados al grafo.</p>${noteText}<button class="btn btn-primary" onclick="exitSesion()">Volver al centro</button></div>`;
    fetchHubStatus(); loadStudySubjectCards(); fetchGamificacion();
}

function closeWalkSession() {
    const raw = document.getElementById('walk-report-json')?.value || '';
    let report;
    try { report = JSON.parse(raw); } catch (error) { alert('El informe no es JSON válido. Pide a la voz que lo genere sin texto adicional.'); return; }
    const button = document.querySelector('.session-finish-btn');
    if (button) { button.disabled = true; button.textContent = 'Actualizando…'; }
    fetch(`/api/study/walks/${paseoSessionId}/close`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({report}) })
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            finishRemoteWalkUi(data);
        }).catch(error => { if (button) { button.disabled = false; button.textContent = 'Guardar cierre y actualizar el grafo'; } alert('No se pudo guardar el paseo: ' + error.message); });
}

function startSesion() {
    if (!lastPlan) { alert('Espera a que carguen las sugerencias.'); return; }
    const items = [
        ...(lastPlan.repasos || []).map(x => ({ ...x, tipo: 'repaso' })),
        ...(lastPlan.nuevos || []).map(x => ({ ...x, tipo: 'nuevo' }))
    ];
    if (!items.length) { alert('No hay sugerencias disponibles.'); return; }
    sesionItems = items;
    sesionIdx = 0;
    sesionStats = { bien: 0, mal: 0, saltados: 0 };
    sesionPreview = [];
    sesionSessionId = null;
    sesionCompleted = false;
    sesionContext = { energy: 3, focus: 3, available_minutes: lastPlan.minutos || 60, goal: 'aprender', obstacle: '' };
    document.getElementById('sesion-overlay').style.display = 'block';
    document.getElementById('sesion-fase').textContent = 'Preparación';
    renderSesionPreparacion();
}

function renderSesionPreparacion() {
    const cont = document.getElementById('sesion-contenido');
    document.getElementById('sesion-progreso').textContent = 'Antes de empezar';
    document.getElementById('sesion-barra').style.width = '0%';
    cont.innerHTML = `<div class="session-prep">
        <div class="session-prep-intro">
            <span class="hub-eyebrow"><i data-lucide="compass"></i> PREPARA TU ATENCIÓN</span>
            <h2>Una sesión buena empieza antes de abrir la teoría</h2>
            <p>Cuéntame cómo vienes y mira las opciones. Puedes trabajar una, varias, cambiar de idea o cerrar cuando quieras; nada de esto sustituye tu propio razonamiento.</p>
        </div>
        <div class="session-prep-grid">
            <div class="session-prep-field">
                <label>¿Cuánta energía tienes?</label>
                <div class="session-choice-row" id="session-energy-choices">
                    ${sessionChoiceButtons('energy', [{v:1,t:'Muy baja'}, {v:2,t:'Baja'}, {v:3,t:'Normal'}, {v:4,t:'Buena'}, {v:5,t:'Alta'}], 3)}
                </div>
            </div>
            <div class="session-prep-field">
                <label>¿Cuánto foco tienes ahora?</label>
                <div class="session-choice-row" id="session-focus-choices">
                    ${sessionChoiceButtons('focus', [{v:1,t:'Disperso'}, {v:2,t:'Costoso'}, {v:3,t:'Normal'}, {v:4,t:'Bueno'}, {v:5,t:'Profundo'}], 3)}
                </div>
            </div>
            <div class="session-prep-field session-prep-inline">
                <label for="session-goal-select">Objetivo principal</label>
                <select id="session-goal-select" onchange="sesionContext.goal=this.value">
                    <option value="aprender">Aprender algo nuevo</option>
                    <option value="consolidar">Consolidar lo estudiado</option>
                    <option value="examen">Entrenar para examen</option>
                </select>
            </div>
        </div>
        <div class="session-obstacle-field">
            <label for="session-obstacle-input">¿Hay algún obstáculo que deba tener en cuenta? <span>(opcional)</span></label>
            <input id="session-obstacle-input" type="text" placeholder="Ej.: estoy cansado, me cuesta empezar, tengo poco tiempo…" oninput="sesionContext.obstacle=this.value">
        </div>
        <div class="session-preview-heading"><div><h3><i data-lucide="binoculars"></i> Opciones para explorar</h3><p>Mira el mapa general: qué aparece, por qué y cómo se conecta. Puedes escoger cualquier opción y no tienes que recorrerlas todas.</p></div><span class="preview-count" id="session-preview-count">${sesionItems.length} opciones</span></div>
        <div id="session-preview-list" class="session-preview-list"><div class="loading-spinner">Preparando el preview…</div></div>
        <div id="session-rail-hint" class="session-rail-hint"></div>
        <div class="session-prep-footer"><label class="session-check"><input id="session-preview-ack" type="checkbox"> He visto el terreno y puedo explicar qué voy a trabajar.</label><button class="btn btn-primary" onclick="confirmSessionStart()"><i data-lucide="play"></i> Empezar la práctica</button></div>
    </div>`;
    lucide.createIcons();
    fetch('/api/study/prepare')
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            sesionPreview = data.preview || [];
            renderSesionPreview();
            if (data.skill) renderRailHint(data.skill);
        })
        .catch(error => { document.getElementById('session-preview-list').innerHTML = `<div class="no-tasks">No se pudo preparar el preview: ${error.message}</div>`; });
}

function sessionChoiceButtons(name, choices, selected) {
    return choices.map(c => `<button type="button" class="session-choice ${c.v === selected ? 'selected' : ''}" onclick="selectSessionChoice('${name}', ${c.v}, this)"><strong>${c.v}</strong><span>${c.t}</span></button>`).join('');
}

function selectSessionChoice(name, value, button) {
    sesionContext[name] = value;
    button.parentElement.querySelectorAll('.session-choice').forEach(b => b.classList.remove('selected'));
    button.classList.add('selected');
}

function renderSesionPreview() {
    const list = document.getElementById('session-preview-list');
    if (!list) return;
    if (!sesionPreview.length) { list.innerHTML = '<div class="no-tasks">No hay preview disponible para este plan.</div>'; return; }
    list.innerHTML = sesionPreview.map((p, index) => {
        const prereqs = p.prerequisitos?.length ? `<div class="preview-relations"><span>Conecta con</span>${p.prerequisitos.map(x => `<em>${x.nombre}</em>`).join('')}</div>` : '<div class="preview-relations muted">Punto de entrada o prerrequisitos ya consolidados</div>';
        const pacerOptions = Object.entries({P:'Procedimental', A:'Análoga', C:'Conceptual', E:'Evidencia', R:'Referencia'}).map(([code, name]) => `<option value="${code}" ${p.pacer?.codigo === code ? 'selected' : ''}>${code} · ${name}</option>`).join('');
        return `<article class="preview-card">
            <div class="preview-card-number">${index + 1}</div><div class="preview-card-main">
                <div class="preview-card-top"><div><span class="preview-type ${p.tipo}">${p.tipo === 'nuevo' ? 'NUEVO' : 'REPASO'}</span><h4>${p.nombre}</h4><small>${p.materia || ''}</small></div><div class="preview-pacer"><label>PACER</label><select onchange="overridePacer('${p.id}', this.value)">${pacerOptions}</select></div></div>
                <p>${p.descripcion || p.motivo}</p><div class="preview-reason">${p.motivo}</div>${prereqs}
            </div>
        </article>`;
    }).join('');
}

function overridePacer(nodeId, code) {
    const item = sesionPreview.find(x => x.id === nodeId);
    if (item) item.pacer = { ...(item.pacer || {}), ...{ codigo: code, nombre: ({P:'Procedimental',A:'Análoga',C:'Conceptual',E:'Evidencia',R:'Referencia'})[code], estimado: false } };
    fetch('/api/study/pacer', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({node_id: nodeId, code}) }).catch(() => {});
}

function confirmSessionStart() {
    const ack = document.getElementById('session-preview-ack');
    if (!ack?.checked) { alert('Marca primero que has visto el preview. Son solo unos segundos y ayuda a orientar la sesión.'); return; }
    const energy = sesionContext.energy;
    const focus = sesionContext.focus;
    sesionContext.obstacle = document.getElementById('session-obstacle-input')?.value || '';
    // La energía y el foco quedan registrados como contexto, pero nunca
    // recortan ni convierten las recomendaciones en una obligación.
    const payload = { ...sesionContext, plan_ids: sesionItems.map(x => x.id), preview_ack: true };
    fetch('/api/study/sessions', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            sesionSessionId = data.session.id;
            document.getElementById('sesion-fase').textContent = energy <= 2 ? 'Modo ligero' : 'Práctica activa';
            renderSesionPaso();
        })
        .catch(error => alert('No se pudo iniciar la sesión: ' + error.message));
}

function exitSesion() {
    document.getElementById('sesion-overlay').style.display = 'none';
    loadStudySubjectCards();
    fetchGamificacion();
}

function renderSesionPaso() {
    const total = sesionItems.length;
    const cont = document.getElementById('sesion-contenido');
    document.getElementById('sesion-fase').textContent = 'Práctica activa';
    document.getElementById('sesion-progreso').textContent = `Opción ${Math.min(sesionIdx + 1, total)} / ${total} · puedes saltar o cerrar`;
    document.getElementById('sesion-barra').style.width = `${(sesionIdx / total) * 100}%`;

    if (sesionIdx >= total) {
        renderSesionCierre();
        return;
    }

    const it = sesionItems[sesionIdx];
    const esNuevo = it.tipo === 'nuevo';
    const preview = sesionPreview.find(p => p.id === it.id) || {};
    const pacer = preview.pacer || { codigo: 'C', nombre: 'Conceptual', accion: 'Explícalo con tus palabras y relaciónalo con algo que ya conozcas.' };
    const badge = esNuevo
        ? '<span style="background:#1d4ed8; color:white; padding:3px 10px; border-radius:999px; font-size:12px;">SUGERENCIA NUEVA</span>'
        : '<span style="background:#b45309; color:white; padding:3px 10px; border-radius:999px; font-size:12px;">SUGERENCIA DE REPASO</span>';

    let probs = '';
    (it.problemas || []).forEach((p, j) => {
        probs += `<div style="background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:12px 14px; margin:8px 0;">
            <div style="color:#9ca3af; font-size:12px; margin-bottom:6px;">Problema ${p.numero} — ${p.titulo} (${p.hoja})${p.hecho ? ' <span style="color:#34d399;">(ya hecho antes)</span>' : ''}</div>
            <div class="math-content" style="line-height:1.6;">${p.enunciado.replace(/\n/g, '<br>')}</div>
            <div style="margin-top:8px; display:flex; gap:8px;">
                <button id="sp-ok-${j}" class="btn" onclick="sesionProblema(${j}, true)" style="background:#374151; color:white; cursor:pointer; padding:4px 12px; font-size:13px;">✓ Bien</button>
                <button id="sp-ko-${j}" class="btn" onclick="sesionProblema(${j}, false)" style="background:#374151; color:white; cursor:pointer; padding:4px 12px; font-size:13px;">✗ Mal</button>
            </div>
        </div>`;
    });
    if (!(it.problemas || []).length) {
        probs = '<p style="color:#6b7280;">Sin problemas en el banco para este nodo: estudia la teoría y resuelve uno del tema por tu cuenta.</p>';
    }

    cont.innerHTML = `
        <div class="session-item-heading">${badge}<span class="session-item-mode">${sesionContext.energy <= 2 ? 'Modo ligero · elige lo que te encaje' : 'Puedes centrarte en una cosa cada vez'}</span></div>
        <h2 style="margin:10px 0 4px;"><code style="color:#60a5fa; font-size:16px;">${it.id}</code> ${it.nombre}</h2>
        <div style="color:#6b7280; font-size:13px; margin-bottom:12px;">${it.materia || ''}${it.fuentes ? ' · 📖 ' + it.fuentes : ''}</div>
        <div class="session-pacer-card"><div class="session-pacer-title"><span>PACER · ${pacer.codigo} · ${pacer.nombre}</span><small>${pacer.estimado === false ? 'ajustado por ti' : 'tipo estimado'}</small></div><p>${pacer.accion}</p><label for="session-encoding-response">Tu intento antes de abrir la teoría</label><textarea id="session-encoding-response" rows="3" placeholder="Escribe una explicación, los primeros pasos, una analogía o un ejemplo…"></textarea></div>
        <div id="sesion-leccion" style="display:none; background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:14px; margin-bottom:14px; line-height:1.6;">
            <span style="color:#9ca3af;">Cargando lección...</span>
        </div>
        <p style="color:#fbbf24; font-size:14px;">${esNuevo ? 'Primero intenta construir una explicación. Después puedes abrir la ayuda de la IA.' : 'Repaso a libro cerrado: intenta recuperar y aplicar lo que sabes antes de mirar la ayuda.'}</p>
        <button class="btn" onclick="document.getElementById('sesion-leccion').style.display='block'; sesionCargarLeccion();" style="background:#374151; color:white; cursor:pointer; margin-bottom:10px;">📖 Abrir apoyo de la IA ${esNuevo ? 'después de intentarlo' : 'si estás bloqueado'}</button>
        <h3 style="margin:14px 0 4px;">Práctica</h3>
        ${probs}
        <div style="border-top:1px solid #2d3748; margin-top:18px; padding-top:15px;">
            <div style="color:#9ca3af; font-size:13px; margin-bottom:8px;">¿Cómo te ha ido con este nodo?</div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                ${CALIDAD_NIVELES.map(n => `<button class="btn" onclick="sesionRegistrar(${n.calidad})" title="${n.ayuda}" style="background:${n.color}; color:white; cursor:pointer; padding:10px 16px;">${n.etiqueta}</button>`).join('')}
                <button class="btn" onclick="sesionRegistrar(null)" style="background:#374151; color:white; cursor:pointer; padding:10px 16px;">Saltar →</button>
            </div>
        </div>`;

    cont.querySelectorAll('.math-content').forEach(el => renderMath(el));
    sesionProblemResults = {};
    window.scrollTo(0, 0);
    document.getElementById('sesion-overlay').scrollTop = 0;
}

function renderSesionCierre() {
    const cont = document.getElementById('sesion-contenido');
    const railOptions = [
        ['relevance', 'Relevancia · explorar qué funciona'],
        ['awareness', 'Conciencia · experimentar y observar errores'],
        ['iteration', 'Iteración · variar y ajustar'],
        ['lifelong', 'Mantenimiento · mantener y refinar'],
    ].map(([value, label]) => `<option value="${value}" ${studyRailStage === value ? 'selected' : ''}>${label}</option>`).join('');
    document.getElementById('sesion-fase').textContent = 'Cierre opcional';
    document.getElementById('sesion-progreso').textContent = 'Puedes cerrar aquí';
    document.getElementById('sesion-barra').style.width = '100%';
    cont.innerHTML = `<div class="session-close-card">
        <div class="session-close-intro"><span class="hub-eyebrow"><i data-lucide="flag"></i> CIERRE DE LA EXPLORACIÓN</span><h2>Has trabajado lo que te encajaba hoy</h2><p>Si quieres, deja una señal breve para que las próximas recomendaciones sean más útiles.</p><div class="session-close-stats"><strong>✓ ${sesionStats.bien} sólidos</strong><strong>≈ ${sesionStats.mal} para reforzar</strong><strong>→ ${sesionStats.saltados} no trabajados</strong></div></div>
        <div class="session-close-grid">
            <div class="session-reflection-block"><label for="session-worked">¿Qué funcionó?</label><textarea id="session-worked" rows="3" placeholder="Ej.: explicar en voz alta me obligó a justificar la simetría…"></textarea></div>
            <div class="session-reflection-block"><label for="session-friction">¿Dónde apareció la fricción?</label><textarea id="session-friction" rows="3" placeholder="Ej.: confundí dos ideas, me distraje, no sabía por dónde empezar…"></textarea></div>
            <div class="session-reflection-block"><label for="session-next-change">Un cambio concreto para la próxima</label><textarea id="session-next-change" rows="3" placeholder="Ej.: haré un dibujo antes de escribir ecuaciones…"></textarea></div>
            <div class="session-reflection-block"><label for="session-energy-after">¿Cómo terminas?</label><select id="session-energy-after"><option value="1">Vacío</option><option value="2">Cansado</option><option value="3" selected>Normal</option><option value="4">Bien</option><option value="5">Con energía</option></select></div>
        </div>
        <div class="session-grind-block"><div><h3><i data-lucide="network"></i> GRIND · mapa mental rápido</h3><p>No hace falta hacer un mapa bonito: marca qué decisiones has tomado al organizar el conocimiento.</p></div><div class="grind-check-grid">${[['grouping','Agrupé ideas relacionadas'],['relational','Expliqué relaciones'],['interconnected','Conecté grupos distintos'],['nonverbal','Usé un dibujo o símbolo'],['directional','Marqué dirección o causalidad'],['emphasized','Elegí qué era esencial']].map(([id,label]) => `<label><input type="checkbox" id="grind-${id}"> ${label}</label>`).join('')}</div><textarea id="grind-map-note" rows="2" placeholder="Opcional: describe aquí los grupos y conexiones de tu mapa…"></textarea></div>
        <div class="session-rail-block"><div><h3><i data-lucide="refresh-cw"></i> RAIL · mejorar tu forma de estudiar</h3><p>Elige la acción que vas a practicar, no una intención vaga.</p></div><div class="session-rail-controls"><select id="session-rail-stage">${railOptions}</select><select id="session-rail-action"><option value="explorar">Explorar</option><option value="experimentar">Experimentar</option><option value="variar">Variar</option><option value="mantener">Mantener</option><option value="reflexionar">Reflexionar</option><option value="ajustar">Ajustar</option></select></div><textarea id="session-rail-experiment" rows="2" placeholder="¿Qué variable vas a cambiar o comprobar en la próxima sesión?"></textarea></div>
        <button class="btn btn-primary session-finish-btn" onclick="finalizarSesion()"><i data-lucide="save"></i> Guardar lo trabajado y cerrar</button>
    </div>`;
    lucide.createIcons();
}

function sesionCargarLeccion() {
    const it = sesionItems[sesionIdx];
    const div = document.getElementById('sesion-leccion');
    if (!div || div.dataset.cargada) return;
    fetch('/api/kg/leccion/' + it.id)
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            div.innerHTML = parseMarkdown(data.md);
            div.dataset.cargada = '1';
            renderMath(div);
        })
        .catch(e => { div.innerHTML = `<span style="color:#f87171;">Error cargando la lección: ${e.message}</span>`; });
}

function sesionProblema(j, ok) {
    const p = sesionItems[sesionIdx].problemas[j];
    document.getElementById(`sp-ok-${j}`).style.background = ok ? '#059669' : '#374151';
    document.getElementById(`sp-ko-${j}`).style.background = ok ? '#374151' : '#dc2626';
    sesionProblemResults[p?.id || String(j)] = ok;
    if (p && p.id) {
        fetch('/api/kg/problema', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: p.id, exito: ok })
        }).catch(() => {});
    }
}

function sesionRegistrar(calidad) {
    const it = sesionItems[sesionIdx];
    const preview = sesionPreview.find(p => p.id === it.id) || {};
    const encodingResponse = document.getElementById('session-encoding-response')?.value || '';
    if (sesionSessionId) {
        fetch(`/api/study/sessions/${sesionSessionId}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'practice', node_id: it.id,
                pacer: preview.pacer?.codigo || 'C',
                quality: calidad === null ? 0 : calidad,
                encoding_response: encodingResponse,
                problem_results: sesionProblemResults,
            })
        }).catch(() => {});
    }
    if (calidad === null) {
        sesionStats.saltados++;
        sesionIdx++;
        renderSesionPaso();
        return;
    }
    const exito = calidad >= 0.5;
    sesionStats[exito ? 'bien' : 'mal']++;
    fetch('/api/kg/registrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: [it.id], exito: exito, calidad: calidad })
    }).finally(() => {
        sesionIdx++;
        renderSesionPaso();
    });
}

function finalizarSesion() {
    if (!sesionSessionId || sesionCompleted) { exitSesion(); return; }
    const payload = {
        worked: document.getElementById('session-worked')?.value || '',
        friction: document.getElementById('session-friction')?.value || '',
        next_change: document.getElementById('session-next-change')?.value || '',
        energy_after: parseInt(document.getElementById('session-energy-after')?.value || '3'),
        grouping: !!document.getElementById('grind-grouping')?.checked,
        relational: !!document.getElementById('grind-relational')?.checked,
        interconnected: !!document.getElementById('grind-interconnected')?.checked,
        nonverbal: !!document.getElementById('grind-nonverbal')?.checked,
        directional: !!document.getElementById('grind-directional')?.checked,
        emphasized: !!document.getElementById('grind-emphasized')?.checked,
        map_note: document.getElementById('grind-map-note')?.value || '',
        rail_stage: document.getElementById('session-rail-stage')?.value || 'relevance',
        rail_action: document.getElementById('session-rail-action')?.value || 'reflexionar',
        rail_experiment: document.getElementById('session-rail-experiment')?.value || '',
    };
    const button = document.querySelector('.session-finish-btn');
    if (button) { button.disabled = true; button.textContent = 'Guardando…'; }
    fetch(`/api/study/sessions/${sesionSessionId}/finish`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    }).then(r => r.json()).then(data => {
        if (data.error) throw new Error(data.error);
        sesionCompleted = true;
        document.getElementById('sesion-fase').textContent = 'Sesión guardada';
        document.getElementById('sesion-contenido').innerHTML = `<div class="session-saved"><div class="voice-review-icon"><i data-lucide="check"></i></div><h2>Sesión guardada</h2><p>La reflexión, el mapa y el ajuste de técnica quedan registrados para mejorar la siguiente sesión.</p><div class="session-close-stats"><strong>✓ ${sesionStats.bien} sólidos</strong><strong>≈ ${sesionStats.mal} para reforzar</strong></div><div class="session-saved-actions"><button class="btn" onclick="openGraphFromHub(); exitSesion();">Ver grafo</button><button class="btn btn-primary" onclick="exitSesion()">Volver al centro</button></div></div>`;
        lucide.createIcons();
        fetchHubStatus();
        fetchGamificacion();
        }).catch(error => { if (button) { button.disabled = false; button.textContent = 'Guardar lo trabajado y cerrar'; } alert('No se pudo guardar el cierre: ' + error.message); });
}

function registrarNodo(id, exito) {
    if (!confirm(`¿Registrar "${id}" como ${exito ? 'ÉXITO' : 'FALLO'}? (Si subes el PDF al Inbox, no hace falta: se registra solo)`)) return;
    fetch('/api/kg/registrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: [id], exito: exito })
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            loadStudySubjectCards();
        })
        .catch(e => alert('Error: ' + e.message));
}

// ---- Configuración de exámenes ----
function fetchExamConfig() {
    fetch('/api/kg/examenes')
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            examConfig = data;
            renderExamRows();
        })
        .catch(e => console.error(e));
}

function renderExamRows() {
    let html = `<tr style="color:#9ca3af; text-align:left; border-bottom:1px solid #2d3748;">
        <th style="padding:8px;">Asignatura</th><th>Fecha oficial</th><th>Preparación</th><th>Importancia</th><th>Descripción</th><th>Temas (vacío = todos)</th><th></th></tr>`;
    (examConfig.examenes || []).forEach((ex, i) => {
        const temas = ex.temas === null || ex.temas === undefined ? '' : ex.temas.join(',');
        html += `<tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:6px;"><input value="${ex.materia}" onchange="examConfig.examenes[${i}].materia=this.value" style="width:95%; background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
                        <td><input type="date" value="${ex.fecha}" onchange="examConfig.examenes[${i}].fecha=this.value" style="background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
            <td><input type="date" value="${ex.fecha_preparacion || ""}" onchange="examConfig.examenes[${i}].fecha_preparacion=this.value" style="background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
            <td><input type="number" min="0.1" max="3" step="0.1" value="${ex.importancia || 1}" onchange="examConfig.examenes[${i}].importancia=parseFloat(this.value)||1" style="width:65px; background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
            <td><input value="${(ex.descripcion || '').replace(/"/g, '&quot;')}" onchange="examConfig.examenes[${i}].descripcion=this.value" style="width:95%; background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
            <td><input value="${temas}" placeholder="ej: 0,1,2,3" onchange="setExamTemas(${i}, this.value)" style="width:100px; background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
            <td><button onclick="removeExamRow(${i})" style="background:none; border:none; color:#f87171; cursor:pointer; font-size:16px;">🗑</button></td></tr>`;
    });
    document.getElementById('plan-examenes-tabla').innerHTML = html;
}

function setExamTemas(i, valor) {
    const v = valor.trim();
    examConfig.examenes[i].temas = v === '' ? null : v.split(',').map(x => parseInt(x.trim())).filter(x => !isNaN(x));
}

function addExamRow() {
    examConfig.examenes.push({ materia: '', fecha: new Date().toISOString().slice(0, 10), fecha_preparacion: '', importancia: 1, descripcion: '', temas: null });
    renderExamRows();
}

function removeExamRow(i) {
    examConfig.examenes.splice(i, 1);
    renderExamRows();
}

function saveExamConfig() {
    examConfig.examenes = examConfig.examenes.filter(ex => ex.materia.trim() !== '');
    fetch('/api/kg/examenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(examConfig)
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            document.getElementById('plan-config-status').textContent = '✓ Guardado';
            setTimeout(() => document.getElementById('plan-config-status').textContent = '', 3000);
            loadStudySubjectCards();
        })
        .catch(e => alert('Error al guardar: ' + e.message));
}

function fetchGrafosSelect() {
    fetch('/api/kg/grafos')
        .then(r => r.json())
        .then(grafos => {
            const sel = document.getElementById('banco-grafo');
            sel.innerHTML = grafos.map(g =>
                `<option value="${g.archivo}">${g.curso}º · ${g.materia} (${g.nodos} nodos)</option>`).join('');
            // Electromagnetismo por defecto si existe
            const em = grafos.find(g => g.archivo === 'electromagnetismo.json');
            if (em) sel.value = em.archivo;
        });
}

function uploadBanco() {
    const input = document.getElementById('banco-file');
    if (!input.files.length) { alert('Selecciona el MD de problemas primero.'); return; }
    const fd = new FormData();
    fd.append('file', input.files[0]);
    fd.append('grafo', document.getElementById('banco-grafo').value);
    document.getElementById('banco-status').textContent = 'Clasificando con IA (1-2 min, no cierres la pestaña)...';
    fetch('/api/kg/banco', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            document.getElementById('banco-status').textContent =
                `✓ ${data.problemas} problemas añadidos a ${data.materia} (${data.con_nodos} con nodos específicos)`;
            input.value = '';
        })
        .catch(e => { document.getElementById('banco-status').textContent = 'Error: ' + e.message; });
}


// =====================================================================
// GESTIÓN DE CUADERNOS GEMINI Y LOS 3 MODOS DE ESTUDIO
// =====================================================================
window.cuadernosGemini = {};
window.currentRecommendedMateria = "Electrónica";

function fetchCuadernosConfig() {
    return fetch('/api/kg/cuadernos')
        .then(r => r.json())
        .then(data => {
            window.cuadernosGemini = data || {};
            return data;
        })
        .catch(() => {});
}

function mostrarToast(mensaje, duracion = 4500) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:99999; display:flex; flex-direction:column; gap:10px; pointer-events:none;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.style.cssText = 'background:#1e293b; color:#f8fafc; border:1px solid #3b82f6; border-radius:8px; padding:12px 18px; font-size:14px; box-shadow:0 8px 24px rgba(0,0,0,0.5); pointer-events:auto; display:flex; align-items:center; gap:10px; opacity:0; transform:translateY(10px); transition:all 0.3s ease; max-width:420px;';
    toast.innerHTML = `<i data-lucide="info" style="color:#60a5fa; width:18px; height:18px; flex-shrink:0;"></i><span>${mensaje}</span>`;
    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 350);
    }, duracion);
}

function abrirCuadernoMateria(materia) {
    const config = (window.cuadernosGemini && window.cuadernosGemini[materia]) || {};
    const url = config.url || 'https://gemini.google.com/notebooks/create?subtype=study';
    window.open(url, '_blank');
    mostrarToast(`📖 Abriendo Cuaderno Gemini de ${materia}`);
}

function openRecommendedNotebook() {
    const mat = window.currentRecommendedMateria || 'Electrónica';
    abrirCuadernoMateria(mat);
}

function abrirCuadernoLeccion(materia, id, nombre) {
    const promptSocratico = `Actúa como mi tutor socrático para la asignatura "${materia}" del Grado en Física (UVa).
Tengo cargados mis apuntes y problemas en este cuaderno. Ponme a prueba a fondo sobre el concepto del temario:
"${id}: ${nombre}"

OBJETIVO ANTES DE RESOLVER PROBLEMAS:
Asegúrate de que NO tenga ninguna laguna teórica o de planteamiento. Evalúame con los 4 pilares:
1. Mecanismo causal físico cualitativo (qué ocurre en el sistema antes de formular matemáticas).
2. Hipótesis y límites de validez de las aproximaciones.
3. Planteamiento y condiciones de contorno para el problema matemático.
4. Casos límite asintóticos y trampas típicas del examen.

Hazme una sola pregunta cada vez y no me des la respuesta masticada.`;

    navigator.clipboard.writeText(promptSocratico).catch(() => {});
    abrirCuadernoMateria(materia);
    mostrarToast(`📖 Abriendo Cuaderno de ${materia}. ¡Prompt socrático de "${id}" copiado al portapapeles! Pégalo en el chat de Gemini.`);
}

function abrirMaterialesCarpeta(materia) {
    fetch('/api/cuadernos/abrir_materiales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ materia: materia })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            mostrarToast(`📂 Abierta la carpeta de apuntes de ${materia}`);
        } else {
            mostrarToast(`Error al abrir carpeta: ${data.error}`);
        }
    })
    .catch(err => mostrarToast(`Error: ${err}`));
}

function openCuadernosModal() {
    const modal = document.getElementById('cuadernos-modal');
    if (!modal) return;
    modal.classList.add('active');
    const container = document.getElementById('cuadernos-list');
    if (!container) return;
    
    fetchCuadernosConfig().then(cuadernos => {
        let html = `
            <div style="background:#0f172a; border:1px solid #3b82f6; border-radius:8px; padding:12px 16px; margin-bottom:14px; font-size:13px; color:#cbd5e1; line-height:1.5;">
                💡 <strong>Materiales listos y empaquetados:</strong> Pulsa <strong style="color:#93c5fd;">Ver PDFs</strong> para abrir la carpeta de la asignatura en tu disco con los exámenes y apuntes limpios. Solo arrastra esos PDFs a Gemini cuando quieras sincronizar un nuevo cuaderno.
            </div>
        `;
        const materias = [
            "Electrónica", "Física del Estado Sólido", "Electrodinámica Clásica", 
            "Mecánica Cuántica", "Electromagnetismo", "Física Nuclear y de Partículas", 
            "Gravitación y Cosmología", "Simetrías, Campos y Partículas"
        ];
        materias.forEach(m => {
            const item = cuadernos[m] || { url: 'https://gemini.google.com/notebooks/create?subtype=study', nombre: `${m} — 4º Física UVa` };
            html += `
                <div style="background:#11141d; border:1px solid #2d3748; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <strong style="color:#f3f4f6; font-size:15px;">${item.nombre || m}</strong>
                        <div style="display:flex; gap:6px;">
                            <button class="btn btn-sm" onclick="abrirMaterialesCarpeta('${m}')" style="background:#1e293b; color:#93c5fd; border:1px solid #3b82f6; padding:4px 10px; font-size:12px; display:inline-flex; align-items:center; gap:4px;" title="Abre en el Explorador los PDFs preparados">
                                <i data-lucide="folder" style="width:12px;height:12px;"></i> Ver PDFs
                            </button>
                            <button class="btn btn-sm" onclick="window.open('${item.url}', '_blank')" style="background:#3b82f6; color:white; padding:4px 10px; font-size:12px; display:inline-flex; align-items:center; gap:4px;">
                                <i data-lucide="external-link" style="width:12px;height:12px;"></i> Abrir Gemini
                            </button>
                        </div>
                    </div>
                    <div style="display:flex; gap:8px; align-items:center;">
                        <label style="color:#9ca3af; font-size:12px; white-space:nowrap;">URL:</label>
                        <input type="text" id="cuaderno-url-${m.replace(/[^a-zA-Z0-9]/g, '_')}" value="${item.url}" style="width:100%; background:#0a0b0e; border:1px solid #1e293b; color:#d1d5db; padding:6px 10px; border-radius:4px; font-size:12px;">
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
        if (window.lucide) lucide.createIcons();
    });
}

function closeCuadernosModal() {
    const modal = document.getElementById('cuadernos-modal');
    if (modal) modal.classList.remove('active');
}

function saveCuadernosConfig() {
    const materias = [
        "Electrónica", "Física del Estado Sólido", "Electrodinámica Clásica", 
        "Mecánica Cuántica", "Electromagnetismo", "Física Nuclear y de Partículas", 
        "Gravitación y Cosmología", "Simetrías, Campos y Partículas"
    ];
    materias.forEach(m => {
        const inp = document.getElementById(`cuaderno-url-${m.replace(/[^a-zA-Z0-9]/g, '_')}`);
        if (inp) {
            window.cuadernosGemini[m] = window.cuadernosGemini[m] || {};
            window.cuadernosGemini[m].url = inp.value.trim() || 'https://gemini.google.com/notebooks/create?subtype=study';
        }
    });
    fetch('/api/kg/cuadernos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(window.cuadernosGemini)
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        const status = document.getElementById('cuadernos-save-status');
        if (status) {
            status.textContent = '✓ URLs guardadas correctamente.';
            setTimeout(() => status.textContent = '', 3000);
        }
        mostrarToast('✓ Configuración de Cuadernos Gemini guardada.');
    })
    .catch(e => alert('Error al guardar cuadernos: ' + e.message));
}

// ---- MODO 2: RESOLVER CON WHISPER ----
function openMode2_Whisper(problemId = null, nodeId = null) {
    let targetProblem = null;
    let targetNode = null;
    
    if (problemId && lastPlan) {
        for (const list of [lastPlan.repasos || [], lastPlan.nuevos || []]) {
            for (const item of list) {
                const p = (item.problemas || []).find(x => x.id === problemId);
                if (p) { targetProblem = p; targetNode = item; break; }
            }
            if (targetProblem) break;
        }
    }
    
    if (!targetProblem && lastPlan) {
        for (const list of [lastPlan.repasos || [], lastPlan.nuevos || []]) {
            for (const item of list) {
                if ((item.problemas || []).length) {
                    targetProblem = item.problemas[0];
                    targetNode = item;
                    break;
                }
            }
            if (targetProblem) break;
        }
    }

    if (!targetProblem) {
        const listo = problemaListoEnPlan(problemId);
        if (listo) {
            targetProblem = listo;
            targetNode = {
                id: listo.nodos_requeridos?.[0] || '',
                nombre: 'Nodos requeridos',
                materia: listo.materia || '',
            };
        }
    }
    
    openVoiceRecorder();
    
    const headerHelp = document.querySelector('#voice-modal .voice-help');
    if (headerHelp && targetProblem) {
        headerHelp.innerHTML = `<strong style="color:#60a5fa;">Problema a resolver:</strong> ${targetProblem.id} — ${targetProblem.titulo} (${targetNode?.materia || ''})<br>Resuelve en papel mientras explicas en voz alta. Whisper transcribirá tus pasos.`;
    }
}

// ---- MODO 3: MODO BIBLIOTECA (EN SILENCIO) ----
let currentBibProblem = null;
let currentBibNode = null;
let bibTimerInterval = null;
let bibSeconds = 0;
let selectedBibFeedback = 'resuelto';
const PROBLEMA_FEEDBACK = [
    { k: 'resuelto', calidad: 1.0, etiqueta: '✓ Perfecto', color: '#059669', ayuda: 'Resultado, explicación y justificaciones correctos.' },
    { k: 'hueco_teorico', calidad: 0.75, etiqueta: '≈ Bien, pero hueco teórico', color: '#d97706', ayuda: 'El problema sale, pero hay una explicación o justificación que revisar.' },
    { k: 'incorrecto', calidad: 0.25, etiqueta: '✗ Mal: trabajar el error', color: '#dc2626', ayuda: 'La resolución no sale; hay que localizar el error y volver a trabajarlo.' },
];

function openMode3_Library(problemId = null, nodeId = null) {
    currentBibProblem = null;
    currentBibNode = null;
    
    if (problemId && lastPlan) {
        for (const list of [lastPlan.repasos || [], lastPlan.nuevos || []]) {
            for (const item of list) {
                const p = (item.problemas || []).find(x => x.id === problemId);
                if (p) { currentBibProblem = p; currentBibNode = item; break; }
            }
            if (currentBibProblem) break;
        }
    }
    
    if (!currentBibProblem && lastPlan) {
        for (const list of [lastPlan.repasos || [], lastPlan.nuevos || []]) {
            for (const item of list) {
                if ((item.problemas || []).length) {
                    currentBibProblem = item.problemas[0];
                    currentBibNode = item;
                    break;
                }
            }
            if (currentBibProblem) break;
        }
    }

    if (!currentBibProblem) {
        const listo = problemaListoEnPlan(problemId);
        if (listo) {
            currentBibProblem = listo;
            currentBibNode = {
                id: listo.nodos_requeridos?.[0] || '',
                nombre: 'Nodos requeridos',
                materia: listo.materia || '',
            };
        }
    }
    
    const modal = document.getElementById('biblioteca-modal');
    if (!modal) return;
    
    if (!currentBibProblem) {
        alert('No hay ningún problema seleccionado. Elige primero un problema del banco.');
        return;
    }
    
    document.getElementById('bib-problem-code').textContent = `${currentBibProblem.id} · ${currentBibProblem.titulo}`;
    document.getElementById('bib-problem-materia').textContent = `[${currentBibNode?.materia || ''} — ${currentBibNode?.id || ''}]`;
    document.getElementById('bib-problem-enunciado').innerHTML = (currentBibProblem.enunciado || '').replace(/\n/g, '<br>');
    document.getElementById('bib-comentarios').value = '';
    
    // Render calidad botones
    const btnContainer = document.getElementById('bib-calidad-botones');
    selectedBibFeedback = 'resuelto';
    if (btnContainer) {
        btnContainer.innerHTML = PROBLEMA_FEEDBACK.map((n, i) => `
            <button class="btn bib-q-btn" id="bib-q-${i}" onclick="selectBibFeedback(${i})" style="background:${i === 0 ? n.color : '#1e293b'}; color:white; padding:8px 12px; font-size:12px; border:1px solid #334155; border-radius:6px; cursor:pointer;" title="${n.ayuda}">
                ${n.etiqueta}
            </button>
        `).join('');
    }
    
    // Iniciar temporizador silencioso
    clearInterval(bibTimerInterval);
    bibSeconds = 0;
    const timerEl = document.getElementById('bib-timer');
    timerEl.textContent = '00:00';
    bibTimerInterval = setInterval(() => {
        bibSeconds++;
        const m = Math.floor(bibSeconds / 60);
        const s = bibSeconds % 60;
        timerEl.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }, 1000);
    
    modal.classList.add('active');
    document.querySelectorAll('#bib-problem-enunciado').forEach(el => renderMath(el));
    if (window.lucide) lucide.createIcons();
}

function selectBibFeedback(idx) {
    const level = PROBLEMA_FEEDBACK[idx];
    selectedBibFeedback = level.k;
    document.querySelectorAll('.bib-q-btn').forEach((b, i) => {
        b.style.background = (i === idx) ? PROBLEMA_FEEDBACK[i].color : '#1e293b';
    });
}

function closeBibliotecaModal() {
    clearInterval(bibTimerInterval);
    const modal = document.getElementById('biblioteca-modal');
    if (modal) modal.classList.remove('active');
}

function abrirCuadernoDeProblemaActual() {
    if (currentBibNode) {
        abrirCuadernoLeccion(currentBibNode.materia, currentBibNode.id, currentBibNode.nombre);
    } else {
        openRecommendedNotebook();
    }
}

function submitBibliotecaResolution() {
    if (!currentBibNode && !currentBibProblem) return;
    
    clearInterval(bibTimerInterval);
    const btn = document.getElementById('bib-submit-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Guardando…'; }
    
    const comentarios = document.getElementById('bib-comentarios')?.value || '';
    const payload = {
        nodo_id: currentBibNode?.id,
        problema_id: currentBibProblem?.id,
        veredicto: selectedBibFeedback,
        calidad: PROBLEMA_FEEDBACK.find(x => x.k === selectedBibFeedback)?.calidad || 0.25,
        exito: selectedBibFeedback !== 'incorrecto',
        segundos: bibSeconds,
        comentarios: comentarios
    };
    
    fetch('/api/biblioteca/resolver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        if (btn) { btn.disabled = false; btn.textContent = '✓ Guardar en el Grafo'; }
        if (data.error) throw new Error(data.error);
        closeBibliotecaModal();
        mostrarToast(`✓ Problema ${currentBibProblem?.id} registrado en tu perfil (${bibSeconds}s).`);
        loadStudySubjectCards();
        fetchGamificacion();
    })
    .catch(e => {
        if (btn) { btn.disabled = false; btn.textContent = '✓ Guardar en el Grafo'; }
        alert('Error al registrar problema: ' + e.message);
    });
}
