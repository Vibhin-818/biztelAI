import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import OperationalRecord


REQUIRED = [
    "date",
    "shift",
    "employee_number",
    "operation_code",
    "machine_number",
    "work_order_number",
    "quantity_produced",
]


def validate_record(data: dict[str, Any], confidence: dict[str, float], db: Session, record_id: int | None = None) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    for field in REQUIRED:
        if data.get(field) in (None, ""):
            errors.append({"field": field, "message": "Mandatory field is missing."})

    shift = data.get("shift")
    if shift and str(shift).upper() not in {"A", "B", "C", "DAY", "NIGHT", "I", "II", "III"}:
        errors.append({"field": "shift", "message": "Shift must be A, B, C, DAY, NIGHT, I, II, or III."})

    machine = data.get("machine_number")
    if machine and not re.match(r"^(M|MC|CNC)-?\d{1,4}$", str(machine), flags=re.I):
        errors.append({"field": "machine_number", "message": "Machine code format looks invalid."})

    quantity = data.get("quantity_produced")
    if quantity is not None:
        if quantity <= 0:
            errors.append({"field": "quantity_produced", "message": "Quantity must be greater than zero."})
        elif quantity > 10000:
            errors.append({"field": "quantity_produced", "message": "Quantity is unusually high and needs review."})

    time_taken = data.get("time_taken_minutes")
    if time_taken is not None and time_taken <= 0:
        errors.append({"field": "time_taken_minutes", "message": "Time taken must be greater than zero."})

    work_order = data.get("work_order_number")
    if work_order:
        query = db.query(OperationalRecord).filter(OperationalRecord.work_order_number == str(work_order))
        if record_id is not None:
            query = query.filter(OperationalRecord.id != record_id)
        if query.first():
            errors.append({"field": "work_order_number", "message": "Duplicate work order number."})

    for field, score in confidence.items():
        if score < 0.55:
            errors.append({"field": field, "message": "Low extraction confidence."})

    return errors
