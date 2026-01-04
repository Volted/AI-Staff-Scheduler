"""Utility functions for the scheduler package"""

def extract_json_from_markdown(text: str) -> str:
    if "```json" in text:
        json_start = text.find("```json") + 7
        json_end = text.find("```", json_start)
        return text[json_start:json_end].strip()
    elif "```" in text:
        json_start = text.find("```") + 3
        json_end = text.find("```", json_start)
        return text[json_start:json_end].strip()

    return text.strip()