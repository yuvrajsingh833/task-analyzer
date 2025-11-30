"""
Learning System for Task Prioritization

This module implements a learning system that adjusts algorithm weights
based on user feedback on task prioritization.
"""

from typing import Dict, List, Optional
from django.db.models import Avg, Count, Q
from .models import TaskFeedback


def get_feedback_stats(strategy: str = 'smart_balance') -> Dict:
    """
    Get statistics about user feedback for a given strategy.
    
    Returns:
        Dictionary with feedback statistics
    """
    feedbacks = TaskFeedback.objects.filter(strategy=strategy)
    
    total = feedbacks.count()
    if total == 0:
        return {
            'total': 0,
            'helpful_count': 0,
            'not_helpful_count': 0,
            'helpful_rate': 0.0,
            'avg_priority_score_helpful': 0.0,
            'avg_priority_score_not_helpful': 0.0
        }
    
    helpful = feedbacks.filter(was_helpful=True)
    not_helpful = feedbacks.filter(was_helpful=False)
    
    helpful_count = helpful.count()
    not_helpful_count = not_helpful.count()
    
    avg_helpful_score = helpful.aggregate(avg=Avg('priority_score'))['avg'] or 0.0
    avg_not_helpful_score = not_helpful.aggregate(avg=Avg('priority_score'))['avg'] or 0.0
    
    return {
        'total': total,
        'helpful_count': helpful_count,
        'not_helpful_count': not_helpful_count,
        'helpful_rate': helpful_count / total if total > 0 else 0.0,
        'avg_priority_score_helpful': avg_helpful_score,
        'avg_priority_score_not_helpful': avg_not_helpful_score
    }


def get_adjusted_weights(strategy: str = 'smart_balance', base_weights: Optional[Dict] = None) -> Dict:
    """
    Get adjusted algorithm weights based on user feedback.
    
    This function analyzes feedback to determine if certain factors should
    be weighted more or less heavily.
    
    Args:
        strategy: The scoring strategy to get weights for
        base_weights: Base weights to adjust (if None, uses defaults)
    
    Returns:
        Dictionary of adjusted weights
    """
    if base_weights is None:
        # Default weights for smart_balance strategy
        base_weights = {
            'urgency_weight': 1.0,
            'importance_weight': 1.0,
            'effort_weight': 0.8,
            'dependency_boost': 20.0
        }
    
    stats = get_feedback_stats(strategy)
    
    # If we don't have enough feedback, return base weights
    if stats['total'] < 5:
        return base_weights
    
    # Analyze patterns in feedback
    # If helpful tasks tend to have higher urgency scores, increase urgency weight
    # If not helpful tasks tend to have higher importance, maybe importance is over-weighted
    
    helpful_rate = stats['helpful_rate']
    
    # Adjust weights based on helpful rate
    # If helpful rate is low (< 0.5), we need to adjust more aggressively
    adjustment_factor = 1.0
    
    if helpful_rate < 0.4:
        # Low helpful rate - make more significant adjustments
        adjustment_factor = 1.2
    elif helpful_rate < 0.6:
        # Moderate helpful rate - make moderate adjustments
        adjustment_factor = 1.1
    else:
        # High helpful rate - minimal adjustments
        adjustment_factor = 1.05
    
    # Compare average scores for helpful vs not helpful
    score_diff = stats['avg_priority_score_helpful'] - stats['avg_priority_score_not_helpful']
    
    adjusted_weights = base_weights.copy()
    
    # If helpful tasks have significantly higher scores, we might be under-weighting urgency
    if score_diff > 20 and helpful_rate < 0.6:
        adjusted_weights['urgency_weight'] *= adjustment_factor
    
    # If helpful tasks have lower scores but still helpful, we might be over-weighting urgency
    if score_diff < -10 and helpful_rate > 0.6:
        adjusted_weights['urgency_weight'] *= (1.0 / adjustment_factor)
        adjusted_weights['importance_weight'] *= adjustment_factor
    
    return adjusted_weights


def record_feedback(
    task_id: int,
    task_title: str,
    strategy: str,
    priority_score: float,
    was_helpful: bool,
    task_attributes: Dict,
    feedback_note: Optional[str] = None
) -> TaskFeedback:
    """
    Record user feedback on task prioritization.
    
    Args:
        task_id: ID of the task
        task_title: Title of the task
        strategy: Scoring strategy used
        priority_score: Priority score assigned
        was_helpful: Whether the user found this helpful
        task_attributes: Task attributes at time of feedback
        feedback_note: Optional feedback note
    
    Returns:
        Created TaskFeedback instance
    """
    feedback = TaskFeedback.objects.create(
        task_id=task_id,
        task_title=task_title,
        strategy=strategy,
        priority_score=priority_score,
        was_helpful=was_helpful,
        task_attributes=task_attributes,
        feedback_note=feedback_note
    )
    return feedback

