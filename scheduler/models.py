from datetime import datetime
from typing import List

from pydantic import BaseModel


class Task(BaseModel):
    task_id: int
    category: int  # 0 = vacation, others = work categories
    customer_capacity: int
    required_capacity_per_staff: int
    required_certifications: List[int]
    start: datetime
    end: datetime

class Employee(BaseModel):
    employee_id: int
    name: str
    preferences: List[int]  # ordered list, higher preference first (includes 0 for vacation if allowed)
    certifications: List[int]
    previous_vacations_60_days: int
    approved_requests_60_days: int
    denied_requests_60_days: int

class Assignment(BaseModel):
    task_id: int
    employee_ids: List[int]

class Schedule(BaseModel):
    date: str
    assignments: List[Assignment]
    explanations: List[str] = []