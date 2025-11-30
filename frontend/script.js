// Smart Task Analyzer - Frontend JavaScript

// Global state
let tasks = [];
let taskIdCounter = 1;
let currentView = 'list';
let analyzedTasks = [];
const API_URL = "https://task-analyzer-7sd6.onrender.com/api";

// Strategy descriptions
const strategyDescriptions = {
    'smart_balance': 'Balances urgency, importance, effort, and dependencies intelligently',
    'fastest_wins': 'Prioritizes low-effort tasks for quick wins',
    'high_impact': 'Prioritizes importance over everything else',
    'deadline_driven': 'Prioritizes based on due date urgency'
};

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    // Strategy selector change handler
    const strategySelect = document.getElementById('strategy');
    strategySelect.addEventListener('change', function () {
        updateStrategyDescription();
    });

    // Form submit handler
    const taskForm = document.getElementById('task-form');
    taskForm.addEventListener('submit', function (e) {
        e.preventDefault();
        addTaskFromForm();
    });

    // Load sample tasks
    loadSampleTasks();

    updateTaskPreview();
});

// Switch input mode
function switchInputMode(mode) {
    const formInput = document.getElementById('form-input');
    const jsonInput = document.getElementById('json-input');
    const formBtn = document.getElementById('form-mode-btn');
    const jsonBtn = document.getElementById('json-mode-btn');

    if (mode === 'form') {
        formInput.style.display = 'block';
        jsonInput.style.display = 'none';
        formBtn.classList.add('active');
        jsonBtn.classList.remove('active');
    } else {
        formInput.style.display = 'none';
        jsonInput.style.display = 'block';
        formBtn.classList.remove('active');
        jsonBtn.classList.add('active');
    }
}

// Update strategy description
function updateStrategyDescription() {
    const strategy = document.getElementById('strategy').value;
    const descriptionEl = document.getElementById('strategy-description');
    descriptionEl.textContent = strategyDescriptions[strategy] || '';
}

// Add task from form
function addTaskFromForm() {
    const form = document.getElementById('task-form');
    const formData = new FormData(form);

    const task = {
        id: taskIdCounter++,
        title: formData.get('title'),
        due_date: formData.get('due_date') || null,
        estimated_hours: formData.get('estimated_hours') ? parseFloat(formData.get('estimated_hours')) : null,
        importance: formData.get('importance') ? parseInt(formData.get('importance')) : 5,
        dependencies: formData.get('dependencies')
            ? formData.get('dependencies').split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
            : []
    };

    // Validate
    if (!task.title || task.title.trim() === '') {
        showMessage('Task title is required', 'error');
        return;
    }

    tasks.push(task);
    form.reset();
    updateTaskPreview();
    showMessage('Task added successfully', 'success');
}

// Load tasks from JSON
function loadTasksFromJSON() {
    const jsonText = document.getElementById('json-textarea').value.trim();

    if (!jsonText) {
        showMessage('Please enter JSON data', 'error');
        return;
    }

    try {
        const parsedTasks = JSON.parse(jsonText);

        if (!Array.isArray(parsedTasks)) {
            showMessage('JSON must be an array of tasks', 'error');
            return;
        }

        // Assign IDs if missing
        parsedTasks.forEach((task, index) => {
            if (!task.id) {
                task.id = taskIdCounter++;
            } else {
                taskIdCounter = Math.max(taskIdCounter, task.id + 1);
            }
        });

        tasks = parsedTasks;
        updateTaskPreview();
        showMessage(`Loaded ${tasks.length} task(s)`, 'success');

        // Switch to form mode to show preview
        switchInputMode('form');
    } catch (error) {
        showMessage(`Invalid JSON: ${error.message}`, 'error');
    }
}

