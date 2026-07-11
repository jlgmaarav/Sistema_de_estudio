// Active view state
let currentTab = 'projects';
let activeProjectId = null;
let activeBookId = null;
let allProjectsCached = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchProjectsData();
    fetchBooksData();
});

// Switch Main Tabs
function switchTab(tabId) {
    // Update active tab buttons
    document.getElementById('btn-tab-projects').classList.remove('active');
    document.getElementById('btn-tab-books').classList.remove('active');
    document.getElementById(`btn-tab-${tabId}`).classList.add('active');
    
    // Update active sections
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(`view-${tabId}`).classList.add('active');
    
    // Close detail panels
    closeProjectDetail();
    
    currentTab = tabId;
    
    // Trigger tab-specific refresh
    if (tabId === 'projects') {
        fetchProjectsData();
    } else if (tabId === 'books') {
        fetchBooksData();
    }
    
    lucide.createIcons();
}

// =====================================================================
// 1. PROJECTS CONTROLLER
// =====================================================================
function fetchProjectsData() {
    fetch('/api/projects')
        .then(res => res.json())
        .then(projects => {
            allProjectsCached = projects;
            const container = document.getElementById('projects-container');
            if (projects.length === 0) {
                container.innerHTML = '<div class="no-tasks">No se han registrado proyectos en la bóveda.</div>';
                return;
            }
            
            container.innerHTML = projects.map(p => {
                let tagHtml = p.etiqueta ? `<span class="subject-stat-label" style="background:var(--color-purple-glow); color:var(--color-purple); padding:0.25rem 0.5rem; border-radius:var(--border-radius-sm); border:1px solid rgba(139,92,246,0.2);">${p.etiqueta}</span>` : '';
                return `
                    <div class="subject-card s-cuantica" style="border-left-color: var(--color-purple);" onclick="viewProjectDetail('${p.id}')">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <h3 class="subject-title">${p.titulo}</h3>
                            ${tagHtml}
                        </div>
                        <div class="subject-stats-row" style="margin-top: 1rem;">
                            <div class="subject-stat-item">
                                <span class="subject-stat-label">Estado</span>
                                <span class="subject-stat-value" style="color:var(--color-green); font-size:0.9rem;">${p.estado.toUpperCase()}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            // Populate project select dropdown for book creation
            populateProjectDropdown(projects);
        })
        .catch(err => {
            console.error('Error fetching projects:', err);
            document.getElementById('projects-container').innerHTML = '<div class="no-tasks">Error al cargar proyectos.</div>';
        });
}

function viewProjectDetail(projId) {
    activeProjectId = projId;
    fetch(`/api/projects/${projId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            document.getElementById('project-detail-title').innerText = data.titulo;
            
            const tagBadge = document.getElementById('project-detail-tag');
            if (data.etiqueta) {
                tagBadge.style.display = 'inline-block';
                tagBadge.innerHTML = `<i data-lucide="tag" style="width:12px;height:12px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> ${data.etiqueta}`;
            } else {
                tagBadge.style.display = 'none';
            }
            
            document.getElementById('project-detail-desc').innerText = data.descripcion || 'Sin descripción provista.';
            
            // Populate tasks in editor
            document.getElementById('project-tasks-editor').value = data.tareas;
            
            // Populate project books
            const booksContainer = document.getElementById('project-books-container');
            const sections = Object.keys(data.libros_agrupados);
            
            if (sections.length === 0) {
                booksContainer.innerHTML = '<div class="no-tasks">Este proyecto no tiene libros asociados aún.</div>';
            } else {
                let html = '';
                sections.forEach(secName => {
                    html += `<h3 class="project-section-title"><i data-lucide="bookmark" style="width:16px;height:16px;"></i> ${secName}</h3>`;
                    html += '<div class="book-list-grid">';
                    data.libros_agrupados[secName].forEach(b => {
                        html += `
                            <div class="library-book-card" onclick="viewBookDetail('${b.id}')">
                                <div class="book-card-title">${b.titulo}</div>
                                <div class="book-card-meta">
                                    <span><strong>Autor:</strong> ${b.autor}</span>
                                    <span><strong>Categoría:</strong> ${b.categoria}</span>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                });
                booksContainer.innerHTML = html;
            }
            
            // Open detail panel
            document.getElementById('project-detail-panel').style.display = 'block';
            switchProjectSubTab('books');
            lucide.createIcons();
        })
        .catch(err => console.error('Error fetching project details:', err));
}

function closeProjectDetail() {
    document.getElementById('project-detail-panel').style.display = 'none';
    activeProjectId = null;
}

function switchProjectSubTab(tabName) {
    document.getElementById('btn-projtab-books').classList.remove('active');
    document.getElementById('btn-projtab-tasks').classList.remove('active');
    document.getElementById(`btn-projtab-${tabName}`).classList.add('active');
    
    document.getElementById('project-subtab-books').classList.remove('active');
    document.getElementById('project-subtab-tasks').classList.remove('active');
    document.getElementById(`project-subtab-${tabName}`).classList.add('active');
    
    lucide.createIcons();
}

function saveProjectTasks() {
    if (!activeProjectId) return;
    
    const tasksContent = document.getElementById('project-tasks-editor').value;
    const statusLabel = document.getElementById('project-save-status');
    
    fetch(`/api/projects/${activeProjectId}/tareas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tareas: tasksContent })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        
        statusLabel.style.display = 'inline-block';
        setTimeout(() => {
            statusLabel.style.display = 'none';
        }, 2000);
    })
    .catch(err => {
        console.error('Error saving project tasks:', err);
        alert('Error al guardar tareas del proyecto.');
    });
}

// =====================================================================
// 2. BOOKS/LIBRARY CONTROLLER
// =====================================================================
function fetchBooksData() {
    fetch('/api/books')
        .then(res => res.json())
        .then(books => {
            const container = document.getElementById('books-container');
            if (books.length === 0) {
                container.innerHTML = '<div class="no-tasks">No se han registrado libros en la biblioteca.</div>';
                return;
            }
            
            container.innerHTML = books.map(b => {
                let projectBadgeHtml = b.proyecto ? `<span class="book-card-project-badge"><i data-lucide="folder-git-2" style="width:12px;height:12px;display:inline;vertical-align:middle;margin-right:2px;"></i> ${b.proyecto.replace(/_/g, ' ')}</span>` : '';
                return `
                    <div class="library-book-card" onclick="viewBookDetail('${b.id}')">
                        <div class="book-card-title">${b.titulo}</div>
                        <div class="book-card-meta">
                            <span><strong>Autor:</strong> ${b.autor}</span>
                            <span><strong>Categoría:</strong> ${b.categoria}</span>
                            ${b.seccion && b.seccion !== 'General' ? `<span><strong>Sección:</strong> ${b.seccion}</span>` : ''}
                            <span><strong>Registrado:</strong> ${b.fecha_registro}</span>
                        </div>
                        ${projectBadgeHtml}
                    </div>
                `;
            }).join('');
            lucide.createIcons();
        })
        .catch(err => {
            console.error('Error fetching library books:', err);
            document.getElementById('books-container').innerHTML = '<div class="no-tasks">Error al cargar la biblioteca.</div>';
        });
}

function viewBookDetail(bookId) {
    activeBookId = bookId;
    fetch(`/api/books/${bookId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            document.getElementById('modal-book-title').innerText = data.titulo;
            document.getElementById('modal-book-author').innerText = `Autor: ${data.autor}`;
            document.getElementById('modal-book-category').innerText = `Categoría: ${data.categoria}`;
            
            const projBadge = document.getElementById('modal-book-project');
            if (data.proyecto) {
                projBadge.style.display = 'inline-block';
                projBadge.innerText = `Proyecto: ${data.proyecto.replace(/_/g, ' ')}`;
            } else {
                projBadge.style.display = 'none';
            }
            
            document.getElementById('book-notes-editor').value = data.notes;
            
            // Open Modal
            document.getElementById('book-modal').classList.add('active');
            lucide.createIcons();
        })
        .catch(err => console.error('Error fetching book details:', err));
}

function closeBookModal() {
    document.getElementById('book-modal').classList.remove('active');
    activeBookId = null;
}

function saveBookNotes() {
    if (!activeBookId) return;
    
    const notesContent = document.getElementById('book-notes-editor').value;
    const statusLabel = document.getElementById('book-save-status');
    
    fetch(`/api/books/${activeBookId}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: notesContent })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        
        statusLabel.style.display = 'inline-block';
        setTimeout(() => {
            statusLabel.style.display = 'none';
        }, 2000);
    })
    .catch(err => {
        console.error('Error saving book notes:', err);
        alert('Error al guardar notas de lectura del libro.');
    });
}

// =====================================================================
// 3. PROJECT & BOOK CREATION MODALS
// =====================================================================
function openNewProjectModal() {
    document.getElementById('new-project-modal').classList.add('active');
}

function closeNewProjectModal() {
    document.getElementById('new-project-modal').classList.remove('active');
    document.getElementById('new-project-form').reset();
}

function handleCreateProject(event) {
    event.preventDefault();
    const titulo = document.getElementById('proj-title').value.trim();
    const etiqueta = document.getElementById('proj-tag').value.trim();
    const descripcion = document.getElementById('proj-desc').value.trim();
    
    fetch('/api/projects/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titulo, etiqueta, descripcion })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        closeNewProjectModal();
        fetchProjectsData();
    })
    .catch(err => {
        console.error('Error creating project:', err);
        alert('Error al crear el proyecto.');
    });
}

function populateProjectDropdown(projects) {
    const select = document.getElementById('book-proj-select');
    select.innerHTML = '<option value="">-- Sin Proyecto (Libro Suelto) --</option>' + 
        projects.map(p => `<option value="${p.id}">${p.titulo}</option>`).join('');
}

function openNewBookModal() {
    // Populate projects dropdown first
    populateProjectDropdown(allProjectsCached);
    document.getElementById('new-book-modal').classList.add('active');
}

function closeNewBookModal() {
    document.getElementById('new-book-modal').classList.remove('active');
    document.getElementById('new-book-form').reset();
    document.getElementById('book-section-group').style.display = 'none';
}

function toggleBookSectionInput() {
    const projSelect = document.getElementById('book-proj-select');
    const sectionGroup = document.getElementById('book-section-group');
    if (projSelect.value) {
        sectionGroup.style.display = 'flex';
    } else {
        sectionGroup.style.display = 'none';
    }
}

function handleCreateBook(event) {
    event.preventDefault();
    const titulo = document.getElementById('book-title').value.trim();
    const autor = document.getElementById('book-author').value.trim();
    const categoria = document.getElementById('book-cat').value.trim();
    const proyecto_id = document.getElementById('book-proj-select').value;
    const seccion_proyecto = document.getElementById('book-section').value.trim();
    
    fetch('/api/books/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titulo, autor, categoria, proyecto_id, seccion_proyecto })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        closeNewBookModal();
        if (currentTab === 'projects' && activeProjectId === proyecto_id) {
            viewProjectDetail(proyecto_id);
        } else {
            fetchBooksData();
        }
    })
    .catch(err => {
        console.error('Error creating book:', err);
        alert('Error al añadir el libro.');
    });
}
