# AI Workflow

This project was developed with Codex as an AI pair-programming assistant.

## Tools Used

- Codex for requirement analysis, architecture planning, implementation, and verification guidance.
- FastAPI, SQLAlchemy, React, TypeScript, TailwindCSS, Axios, and React Query as the implementation stack.
- Microsoft TrOCR and Hugging Face Inference Router as the intended AI extraction stack.

## How AI Helped

- Translated the assignment brief into an end-to-end product workflow.
- Designed the data model around upload history, extracted text, structured records, confidence, validations, and review state.
- Implemented adapter boundaries so real OCR/LLM services can run in production while local fallbacks keep the prototype demoable.
- Created operational analytics around shifts, machines, quantities, review queues, and validation failures.

## Prompting And Debugging Workflow

- Started from the assignment document and mandatory architecture.
- Built a minimal production-shaped backend first: API, persistence, validation, scoring, and AI adapters.
- Built frontend views around actual user workflows: upload, review, search/history, dashboard.
- Kept validation rules explicit and explainable so reviewers can inspect why a field was flagged.

## Manual Intervention

- Real deployment credentials, Hugging Face API keys, and production TrOCR dependency tuning must be supplied by the developer.
- Optional PDF rasterization can be added based on the deployment target.
- Demo video and hosted deployment URLs are intentionally left for the submitter to record and publish.