// Update task preview
function updateTaskPreview() {
    const previewList = document.getElementById('task-preview-list');
    const taskCount = document.getElementById('task-count');

    taskCount.textContent = tasks.length;

    if (tasks.length === 0) {
        previewList.innerHTML = '<p style="color: var(--text-secondary);">No tasks added yet</p>';
        return;
    }

    previewList.innerHTML = tasks.map((task, index) => `
        <div class="task-preview-item">
            <div>
                <span class="task-title">${escapeHtml(task.title)}</span>
                ${task.due_date ? `<span style="color: var(--text-secondary); margin-left: 10px;">Due: ${task.due_date}</span>` : ''}
            </div>
            <button class="remove-btn" onclick="removeTask(${index})">Remove</button>
        </div>
    `).join('');
}

// Remove task
function removeTask(index) {
    tasks.splice(index, 1);
    updateTaskPreview();
    showMessage('Task removed', 'success');
}

// Clear all tasks
function clearTasks() {
    if (tasks.length === 0) return;

    if (confirm('Are you sure you want to clear all tasks?')) {
        tasks = [];
        taskIdCounter = 1;
        updateTaskPreview();
        showMessage('All tasks cleared', 'success');
    }
}

// Analyze tasks
async function analyzeTasks() {
    if (tasks.length === 0) {
        showMessage('Please add at least one task', 'error');
        return;
    }

    const strategy = document.getElementById('strategy').value;
    const analyzeBtn = document.getElementById('analyze-btn');
    const analyzeText = document.getElementById('analyze-text');
    const analyzeSpinner = document.getElementById('analyze-spinner');

    // Show loading state
    analyzeBtn.disabled = true;
    analyzeText.textContent = 'Analyzing...';
    analyzeSpinner.style.display = 'inline-block';


    try {
        const response = await fetch(`${API_URL}/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze tasks');
        }

        // Show warning if circular dependencies detected
        if (data.warning) {
            showMessage(data.warning, 'warning');
        }

        analyzedTasks = data.tasks;
        displayResults(data.tasks, strategy);

        // Load dependency graph
        await loadDependencyGraph();

        showMessage(`Analyzed ${data.tasks.length} task(s)`, 'success');

    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
        console.error('Analysis error:', error);
    } finally {
        // Reset button state
        analyzeBtn.disabled = false;
        analyzeText.textContent = 'Analyze Tasks';
        analyzeSpinner.style.display = 'none';
    }
}

// Display results
function displayResults(analyzedTasks, strategy) {
    const resultsContainer = document.getElementById('results-container');

    if (analyzedTasks.length === 0) {
        resultsContainer.innerHTML = '<div class="empty-state"><p>No tasks to display</p></div>';
        return;
    }

    // Respect current view
    if (currentView === 'matrix') {
        displayEisenhowerMatrix(analyzedTasks);
        return;
    }

    // Calculate priority levels
    const scores = analyzedTasks.map(t => t.priority_score);
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);
    const range = maxScore - minScore;

    const getPriorityLevel = (score) => {
        if (range === 0) return 'medium';
        const normalized = (score - minScore) / range;
        if (normalized >= 0.66) return 'high';
        if (normalized >= 0.33) return 'medium';
        return 'low';
    };

    resultsContainer.innerHTML = analyzedTasks.map((task, index) => {
        const priorityLevel = getPriorityLevel(task.priority_score);
        const priorityLabel = priorityLevel === 'high' ? 'High' : priorityLevel === 'medium' ? 'Medium' : 'Low';

        return `
            <div class="task-card ${priorityLevel}-priority">
                <div class="task-header">
                    <div class="task-title">#${index + 1} - ${escapeHtml(task.title)}</div>
                    <div>
                        <div class="priority-badge ${priorityLevel}">${priorityLabel} Priority</div>
                        <div class="priority-score">${task.priority_score.toFixed(1)}</div>
                    </div>
                </div>
                
                <div class="task-details">
                    ${task.due_date ? `
                        <div class="detail-item">
                            <span class="detail-label">Due Date</span>
                            <span class="detail-value">${formatDate(task.due_date)}</span>
                        </div>
                    ` : ''}
                    ${task.estimated_hours !== null && task.estimated_hours !== undefined ? `
                        <div class="detail-item">
                            <span class="detail-label">Estimated Hours</span>
                            <span class="detail-value">${task.estimated_hours}h</span>
                        </div>
                    ` : ''}
                    ${task.importance !== null && task.importance !== undefined ? `
                        <div class="detail-item">
                            <span class="detail-label">Importance</span>
                            <span class="detail-value">${task.importance}/10</span>
                        </div>
                    ` : ''}
                    ${task.dependencies && task.dependencies.length > 0 ? `
                        <div class="detail-item">
                            <span class="detail-label">Dependencies</span>
                            <span class="detail-value">${task.dependencies.join(', ')}</span>
                        </div>
                    ` : ''}
                </div>
                
                <div class="explanation">
                    <strong>Why this priority?</strong> ${escapeHtml(task.explanation || 'No explanation available')}
                </div>
                
                <div class="feedback-section">
                    <span class="feedback-label">Was this prioritization helpful?</span>
                    <div class="feedback-buttons">
                        <button class="feedback-btn helpful-btn" onclick="submitFeedback(${task.id}, '${escapeHtml(task.title)}', '${strategy}', ${task.priority_score}, true, ${JSON.stringify({
            due_date: task.due_date,
            estimated_hours: task.estimated_hours,
            importance: task.importance,
            dependencies: task.dependencies || []
        })}, event)">
                            ✓ Helpful
                        </button>
                        <button class="feedback-btn not-helpful-btn" onclick="submitFeedback(${task.id}, '${escapeHtml(task.title)}', '${strategy}', ${task.priority_score}, false, ${JSON.stringify({
            due_date: task.due_date,
            estimated_hours: task.estimated_hours,
            importance: task.importance,
            dependencies: task.dependencies || []
        })}, event)">
                            ✗ Not Helpful
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Show message
function showMessage(message, type = 'success') {
    const container = document.getElementById('message-container');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    messageEl.textContent = message;

    container.appendChild(messageEl);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageEl.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 300);
    }, 5000);
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'No date';
    const date = new Date(dateString + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Switch view mode
function switchView(view) {
    currentView = view;
    const listBtn = document.getElementById('list-view-btn');
    const matrixBtn = document.getElementById('matrix-view-btn');
    const graphBtn = document.getElementById('graph-view-btn');
    const resultsContainer = document.getElementById('results-container');
    const graphContainer = document.getElementById('dependency-graph-container');

    // Update button states
    listBtn.classList.remove('active');
    matrixBtn.classList.remove('active');
    graphBtn.classList.remove('active');

    if (view === 'list') {
        listBtn.classList.add('active');
        resultsContainer.style.display = 'block';
        graphContainer.style.display = 'none';
    } else if (view === 'matrix') {
        matrixBtn.classList.add('active');
        resultsContainer.style.display = 'block';
        graphContainer.style.display = 'none';
        displayEisenhowerMatrix(analyzedTasks);
    } else if (view === 'graph') {
        graphBtn.classList.add('active');
        resultsContainer.style.display = 'none';
        graphContainer.style.display = 'block';
    }
}

// Load and display dependency graph
async function loadDependencyGraph() {
    if (tasks.length === 0) return;

    try {
        const response = await fetch(`${API_URL}/tasks/dependency-graph/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load dependency graph');
        }

        renderDependencyGraph(data.graph, data.has_circular, data.cycle);
    } catch (error) {
        console.error('Error loading dependency graph:', error);
    }
}

// Render dependency graph visualization
function renderDependencyGraph(graphData, hasCircular, cycle) {
    const container = document.getElementById('graph-visualization');

    if (!graphData || graphData.nodes.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No dependencies to visualize</p>';
        return;
    }

    // Create SVG
    const width = 800;
    const height = Math.max(400, graphData.nodes.length * 80);
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.style.border = '1px solid var(--border-color)';
    svg.style.borderRadius = '8px';
    svg.style.background = 'white';

    // Layout nodes in a hierarchical structure
    const nodePositions = {};
    const nodeRadius = 30;
    const horizontalSpacing = 200;
    const verticalSpacing = 100;

    // Simple layout: arrange nodes in rows
    const nodesPerRow = Math.ceil(Math.sqrt(graphData.nodes.length));
    graphData.nodes.forEach((node, index) => {
        const row = Math.floor(index / nodesPerRow);
        const col = index % nodesPerRow;
        const x = 100 + col * horizontalSpacing;
        const y = 80 + row * verticalSpacing;
        nodePositions[node.id] = { x, y };
    });

    // Draw edges first (so they appear behind nodes)
    graphData.edges.forEach(edge => {
        const from = nodePositions[edge.from];
        const to = nodePositions[edge.to];

        if (from && to) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', from.x);
            line.setAttribute('y1', from.y);
            line.setAttribute('x2', to.x);
            line.setAttribute('y2', to.y);

            // Check if this edge is part of a cycle
            const isCircular = hasCircular &&
                graphData.circular_nodes.includes(edge.from) &&
                graphData.circular_nodes.includes(edge.to);

            line.setAttribute('stroke', isCircular ? '#e74c3c' : '#4a90e2');
            line.setAttribute('stroke-width', isCircular ? '3' : '2');
            line.setAttribute('marker-end', 'url(#arrowhead');
            if (isCircular) {
                line.setAttribute('stroke-dasharray', '5,5');
            }
            svg.appendChild(line);
        }
    });

    // Add arrow marker
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', 'arrowhead');
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '10');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '3');
    marker.setAttribute('orient', 'auto');
    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '0 0, 10 3, 0 6');
    polygon.setAttribute('fill', '#4a90e2');
    marker.appendChild(polygon);
    defs.appendChild(marker);
    svg.appendChild(defs);

    // Draw nodes
    graphData.nodes.forEach(node => {
        const pos = nodePositions[node.id];
        if (!pos) return;

        const isCircular = graphData.circular_nodes.includes(node.id);

        // Draw circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', pos.x);
        circle.setAttribute('cy', pos.y);
        circle.setAttribute('r', nodeRadius);
        circle.setAttribute('fill', isCircular ? '#fee' : '#e3f2fd');
        circle.setAttribute('stroke', isCircular ? '#e74c3c' : '#4a90e2');
        circle.setAttribute('stroke-width', isCircular ? '3' : '2');
        svg.appendChild(circle);

        // Draw text
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', pos.x);
        text.setAttribute('y', pos.y + 5);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '12');
        text.setAttribute('font-weight', '600');
        text.setAttribute('fill', '#2c3e50');
        text.textContent = node.id;
        svg.appendChild(text);

        // Draw title below
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        title.setAttribute('x', pos.x);
        title.setAttribute('y', pos.y + nodeRadius + 20);
        title.setAttribute('text-anchor', 'middle');
        title.setAttribute('font-size', '10');
        title.setAttribute('fill', '#7f8c8d');
        title.textContent = node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title;
        svg.appendChild(title);
    });

    // Add warning if circular dependencies exist
    if (hasCircular) {
        const warning = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        warning.setAttribute('x', width / 2);
        warning.setAttribute('y', 30);
        warning.setAttribute('text-anchor', 'middle');
        warning.setAttribute('font-size', '14');
        warning.setAttribute('font-weight', '600');
        warning.setAttribute('fill', '#e74c3c');
        warning.textContent = `⚠ Circular Dependencies Detected: Tasks ${cycle.join(', ')}`;
        svg.appendChild(warning);
    }

    container.innerHTML = '';
    container.appendChild(svg);
}

// Display Eisenhower Matrix
function displayEisenhowerMatrix(tasks) {
    const resultsContainer = document.getElementById('results-container');

    if (tasks.length === 0) {
        resultsContainer.innerHTML = '<div class="empty-state"><p>No tasks to display</p></div>';
        return;
    }

    // Calculate urgency and importance for each task
    // Urgency: normalize priority_score to 0-10 scale, or use due date urgency
    // Importance: use task.importance (1-10)
    const maxScore = Math.max(...tasks.map(t => t.priority_score || 0));
    const minScore = Math.min(...tasks.map(t => t.priority_score || 0));
    const scoreRange = maxScore - minScore || 1;

    const matrixTasks = tasks.map(task => {
        // Calculate urgency from due date (0-10 scale)
        let urgency = calculateUrgencyForMatrix(task);

        // Also consider priority score as a factor
        const normalizedScore = scoreRange > 0 ? ((task.priority_score - minScore) / scoreRange) * 10 : 5;
        urgency = (urgency * 0.7 + normalizedScore * 0.3); // Blend both

        const importance = task.importance || 5;
        return { ...task, urgency, importance };
    });

    // Calculate thresholds (median values)
    const urgencies = matrixTasks.map(t => t.urgency);
    const importances = matrixTasks.map(t => t.importance);
    const urgencyThreshold = urgencies.length > 0 ?
        urgencies.sort((a, b) => a - b)[Math.floor(urgencies.length / 2)] : 5;
    const importanceThreshold = importances.length > 0 ?
        importances.sort((a, b) => a - b)[Math.floor(importances.length / 2)] : 5;

    // Categorize into quadrants
    const quadrants = {
        'urgent-important': matrixTasks.filter(t => t.urgency >= urgencyThreshold && t.importance >= importanceThreshold),
        'not-urgent-important': matrixTasks.filter(t => t.urgency < urgencyThreshold && t.importance >= importanceThreshold),
        'urgent-not-important': matrixTasks.filter(t => t.urgency >= urgencyThreshold && t.importance < importanceThreshold),
        'not-urgent-not-important': matrixTasks.filter(t => t.urgency < urgencyThreshold && t.importance < importanceThreshold)
    };

    resultsContainer.innerHTML = `
        <div class="eisenhower-matrix">
            <div class="matrix-header">
                <div class="matrix-axis-label importance-label">Important</div>
                <div class="matrix-axis-label urgency-label">Urgent</div>
            </div>
            <div class="matrix-grid">
                <div class="matrix-quadrant urgent-important">
                    <h3>🔴 Do First<br><small>Urgent & Important</small></h3>
                    <div class="quadrant-count">${quadrants['urgent-important'].length} task(s)</div>
                    <div class="quadrant-tasks">
                        ${quadrants['urgent-important'].length === 0 ?
            '<p class="empty-quadrant">No tasks</p>' :
            quadrants['urgent-important'].map(task => `
                            <div class="matrix-task-card">
                                <strong>${escapeHtml(task.title)}</strong>
                                <div class="matrix-scores">
                                    <span>Urgency: ${task.urgency.toFixed(1)}/10</span>
                                    <span>Importance: ${task.importance}/10</span>
                                </div>
                                ${task.due_date ? `<div class="matrix-due-date">Due: ${formatDate(task.due_date)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="matrix-quadrant not-urgent-important">
                    <h3>🟢 Schedule<br><small>Not Urgent & Important</small></h3>
                    <div class="quadrant-count">${quadrants['not-urgent-important'].length} task(s)</div>
                    <div class="quadrant-tasks">
                        ${quadrants['not-urgent-important'].length === 0 ?
            '<p class="empty-quadrant">No tasks</p>' :
            quadrants['not-urgent-important'].map(task => `
                            <div class="matrix-task-card">
                                <strong>${escapeHtml(task.title)}</strong>
                                <div class="matrix-scores">
                                    <span>Urgency: ${task.urgency.toFixed(1)}/10</span>
                                    <span>Importance: ${task.importance}/10</span>
                                </div>
                                ${task.due_date ? `<div class="matrix-due-date">Due: ${formatDate(task.due_date)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="matrix-quadrant urgent-not-important">
                    <h3>🟡 Delegate<br><small>Urgent & Not Important</small></h3>
                    <div class="quadrant-count">${quadrants['urgent-not-important'].length} task(s)</div>
                    <div class="quadrant-tasks">
                        ${quadrants['urgent-not-important'].length === 0 ?
            '<p class="empty-quadrant">No tasks</p>' :
            quadrants['urgent-not-important'].map(task => `
                            <div class="matrix-task-card">
                                <strong>${escapeHtml(task.title)}</strong>
                                <div class="matrix-scores">
                                    <span>Urgency: ${task.urgency.toFixed(1)}/10</span>
                                    <span>Importance: ${task.importance}/10</span>
                                </div>
                                ${task.due_date ? `<div class="matrix-due-date">Due: ${formatDate(task.due_date)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="matrix-quadrant not-urgent-not-important">
                    <h3>⚪ Eliminate<br><small>Not Urgent & Not Important</small></h3>
                    <div class="quadrant-count">${quadrants['not-urgent-not-important'].length} task(s)</div>
                    <div class="quadrant-tasks">
                        ${quadrants['not-urgent-not-important'].length === 0 ?
            '<p class="empty-quadrant">No tasks</p>' :
            quadrants['not-urgent-not-important'].map(task => `
                            <div class="matrix-task-card">
                                <strong>${escapeHtml(task.title)}</strong>
                                <div class="matrix-scores">
                                    <span>Urgency: ${task.urgency.toFixed(1)}/10</span>
                                    <span>Importance: ${task.importance}/10</span>
                                </div>
                                ${task.due_date ? `<div class="matrix-due-date">Due: ${formatDate(task.due_date)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Calculate urgency score for matrix (0-10 scale)
function calculateUrgencyForMatrix(task) {
    if (!task.due_date) return 3; // No due date = low urgency

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(task.due_date + 'T00:00:00');
    const daysDiff = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

    if (daysDiff < 0) return 10; // Overdue
    if (daysDiff === 0) return 10; // Due today
    if (daysDiff <= 1) return 9;
    if (daysDiff <= 3) return 8;
    if (daysDiff <= 7) return 6;
    if (daysDiff <= 14) return 4;
    return 2;
}

// Submit feedback
async function submitFeedback(taskId, taskTitle, strategy, priorityScore, wasHelpful, taskAttributes, event) {
    try {
        const response = await fetch(`${API_URL}/tasks/feedback/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task_id: taskId,
                task_title: taskTitle,
                strategy: strategy,
                priority_score: priorityScore,
                was_helpful: wasHelpful,
                task_attributes: taskAttributes
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to submit feedback');
        }

        showMessage(
            wasHelpful
                ? 'Thank you for your feedback! The system will learn from this.'
                : 'Thank you for your feedback! We\'ll use this to improve prioritization.',
            'success'
        );

        // Disable feedback buttons for this task
        if (event && event.target) {
            const buttons = event.target.closest('.feedback-section').querySelectorAll('.feedback-btn');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.6';
            });

            // Highlight the selected button
            event.target.style.background = wasHelpful ? '#50c878' : '#e74c3c';
            event.target.style.color = 'white';
        }

    } catch (error) {
        showMessage(`Error submitting feedback: ${error.message}`, 'error');
        console.error('Feedback error:', error);
    }
}

// Load sample tasks
function loadSampleTasks() {
    const sampleTasks = [
        {
            "title": "Fix login bug",
            "due_date": "2025-11-30",
            "estimated_hours": 3,
            "importance": 8,
            "dependencies": []
        },
        {
            "title": "Write documentation",
            "due_date": "2025-12-15",
            "estimated_hours": 5,
            "importance": 6,
            "dependencies": [1]
        },
        {
            "title": "Code review for PR #42",
            "due_date": "2025-11-28",
            "estimated_hours": 2,
            "importance": 7,
            "dependencies": []
        },
        {
            "title": "Update dependencies",
            "due_date": null,
            "estimated_hours": 4,
            "importance": 5,
            "dependencies": []
        }
    ];

    // Assign IDs
    sampleTasks.forEach((task, index) => {
        task.id = index + 1;
    });

    tasks = sampleTasks;
    taskIdCounter = sampleTasks.length + 1;
    updateTaskPreview();
}

