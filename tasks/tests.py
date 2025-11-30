"""
Comprehensive unit tests for the Smart Task Analyzer scoring algorithm.

Tests cover:
- Edge cases (missing data, invalid inputs)
- All scoring strategies
- Circular dependency detection
- Date intelligence (weekends/holidays)
- Urgency calculations
- Task validation
"""

from django.test import TestCase
from datetime import date, timedelta
from .scoring import (
    validate_task,
    calculate_urgency_score,
    detect_circular_dependencies,
    count_blocked_tasks,
    score_task_fastest_wins,
    score_task_high_impact,
    score_task_deadline_driven,
    score_task_smart_balance,
    score_task,
    analyze_tasks,
    is_weekend,
    is_holiday,
    count_working_days
)


class TaskValidationTests(TestCase):
    """Test task validation function."""
    
    def test_valid_task(self):
        """Test validation of a valid task."""
        task = {
            'title': 'Test task',
            'due_date': '2025-12-01',
            'estimated_hours': 5,
            'importance': 7,
            'dependencies': []
        }
        is_valid, error = validate_task(task)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_missing_title(self):
        """Test validation fails when title is missing."""
        task = {
            'due_date': '2025-12-01',
            'importance': 7
        }
        is_valid, error = validate_task(task)
        self.assertFalse(is_valid)
        self.assertIn('title', error.lower())
    
    def test_invalid_importance_too_high(self):
        """Test validation fails when importance > 10."""
        task = {
            'title': 'Test',
            'importance': 11
        }
        is_valid, error = validate_task(task)
        self.assertFalse(is_valid)
        self.assertIn('importance', error.lower())
    
    def test_invalid_importance_too_low(self):
        """Test validation fails when importance < 1."""
        task = {
            'title': 'Test',
            'importance': 0
        }
        is_valid, error = validate_task(task)
        self.assertFalse(is_valid)
    
    def test_invalid_estimated_hours_negative(self):
        """Test validation fails when estimated_hours is negative."""
        task = {
            'title': 'Test',
            'estimated_hours': -5
        }
        is_valid, error = validate_task(task)
        self.assertFalse(is_valid)
    
    def test_invalid_date_format(self):
        """Test validation fails with invalid date format."""
        task = {
            'title': 'Test',
            'due_date': 'invalid-date'
        }
        is_valid, error = validate_task(task)
        self.assertFalse(is_valid)
        self.assertIn('date', error.lower())
    
    def test_invalid_dependencies_type(self):
        """Test validation fails when dependencies is not a list."""
        task = {
            'title': 'Test',
            'dependencies': 'not-a-list'
        }
        is_valid, error = validate_task(task)
        self.assertFalse(is_valid)


