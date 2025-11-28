"""
URL routing for tasks app
"""

from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('analyze/', views.analyze_tasks_view, name='analyze'),
    path('suggest/', views.suggest_tasks_view, name='suggest'),
    path('', views.task_list_view, name='task-list'),
    path('<int:task_id>/', views.task_detail_view, name='task-detail'),
]

