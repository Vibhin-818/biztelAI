# BiztelAI AI-Powered Workflow Automation System

Production-style prototype for digitizing handwritten or semi-structured manufacturing operational documents.

## What It Does

- Upload handwritten images or PDFs.
- Preview uploaded documents and keep upload history.
- Extract text with Microsoft TrOCR when ML dependencies are installed.
- Convert extracted text into structured operational records through Hugging Face Inference Router.
- Fall back to deterministic parsing when API keys or models are unavailable.
- Score field confidence.
- Validate business rules.
- Support human review and correction.
- Store uploads and records in SQLite, with PostgreSQL-ready configuration.
- Provide dashboard analytics and searchable history.

## Architecture

```text
Handwritten Image / PDF
        |
Upload Module
        |
Microsoft TrOCR OCR Adapter
        |
Extracted Text
        |
Hugging Face Router
(Llama / Mistral)
        |
Structured JSON
        |
Confidence Scoring
        |
Validation Engine
        |
Human Review Screen
        |
Database Storage
        |
Analytics Dashboard
```

## Tech Stack

Frontend:

- React
- TypeScript
- TailwindCSS
- ShadCN-style local UI primitives
- Axios
- React Query

Backend:

- FastAPI
- Python 3.12
- Pydantic
- SQLAlchemy
- SQLite by default, PostgreSQL-ready

AI Layer:

- Microsoft TrOCR
- Hugging Face Inference Router
- `mistralai/Mistral-Small-3.1-24B-Instruct` by default
- Optional `meta-llama/Llama-3.3-70B-Instruct`

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
uvicorn app.main:app --reload --port 8000
```

For full TrOCR support, install the optional OCR dependencies:

```bash
pip install -r requirements-ocr.txt
```

Without optional OCR dependencies, the backend still works by using uploaded `.txt` files or filename/sample-text fallback extraction so the workflow remains demoable.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

## Environment Variables

Create `.env` from `.env.example`.

```env
HF_API_KEY=
HF_MODEL=mistralai/Mistral-Small-3.1-24B-Instruct
DATABASE_URL=sqlite:///records.db
UPLOAD_DIR=uploads
```

## Business Rules

The validation engine flags:

- Missing mandatory fields: date, shift, employee number, operation code, machine number, work order number, quantity produced.
- Invalid shifts outside `A`, `B`, `C`, `DAY`, `NIGHT`.
- Machine numbers that do not match formats like `M-102`, `MC-12`, or `CNC-04`.
- Non-positive or suspicious quantities.
- Non-positive time taken.
- Duplicate work order numbers.
- Low-confidence fields.

## Deployment Notes

Frontend:

- Deploy `frontend` to Vercel.
- Set `VITE_API_BASE_URL` to the Render backend URL.

Backend:

- Deploy `backend` to Render.
- Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Set `DATABASE_URL` to Render/PostgreSQL when moving beyond SQLite.

## Tradeoffs

- The OCR and LLM layers are adapter-based. Real TrOCR and Hugging Face Router are used when credentials/dependencies are present; robust fallbacks keep the prototype testable during review.
- ShadCN UI is represented by local, typed primitives instead of generated registry components to keep the repo dependency-light and portable.
- PDF preview is browser-native. OCR for PDFs is represented by a placeholder text path unless PDF rasterization dependencies are added.
