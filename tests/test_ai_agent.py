import json
from pathlib import Path

import pytest

from scheduler.lawyer import Lawyer
from scheduler.models import (
    Employee, Task, ScheduleRequest, ScheduleResponse,
    Plan, Assignment, ValidationResult, ReviewResult
)
from scheduler.orchestrator import Orchestrator
from scheduler.planner import Planner
from scheduler.reviewer import Reviewer
from scheduler.scheduler import Scheduler


# Fixtures

@pytest.fixture
def sample_employees():
    """Load sample employees"""
    data_path = Path(__file__).parent.parent / "data" / "sample_employees.json"
    with open(data_path) as f:
        data = json.load(f)
    return [Employee(**emp) for emp in data]


@pytest.fixture
def sample_tasks():
    """Load sample tasks"""
    data_path = Path(__file__).parent.parent / "data" / "sample_tasks.json"
    with open(data_path) as f:
        data = json.load(f)
    return [Task(**task) for task in data]


@pytest.fixture
def schedule_request(sample_employees, sample_tasks):
    """Create schedule request"""
    return ScheduleRequest(
        employees=sample_employees,
        tasks=sample_tasks,
        constraints={"max_hours_per_week": 40, "min_rest_hours": 11}
    )


@pytest.fixture
def mock_api_key():
    """Mock an API key for testing"""
    return "test-api-key-12345"


# Unit Tests - Models

class TestModels:
    """Test Pydantic models"""

    def test_employee_creation(self):
        emp = Employee(
            employee_id=1,
            name="Test Employee",
            certifications=[1, 2, 3]
        )
        assert emp.employee_id == 1
        assert len(emp.certifications) == 3

    def test_task_duration(self):
        task = Task(
            task_id=1,
            category=3,
            customer_capacity=30,
            required_capacity_per_staff=6,
            required_certifications=[1, 3],
            start="2026-01-03 08:00:00",
            end="2026-01-03 09:00:00"
        )
        assert task.duration_hours == 1.0

    def test_schedule_request_validation(self, sample_employees, sample_tasks):
        request = ScheduleRequest(
            employees=sample_employees,
            tasks=sample_tasks
        )
        assert len(request.employees) > 0
        assert len(request.tasks) > 0
        assert isinstance(request.constraints, dict)

    def test_assignment_confidence_bounds(self):
        # Valid confidence
        Assignment(task_id=1, employee_id=1, employee_name="Test", confidence=0.5)

        # Invalid confidence (should raise)
        with pytest.raises(Exception):
            Assignment(task_id=1, employee_id=1, employee_name="Test", confidence=1.5)


# Integration Tests - Components

class TestPlanner:
    """Test Planner agent"""

    @pytest.mark.asyncio
    async def test_fallback_plan_creation(self, mock_api_key, schedule_request):
        planner = Planner(mock_api_key)
        plan = planner._create_fallback_plan()

        assert isinstance(plan, Plan)
        assert len(plan.steps) > 0
        assert plan.estimated_complexity in ["low", "medium", "high"]

    def test_plan_parsing(self, mock_api_key):
        planner = Planner(mock_api_key)
        plan_json = json.dumps({
            "strategy": "Test strategy",
            "estimated_complexity": "low",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Test step",
                    "tool": "scheduler",
                    "parameters": {}
                }
            ]
        })

        plan_dict = planner._parse_plan_response(plan_json)
        assert "strategy" in plan_dict
        assert len(plan_dict["steps"]) == 1


class TestScheduler:
    """Test Scheduler tool"""

    def test_fallback_schedule_creation(self, mock_api_key, schedule_request):
        scheduler = Scheduler(mock_api_key)
        assignments = scheduler._create_fallback_schedule(schedule_request)

        # Should create some assignments
        assert isinstance(assignments, list)
        for assignment in assignments:
            assert isinstance(assignment, Assignment)
            assert 0 <= assignment.confidence <= 1

    def test_assignment_parsing(self, mock_api_key, schedule_request):
        scheduler = Scheduler(mock_api_key)

        response_text = json.dumps([
            {
                "task_id": 12,
                "employee_id": 65223,
                "employee_name": "John Doe",
                "confidence": 0.9
            }
        ])

        assignments = scheduler._parse_assignments(response_text, schedule_request)
        assert len(assignments) == 1
        assert assignments[0].task_id == 12
        assert assignments[0].confidence == 0.9


