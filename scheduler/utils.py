import json
from loguru import logger
from datetime import datetime

def load_json(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)

def parse_datetime(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

logger.add("logs/scheduler.log", rotation="10 MB")