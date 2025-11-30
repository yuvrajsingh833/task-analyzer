# Smart Task Analyzer

A mini-application that intelligently scores and prioritizes tasks based on multiple factors including urgency, importance, effort, and dependencies. This project demonstrates problem-solving ability, algorithmic thinking, and clean code practices.

## 🎯 Features

- **Multiple Scoring Strategies**: Choose from 4 different prioritization algorithms
  - **Smart Balance**: Intelligently balances all factors (recommended)
  - **Fastest Wins**: Prioritizes low-effort tasks for quick wins
  - **High Impact**: Prioritizes importance over everything else
  - **Deadline Driven**: Prioritizes based on due date urgency

- **Intelligent Algorithm**: Considers multiple factors:
  - **Urgency**: Days until due date (with exponential penalty for overdue tasks)
  - **Importance**: User-provided rating (1-10 scale)
  - **Effort**: Estimated hours (lower effort = higher priority for quick wins)
  - **Dependencies**: Tasks that block other tasks get higher priority

- **Edge Case Handling**:
  - Past due dates with exponential penalty
  - Missing or invalid data validation
  - Circular dependency detection
  - Graceful error handling
 
  - Supports:
- Missing fields  
- Date parsing  
- Overdue exponential penalty  
- Dynamic weighting  
- Circular dependency detection  

---

### Visual Features**
#### **✔ Eisenhower Matrix View**
Tasks plotted in a 2×2 grid  
(Important vs Urgent)

#### ** Dependency Graph Visualization**
- Auto-generated SVG graph  
- Shows nodes + directional edges  
- Red highlighting for circular dependencies  
- Cycle path shown at top if detected  

---

### Learning System (Feedback API)**
Users can mark results as:

- **Helpful**  
- **Not Helpful**

Feedback is sent to the backend via:  
`POST {API_URL}/api/tasks/feedback/`

This system enables future improvements and adaptive scoring.

---

###  Unit Tests
Complete test suite added for:

- Scoring logic  
- Urgency/Importance calculation  
- Dependency scoring  
- Circular detection  
- Strategy correctness  

---

### API-Driven Architecture**
Backend: **Django 5 + REST-style views**  
Frontend: **HTML/CSS/JS (no frameworks)**



- **Modern UI**: Clean, responsive interface with:
  - Form-based and JSON input modes
  - Visual priority indicators (color-coded)
  - Detailed explanations for each priority score
  - Real-time task preview

## 🏗️ Architecture & Design Decisions

### Algorithm Design

The core challenge was designing a scoring function that intelligently weighs multiple competing factors. Here's how each strategy works:

#### Smart Balance (Default Strategy)

This is the most sophisticated algorithm, using dynamic weighting based on context:

1. **Urgency Calculation**:
   - Past due: Exponential penalty (100 + days_overdue × 2.5, capped at 200)
   - Due today: 100 points
   - Due tomorrow: 90 points
   - Due in 2-3 days: 75 points
   - Due in a week: 60 points
   - Due in 2 weeks: 45 points
   - Due in a month: 30 points
   - Far future: 15 points

2. **Dynamic Weighting**:
   - **Overdue tasks**: Urgency weight = 2.5, Importance = 1.0, Effort = 0.3
   - **Due soon (≤3 days)**: Urgency = 1.5, Importance = 1.2, Effort = 0.5
   - **Normal**: Urgency = 1.0, Importance = 1.0, Effort = 0.8

3. **Dependency Boost**: Tasks that block other tasks get +20 points per blocked task

4. **Effort Score**: Inverted (lower hours = higher score): `50 / (hours + 1)`

**Why this approach?**
- Overdue tasks need immediate attention, so urgency dominates
- Soon-due tasks balance urgency with importance
- Normal tasks balance all factors for optimal productivity
- Dependencies ensure blocking tasks are prioritized

#### Fastest Wins Strategy

Prioritizes low-effort tasks:
- Effort score: `100 / (hours + 1)` (primary factor)
- Urgency: 30% weight
- Importance: Linear scaling

**Use case**: When you need quick momentum or have many small tasks.

#### High Impact Strategy

Prioritizes importance:
- Importance: `importance × 20` (primary factor)
- Dependency boost: `+15 per blocked task`
- Urgency: 40% weight

**Use case**: When strategic value matters more than deadlines.

#### Deadline Driven Strategy

Prioritizes urgency:
- Urgency: `urgency × 2.0` (primary factor)
- Importance: `importance × 3.0`
- Effort bonus: `20 - hours` (prefers lower effort when urgency is similar)

**Use case**: When deadlines are critical and non-negotiable.

### Edge Case Handling

1. **Past Due Dates**: Exponential penalty ensures overdue tasks are always prioritized, but doesn't let extremely old tasks dominate forever (capped at 200).

2. **Missing Data**: 
   - Missing due date: Moderate urgency (30 points)
   - Missing importance: Defaults to 5 (neutral)
   - Missing estimated_hours: Defaults to 8 (average)

