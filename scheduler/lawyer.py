import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from loguru import logger
from scheduler.models import ScheduleRequest, Assignment, ValidationResult
from scheduler.utils import extract_json_from_markdown


class Lawyer:
    """AI-powered constraint validation tool"""

    def __init__(self, xai_api_key: str):
        self.client = AsyncOpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-beta"

    async def validate_constraints(
            self,
            request: ScheduleRequest,
            assignments: List[Assignment],
            parameters: Dict[str, Any]
    ) -> ValidationResult:
        """Validate scheduling constraints and labor laws"""

        prompt = self._build_validation_prompt(request, assignments, parameters)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam
                        (
                        role="system",
                        content="""You are a labor law compliance expert for staff scheduling.
                        Validate schedules against:
                        - Certification requirements
                        - Maximum working hours
                        - Required rest periods
                        - Vacation/time-off requests
                        - Fair workload distribution

                        Return JSON with: is_valid (bool), violations (array), warnings (array), suggestions (array)."""
                    ),
                    ChatCompletionUserMessageParam(role="user", content=prompt)
                ],
                temperature=0.2,
                max_tokens=2000
            )
            validation_text = response.choices[0].message.content
            result = self._parse_validation(validation_text)

            logger.info(f"Validation: valid={result.is_valid}, violations={len(result.violations)}")
            return result

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                violations=[f"Validation error: {str(e)}"],
                warnings=["Could not complete validation"]
            )

    @staticmethod
    def _build_validation_prompt(
            request: ScheduleRequest,
            assignments: List[Assignment],
            parameters: Dict[str, Any]
    ) -> str:

        validate_all = parameters.get("validate_all", True)
        context = "pre-scheduling constraint check" if not assignments else "post-scheduling validation"
        return f"""Validate this scheduling scenario ({context}):

EMPLOYEES:
{json.dumps([e.model_dump() for e in request.employees], indent=2)}

TASKS:
{json.dumps([t.model_dump() for t in request.tasks], indent=2)}

ASSIGNMENTS:
{json.dumps([a.model_dump() for a in assignments], indent=2) if assignments else "No assignments yet"}

CONSTRAINTS:
{json.dumps(request.constraints, indent=2)}

VALIDATION SCOPE: {"Comprehensive" if validate_all else "Basic"}

Check for:
1. Certification mismatches
2. Time conflicts (same employee, overlapping tasks)
3. Excessive workload (too many nights/weekends/holidays)
4. Vacation request conflicts (category 0 tasks)
5. Capacity requirements met
6. Fair distribution"""

    @staticmethod
    def _parse_validation(response_text: str) -> ValidationResult:
        """Parse validation response"""
        try:
            response_text = extract_json_from_markdown(response_text)
            data = json.loads(response_text)

            return ValidationResult(
                is_valid=data.get("is_valid", False),
                violations=data.get("violations", []),
                warnings=data.get("warnings", []),
                suggestions=data.get("suggestions", [])
            )

        except Exception as e:
            logger.error(f"Failed to parse validation: {e}")
            return ValidationResult(
                is_valid=True,  # Fail open
                warnings=[f"Could not parse validation: {str(e)}"]
            )
