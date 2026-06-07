import json
from typing import Any


REQUIRED_FIELDS = [
    "date",
    "shift",
    "employee_number",
    "operation_code",
    "machine_number",
    "work_order_number",
    "quantity_produced",
]


def score_confidence(record: dict[str, Any], extracted_text: str, structured_source: dict[str, Any] | None = None) -> tuple[dict[str, float], float]:
    confidence: dict[str, float] = {}
    text_lower = extracted_text.lower()
    source_text = json.dumps(structured_source or {}, default=str).lower()

    for field, value in record.items():
        if value in (None, ""):
            confidence[field] = 0.15
            continue

        value_text = str(value).lower()
        base = 0.68
        if value_text in text_lower:
            base += 0.22
        elif value_text in source_text:
            base += 0.18
        if field in REQUIRED_FIELDS:
            base += 0.04
        if field in {"quantity_produced", "time_taken_minutes"} and isinstance(value, int) and value > 0:
            base += 0.04
        confidence[field] = round(min(base, 0.98), 2)

    overall = round(sum(confidence.values()) / max(len(confidence), 1), 2)
    return confidence, overall
