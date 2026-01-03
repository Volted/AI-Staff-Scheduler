# AI-Staff-Scheduler

## Overview

AI-Staff-Scheduler is an agentic AI-powered staff scheduling module designed to automate the assignment of employees to daily tasks, including vacations, while ensuring fairness, compliance with business and legal requirements, and optimization based on employee preferences and qualifications. This project leverages xAI's Grok models through the public API to handle complex decision-making processes, such as balancing workloads, respecting vacation laws, and incorporating historical data for fair distribution.

The system processes inputs like task lists (including a full-day vacation task), employee profiles, and task requirements. It uses AI to generate scheduling recommendations, validate them against constraints (e.g., certification matches, capacity needs, and legal vacation mandates), and output a fair task-to-staff mapping. The core logic is implemented in Python, with Grok API integration for agentic reasoning—such as interpreting preferences, resolving conflicts, and ensuring fairness over time.

This module is ideal for businesses in sectors like retail, hospitality, healthcare, or logistics where dynamic staffing is crucial. It promotes employee satisfaction by considering preferences and historical approvals/ denials while maintaining operational efficiency.

## Key Features

- **Input Processing**: Handles lists of tasks and employees in JSON format, including details like preferences, certifications, historical vacations, and approval/denial rates.
- **AI-Driven Assignment**: Uses xAI's Grok API to intelligently assign staff to tasks based on preferences, certifications, and fairness metrics.
- **Vacation Management**: Includes a dedicated full-day vacation task; checks against country-specific labor laws (e.g., minimum vacation days, accrual rules) using web searches or predefined rules.
- **Fairness and Equity**: Analyzes historical data (e.g., vacations over 60 days, approval/denial ratios) to ensure balanced distribution and prevent burnout or favoritism.
- **Capacity Optimization**: Matches staff to tasks based on required capacity (e.g., one staffer per 6 customers) and customer demand.
- **Legal Compliance**: Dynamically queries or references laws for vacations in the business's country (configurable).
- **Output Generation**: Produces a schedule in JSON or human-readable format, with explanations for assignments.
- **Extensibility**: Modular design allows for adding more AI agents (e.g., for conflict resolution) or integrating with calendars/HR systems.
- **Error Handling and Validation**: Validates inputs, handles edge cases like insufficient staff, and provides fallback manual overrides.

## Prerequisites and Dependencies

- **Python Version**: Python 3.8 or higher.
- **xAI Grok API**: Requires an API key from xAI's public API (sign up at xAI's developer portal). The API is used for natural language processing and decision-making.
- **Libraries**:
  - `requests`: For API calls to xAI Grok.
  - `json`: For handling input/output data.
  - `datetime`: For date calculations (e.g., 60-day windows).
  - `os` and `sys`: For file I/O and command-line interfaces.
  - `pydantic`: For data validation and modeling (employee/task schemas).
  - `loguru`: For logging.
  - Optional: `pandas` for data analysis in reporting; `google-search` or similar for dynamic law queries (if not using predefined rules).

Install dependencies via:
```
pip install requests pydantic loguru pandas
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AI-Staff-Scheduler.git
   cd AI-Staff-Scheduler
   ```

2. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add your xAI Grok API key: `GROK_API_KEY=your_api_key_here`.
   - Optionally, set `COUNTRY_CODE=US` for default labor law checks.

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run tests:
   ```
   python -m unittest discover tests
   ```

## Usage

### Command-Line Interface
Run the scheduler with input files:
```
python main.py --tasks tasks.json --employees employees.json --date 2026-01-03 --country US
```
- `--tasks`: Path to JSON file with a task list.
- `--employees`: Path to JSON file with an employee list.
- `--date`: Scheduling date (YYYY-MM-DD).
- `--country`: ISO country code for vacation laws (default: US).
- Output: Generates `schedule.json` and logs explanations.

### Example Input Formats

**tasks.json** (Array of tasks, including one vacation task):
```json
[
  {
    "task_id": 12,
    "category": 3,
    "customer_capacity": 30,
    "required_capacity_per_staff": 6, 
    "required_certifications": [1,3,5],
    "start": "2026-01-03 08:00:00",
    "end": "2026-01-03 09:00:00"
  },
  {
    "task_id": 356,
    "category": 3,
    "customer_capacity": 12,
    "required_capacity_per_staff": 6, 
    "required_certifications": [2,4],
    "start": "2026-01-03 10:00:00",
    "end": "2026-01-03 11:00:00" 
  },
  {
    "task_id": 0,
    "category": 0,
    "customer_capacity": 0,
    "required_capacity_per_staff": 1,
    "required_certifications": [],
    "start": "2026-01-03 08:00:00",
    "end": "2026-01-03 16:00:00" 
  }
]
```

