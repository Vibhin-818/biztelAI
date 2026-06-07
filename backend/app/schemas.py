from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OperationalRecordBase(BaseModel):
    date: str | None = None
    shift: str | None = None
    employee_number: str | None = None
    operation_code: str | None = None
    machine_number: str | None = None
    work_order_number: str | None = None
    quantity_produced: int | None = None
    time_taken_minutes: int | None = None


class OperationalRecordUpdate(OperationalRecordBase):
    reviewer_notes: str | None = None
    review_status: str = "approved"


class OperationalRecordOut(OperationalRecordBase):
    id: int
    document_id: int
    raw_json: dict[str, Any]
    field_confidence: dict[str, float]
    overall_confidence: float
    validation_errors: list[dict[str, str]]
    review_status: str
    reviewer_notes: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    status: str
    extracted_text: str
    created_at: datetime
    records: list[OperationalRecordOut] = []

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    document: DocumentOut
    message: str = "Document processed"


class DashboardAnalytics(BaseModel):
    total_uploads: int
    total_records: int
    needs_review: int
    validation_failures: int
    total_quantity: int
    average_confidence: float
    shift_summary: dict[str, int]
    machine_summary: dict[str, int]
    quantity_by_shift: dict[str, int]
    recent_failures: list[dict[str, Any]] = Field(default_factory=list)
