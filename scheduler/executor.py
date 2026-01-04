from typing import List, Tuple, Dict, Any
from loguru import logger
from scheduler.models import Plan, Assignment, ScheduleRequest
from scheduler.lawyer import Lawyer
from scheduler.scheduler import Scheduler


class Executor:
    """Executes the plan using available tools"""

    def __init__(self, xai_api_key: str):
        self.lawyer = Lawyer(xai_api_key)
        self.scheduler = Scheduler(xai_api_key)
        logger.info("Executor initialized with tools: lawyer, scheduler")

    async def execute_plan(
            self,
            plan: Plan,
            request: ScheduleRequest
    ) -> Tuple[List[Assignment], Dict[str, Any]]:
        """Execute plan steps sequentially"""

        metadata = {
            "plan_strategy": plan.strategy,
            "steps_executed": [],
            "tool_calls": 0
        }

        assignments: List[Assignment] = []
        validation_result = None

        for step in plan.steps:
            logger.info(f"Executing step {step.step_number}: {step.description}")

            try:
                if step.tool == "lawyer":
                    validation_result = await self.lawyer.validate_constraints(
                        request=request,
                        assignments=assignments,
                        parameters=step.parameters
                    )
                    metadata["steps_executed"].append({
                        "step": step.step_number,
                        "tool": "lawyer",
                        "result": "valid" if validation_result.is_valid else "invalid"
                    })
                    metadata["tool_calls"] += 1

                    if not validation_result.is_valid:
                        logger.warning(f"Validation failed: {validation_result.violations}")

                elif step.tool == "scheduler":
                    assignments = await self.scheduler.generate_schedule(
                        request=request,
                        validation_context=validation_result,
                        parameters=step.parameters
                    )
                    metadata["steps_executed"].append({
                        "step": step.step_number,
                        "tool": "scheduler",
                        "result": f"{len(assignments)} assignments"
                    })
                    metadata["tool_calls"] += 1

                else:
                    logger.warning(f"Unknown tool: {step.tool}")

            except Exception as e:
                logger.error(f"Step {step.step_number} failed: {e}")
                metadata["steps_executed"].append({
                    "step": step.step_number,
                    "tool": step.tool,
                    "error": str(e)
                })

        return assignments, metadata