**employees.json** (Array of employees):
```json
[
  {
    "employee_id": 65223,
    "name": "John Doe",
    "preferences": [3],
    "certifications": [1,2,3,5],
    "previous_vacations_60_days": 5, 
    "approved_requests_60_days": 8,
    "denied_requests_60_days": 2
  }
]
```

### API Integration
The system calls xAI's Grok API with prompts like:
- "Given these employee preferences and task requirements, suggest fair assignments while ensuring no one exceeds vacation limits per [country] laws."
Grok responds with reasoned assignments, which are then validated programmatically.

## File Structure

```
AI-Staff-Scheduler/
├── README.md               # This file: Project overview, usage, and docs
├── main.py                 # Entry point: CLI handler, orchestrates scheduling
├── scheduler/
│   ├── __init__.py
│   ├── core.py             # Core scheduling logic: Assignment algorithm, fairness checks
│   ├── models.py           # Pydantic models for Employee, Task, Schedule
│   ├── ai_agent.py         # xAI Grok API integration: Prompt generation, API calls
│   ├── validators.py       # Input validation, certification matching, capacity calcs
│   ├── laws.py             # Vacation law checker: Predefined rules or web query stubs
│   └── utils.py            # Utilities: Date handling, JSON I/O, logging
├── data/
│   ├── sample_tasks.json   # Sample task input
│   └── sample_employees.json # Sample employee input
├── tests/
│   ├── __init__.py
│   ├── test_core.py        # Unit tests for scheduling logic
│   ├── test_ai_agent.py    # Tests for API integration (mocked)
│   └── test_validators.py  # Tests for validation functions
├── config/
│   └── config.yaml         # Configuration: API endpoints, default params
├── logs/                   # Runtime logs (generated)
├── requirements.txt        # Python dependencies
└── .env.example            # Example env file for API keys
```

## Detailed Functions and Modules

### scheduler/core.py
- `generate_schedule(tasks: List[Task], employees: List[Employee], date: str, country: str) -> Schedule`: Main function. Processes inputs, calls AI for suggestions, applies validations, and ensures fairness.
- `calculate_fairness_score(employee: Employee) -> float`: Computes a score based on historical approvals/denials and vacations to prioritize underserved employees.
- `assign_staff_to_tasks(ai_suggestions: Dict) -> Dict[str, List[str]]`: Maps task_ids to employee_ids, handling conflicts.

### scheduler/ai_agent.py
- `call_grok_api(prompt: str) -> str`: Sends prompt to xAI Grok API and returns response.
- `build_prompt(tasks, employees, laws) -> str`: Constructs a detailed prompt for Grok, including all data and instructions for fair assignment.
- Handles retries and error parsing for API calls.

### scheduler/validators.py
- `validate_certifications(employee: Employee, task: Task) -> bool`: Checks if employee has required certs.
- `check_capacity(task: Task, assigned_staff: int) -> bool`: Ensures staff count meets customer capacity / required_per_staff.
- `validate_vacation_laws(country: str, employee: Employee) -> bool`: Verifies against laws (e.g., US: FMLA rules; EU: 4 weeks min).

### scheduler/laws.py
- `get_vacation_rules(country: str) -> Dict`: Returns rules like min_days, accrual_rate. (Stub for expansion to web searches.)
- Supports extensibility for dynamic checks via tools like web_search (if integrated).

### scheduler/models.py
- `class Employee(BaseModel)`: Defines fields like id, preferences, certifications, etc.
- `class Task(BaseModel)`: Defines fields like id, category, capacities, etc.
- `class Schedule(BaseModel)`: Output structure with assignments and explanations.

### scheduler/utils.py
- `load_json(file_path: str) -> Dict`: Loads input files.
- `save_schedule(schedule: Schedule, output_path: str)`: Saves output.
- Logging setup with loguru for debug/info/error levels.

## Development and Contribution

- **Testing**: Use unittest for coverage. Mock API calls in tests to avoid real API usage.
- **Extending AI**: Add more Grok prompts for scenarios like overstaffing or emergencies.
- **Compliance Note**: Vacation laws are approximations; consult legal experts for production use.
- **License**: MIT License. Contributions welcome via pull requests.

## Roadmap

- Integrate calendar APIs (e.g., Google Calendar) for real-time scheduling.
- Add GUI via Streamlit or Flask.
- Support multi-day scheduling.
- Enhance AI with multi-agent systems (e.g., one for fairness, one for optimization).

For questions or issues, open a GitHub issue. Happy scheduling!