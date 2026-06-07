import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
});

export type ValidationError = {
  field: string;
  message: string;
};

export type OperationalRecord = {
  id: number;
  document_id: number;
  date: string | null;
  shift: string | null;
  employee_number: string | null;
  operation_code: string | null;
  machine_number: string | null;
  work_order_number: string | null;
  quantity_produced: number | null;
  time_taken_minutes: number | null;
  raw_json: Record<string, unknown>;
  field_confidence: Record<string, number>;
  overall_confidence: number;
  validation_errors: ValidationError[];
  review_status: string;
  reviewer_notes: string | null;
  updated_at: string;
};

export type DocumentUpload = {
  id: number;
  filename: string;
  content_type: string;
  status: string;
  extracted_text: string;
  created_at: string;
  records: OperationalRecord[];
};

export type Analytics = {
  total_uploads: number;
  total_records: number;
  needs_review: number;
  validation_failures: number;
  total_quantity: number;
  average_confidence: number;
  shift_summary: Record<string, number>;
  machine_summary: Record<string, number>;
  quantity_by_shift: Record<string, number>;
  recent_failures: Array<{ record_id: number; work_order_number: string | null; errors: ValidationError[] }>;
};

export async function uploadDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<{ document: DocumentUpload }>("/documents/upload", form);
  return data.document;
}

export async function fetchDocuments(q = "", status = "") {
  const { data } = await api.get<DocumentUpload[]>("/documents", { params: { q: q || undefined, status: status || undefined } });
  return data;
}

export async function fetchAnalytics() {
  const { data } = await api.get<Analytics>("/analytics");
  return data;
}

export async function updateRecord(record: OperationalRecord, reviewer_notes: string) {
  const { data } = await api.put<OperationalRecord>(`/records/${record.id}`, {
    date: record.date,
    shift: record.shift,
    employee_number: record.employee_number,
    operation_code: record.operation_code,
    machine_number: record.machine_number,
    work_order_number: record.work_order_number,
    quantity_produced: record.quantity_produced,
    time_taken_minutes: record.time_taken_minutes,
    reviewer_notes,
    review_status: "approved"
  });
  return data;
}
