"""
API Views for Smart Task Analyzer

Endpoints:
- POST /api/tasks/analyze/ - Analyze and sort tasks by priority
- GET /api/tasks/suggest/ - Get top 3 recommended tasks
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .scoring import analyze_tasks, get_top_tasks, detect_circular_dependencies


@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks_view(request):
    """
    POST /api/tasks/analyze/
    
    Accepts a JSON body with:
    {
        "tasks": [...],
        "strategy": "smart_balance"  // optional
    }
    
    Returns sorted tasks with priority scores.
    """
    try:
        # Parse request body
        body = json.loads(request.body)
        tasks = body.get('tasks', [])
        strategy = body.get('strategy', 'smart_balance')
        
        # Validate tasks is a list
        if not isinstance(tasks, list):
            return JsonResponse({
                'error': 'Tasks must be a list'
            }, status=400)
        
        # Check for circular dependencies
        has_circular, cycle = detect_circular_dependencies(tasks)
        warning = None
        if has_circular:
            warning = f"Warning: Circular dependency detected involving tasks: {cycle}"
        
        # Analyze tasks
        analyzed_tasks = analyze_tasks(tasks, strategy)
        
        response_data = {
            'tasks': analyzed_tasks,
            'strategy': strategy,
            'count': len(analyzed_tasks)
        }
        
        if warning:
            response_data['warning'] = warning
        
        return JsonResponse(response_data, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def suggest_tasks_view(request):
    """
    GET/POST /api/tasks/suggest/
    
    Returns top 3 tasks with explanations.
    
    GET: ?strategy=smart_balance&tasks=[...] (URL-encoded JSON)
    POST: { "tasks": [...], "strategy": "smart_balance" }
    
    Note: In a real app, tasks would come from a database.
    For this demo, we accept tasks as a query parameter or JSON body.
    """
    try:
        # Get strategy
        if request.method == 'POST':
            try:
                body = json.loads(request.body)
                strategy = body.get('strategy', 'smart_balance')
                tasks = body.get('tasks', [])
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON in request body'
                }, status=400)
        else:
            strategy = request.GET.get('strategy', 'smart_balance')
            # Try to get tasks from query parameter (URL-encoded JSON)
            tasks_json = request.GET.get('tasks', '[]')
            try:
                tasks = json.loads(tasks_json)
            except json.JSONDecodeError:
                tasks = []
        
        if not isinstance(tasks, list):
            return JsonResponse({
                'error': 'Tasks must be a list'
            }, status=400)
        
        if not tasks:
            return JsonResponse({
                'error': 'No tasks provided. Please provide tasks in the request.',
                'suggestions': []
            }, status=400)
        
        # Get top 3 tasks
        top_tasks = get_top_tasks(tasks, strategy, top_n=3)
        
        return JsonResponse({
            'suggestions': top_tasks,
            'strategy': strategy,
            'count': len(top_tasks)
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)