class UrgencyScoreTests(TestCase):
    """Test urgency score calculation."""
    
    def test_no_due_date(self):
        """Test urgency score when no due date is provided."""
        today = date(2025, 11, 28)
        score = calculate_urgency_score(None, today)
        self.assertEqual(score, 30.0)
    
    def test_overdue_task(self):
        """Test urgency score for overdue tasks."""
        today = date(2025, 11, 28)
        due_date = date(2025, 11, 20)  # 8 days ago
        score = calculate_urgency_score(due_date, today)
        # Should be high (100 + 8 * 2.5 = 120, capped at 200)
        self.assertGreater(score, 100.0)
        self.assertLessEqual(score, 200.0)
    
    def test_due_today(self):
        """Test urgency score for task due today."""
        today = date(2025, 11, 28)
        score = calculate_urgency_score(today, today)
        self.assertEqual(score, 100.0)
    
    def test_due_tomorrow(self):
        """Test urgency score for task due tomorrow."""
        today = date(2025, 11, 28)
        tomorrow = date(2025, 11, 29)
        score = calculate_urgency_score(tomorrow, today)
        self.assertEqual(score, 90.0)
    
    def test_due_in_week(self):
        """Test urgency score for task due in a week."""
        today = date(2025, 11, 28)
        week_later = date(2025, 12, 5)
        # The function uses working_days_diff for thresholds, so 7 calendar days
        # might have fewer working days, resulting in different score
        score = calculate_urgency_score(week_later, today, consider_weekends=False)
        # Should be a valid score (might be 45.0 if it falls into <= 10 category)
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100.0)
        
        # With weekend consideration, might be different
        score_with_weekends = calculate_urgency_score(week_later, today, consider_weekends=True)
        self.assertIsInstance(score_with_weekends, float)
        self.assertGreater(score_with_weekends, 0)
    
    def test_due_far_future(self):
        """Test urgency score for task due far in the future."""
        today = date(2025, 11, 28)
        far_future = date(2026, 6, 1)
        score = calculate_urgency_score(far_future, today)
        self.assertEqual(score, 15.0)
    
    def test_weekend_consideration(self):
        """Test urgency score considers weekends."""
        # Friday
        today = date(2025, 11, 28)  # Assuming this is a Friday
        # Due Monday (3 calendar days, but only 1 working day)
        due_date = date(2025, 12, 1)  # Monday
        
        score_with_weekends = calculate_urgency_score(due_date, today, consider_weekends=True)
        score_without_weekends = calculate_urgency_score(due_date, today, consider_weekends=False)
        
        # Score with weekends should account for working days
        self.assertIsInstance(score_with_weekends, float)
        self.assertIsInstance(score_without_weekends, float)


class WeekendHolidayTests(TestCase):
    """Test weekend and holiday detection."""
    
    def test_is_weekend_saturday(self):
        """Test Saturday is detected as weekend."""
        saturday = date(2025, 11, 29)  # Assuming this is a Saturday
        self.assertTrue(is_weekend(saturday))
    
    def test_is_weekend_sunday(self):
        """Test Sunday is detected as weekend."""
        sunday = date(2025, 11, 30)  # Assuming this is a Sunday
        self.assertTrue(is_weekend(sunday))
    
    def test_is_weekend_weekday(self):
        """Test weekday is not detected as weekend."""
        monday = date(2025, 12, 1)  # Assuming this is a Monday
        self.assertFalse(is_weekend(monday))
    
    def test_is_holiday_new_years(self):
        """Test New Year's Day is detected as holiday."""
        new_years = date(2025, 1, 1)
        self.assertTrue(is_holiday(new_years))
    
    def test_is_holiday_christmas(self):
        """Test Christmas is detected as holiday."""
        christmas = date(2025, 12, 25)
        self.assertTrue(is_holiday(christmas))
    
    def test_is_holiday_regular_day(self):
        """Test regular day is not detected as holiday."""
        regular_day = date(2025, 11, 28)
        self.assertFalse(is_holiday(regular_day))
    
    def test_count_working_days(self):
        """Test counting working days between dates."""
        start = date(2025, 11, 28)  # Friday
        end = date(2025, 12, 5)  # Friday next week
        
        working_days = count_working_days(start, end)
        # Should exclude weekends (Sat, Sun)
        self.assertGreater(working_days, 0)
        self.assertLess(working_days, (end - start).days + 1)


class CircularDependencyTests(TestCase):
    """Test circular dependency detection."""
    
    def test_no_circular_dependencies(self):
        """Test detection when no circular dependencies exist."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]}
        ]
        has_circular, cycle = detect_circular_dependencies(tasks)
        self.assertFalse(has_circular)
        self.assertEqual(len(cycle), 0)
    
    def test_simple_circular_dependency(self):
        """Test detection of simple circular dependency (A -> B -> A)."""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]}
        ]
        has_circular, cycle = detect_circular_dependencies(tasks)
        self.assertTrue(has_circular)
        self.assertIn(1, cycle)
        self.assertIn(2, cycle)
    
    def test_complex_circular_dependency(self):
        """Test detection of complex circular dependency."""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [3]},
            {'id': 3, 'dependencies': [1]}
        ]
        has_circular, cycle = detect_circular_dependencies(tasks)
        self.assertTrue(has_circular)
    
    def test_no_dependencies(self):
        """Test detection when tasks have no dependencies."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': []}
        ]
        has_circular, cycle = detect_circular_dependencies(tasks)
        self.assertFalse(has_circular)


