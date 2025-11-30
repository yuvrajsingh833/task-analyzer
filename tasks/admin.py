from django.contrib import admin
from .models import Task, TaskFeedback


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    """
    list_display = ['title', 'due_date', 'estimated_hours', 'importance', 'is_overdue', 'created_at']
    list_filter = ['due_date', 'importance', 'created_at']
    search_fields = ['title']
    date_hierarchy = 'due_date'
    filter_horizontal = ['dependencies']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'importance')
        }),
        ('Timing', {
            'fields': ('due_date', 'estimated_hours')
        }),
        ('Dependencies', {
            'fields': ('dependencies',),
            'description': 'Select tasks that must be completed before this task'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_overdue(self, obj):
        """Display overdue status in admin list."""
        if obj.is_overdue:
            return " Overdue"
        return " On time"
    is_overdue.short_description = "Status"


@admin.register(TaskFeedback)
class TaskFeedbackAdmin(admin.ModelAdmin):
    """
    Admin interface for TaskFeedback model.
    """
    list_display = ['task_title', 'strategy', 'priority_score', 'was_helpful', 'created_at']
    list_filter = ['strategy', 'was_helpful', 'created_at']
    search_fields = ['task_title', 'feedback_note']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('task_id', 'task_title', 'strategy', 'priority_score')
        }),
        ('Feedback', {
            'fields': ('was_helpful', 'feedback_note')
        }),
        ('Task Attributes', {
            'fields': ('task_attributes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
