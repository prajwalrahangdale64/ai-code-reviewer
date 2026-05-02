import json, os
from datetime import datetime

DUMP_DIR = "error_dumps"

def save_dump(result: dict, label: str = "review") -> str:
    """
    Saves a review result dict to a timestamped JSON file.
    Returns the file path that was written.
    """
    os.makedirs(DUMP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{DUMP_DIR}/{label}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return filename