3. **Circular Dependencies**: 
   - Detected using DFS algorithm
   - Tasks in cycles are flagged with warnings
   - Still processed but user is informed

4. **Invalid Data**: 
   - Comprehensive validation before scoring
   - Returns error messages instead of crashing
   - Graceful degradation

### Code Quality Decisions

1. **Separation of Concerns**:
   - `scoring.py`: Pure algorithm logic (testable, reusable)
   - `views.py`: API layer (handles HTTP, validation)
   - Frontend: Presentation layer (UI, user interaction)

2. **Type Hints**: Used throughout for better code clarity and IDE support

3. **Error Handling**: 
   - Validation at multiple levels (frontend + backend)
   - Meaningful error messages
   - No silent failures

4. **Documentation**: 
   - Docstrings for all functions
   - Inline comments for complex logic
   - README with design rationale

## 📁 Project Structure

```
task-analyzer/
├── backend/                  # Django project
│   ├── settings.py           # Django configuration
│   ├── urls.py               # Main URL routing
│   └── ...
├── tasks/                    # Tasks app
│   ├── scoring.py            # Core algorithm (THE BRAIN)
│   ├── views.py              # API endpoints
│   ├── urls.py               # App URL routing
│   └── ...
├── frontend/                 # Frontend files
│   ├── index.html            # Main UI
│   ├── styles.css            # Styling
│   └── script.js             # Frontend logic
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Setup & Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)

### Installation Steps

1. **Clone or navigate to the project directory**:
   ```bash
   cd task-analyzer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - **Windows (Git Bash)**:
     ```bash
     source venv/Scripts/activate
     ```
   - **Windows (Command Prompt)**:
     ```bash
     venv\Scripts\activate
     ```
   - **Mac/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations** (optional, no database models currently):
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Open your browser** and navigate to:
   ```
   http://127.0.0.1:8000
   ```

## 📖 Usage

### Adding Tasks

**Method 1: Form Input**
1. Use the form to add tasks one by one
2. Fill in title (required), due date, estimated hours, importance, and dependencies
3. Click "Add Task" after each task

**Method 2: JSON Input**
1. Click "JSON Input" tab
2. Paste a JSON array of tasks:
   ```json
   [
     {
       "title": "Fix login bug",
       "due_date": "2025-11-30",
       "estimated_hours": 3,
       "importance": 8,
       "dependencies": []
     }
   ]
   ```
3. Click "Load Tasks"

### Analyzing Tasks

1. Select a sorting strategy from the dropdown
2. Click "Analyze Tasks"
3. View prioritized results with:
   - Priority scores
   - Color-coded priority levels (High/Medium/Low)
   - Detailed explanations for each score

### API Endpoints

#### POST `{API_URL}/api/tasks/analyze/`

Analyze and sort tasks by priority.

**Request Body**:
```json
{
  "tasks": [
    {
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ],
  "strategy": "smart_balance"
}
```

**Response**:
```json
{
  "tasks": [
    {
      "title": "Fix login bug",
      "priority_score": 125.5,
      "explanation": "Smart Balance: due in 2 days, high importance (8/10)"
    }
  ],
  "strategy": "smart_balance",
  "count": 1
}
```

#### GET `{API_URL}/api/tasks/suggest/`

Get top 3 recommended tasks.

**Query Parameters**:
- `strategy`: Scoring strategy (default: "smart_balance")
- `tasks`: JSON array of tasks (URL-encoded)

**Response**:
```json
{
  "suggestions": [...],
  "strategy": "smart_balance",
  "count": 3
}
```

## 🧪 Testing Edge Cases

The system handles various edge cases:

1. **Past Due Dates**: Try a task with `due_date: "2020-01-01"` - it will get high priority
2. **Missing Fields**: Tasks with missing optional fields are handled gracefully
3. **Circular Dependencies**: Try tasks with circular dependencies - warnings will appear
4. **Invalid Data**: Invalid dates, out-of-range importance, etc. are validated

## 🎨 UI Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Visual Priority Indicators**: Color-coded cards (Red=High, Orange=Medium, Green=Low)
- **Real-time Preview**: See tasks as you add them
- **Error Handling**: User-friendly error messages
- **Loading States**: Visual feedback during API calls

## 🔧 Technical Stack

- **Backend**: Python 3.12, Django 5.2.8
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (no frameworks)
- **Database**: SQLite (default Django database)
- **API**: RESTful JSON API

## 📝 Design Philosophy

1. **Simplicity**: No unnecessary complexity - clean, readable code
2. **Flexibility**: Multiple strategies for different use cases
3. **Robustness**: Handles edge cases gracefully
4. **User Experience**: Clear feedback, intuitive interface
5. **Maintainability**: Well-documented, modular code

## 🚧 Future Enhancements

Potential improvements (not implemented):
- User authentication and task persistence
- Task categories/tags
- Recurring tasks
- Task history and analytics
- Custom strategy configuration
- Export/import functionality


## 👤 Author

Created By Yuvraj Singh Rathore.aaaa