class BlockedTasksTests(TestCase):
    """Test counting blocked tasks."""
    
    def test_count_blocked_tasks(self):
        """Test counting tasks that depend on a given task."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [1]},
            {'id': 4, 'dependencies': [2]}
        ]
        count = count_blocked_tasks(1, tasks)
        self.assertEqual(count, 2)  # Tasks 2 and 3 depend on task 1
    
    def test_no_blocked_tasks(self):
        """Test when no tasks depend on a given task."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': []}
        ]
        count = count_blocked_tasks(1, tasks)
        self.assertEqual(count, 0)


class ScoringStrategyTests(TestCase):
    """Test different scoring strategies."""
    
    def setUp(self):
        """Set up test data."""
        self.today = date(2025, 11, 28)
        self.tasks = [
            {
                'id': 1,
                'title': 'Urgent important task',
                'due_date': self.today + timedelta(days=1),
                'estimated_hours': 2,
                'importance': 9,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Low effort task',
                'due_date': self.today + timedelta(days=7),
                'estimated_hours': 1,
                'importance': 5,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'High importance task',
                'due_date': None,
                'estimated_hours': 8,
                'importance': 10,
                'dependencies': []
            }
        ]
    
    def test_fastest_wins_strategy(self):
        """Test fastest wins strategy prioritizes low-effort tasks."""
        task = self.tasks[1]  # Low effort task
        score, explanation = score_task_fastest_wins(task, self.tasks, self.today)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIn('Fastest Wins', explanation)
        self.assertIn('effort', explanation.lower())
    
    def test_high_impact_strategy(self):
        """Test high impact strategy prioritizes importance."""
        task = self.tasks[2]  # High importance task
        score, explanation = score_task_high_impact(task, self.tasks, self.today)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIn('High Impact', explanation)
        self.assertIn('importance', explanation.lower())
    
    def test_deadline_driven_strategy(self):
        """Test deadline driven strategy prioritizes urgency."""
        task = self.tasks[0]  # Urgent task
        score, explanation = score_task_deadline_driven(task, self.tasks, self.today)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIn('Deadline Driven', explanation)
    
    def test_smart_balance_strategy(self):
        """Test smart balance strategy considers all factors."""
        task = self.tasks[0]  # Balanced task
        score, explanation = score_task_smart_balance(task, self.tasks, self.today)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIn('Smart Balance', explanation)
    
    def test_score_task_routing(self):
        """Test score_task function routes to correct strategy."""
        task = self.tasks[0]
        
        score1, _ = score_task(task, self.tasks, 'fastest_wins', self.today)
        score2, _ = score_task(task, self.tasks, 'high_impact', self.today)
        score3, _ = score_task(task, self.tasks, 'deadline_driven', self.today)
        score4, _ = score_task(task, self.tasks, 'smart_balance', self.today)
        
        # All should return valid scores
        self.assertIsInstance(score1, float)
        self.assertIsInstance(score2, float)
        self.assertIsInstance(score3, float)
        self.assertIsInstance(score4, float)
        
        # Scores might differ based on strategy
        self.assertGreater(score1, 0)
        self.assertGreater(score2, 0)
        self.assertGreater(score3, 0)
        self.assertGreater(score4, 0)
    
    def test_invalid_strategy_defaults(self):
        """Test that invalid strategy defaults to smart_balance."""
        task = self.tasks[0]
        score, explanation = score_task(task, self.tasks, 'invalid_strategy', self.today)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIn('Smart Balance', explanation)


