// Active view state
let currentTab = 'dashboard';
let errorChartInstance = null;
let currentSubjectData = null;
let activeTopicFilter = null;
let currentExerciseDetail = null;

let quizExercises = [];
let quizCurrentIndex = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchDashboardData();
    fetchSubjectsData();
});

// Switch Main Tabs
function switchTab(tabId) {
    // Update active tab buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
    
    // Update active sections
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(`view-dashboard`).classList.remove('active'); // force reset
    document.getElementById(`view-${tabId}`).classList.add('active');
    
    // Close detail panels
    closeSubjectDetail();
    
    currentTab = tabId;
    
    // Trigger tab-specific refresh if needed
    if (tabId === 'dashboard') {
        fetchDashboardData();
    } else if (tabId === 'subjects') {
        fetchSubjectsData();
    } else if (tabId === 'quiz') {
        document.getElementById('quiz-setup-panel').style.display = 'block';
        document.getElementById('quiz-play-panel').style.display = 'none';
        fetchSubjectsData();
    } else if (tabId === 'plan') {
        loadPlanTab();
    } else if (tabId === 'mapa') {
        loadMapaFrame();
    } else if (tabId === 'correcciones') {
        fetchCorrecciones();
    }

    // Update icons
    lucide.createIcons();
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
    
    container.innerHTML = agenda.map(item => `
        <div class="agenda-item" onclick="viewExercise('${item.id}')">
            <div class="agenda-item-left">
                <span class="agenda-item-title">${item.id} — ${item.tema}</span>
                <span class="agenda-item-meta">${item.asignatura}</span>
            </div>
            <div class="agenda-item-right">
                <span class="badge ${item.estado}">${item.estado}</span>
                <span class="agenda-date"><i data-lucide="clock" style="width:12px;height:12px;display:inline;"></i> Repaso: ${item.proxima_revision}</span>
            </div>
        </div>
    `).join('');
    
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
                <span class="web-exercise-card-date">Repaso: ${ex.proxima_revision}</span>
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
    document.getElementById('edit-proxima').value = currentExerciseDetail.proxima_revision;
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
        proxima_revision: document.getElementById('edit-proxima').value.trim(),
        enunciado: document.getElementById('edit-enunciado').value.trim()
    };
    
    // Validar fecha en formato DD/MM/YYYY
    const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
    if (!dateRegex.test(updatedData.proxima_revision)) {
        alert('La fecha de próxima revisión debe tener el formato DD/MM/YYYY.');
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
                .then(data => data.agenda);
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
                        const exDate = parseDateDMY(ex.proxima_revision);
                        return exDate <= hoyDate;
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

function executeSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<div class="loading-spinner"><i data-lucide="sparkles" class="logo-icon spinning"></i> Consultando al motor semántico de Gemini...</div>';
    lucide.createIcons();
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            resultsContainer.innerHTML = `
                <div class="markdown-body">
                    ${data.html}
                </div>
            `;
            
            // Render any mathematical output from the search response
            renderMath(resultsContainer);
        })
        .catch(err => {
            console.error('Error running search:', err);
            resultsContainer.innerHTML = '<div class="no-tasks">Error al ejecutar la búsqueda semántica. Inténtalo de nuevo.</div>';
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
    fetchPlan();
    fetchExamConfig();
    fetchGrafosSelect();
    fetchGamificacion();
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
        cont.innerHTML = `<div class="no-tasks">Aún no hay correcciones. Resuelve un problema en el reMarkable (escribe su código, ej. <b>3.1</b>), pulsa <b>Corregir lo nuevo</b>: el feedback aparecerá aquí.</div>`;
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

function corregirLoNuevo() {
    const btn = document.getElementById('btn-corregir');
    const cont = document.getElementById('correcciones-list');
    if (btn) { btn.disabled = true; btn.style.opacity = '0.6'; btn.style.cursor = 'wait'; }
    fetch('/api/corregir', { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            if (res.error) throw new Error(res.error);
            if (cont) cont.insertAdjacentHTML('afterbegin',
                `<div class="no-tasks" id="corregir-aviso" style="border:1px solid #2563eb; color:#bfdbfe;">⏳ ${res.mensaje || 'Sincronizando y corrigiendo en segundo plano...'} Pulsa <b>Actualizar</b> en un par de minutos.</div>`);
        })
        .catch(e => alert('No se pudo iniciar: ' + e.message))
        .finally(() => { if (btn) { btn.disabled = false; btn.style.opacity = '1'; btn.style.cursor = 'pointer'; } });
}

function limpiarCorrecciones() {
    if (!confirm('¿Vaciar la lista de correcciones? (No borra el registro de Obsidian)')) return;
    fetch('/api/kg/correcciones', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: '{}' })
        .then(() => fetchCorrecciones());
}

function fetchPlan() {
    document.getElementById('plan-hoy').innerHTML = '<div class="loading-spinner">Calculando plan...</div>';
    fetch('/api/kg/plan')
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            renderViabilidad(data);
            renderPlanHoy(data.plan);
        })
        .catch(e => {
            document.getElementById('plan-semaforo').innerHTML = '';
            document.getElementById('plan-hoy').innerHTML =
                `<p style="color:#f87171;">Error: ${e.message}. Configura tus exámenes abajo y guarda.</p>`;
        });
}

