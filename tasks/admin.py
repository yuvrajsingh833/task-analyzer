from django.contrib import admin
from .models import Task


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
            return "⚠️ Overdue"
        return "✓ On time"
    is_overdue.short_description = "Status"
