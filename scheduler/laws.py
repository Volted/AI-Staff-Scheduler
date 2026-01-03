"""
laws.py
--------
Handles country-specific labor law checks, particularly around vacations,
mandatory rest, maximum working hours, and fairness requirements.

Currently, uses hardcoded rules for major countries.
Future extensions:
- Integrate web_search tool for up-to-date laws
- Connect to official government APIs or legal databases
- Add support for state/province-level rules (e.g., US states, EU countries)

Note: This is NOT legal advice. Always consult HR/legal experts for production use.
"""

from typing import Dict, Optional
from loguru import logger

# Hardcoded basic vacation entitlement rules (annual minimum days, full-time equivalent)
# Sources: General knowledge as of 2026; based on common labor standards
VACATION_RULES: Dict[str, Dict] = {
    "US": {
        "name": "United States",
        "federal_mandatory_vacation_days": 0,  # No federal mandate
        "notes": "No federal paid vacation required. Common practice: 10-15 days after 1 year.",
        "fmla_unpaid_leave": True,
        "max_consecutive_work_days": None,
    },
    "EU": {
        "name": "European Union (minimum standard)",
        "mandatory_vacation_days": 20,  # 4 weeks paid (working days)
        "notes": "Directive 2003/88/EC: at least 4 weeks paid annual leave",
    },
    "GB": {  # United Kingdom
        "name": "United Kingdom",
        "mandatory_vacation_days": 28,  # Includes public holidays for many
    },
    "CA": {  # Canada (federal)
        "name": "Canada",
        "mandatory_vacation_days": 10,  # 2 weeks after 1 year, 15 after 5 years
        "notes": "Provincial laws often more generous",
    },
    "DE": {  # Germany
        "name": "Germany",
        "mandatory_vacation_days": 24,  # Minimum for a 6-day week; effectively ~20 for 5-day
    },
    "FR": {  # France
        "name": "France",
        "mandatory_vacation_days": 25,
    },
    "AU": {  # Australia
        "name": "Australia",
        "mandatory_vacation_days": 20,
    },
    "JP": {  # Japan
        "name": "Japan",
        "mandatory_vacation_days": 10,  # Increases with tenure
    },
}


def get_vacation_rules(country: str) -> Optional[Dict]:
    """
    Retrieve vacation law rules for a given country code (ISO 2-letter preferred).

    Args:
        country: Country code (e.g., 'US', 'DE', 'FR')

    Returns:
        Dict with rules if available, else None
    """
    code = country.upper()
    rules = VACATION_RULES.get(code)

    if rules:
        logger.info(f"Loaded vacation rules for {rules['name']} ({code})")
        return rules
    else:
        logger.warning(f"No predefined vacation rules for country: {country}")
        return {
            "name": f"Unknown ({country})",
            "mandatory_vacation_days": None,
            "notes": "No rules defined. Defaulting to permissive mode.",
        }


def can_assign_vacation(employee_vacations_60_days: int, country_rules: Dict) -> bool:
    """
    Basic check: placeholder for whether an employee is eligible for vacation today.
    Currently permissive — real logic would track accrual, tenure, etc.
    """
    # Example future logic:
    # if too many recent vacations → deny to prevent abuse
    if employee_vacations_60_days > 12:
        logger.info("High recent vacations — considering denying additional vacation for fairness/balance")
        return False  # or lower priority
    return True


def validate_schedule_against_laws(schedule, country: str) -> list[str]:
    """
    Validate a generated schedule against basic labor laws.
    Returns a list of warnings/issues.
    """
    warnings = []
    rules = get_vacation_rules(country)

    if rules.get("federal_mandatory_vacation_days") == 0 and country == "US":
        warnings.append("US has no federal paid vacation mandate — ensure company policy is followed.")

    # Future: check for excessive consecutive work days, overtime, rest periods, etc.

    return warnings