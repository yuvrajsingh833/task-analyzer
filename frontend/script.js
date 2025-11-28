// Smart Task Analyzer - Frontend JavaScript

// Global state
let tasks = [];
let taskIdCounter = 1;

// Strategy descriptions
const strategyDescriptions = {
    'smart_balance': 'Balances urgency, importance, effort, and dependencies intelligently',
    'fastest_wins': 'Prioritizes low-effort tasks for quick wins',
    'high_impact': 'Prioritizes importance over everything else',
    'deadline_driven': 'Prioritizes based on due date urgency'
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Strategy selector change handler
    const strategySelect = document.getElementById('strategy');
    strategySelect.addEventListener('change', function() {
        updateStrategyDescription();
    });
    
    // Form submit handler
    const taskForm = document.getElementById('task-form');
    taskForm.addEventListener('submit', function(e) {
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
        const response = await fetch('/api/tasks/analyze/', {
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
        
        displayResults(data.tasks, strategy);
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

