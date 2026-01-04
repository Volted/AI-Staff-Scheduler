import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from loguru import logger
from scheduler.models import ScheduleRequest, Assignment, ValidationResult
from scheduler.utils import extract_json_from_markdown

class Scheduler:
    """AI-powered scheduling tool"""

    def __init__(self, xai_api_key: str):
        self.client = AsyncOpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-beta"

    async def generate_schedule(
            self,
            request: ScheduleRequest,
            validation_context: Optional[ValidationResult] = None,
            parameters: Dict[str, Any] = None
    ) -> List[Assignment]:
        """Generate optimal task assignments"""

        prompt = self._build_scheduling_prompt(request, validation_context, parameters)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content="""You are an expert workforce scheduler.
                        Assign employees to tasks optimally considering:
                        - Required certifications
                        - Employee preferences
                        - Workload balance (nights, weekends, holidays)
                        - Time conflicts
                        - Capacity requirements

                        Return JSON array of assignments with: task_id, employee_id, employee_name, confidence (0-1).
                        Prioritize fairness and employee satisfaction."""
                    ),
                    ChatCompletionUserMessageParam(role="user", content=prompt)
                ],
                temperature=0.5,
                max_tokens=4000
            )

            assignments_text = response.choices[0].message.content
            assignments = self._parse_assignments(assignments_text, request)

            logger.info(f"Generated {len(assignments)} assignments")
            return assignments

        except Exception as e:
            logger.error(f"Scheduling failed: {e}")
            return self._create_fallback_schedule(request)
    @staticmethod
    def _build_scheduling_prompt(
            request: ScheduleRequest,
            validation_context: Optional[ValidationResult],
            parameters: Optional[Dict[str, Any]]
    ) -> str:
        """Build scheduling prompt"""

        optimize_for = parameters.get("optimize_for", "balance") if parameters else "balance"

        context = ""
        if validation_context and not validation_context.is_valid:
            context = f"\nIMPORTANT: Previous validation found issues: {', '.join(validation_context.violations[:3])}"

        return f"""Create optimal staff schedule:

EMPLOYEES ({len(request.employees)}):
{json.dumps([e.model_dump() for e in request.employees], indent=2)}

TASKS ({len(request.tasks)}):
{json.dumps([t.model_dump() for t in request.tasks], indent=2)}

CONSTRAINTS:
{json.dumps(request.constraints, indent=2)}

OPTIMIZATION: {optimize_for}
{context}

Generate assignments ensuring:
1. All tasks are covered if possible
2. Employees have required certifications
3. No time conflicts for same employee
4. Fair distribution of workload
5. Respect vacation requests (task category 0)"""

    @staticmethod
    def _parse_assignments(
            response_text: str,
            request: ScheduleRequest
    ) -> List[Assignment]:
        """Parse AI response into assignments"""
        try:
            response_text = extract_json_from_markdown(response_text)
            data = json.loads(response_text)

            # Handle both array and object with assignments key
            if isinstance(data, dict) and "assignments" in data:
                data = data["assignments"]

            assignments = []
            employee_map = {e.employee_id: e.name for e in request.employees}

            for item in data:
                if "employee_id" in item and "task_id" in item:
                    assignments.append(Assignment(
                        task_id=item["task_id"],
                        employee_id=item["employee_id"],
                        employee_name=item.get("employee_name", employee_map.get(item["employee_id"], "Unknown")),
                        confidence=item.get("confidence", 0.9)
                    ))

            return assignments

        except Exception as e:
            logger.error(f"Failed to parse assignments: {e}")
            return []
    @staticmethod
    def _create_fallback_schedule(request: ScheduleRequest) -> List[Assignment]:
        """Simple fallback: round-robin assignment"""
        assignments = []

        if not request.employees or not request.tasks:
            return assignments

        employee_idx = 0
        for task in request.tasks:
            # Simple matching: find employee with certifications
            assigned = False
            for i in range(len(request.employees)):
                employee = request.employees[(employee_idx + i) % len(request.employees)]

                # Check certifications
                if all(cert in employee.certifications for cert in task.required_certifications):
                    assignments.append(Assignment(
                        task_id=task.task_id,
                        employee_id=employee.employee_id,
                        employee_name=employee.name,
                        confidence=0.6  # Low confidence for fallback
                    ))
                    employee_idx = (employee_idx + i + 1) % len(request.employees)
                    assigned = True
                    break

            if not assigned:
                logger.warning(f"Could not assign task {task.task_id} in fallback")

        return assignments