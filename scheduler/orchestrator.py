from typing import Dict, Any, List

from loguru import logger

from scheduler.executor import Executor
from scheduler.models import (
    ScheduleRequest, ScheduleResponse, Assignment,
    ReviewResult
)
from scheduler.planner import Planner
from scheduler.reviewer import Reviewer


class Orchestrator:
    """Central orchestrator managing the agentic workflow"""

    def __init__(self, xai_api_key: str):
        self.planner = Planner(xai_api_key)
        self.executor = Executor(xai_api_key)
        self.reviewer = Reviewer(xai_api_key)

        logger.info("Orchestrator initialized with all agents")

    async def process_schedule_request(
            self,
            request: ScheduleRequest
    ) -> ScheduleResponse:
        """
        Main orchestration flow:
        1. Planner creates execution plan
        2. Executor runs the plan (using scheduler + lawyer tools)
        3. Reviewer validates quality
        4. Return curated result
        """
        try:
            logger.info(
                f"Processing schedule request with {len(request.employees)} employees and {len(request.tasks)} tasks")

            # Step 1: Planning phase
            plan = await self.planner.create_plan(request)
            logger.info(f"Plan created with {len(plan.steps)} steps, strategy: {plan.strategy}")

            # Step 2: Execution phase
            assignments, metadata = await self.executor.execute_plan(
                plan=plan,
                request=request
            )
            logger.info(f"Execution complete: {len(assignments)} assignments created")

            # Step 3: Review phase
            review = await self.reviewer.review_schedule(
                assignments=assignments,
                request=request,
                metadata=metadata
            )
            logger.info(f"Review complete: approved={review.approved}, quality={review.quality_score}")

            # Step 4: Curate a final response
            response = self._curate_response(
                assignments=assignments,
                review=review,
                metadata=metadata
            )

            return response

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return ScheduleResponse(
                assignments=[],
                success=False,
                warnings=[f"Scheduling failed: {str(e)}"],
                metadata={"error": str(e)}
            )
    @staticmethod
    def _curate_response(
            assignments: List[Assignment],
            review: ReviewResult,
            metadata: Dict[str, Any]
    ) -> ScheduleResponse:
        """Curate final response based on review"""

        # Add review metadata
        metadata["quality_score"] = review.quality_score
        metadata["review_approved"] = review.approved

        # Collect warnings from review
        warnings = []
        if not review.approved:
            warnings.append("Schedule did not pass quality review")
        warnings.extend(review.issues)

        # Filter low-confidence assignments if review found issues
        if review.quality_score < 0.7:
            original_count = len(assignments)
            assignments = [a for a in assignments if a.confidence >= 0.5]
            if len(assignments) < original_count:
                warnings.append(
                    f"Filtered {original_count - len(assignments)} low-confidence assignments"
                )

        return ScheduleResponse(
            assignments=assignments,
            metadata=metadata,
            warnings=warnings,
            success=review.approved and len(assignments) > 0
        )