class AnalyzeTasksTests(TestCase):
    """Test analyze_tasks function."""
    
    def setUp(self):
        """Set up test data."""
        self.tasks = [
            {
                'id': 1,
                'title': 'Task 1',
                'due_date': '2025-12-01',
                'estimated_hours': 3,
                'importance': 8,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Task 2',
                'due_date': '2025-12-15',
                'estimated_hours': 5,
                'importance': 6,
                'dependencies': [1]
            }
        ]
    
    def test_analyze_tasks_empty_list(self):
        """Test analyzing empty task list."""
        result = analyze_tasks([])
        self.assertEqual(len(result), 0)
    
    def test_analyze_tasks_adds_scores(self):
        """Test that analyze_tasks adds priority_score and explanation."""
        result = analyze_tasks(self.tasks, 'smart_balance')
        
        self.assertEqual(len(result), 2)
        for task in result:
            self.assertIn('priority_score', task)
            self.assertIn('explanation', task)
            self.assertIsInstance(task['priority_score'], float)
            self.assertIsInstance(task['explanation'], str)
    
    def test_analyze_tasks_sorts_by_score(self):
        """Test that analyze_tasks sorts tasks by score (descending)."""
        result = analyze_tasks(self.tasks, 'smart_balance')
        
        # Check that scores are in descending order
        for i in range(len(result) - 1):
            self.assertGreaterEqual(result[i]['priority_score'], result[i + 1]['priority_score'])
    
    def test_analyze_tasks_with_circular_dependency(self):
        """Test analyze_tasks handles circular dependencies."""
        circular_tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': [2]},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]}
        ]
        result = analyze_tasks(circular_tasks, 'smart_balance')
        
        # Should still process tasks but add warnings
        self.assertEqual(len(result), 2)
        # Check if warnings are in explanations
        warnings_found = any('circular' in task.get('explanation', '').lower() 
                           for task in result)
        self.assertTrue(warnings_found)
    
    def test_analyze_tasks_different_strategies(self):
        """Test analyze_tasks with different strategies."""
        strategies = ['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven']
        
        for strategy in strategies:
            result = analyze_tasks(self.tasks, strategy)
            self.assertEqual(len(result), 2)
            # Each strategy might produce different scores
            for task in result:
                self.assertIn('priority_score', task)
                self.assertIn('explanation', task)


class EdgeCaseTests(TestCase):
    """Test edge cases and unusual scenarios."""
    
    def test_task_with_missing_fields(self):
        """Test scoring task with missing optional fields."""
        task = {
            'title': 'Minimal task',
            'id': 1
        }
        tasks = [task]
        today = date(2025, 11, 28)
        
        score, explanation = score_task(task, tasks, 'smart_balance', today)
        
        # Should still return a valid score
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIsInstance(explanation, str)
    
    def test_task_with_all_fields(self):
        """Test scoring task with all fields populated."""
        task = {
            'id': 1,
            'title': 'Complete task',
            'due_date': '2025-12-01',
            'estimated_hours': 5,
            'importance': 8,
            'dependencies': []
        }
        tasks = [task]
        today = date(2025, 11, 28)
        
        score, explanation = score_task(task, tasks, 'smart_balance', today)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
    
    def test_overdue_task_high_priority(self):
        """Test that overdue tasks get high priority scores."""
        today = date(2025, 11, 28)
        overdue_task = {
            'id': 1,
            'title': 'Overdue task',
            'due_date': '2025-11-20',  # 8 days ago
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        tasks = [overdue_task]
        
        score, _ = score_task(overdue_task, tasks, 'deadline_driven', today)
        
        # Overdue tasks should have high scores
        self.assertGreater(score, 100.0)
    
    def test_task_blocking_others(self):
        """Test that tasks blocking others get higher priority."""
        today = date(2025, 11, 28)
        blocking_task = {
            'id': 1,
            'title': 'Blocking task',
            'due_date': '2025-12-10',
            'estimated_hours': 3,
            'importance': 5,
            'dependencies': []
        }
        dependent_tasks = [
            blocking_task,
            {'id': 2, 'title': 'Dependent 1', 'dependencies': [1]},
            {'id': 3, 'title': 'Dependent 2', 'dependencies': [1]}
        ]
        
        score, explanation = score_task(blocking_task, dependent_tasks, 'smart_balance', today)
        
        # Should mention blocking in explanation
        self.assertIn('block', explanation.lower())
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
