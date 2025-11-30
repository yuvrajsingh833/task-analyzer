from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Task(models.Model):
    """
    Task model for storing task information.
    
    Fields:
    - title: Task title (required)
    - due_date: When the task is due (optional)
    - estimated_hours: Estimated time to complete (optional)
    - importance: Importance rating 1-10 (optional, defaults to 5)
    - created_at: Timestamp when task was created
    - updated_at: Timestamp when task was last updated
    - dependencies: Many-to-many relationship with other tasks
    """
    title = models.CharField(max_length=200, help_text="Task title")
    due_date = models.DateField(null=True, blank=True, help_text="Due date (YYYY-MM-DD)")
    estimated_hours = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Estimated hours to complete"
    )
    importance = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Importance rating from 1-10"
    )
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_tasks',
        help_text="Tasks that must be completed before this task"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
    
    def __str__(self):
        return self.title
    
    def to_dict(self):
        """
        Convert task instance to dictionary format compatible with scoring algorithm.
        
        Returns:
            dict: Task data in the format expected by the scoring functions
        """
        return {
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_hours': self.estimated_hours,
            'importance': self.importance,
            'dependencies': list(self.dependencies.values_list('id', flat=True))
        }
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date:
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def days_until_due(self):
        """Get number of days until due date (negative if overdue)."""
        if self.due_date:
            return (self.due_date - timezone.now().date()).days
        return None


class TaskFeedback(models.Model):
    """
    Model for storing user feedback on task prioritization.
    
    This enables the learning system to adjust algorithm weights based on
    whether users found the suggested priorities helpful.
    """
    task_id = models.IntegerField(help_text="ID of the task that was prioritized")
    task_title = models.CharField(max_length=200, help_text="Title of the task")
    strategy = models.CharField(max_length=50, help_text="Scoring strategy used")
    priority_score = models.FloatField(help_text="Priority score assigned")
    was_helpful = models.BooleanField(help_text="Whether the user found this prioritization helpful")
    feedback_note = models.TextField(blank=True, null=True, help_text="Optional feedback note")
    task_attributes = models.JSONField(
        default=dict,
        help_text="Task attributes at time of feedback (due_date, importance, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task Feedback"
        verbose_name_plural = "Task Feedbacks"
    
    def __str__(self):
        return f"Feedback for '{self.task_title}' - {'Helpful' if self.was_helpful else 'Not Helpful'}"