class TestLawyer:
    """Test Lawyer tool"""

    def test_validation_parsing(self, mock_api_key):
        lawyer = Lawyer(mock_api_key)

        response_text = json.dumps({
            "is_valid": True,
            "violations": [],
            "warnings": ["Minor issue"],
            "suggestions": ["Consider rotating night shifts"]
        })

        result = lawyer._parse_validation(response_text)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1


class TestReviewer:
    """Test Reviewer agent"""

    def test_review_parsing(self, mock_api_key):
        reviewer = Reviewer(mock_api_key)

        response_text = json.dumps({
            "approved": True,
            "quality_score": 0.85,
            "issues": [],
            "improvements": ["Could improve fairness by 5%"]
        })

        result = reviewer._parse_review(response_text)
        assert isinstance(result, ReviewResult)
        assert result.approved is True
        assert result.quality_score == 0.85
        assert len(result.improvements) == 1


class TestOrchestrator:
    """Test Orchestrator coordination"""

    def test_response_curation(self, mock_api_key):
        orchestrator = Orchestrator(mock_api_key)

        assignments = [
            Assignment(task_id=1, employee_id=1, employee_name="Test", confidence=0.9)
        ]

        review = ReviewResult(
            approved=True,
            quality_score=0.85,
            issues=[],
            improvements=[]
        )

        metadata = {"test": "data"}

        response = orchestrator._curate_response(assignments, review, metadata)

        assert isinstance(response, ScheduleResponse)
        assert response.success is True
        assert len(response.assignments) == 1
        assert "quality_score" in response.metadata


# End-to-End Tests

class TestEndToEnd:
    """End-to-end workflow tests"""

    def test_complete_request_structure(self, schedule_request):
        """Test that the request has all necessary data"""
        assert len(schedule_request.employees) > 0
        assert len(schedule_request.tasks) > 0

        emp = schedule_request.employees[0]
        assert hasattr(emp, 'certifications')
        assert hasattr(emp, 'preferences')

        task = schedule_request.tasks[0]
        assert hasattr(task, 'required_certifications')
        assert hasattr(task, 'start')
        assert hasattr(task, 'end')

    def test_response_structure_validity(self):
        """Test response model structure"""
        response = ScheduleResponse(
            assignments=[
                Assignment(
                    task_id=12,
                    employee_id=65223,
                    employee_name="John Doe",
                    confidence=0.9
                )
            ],
            metadata={"plan": "sequential"},
            warnings=[],
            success=True
        )

        # Validate it serializes correctly
        response_json = response.model_dump_json()
        assert "assignments" in response_json
        assert "success" in response_json


# Performance Tests

class TestPerformance:
    """Basic performance tests"""

    def test_model_serialization_speed(self, schedule_request):
        """Test that serialization is fast enough"""
        import time

        start = time.time()
        for _ in range(100):
            _ = schedule_request.model_dump_json()
        elapsed = time.time() - start

        assert elapsed < 1.0, "Serialization too slow"

    def test_large_dataset_handling(self):
        """Test with larger datasets"""
        employees = [
            Employee(
                employee_id=i,
                name=f"Employee {i}",
                certifications=[1, 2, 3]
            )
            for i in range(100)
        ]

        tasks = [
            Task(
                task_id=i,
                category=3,
                customer_capacity=30,
                required_capacity_per_staff=6,
                required_certifications=[1],
                start="2026-01-03 08:00:00",
                end="2026-01-03 09:00:00"
            )
            for i in range(50)
        ]

        request = ScheduleRequest(employees=employees, tasks=tasks)
        assert len(request.employees) == 100
        assert len(request.tasks) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