function renderViabilidad(data) {
    const colores = { 'HOLGADO': '#34d399', 'AJUSTADO': '#fbbf24', 'INSUFICIENTE': '#f87171' };
    const iconos = { 'HOLGADO': '✅', 'AJUSTADO': '🟡', 'INSUFICIENTE': '🔴' };
    document.getElementById('plan-semaforo').innerHTML =
        `<span style="color:${colores[data.estado]};">${iconos[data.estado]} ${data.estado}</span>
         <span style="color:#9ca3af; font-weight:400; font-size:14px;"> — necesitas ${data.ritmo_total} min/día y tienes ${data.minutos} disponibles</span>`;

    const filas = data.viabilidad.sort((a, b) => a.fecha.localeCompare(b.fecha));
    let html = `<tr style="color:#9ca3af; text-align:left; border-bottom:1px solid #2d3748;">
        <th style="padding:8px;">Examen</th><th>Fecha</th><th>Pendientes</th><th>Carga</th><th>Ritmo necesario</th><th>Tu ritmo real</th></tr>`;
    filas.forEach(f => {
        let real;
        if (f.proyeccion && f.retraso_dias > 0) {
            real = `<span style="color:#f87171;">⚠ ${f.reales_sem} vs ${f.necesarios_sem} nodos/sem<br><small>a este ritmo acabas el ${f.proyeccion} (${f.retraso_dias} días tarde)</small></span>`;
        } else if (f.reales_sem > 0) {
            real = `<span style="color:#34d399;">✓ ${f.reales_sem} vs ${f.necesarios_sem} nodos/sem</span>`;
        } else {
            real = `<span style="color:#6b7280;">— (necesitas ${f.necesarios_sem}/sem)</span>`;
        }
        html += `<tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:8px;">${f.materia} <span style="color:#6b7280;">${f.desc}</span></td>
            <td>${f.fecha}</td>
            <td>${f.pendientes}/${f.total}</td>
            <td>${f.carga_h.toFixed(0)} h</td>
            <td><strong>${f.ritmo.toFixed(0)} min/día</strong></td>
            <td>${real}</td></tr>`;
    });
    document.getElementById('plan-viabilidad').innerHTML = html;
}

let lastPlan = null;

