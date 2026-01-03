import os
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv
from typing import List
from .models import Task, Employee

load_dotenv()

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

MODEL = "grok-4"  # or "grok-beta" if needed; use the latest available

def build_prompt(tasks: List[Task], employees: List[Employee], country: str = "US") -> str:
    prompt = """
You are an expert staff scheduler. Your goal is to assign employees to tasks fairly while respecting all constraints.

Rules:
- Task ID 0 with category 0 is VACATION (full-day, exclusive). Employees CANNOT be assigned to any other task if on vacation.
- An employee can only be assigned to ONE task at a time if time slots overlap.
- Vacation is exclusive: if assigned to vacation, no other tasks.
- Employees prefer categories in order of their preferences list.
- Prioritize employees with higher denied_requests_60_days or lower previous_vacations_60_days for fairness (especially vacation).
- Only assign employees who have ALL required_certifications for a task.
- Each task needs exactly the calculated number of staff (or as many as possible if insufficient).
- Do not assign vacation unless the employee strongly needs it for fairness.

Output ONLY a valid JSON array of assignments like:
[
  {"task_id": 12, "employee_ids": [65223]},
  {"task_id": 356, "employee_ids": []},
  {"task_id": 0, "employee_ids": []}
]

Tasks:
"""
    for t in tasks:
        prompt += f"\n- ID {t.task_id}, Category {t.category}, Time {t.start}-{t.end}, Needed staff: {needed_staff(t)}, Certs: {t.required_certifications}"

    prompt += "\n\nEmployees:\n"
    for e in employees:
        pref_str = ", ".join(map(str, e.preferences))
        prompt += f"\n- ID {e.employee_id}, {e.name}, Preferences: [{pref_str}], Certs: {e.certifications}, Vacations last 60d: {e.previous_vacations_60_days}, Approved/Denied: {e.approved_requests_60_days}/{e.denied_requests_60_days}"

    prompt += "\n\nProvide the JSON only. Reason step-by-step first if needed, but end with the JSON."

    return prompt

def get_grok_suggestion(tasks: List[Task], employees: List[Employee]) -> dict:
    prompt = build_prompt(tasks, employees)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048
        )
        content = response.choices[0].message.content.strip()
        logger.info(f"Grok raw response: {content}")

        # Extract JSON if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        assignments = json.loads(content)
        return {a["task_id"]: a["employee_ids"] for a in assignments}
    except Exception as e:
        logger.error(f"Grok API error: {e}")
        return {}