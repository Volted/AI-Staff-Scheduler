import argparse
from scheduler.core import generate_schedule
from scheduler.utils import load_json
import json

def main():
    parser = argparse.ArgumentParser(description="AI Staff Scheduler using xAI Grok")
    parser.add_argument("--tasks", required=True, help="Path to tasks.json")
    parser.add_argument("--employees", required=True, help="Path to employees.json")
    parser.add_argument("--date", required=True, help="Schedule date YYYY-MM-DD")
    parser.add_argument("--country", default="US", help="Country for labor laws")
    parser.add_argument("--output", default="schedule.json", help="Output file")

    args = parser.parse_args()

    tasks_data = load_json(args.tasks)
    employees_data = load_json(args.employees)

    schedule = generate_schedule(tasks_data, employees_data, args.date, args.country)

    with open(args.output, "w") as f:
        json.dump(schedule.dict(), f, indent=2, default=str)

    print(f"Schedule generated: {args.output}")
    print(schedule)

if __name__ == "__main__":
    main()