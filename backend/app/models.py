from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentUpload(Base):
    __tablename__ = "document_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="processed")
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    record: Mapped["OperationalRecord"] = relationship(back_populates="document", uselist=False)


class OperationalRecord(Base):
    __tablename__ = "operational_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document_uploads.id"), nullable=False)
    date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    shift: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employee_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    operation_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    machine_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    work_order_number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    quantity_produced: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_taken_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_json: Mapped[dict] = mapped_column(JSON, default=dict)
    field_confidence: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    review_status: Mapped[str] = mapped_column(String(40), default="needs_review")
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document: Mapped[DocumentUpload] = relationship(back_populates="record")
