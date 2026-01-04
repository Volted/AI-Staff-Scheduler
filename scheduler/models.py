from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TaskCategory(int, Enum):
    """Task categories"""
    VACATION = 0
    SICK_LEAVE = 1
    TRAINING = 2
    SHIFT = 3


class Employee(BaseModel):
    """Employee data model"""
    employee_id: int
    name: str
    preferences: List[int] = Field(default_factory=list)
    certifications: List[int] = Field(default_factory=list)
    previous_vacations_60_days: int = 0
    approved_requests_60_days: int = 0
    denied_requests_60_days: int = 0
    vacation_days_remaining: int = 0
    vacation_days_used: int = 0
    worked_nights: int = 0
    worked_weekends: int = 0
    worked_holidays: int = 0


class Task(BaseModel):
    """Task/Shift data model"""
    task_id: int
    category: int
    customer_capacity: int = 0
    required_capacity_per_staff: int = 1
    required_certifications: List[int] = Field(default_factory=list)
    start: str  # ISO format datetime
    end: str    # ISO format datetime

    @property
    def duration_hours(self) -> float:
        """Calculate task duration in hours"""
        start_dt = datetime.fromisoformat(self.start)
        end_dt = datetime.fromisoformat(self.end)
        return (end_dt - start_dt).total_seconds() / 3600


class ScheduleRequest(BaseModel):
    """API request model"""
    employees: List[Employee]
    tasks: List[Task]
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Assignment(BaseModel):
    """Single task assignment"""
    task_id: int
    employee_id: int
    employee_name: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class ScheduleResponse(BaseModel):
    """API response model"""
    assignments: List[Assignment]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    success: bool = True


class PlanStep(BaseModel):
    """Planner step model"""
    step_number: int
    description: str
    tool: str  # "scheduler" or "lawyer"
    parameters: Dict[str, Any]


class Plan(BaseModel):
    """Complete execution plan"""
    steps: List[PlanStep]
    strategy: str
    estimated_complexity: str  # "low", "medium", "high"


class ValidationResult(BaseModel):
    """Lawyer validation result"""
    is_valid: bool
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ReviewResult(BaseModel):
    """Reviewer assessment"""
    approved: bool
    quality_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)