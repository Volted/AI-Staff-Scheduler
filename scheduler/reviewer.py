import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from loguru import logger
from scheduler.models import Assignment, ScheduleRequest, ReviewResult
from scheduler.utils import extract_json_from_markdown


class Reviewer:
    """AI reviewer - final quality check"""

    def __init__(self, xai_api_key: str):
        self.client = AsyncOpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-beta"

    async def review_schedule(
            self,
            assignments: List[Assignment],
            request: ScheduleRequest,
            metadata: Dict[str, Any]
    ) -> ReviewResult:
        """Final quality review of schedule"""

        prompt = self._build_review_prompt(assignments, request, metadata)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content="""You are a quality assurance reviewer for staff schedules.
                        Assess the quality and completeness of assignments:
                        - Coverage: Are all critical tasks assigned?
                        - Fairness: Is workload distributed equitably?
                        - Compliance: Do assignments respect constraints?
                        - Employee satisfaction: Are preferences considered?

                        Return JSON with: approved (bool), quality_score (0-1), issues (array), improvements (array)."""
                    ),
                    ChatCompletionUserMessageParam(role="user", content=prompt)
                ],
                temperature=0.3,
                max_tokens=1500
            )

            review_text = response.choices[0].message.content
            result = self._parse_review(review_text)

            logger.info(f"Review: approved={result.approved}, score={result.quality_score}")
            return result

        except Exception as e:
            logger.error(f"Review failed: {e}")
            return ReviewResult(
                approved=True,  # Fail open
                quality_score=0.5,
                issues=[f"Review error: {str(e)}"]
            )
    @staticmethod
    def _build_review_prompt(
            assignments: List[Assignment],
            request: ScheduleRequest,
            metadata: Dict[str, Any]
    ) -> str:
        """Build review prompt"""

        coverage = len(assignments) / len(request.tasks) if request.tasks else 0

        return f"""Review this completed schedule:

ORIGINAL REQUEST:
- Employees: {len(request.employees)}
- Tasks: {len(request.tasks)}
- Constraints: {json.dumps(request.constraints)}

GENERATED SCHEDULE:
- Assignments: {len(assignments)}
- Coverage: {coverage:.1%}
- Tool calls: {metadata.get('tool_calls', 0)}
- Strategy: {metadata.get('plan_strategy', 'unknown')}

ASSIGNMENTS:
{json.dumps([a.model_dump() for a in assignments], indent=2)}

Assess:
1. Task coverage completeness
2. Assignment quality and confidence
3. Potential issues or conflicts
4. Employee satisfaction indicators
5. Overall schedule quality

Provide quality score (0-1) and approval decision."""
    @staticmethod
    def _parse_review(response_text: str) -> ReviewResult:
        """Parse review response"""
        try:
            response_text = extract_json_from_markdown(response_text)
            data = json.loads(response_text)
            return ReviewResult(
                approved=data.get("approved", True),
                quality_score=float(data.get("quality_score", 0.7)),
                issues=data.get("issues", []),
                improvements=data.get("improvements", [])
            )

        except Exception as e:
            logger.error(f"Failed to parse review: {e}")
            return ReviewResult(
                approved=True,
                quality_score=0.7,
                issues=[f"Parse error: {str(e)}"]
            )