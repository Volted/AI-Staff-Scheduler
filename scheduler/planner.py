import json
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from loguru import logger
from scheduler.models import ScheduleRequest, Plan, PlanStep
from scheduler.utils import extract_json_from_markdown


class Planner:
    """AI Planner agent - creates execution strategy"""

    def __init__(self, xai_api_key: str):
        self.client = AsyncOpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-beta"

    async def create_plan(self, request: ScheduleRequest) -> Plan:
        """Create execution plan for scheduling request"""

        prompt = self._build_planning_prompt(request)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content="""You are a strategic planner for staff scheduling.
                                    Create a step-by-step execution plan using available tools:
                                    - 'scheduler': Assigns employees to tasks optimally
                                    - 'lawyer': Validates labor laws, certifications, constraints

                                    Return JSON plan with: strategy, estimated_complexity, and steps array.
                                    Each step has: step_number, description, tool, parameters."""
                    ),
                    ChatCompletionUserMessageParam(role="user", content=prompt)
                ],
                temperature=0.3,
                max_tokens=2000
            )

            plan_text = response.choices[0].message.content
            plan_data = self._parse_plan_response(plan_text)

            return Plan(**plan_data)

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Fallback to the default plan
            return self._create_fallback_plan()
    @staticmethod
    def _build_planning_prompt(request: ScheduleRequest) -> str:
        """Build prompt for planner"""
        return f"""Create an execution plan for this scheduling request:

Employees: {len(request.employees)} staff members
Tasks: {len(request.tasks)} tasks/shifts
Constraints: {json.dumps(request.constraints)}

Sample employee: {request.employees[0].model_dump_json() if request.employees else 'None'}
Sample task: {request.tasks[0].model_dump_json() if request.tasks else 'None'}

Determine:
1. Should we validate constraints first (lawyer) or schedule first?
2. What's the optimal strategy?
3. What steps are needed?"""

    def _parse_plan_response(self, response_text: str) -> dict:
        """Parse AI response into plan dict"""
        try:
            response_text = extract_json_from_markdown(response_text)
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse plan JSON, using fallback")
            return self._create_fallback_plan_dict()
    @staticmethod
    def _create_fallback_plan() -> Plan:
        return Plan(
            strategy="Simple sequential: validate then schedule",
            estimated_complexity="medium",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Validate labor law constraints",
                    tool="lawyer",
                    parameters={"validate_all": True}
                ),
                PlanStep(
                    step_number=2,
                    description="Generate optimal schedule",
                    tool="scheduler",
                    parameters={"optimize_for": "balance"}
                )
            ]
        )
    @staticmethod
    def _create_fallback_plan_dict() -> dict:
        """Fallback plan as dict"""
        return {
            "strategy": "Simple sequential: validate then schedule",
            "estimated_complexity": "medium",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Validate labor law constraints",
                    "tool": "lawyer",
                    "parameters": {"validate_all": True}
                },
                {
                    "step_number": 2,
                    "description": "Generate optimal schedule",
                    "tool": "scheduler",
                    "parameters": {"optimize_for": "balance"}
                }
            ]
        }