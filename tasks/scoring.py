"""
Smart Task Analyzer - Priority Scoring Algorithm

This module implements multiple scoring strategies for task prioritization:
- Fastest Wins: Prioritizes low-effort tasks
- High Impact: Prioritizes importance over everything
- Deadline Driven: Prioritizes based on due date urgency
- Smart Balance: Balances all factors intelligently
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import json


def validate_task(task: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate task data and return (is_valid, error_message).
    
    Handles edge cases:
    - Missing required fields
    - Invalid data types
    - Invalid date formats
    - Invalid importance range
    """
    required_fields = ['title']
    for field in required_fields:
        if field not in task:
            return False, f"Missing required field: {field}"
    
    # Validate importance (1-10)
    if 'importance' in task:
        try:
            importance = int(task['importance'])
            if not (1 <= importance <= 10):
                return False, f"Importance must be between 1 and 10, got {importance}"
        except (ValueError, TypeError):
            return False, "Importance must be an integer"
    
    # Validate estimated_hours
    if 'estimated_hours' in task:
        try:
            hours = float(task['estimated_hours'])
            if hours < 0:
                return False, "Estimated hours must be non-negative"
        except (ValueError, TypeError):
            return False, "Estimated hours must be a number"
    
    # Validate due_date
    if 'due_date' in task and task['due_date']:
        try:
            if isinstance(task['due_date'], str):
                datetime.strptime(task['due_date'], '%Y-%m-%d')
        except ValueError:
            return False, f"Invalid date format: {task['due_date']}. Expected YYYY-MM-DD"
    
    # Validate dependencies
    if 'dependencies' in task:
        if not isinstance(task['dependencies'], list):
            return False, "Dependencies must be a list"
    
    return True, None


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None
    if isinstance(date_str, str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def calculate_urgency_score(due_date: Optional[date], today: date) -> float:
    """
    Calculate urgency score based on due date.
    
    - Past due dates get high urgency (exponential penalty)
    - Near-term dates get high urgency
    - Far future dates get low urgency
    
    Returns a score between 0 and 100.
    """
    if not due_date:
        return 30.0  # No due date = moderate urgency
    
    days_diff = (due_date - today).days
    
    if days_diff < 0:
        # Past due: exponential penalty
        # 1 day overdue = 100, 7 days = ~150, 30 days = ~200
        return min(200.0, 100.0 + abs(days_diff) * 2.5)
    elif days_diff == 0:
        return 100.0  # Due today
    elif days_diff <= 1:
        return 90.0   # Due tomorrow
    elif days_diff <= 3:
        return 75.0   # Due in 2-3 days
    elif days_diff <= 7:
        return 60.0   # Due in a week
    elif days_diff <= 14:
        return 45.0   # Due in 2 weeks
    elif days_diff <= 30:
        return 30.0   # Due in a month
    else:
        return 15.0   # Far future


def build_dependency_graph(tasks: List[Dict]) -> Dict:
    """
    Build dependency graph structure for visualization.
    
    Returns:
        {
            'nodes': [{'id': task_id, 'title': task_title, ...}],
            'edges': [{'from': task_id, 'to': dep_id}],
            'circular_nodes': set of task_ids in cycles
        }
    """
    task_ids = {task.get('id', i): i for i, task in enumerate(tasks)}
    nodes = []
    edges = []
    
    # Build nodes
    for i, task in enumerate(tasks):
        task_id = task.get('id', i)
        nodes.append({
            'id': task_id,
            'title': task.get('title', f'Task {task_id}'),
            'label': f"{task_id}: {task.get('title', 'Untitled')[:20]}"
        })
    
    # Build edges
    for i, task in enumerate(tasks):
        task_id = task.get('id', i)
        deps = task.get('dependencies', [])
        for dep in deps:
            if dep in task_ids:
                edges.append({
                    'from': task_id,
                    'to': dep
                })
    
    # Detect circular dependencies
    has_circular, cycle = detect_circular_dependencies(tasks)
    circular_nodes = set(cycle) if has_circular else set()
    
    return {
        'nodes': nodes,
        'edges': edges,
        'circular_nodes': list(circular_nodes)
    }


def detect_circular_dependencies(tasks: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Detect circular dependencies in task list.
    
    Returns (has_circular, cycle_path).
    Uses DFS to detect cycles.
    """
    # Build dependency graph
    task_ids = {task.get('id', i): i for i, task in enumerate(tasks)}
    graph = {}
    
    for i, task in enumerate(tasks):
        task_id = task.get('id', i)
        graph[task_id] = []
        deps = task.get('dependencies', [])
        for dep in deps:
            if dep in task_ids:
                graph[task_id].append(dep)
    
    # DFS to detect cycles
    visited = set()
    rec_stack = set()
    cycle_path = []
    
    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path):
                    return True
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycle_path.extend(path[cycle_start:] + [neighbor])
                return True
        
        rec_stack.remove(node)
        path.pop()
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node, []):
                return True, cycle_path
    
    return False, []


def count_blocked_tasks(task_id: str, tasks: List[Dict]) -> int:
    """Count how many tasks depend on this task."""
    count = 0
    for task in tasks:
        deps = task.get('dependencies', [])
        if task_id in deps:
            count += 1
    return count


def score_task_fastest_wins(task: Dict, tasks: List[Dict], today: date) -> Tuple[float, str]:
    """
    Strategy: Prioritize low-effort tasks for quick wins.
    
    Scoring:
    - Low effort = high score
    - Still considers urgency and importance but weights effort heavily
    """
    estimated_hours = task.get('estimated_hours', 8)
    importance = task.get('importance', 5)
    due_date = parse_date(task.get('due_date'))
    
    # Effort score: lower hours = higher score (inverted)
    # 1 hour = 100, 8 hours = 50, 16 hours = 25
    effort_score = max(10.0, 100.0 / (estimated_hours + 1))
    
    # Urgency still matters but less
    urgency_score = calculate_urgency_score(due_date, today) * 0.3
    
    # Importance matters but less
    importance_score = importance * 5.0
    
    total_score = effort_score + urgency_score + importance_score
    
    explanation = f"Fastest Wins: Low effort ({estimated_hours}h) prioritized"
    if due_date:
        days_diff = (due_date - today).days
        if days_diff < 0:
            explanation += f", but overdue by {abs(days_diff)} days"
        elif days_diff <= 3:
            explanation += f", due in {days_diff} days"
    
    return total_score, explanation


def score_task_high_impact(task: Dict, tasks: List[Dict], today: date) -> Tuple[float, str]:
    """
    Strategy: Prioritize importance over everything else.
    
    Scoring:
    - Importance is the primary factor
    - Dependencies boost score (blocking other tasks)
    - Urgency is secondary
    """
    importance = task.get('importance', 5)
    due_date = parse_date(task.get('due_date'))
    task_id = task.get('id', tasks.index(task) if task in tasks else 0)
    
    # Importance is the main factor (1-10 scale, multiplied by 20)
    importance_score = importance * 20.0
    
    # Dependencies boost: tasks that block others get higher priority
    blocked_count = count_blocked_tasks(task_id, tasks)
    dependency_boost = blocked_count * 15.0
    
    # Urgency matters but less
    urgency_score = calculate_urgency_score(due_date, today) * 0.4
    
    total_score = importance_score + dependency_boost + urgency_score
    
    explanation = f"High Impact: Importance {importance}/10"
    if blocked_count > 0:
        explanation += f", blocks {blocked_count} other task(s)"
    if due_date:
        days_diff = (due_date - today).days
        if days_diff < 0:
            explanation += f", overdue by {abs(days_diff)} days"
    
    return total_score, explanation


def score_task_deadline_driven(task: Dict, tasks: List[Dict], today: date) -> Tuple[float, str]:
    """
    Strategy: Prioritize based on due date urgency.
    
    Scoring:
    - Urgency is the primary factor
    - Past due tasks get highest priority
    - No due date = low priority
    """
    due_date = parse_date(task.get('due_date'))
    importance = task.get('importance', 5)
    
    # Urgency is the main factor
    urgency_score = calculate_urgency_score(due_date, today) * 2.0
    
    # Importance is secondary
    importance_score = importance * 3.0
    
    # Effort: slightly prefer lower effort when urgency is similar
    estimated_hours = task.get('estimated_hours', 8)
    effort_bonus = max(0, 20.0 - estimated_hours)
    
    total_score = urgency_score + importance_score + effort_bonus
    
    if due_date:
        days_diff = (due_date - today).days
        if days_diff < 0:
            explanation = f"Deadline Driven: OVERDUE by {abs(days_diff)} days"
        elif days_diff == 0:
            explanation = "Deadline Driven: Due TODAY"
        elif days_diff <= 3:
            explanation = f"Deadline Driven: Due in {days_diff} days (urgent)"
        else:
            explanation = f"Deadline Driven: Due in {days_diff} days"
    else:
        explanation = "Deadline Driven: No due date (low priority)"
    
    return total_score, explanation


def score_task_smart_balance(task: Dict, tasks: List[Dict], today: date) -> Tuple[float, str]:
    """
    Strategy: Intelligently balance all factors.
    
    This is the "smart" algorithm that considers:
    - Urgency (with exponential penalty for overdue)
    - Importance (user-provided)
    - Effort (quick wins when appropriate)
    - Dependencies (blocking other tasks)
    
    The algorithm uses weighted scoring with dynamic adjustments.
    """
    due_date = parse_date(task.get('due_date'))
    importance = task.get('importance', 5)
    estimated_hours = task.get('estimated_hours', 8)
    task_id = task.get('id', tasks.index(task) if task in tasks else 0)
    
    # Calculate base components
    urgency_score = calculate_urgency_score(due_date, today)
    importance_score = importance * 10.0
    
    # Effort: inverted (lower = better), but not as dominant as "Fastest Wins"
    effort_score = max(10.0, 50.0 / (estimated_hours + 1))
    
    # Dependency boost: tasks blocking others get priority
    blocked_count = count_blocked_tasks(task_id, tasks)
    dependency_boost = blocked_count * 20.0
    
    # Smart weighting based on context
    # If task is overdue, urgency dominates
    if due_date and (due_date - today).days < 0:
        urgency_weight = 2.5
        importance_weight = 1.0
        effort_weight = 0.3
    # If task is due soon, balance urgency and importance
    elif due_date and (due_date - today).days <= 3:
        urgency_weight = 1.5
        importance_weight = 1.2
        effort_weight = 0.5
    # Otherwise, balance all factors
    else:
        urgency_weight = 1.0
        importance_weight = 1.0
        effort_weight = 0.8
    
    total_score = (
        urgency_score * urgency_weight +
        importance_score * importance_weight +
        effort_score * effort_weight +
        dependency_boost
    )
    
    # Build explanation
    factors = []
    if due_date:
        days_diff = (due_date - today).days
        if days_diff < 0:
            factors.append(f"OVERDUE ({abs(days_diff)} days)")
        elif days_diff <= 3:
            factors.append(f"due in {days_diff} days")
    if importance >= 8:
        factors.append(f"high importance ({importance}/10)")
    if estimated_hours <= 2:
        factors.append("quick win")
    if blocked_count > 0:
        factors.append(f"blocks {blocked_count} task(s)")
    
    explanation = "Smart Balance: " + ", ".join(factors) if factors else "Smart Balance: Balanced priority"
    
    return total_score, explanation


def score_task(task: Dict, tasks: List[Dict], strategy: str = 'smart_balance', today: Optional[date] = None) -> Tuple[float, str]:
    """
    Main scoring function that routes to the appropriate strategy.
    
    Args:
        task: Task dictionary
        tasks: List of all tasks (for dependency analysis)
        strategy: One of 'fastest_wins', 'high_impact', 'deadline_driven', 'smart_balance'
        today: Current date (defaults to today)
    
    Returns:
        Tuple of (score, explanation)
    """
    if today is None:
        today = date.today()
    
    # Validate task
    is_valid, error = validate_task(task)
    if not is_valid:
        return 0.0, f"Invalid task: {error}"
    
    # Route to appropriate strategy
    strategy_map = {
        'fastest_wins': score_task_fastest_wins,
        'high_impact': score_task_high_impact,
        'deadline_driven': score_task_deadline_driven,
        'smart_balance': score_task_smart_balance,
    }
    
    if strategy not in strategy_map:
        strategy = 'smart_balance'  # Default
    
    return strategy_map[strategy](task, tasks, today)


def analyze_tasks(tasks: List[Dict], strategy: str = 'smart_balance') -> List[Dict]:
    """
    Analyze and sort tasks by priority score.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy to use
    
    Returns:
        List of tasks with added 'priority_score' and 'explanation' fields, sorted by score (descending)
    """
    if not tasks:
        return []
    
    # Check for circular dependencies
    has_circular, cycle = detect_circular_dependencies(tasks)
    if has_circular:
        # Still process but warn in explanation
        for task in tasks:
            task_id = task.get('id', tasks.index(task))
            if task_id in cycle:
                task['_circular_warning'] = True
    
    today = date.today()
    
    # Score all tasks
    scored_tasks = []
    for task in tasks:
        score, explanation = score_task(task, tasks, strategy, today)
        task_copy = task.copy()
        task_copy['priority_score'] = round(score, 2)
        task_copy['explanation'] = explanation
        
        # Add circular dependency warning if applicable
        if task_copy.get('_circular_warning'):
            task_copy['explanation'] += " [WARNING: Part of circular dependency]"
            del task_copy['_circular_warning']
        
        scored_tasks.append(task_copy)
    
    # Sort by score (descending)
    scored_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return scored_tasks


def get_top_tasks(tasks: List[Dict], strategy: str = 'smart_balance', top_n: int = 3) -> List[Dict]:
    """
    Get top N tasks with detailed explanations.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy to use
        top_n: Number of top tasks to return
    
    Returns:
        List of top N tasks with priority scores and explanations
    """
    analyzed = analyze_tasks(tasks, strategy)
    return analyzed[:top_n]

