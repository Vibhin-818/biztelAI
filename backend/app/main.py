from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import Base, engine, get_db
from app.models import DocumentUpload, OperationalRecord
from app.schemas import DashboardAnalytics, DocumentOut, OperationalRecordOut, OperationalRecordUpdate, UploadResponse
from app.services.llm import LLMExtractionService
from app.services.ocr import OCRService
from app.services.scoring import score_confidence
from app.services.validation import validate_record
from app.services.vision import VisionExtractionService


Base.metadata.create_all(bind=engine)

app = FastAPI(title="BiztelAI Workflow Automation API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_path)), name="uploads")

ocr_service = OCRService()
llm_service = LLMExtractionService()
vision_service = VisionExtractionService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadResponse:
    suffix = Path(file.filename or "document").suffix
    stored_name = f"{uuid4().hex}{suffix}"
    file_path = settings.upload_path / stored_name
    file_path.write_bytes(await file.read())

    extracted_text = ocr_service.extract_text(file_path, file.content_type or "application/octet-stream")
    is_image = (file.content_type or "").startswith("image/") or file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    vision_context = "" if extracted_text.startswith("Source file ") else extracted_text
    structured = await vision_service.structure_image(file_path, vision_context) if is_image else None
    if structured is None:
        structured = await llm_service.structure_text(extracted_text)

    record_fields = {
        "date": structured.get("date"),
        "shift": structured.get("shift"),
        "employee_number": structured.get("employee_number"),
        "operation_code": structured.get("operation_code"),
        "machine_number": structured.get("machine_number"),
        "work_order_number": structured.get("work_order_number"),
        "quantity_produced": structured.get("quantity_produced"),
        "time_taken_minutes": structured.get("time_taken_minutes"),
    }
    confidence, overall = score_confidence(record_fields, extracted_text, structured)
    validations = validate_record(record_fields, confidence, db)
    review_status = "approved" if not validations and overall >= 0.78 else "needs_review"

    document = DocumentUpload(
        filename=file.filename or stored_name,
        content_type=file.content_type or "application/octet-stream",
        file_path=str(file_path),
        extracted_text=extracted_text,
        status="processed",
    )
    db.add(document)
    db.flush()

    record = OperationalRecord(
        document_id=document.id,
        raw_json=structured,
        field_confidence=confidence,
        overall_confidence=overall,
        validation_errors=validations,
        review_status=review_status,
        **record_fields,
    )
    db.add(record)
    db.commit()
    db.refresh(document)
    return UploadResponse(document=document)


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(q: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> list[DocumentUpload]:
    query = db.query(DocumentUpload).options(joinedload(DocumentUpload.record)).join(OperationalRecord)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                DocumentUpload.filename.ilike(like),
                DocumentUpload.extracted_text.ilike(like),
                OperationalRecord.work_order_number.ilike(like),
                OperationalRecord.machine_number.ilike(like),
                OperationalRecord.employee_number.ilike(like),
            )
        )
    if status:
        query = query.filter(OperationalRecord.review_status == status)
    return query.order_by(DocumentUpload.created_at.desc()).all()


@app.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentUpload:
    document = db.query(DocumentUpload).options(joinedload(DocumentUpload.record)).filter(DocumentUpload.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.put("/records/{record_id}", response_model=OperationalRecordOut)
def update_record(record_id: int, payload: OperationalRecordUpdate, db: Session = Depends(get_db)) -> OperationalRecord:
    record = db.query(OperationalRecord).filter(OperationalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    data = payload.model_dump(exclude={"reviewer_notes", "review_status"})
    confidence, overall = score_confidence(data, record.document.extracted_text if record.document else "")
    validations = validate_record(data, confidence, db, record_id=record.id)

    for key, value in data.items():
        setattr(record, key, value)
    record.raw_json = data
    record.field_confidence = confidence
    record.overall_confidence = overall
    record.validation_errors = validations
    record.review_status = payload.review_status if not validations else "needs_review"
    record.reviewer_notes = payload.reviewer_notes
    db.commit()
    db.refresh(record)
    return record


@app.get("/analytics", response_model=DashboardAnalytics)
def analytics(db: Session = Depends(get_db)) -> DashboardAnalytics:
    records = db.query(OperationalRecord).all()
    total_uploads = db.query(func.count(DocumentUpload.id)).scalar() or 0
    total_records = len(records)
    needs_review = sum(1 for record in records if record.review_status == "needs_review")
    validation_failures = sum(1 for record in records if record.validation_errors)
    quantities = [record.quantity_produced or 0 for record in records]
    confidences = [record.overall_confidence or 0 for record in records]

    shift_summary: dict[str, int] = {}
    machine_summary: dict[str, int] = {}
    quantity_by_shift: dict[str, int] = {}
    recent_failures = []

    for record in records:
        shift = record.shift or "Unknown"
        machine = record.machine_number or "Unknown"
        shift_summary[shift] = shift_summary.get(shift, 0) + 1
        machine_summary[machine] = machine_summary.get(machine, 0) + 1
        quantity_by_shift[shift] = quantity_by_shift.get(shift, 0) + (record.quantity_produced or 0)
        if record.validation_errors:
            recent_failures.append(
                {
                    "record_id": record.id,
                    "work_order_number": record.work_order_number,
                    "errors": record.validation_errors[:3],
                }
            )

    return DashboardAnalytics(
        total_uploads=total_uploads,
        total_records=total_records,
        needs_review=needs_review,
        validation_failures=validation_failures,
        total_quantity=sum(quantities),
        average_confidence=round(sum(confidences) / max(len(confidences), 1), 2),
        shift_summary=shift_summary,
        machine_summary=machine_summary,
        quantity_by_shift=quantity_by_shift,
        recent_failures=recent_failures[:5],
    )
