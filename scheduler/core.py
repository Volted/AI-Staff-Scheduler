from typing import List, Dict
from .ai_agent import get_grok_suggestion
from .models import Task, Employee, Assignment, Schedule
from .utils import parse_datetime
from .validators import has_required_certs, needed_staff


def generate_schedule(tasks_data: List[dict], employees_data: List[dict], schedule_date: str, country: str = "US") -> Schedule:
    tasks = [Task(**t, start=parse_datetime(t["start"]), end=parse_datetime(t["end"])) for t in tasks_data]
    employees = [Employee(**e) for e in employees_data]

    vacation_task = next(t for t in tasks if t.task_id == 0)

    # Get AI suggestion
    suggested = get_grok_suggestion(tasks, employees)

    # Validate and fallback with a greedy assignment
    assignments: Dict[int, List[int]] = {t.task_id: [] for t in tasks}
    assigned_employees = set()

    for task in sorted(tasks, key=lambda t: t.start):  # process in time order
        if task.task_id == 0:
            continue  # handle vacation last

        needed = needed_staff(task)
        candidates = [e for e in employees if e.employee_id not in assigned_employees and has_required_certs(e, task)]

        # Prioritize from Grok suggestion
        preferred = suggested.get(task.task_id, [])
        selected = []
        for emp_id in preferred:
            emp = next((e for e in candidates if e.employee_id == emp_id), None)
            if emp and len(selected) < needed:
                selected.append(emp.employee_id)
                assigned_employees.add(emp.employee_id)

        # Fill the remaining with the best available (preference match + fairness)
        for emp in sorted(candidates, key=lambda e: (
            -e.preferences.index(task.category) if task.category in e.preferences else 999,
            -e.denied_requests_60_days,
            e.previous_vacations_60_days
        )):
            if len(selected) >= needed:
                break
            if emp.employee_id not in assigned_employees:
                selected.append(emp.employee_id)
                assigned_employees.add(emp.employee_id)

        assignments[task.task_id] = selected

    # Handle vacation (off-day for remaining employees, but exclusive)
    remaining_employees = [e for e in employees if e.employee_id not in assigned_employees]
    # Optional: assign some to vacation based on fairness
    # For now, leave unassigned = off / available for vacation if needed
    # But since a vacation task exists, we can assign remaining if we want "off" as vacation,
    # According to the updated rule: vacation is exclusive, but not mandatory
    assignments[0] = []  # or assign some based on a need

    schedule_assignments = [Assignment(task_id=tid, employee_ids=eids) for tid, eids in assignments.items()]

    return Schedule(date=schedule_date, assignments=schedule_assignments, explanations=["AI-assisted scheduling with validation fallback"])
