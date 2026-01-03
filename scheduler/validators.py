from typing import List
from .models import Task, Employee

def has_required_certs(employee: Employee, task: Task) -> bool:
    return all(cert in employee.certifications for cert in task.required_certifications)

def needed_staff(task: Task) -> int:
    if task.customer_capacity == 0:  # vacation
        return task.required_capacity_per_staff  # usually unlimited or set
    return max(1, (task.customer_capacity + task.required_capacity_per_staff - 1) // task.required_capacity_per_staff)

def tasks_overlap(task1: Task, task2: Task) -> bool:
    return max(task1.start, task2.start) < min(task1.end, task2.end)