function renderPlanHoy(plan) {
    lastPlan = plan;
    let html = '';
    if (plan.repasos && plan.repasos.length) {
        html += `<h3 style="color:#fbbf24; margin-bottom:10px;">Repasos (${plan.repasos.length})</h3>`;
        plan.repasos.forEach(r => { html += planItemHtml(r, true); });
    }
    html += `<h3 style="color:#60a5fa; margin: 15px 0 10px;">Lecciones nuevas (${plan.nuevos.length})</h3>`;
    if (!plan.nuevos.length) html += '<p style="color:#9ca3af;">No hay lecciones nuevas (¿frontera vacía o sin presupuesto?).</p>';
    plan.nuevos.forEach(n => { html += planItemHtml(n, false); });
    if (plan.implicitos && plan.implicitos.length) {
        html += `<p style="color:#6b7280; font-size:13px; margin-top:12px;">Repasados implícitamente hoy: ${plan.implicitos.join(', ')}</p>`;
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

    let probs = '';
    (item.problemas || []).forEach(p => {
        const tag = p.hecho ? ' <span style="color:#34d399; font-size:11px;">(ya hecho)</span>' : '';
        probs += `<details style="margin:6px 0; background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:8px 12px;">
            <summary style="cursor:pointer; color:#d1d5db;">Problema ${p.numero} — ${p.titulo} <span style="color:#6b7280;">(${p.hoja})</span>${tag}</summary>
            <div class="math-content" style="margin-top:8px; line-height:1.6; color:#d1d5db;">${p.enunciado.replace(/\n/g, '<br>')}</div>
        </details>`;
    });
    if (!(item.problemas || []).length) {
        probs = '<div style="color:#6b7280; font-size:13px;">Sin problemas en el banco: estudia la teoría y usa uno del tema.</div>';
    }

    return `<div style="background:#11141d; border-left:3px solid ${borde}; border-radius:8px; padding:14px 16px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div><code style="color:${borde};">${item.id}</code> <strong>${item.nombre}</strong>
                 <span style="color:#6b7280; font-size:13px;">[${item.materia || ''}]</span></div>
            <div style="display:flex; gap:8px;">
                <button class="btn" onclick="verLeccion('${item.id}')" style="background:#374151; color:white; cursor:pointer; padding:6px 12px;">📖 Lección</button>
                <button class="btn" onclick="registrarNodo('${item.id}', true)" style="background:#059669; color:white; cursor:pointer; padding:6px 12px;">✓ Hecho</button>
                <button class="btn" onclick="registrarNodo('${item.id}', false)" style="background:#dc2626; color:white; cursor:pointer; padding:6px 12px;">✗ Fallado</button>
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
        else fetch('/api/kg/examenes').then(r => r.json()).then(cfg => { kgQuizExamenes = cfg.examenes || []; pinta(); });
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
        registros.push(fetch('/api/kg/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: [q.id], exito: q.resultado, calidad: q.calidad, segundos: q.segundos })
        }));
        if (q.problema && q.problema.id) {
            registros.push(fetch('/api/kg/problema', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: q.problema.id, exito: q.resultado })
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

function startSesion() {
    if (!lastPlan) { alert('Espera a que cargue el plan de hoy.'); return; }
    sesionItems = [
        ...(lastPlan.repasos || []).map(x => ({ ...x, tipo: 'repaso' })),
        ...(lastPlan.nuevos || []).map(x => ({ ...x, tipo: 'nuevo' }))
    ];
    if (!sesionItems.length) { alert('El plan de hoy está vacío.'); return; }
    sesionIdx = 0;
    sesionStats = { bien: 0, mal: 0, saltados: 0 };
    document.getElementById('sesion-overlay').style.display = 'block';
    renderSesionPaso();
}

function exitSesion() {
    document.getElementById('sesion-overlay').style.display = 'none';
    fetchPlan();
    fetchGamificacion();
}

function renderSesionPaso() {
    const total = sesionItems.length;
    const cont = document.getElementById('sesion-contenido');
    document.getElementById('sesion-progreso').textContent = `${Math.min(sesionIdx + 1, total)} / ${total}`;
    document.getElementById('sesion-barra').style.width = `${(sesionIdx / total) * 100}%`;

    if (sesionIdx >= total) {
        document.getElementById('sesion-barra').style.width = '100%';
        cont.innerHTML = `<h2 style="margin-top:0;">Sesión completada 🎉</h2>
            <p style="font-size:16px;">✓ ${sesionStats.bien} dominados · ✗ ${sesionStats.mal} fallados · ${sesionStats.saltados} saltados</p>
            <p style="color:#9ca3af;">Tu perfil, el mapa y el plan de mañana ya están actualizados.</p>
            <button class="btn btn-primary" onclick="exitSesion()" style="cursor:pointer; padding:10px 24px;">Cerrar</button>`;
        return;
    }

    const it = sesionItems[sesionIdx];
    const esNuevo = it.tipo === 'nuevo';
    const badge = esNuevo
        ? '<span style="background:#1d4ed8; color:white; padding:3px 10px; border-radius:999px; font-size:12px;">LECCIÓN NUEVA</span>'
        : '<span style="background:#b45309; color:white; padding:3px 10px; border-radius:999px; font-size:12px;">REPASO</span>';

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
        ${badge}
        <h2 style="margin:10px 0 4px;"><code style="color:#60a5fa; font-size:16px;">${it.id}</code> ${it.nombre}</h2>
        <div style="color:#6b7280; font-size:13px; margin-bottom:12px;">${it.materia || ''}${it.fuentes ? ' · 📖 ' + it.fuentes : ''}</div>
        <div id="sesion-leccion" style="display:${esNuevo ? 'block' : 'none'}; background:#0a0b0e; border:1px solid #1e293b; border-radius:6px; padding:14px; margin-bottom:14px; line-height:1.6;">
            <span style="color:#9ca3af;">Cargando lección...</span>
        </div>
        ${!esNuevo ? '<p style="color:#fbbf24; font-size:14px;">Repaso a libro cerrado: intenta el problema SIN mirar teoría. Solo si te quedas bloqueado, abre la lección.</p><button class="btn" onclick="document.getElementById(\'sesion-leccion\').style.display=\'block\'; sesionCargarLeccion();" style="background:#374151; color:white; cursor:pointer; margin-bottom:10px;">📖 Abrir lección (solo si estás bloqueado)</button>' : ''}
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
    if (esNuevo) sesionCargarLeccion();
    window.scrollTo(0, 0);
    document.getElementById('sesion-overlay').scrollTop = 0;
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
    if (p && p.id) {
        fetch('/api/kg/problema', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: p.id, exito: ok })
        }).catch(() => {});
    }
}

function sesionRegistrar(calidad) {
    if (calidad === null) {
        sesionStats.saltados++;
        sesionIdx++;
        renderSesionPaso();
        return;
    }
    const exito = calidad >= 0.5;
    sesionStats[exito ? 'bien' : 'mal']++;
    const it = sesionItems[sesionIdx];
    fetch('/api/kg/registrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: [it.id], exito: exito, calidad: calidad })
    }).finally(() => {
        sesionIdx++;
        renderSesionPaso();
    });
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
            fetchPlan();
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
            document.getElementById('plan-minutos').value = data.minutos_dia || 120;
            document.getElementById('plan-min-nuevo').value = data.min_nodo_nuevo || 40;
            document.getElementById('plan-min-repaso').value = data.min_repaso || 15;
            renderExamRows();
        })
        .catch(e => console.error(e));
}

function renderExamRows() {
    let html = `<tr style="color:#9ca3af; text-align:left; border-bottom:1px solid #2d3748;">
        <th style="padding:8px;">Asignatura</th><th>Fecha</th><th>Descripción</th><th>Temas (vacío = todos)</th><th></th></tr>`;
    (examConfig.examenes || []).forEach((ex, i) => {
        const temas = ex.temas === null || ex.temas === undefined ? '' : ex.temas.join(',');
        html += `<tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:6px;"><input value="${ex.materia}" onchange="examConfig.examenes[${i}].materia=this.value" style="width:95%; background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
            <td><input type="date" value="${ex.fecha}" onchange="examConfig.examenes[${i}].fecha=this.value" style="background:#0a0b0e; border:1px solid #2d3748; color:white; padding:6px; border-radius:4px;"></td>
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
    examConfig.examenes.push({ materia: '', fecha: new Date().toISOString().slice(0, 10), descripcion: '', temas: null });
    renderExamRows();
}

function removeExamRow(i) {
    examConfig.examenes.splice(i, 1);
    renderExamRows();
}

function saveExamConfig() {
    examConfig.minutos_dia = parseInt(document.getElementById('plan-minutos').value) || 120;
    examConfig.min_nodo_nuevo = parseInt(document.getElementById('plan-min-nuevo').value) || 40;
    examConfig.min_repaso = parseInt(document.getElementById('plan-min-repaso').value) || 15;
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
            fetchPlan();
        })
        .catch(e => alert('Error al guardar: ' + e.message));
}

// ---- Subidas ----
function uploadInbox() {
    const input = document.getElementById('inbox-file');
    if (!input.files.length) { alert('Selecciona un archivo primero.'); return; }
    const fd = new FormData();
    fd.append('file', input.files[0]);
    document.getElementById('inbox-status').textContent = 'Subiendo...';
    fetch('/api/kg/inbox', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            document.getElementById('inbox-status').textContent = data.mensaje;
            input.value = '';
        })
        .catch(e => { document.getElementById('inbox-status').textContent = 'Error: ' + e.message; });
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
