import { useEffect, useState } from "react";
import { UseMutationResult, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, Check, ClipboardList, FileSearch, History, Loader2, Search, Upload } from "lucide-react";
import { Analytics, DocumentUpload, OperationalRecord, fetchAnalytics, fetchDocuments, updateRecord, uploadDocument } from "./lib/api";
import { Badge, Button, Card, Input, Select, Textarea } from "./components/ui";

const fields: Array<keyof OperationalRecord> = [
  "date",
  "shift",
  "employee_number",
  "operation_code",
  "machine_number",
  "work_order_number",
  "quantity_produced",
  "time_taken_minutes"
];

function App() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<DocumentUpload | null>(null);
  const queryClient = useQueryClient();

  const documents = useQuery({ queryKey: ["documents", query, status], queryFn: () => fetchDocuments(query, status) });
  const analytics = useQuery({ queryKey: ["analytics"], queryFn: fetchAnalytics });

  const upload = useMutation({
    mutationFn: uploadDocument,
    onSuccess: (doc) => {
      setSelected(doc);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    }
  });

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-primary">BiztelAI Operations</p>
            <h1 className="text-2xl font-semibold">AI Workflow Automation System</h1>
          </div>
          <div className="flex gap-2 text-sm text-muted-foreground">
            <span>TrOCR</span>
            <span>-</span>
            <span>HF Router</span>
            <span>-</span>
            <span>Review</span>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-5 lg:grid-cols-[360px_1fr]">
        <section className="space-y-5">
          <UploadPanel upload={upload} />
          <SearchPanel query={query} status={status} setQuery={setQuery} setStatus={setStatus} />
          <HistoryPanel documents={documents.data ?? []} selected={selected} setSelected={setSelected} isLoading={documents.isLoading} />
        </section>

        <section className="space-y-5">
          <Dashboard analytics={analytics.data} />
          <ReviewPanel document={selected ?? documents.data?.[0] ?? null} onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ["documents"] });
            queryClient.invalidateQueries({ queryKey: ["analytics"] });
          }} />
        </section>
      </div>
    </main>
  );
}

function UploadPanel({ upload }: { upload: UseMutationResult<DocumentUpload, Error, File> }) {
  const [preview, setPreview] = useState<string | null>(null);

  return (
    <Card className="p-4">
      <div className="mb-4 flex items-center gap-2">
        <Upload className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">Upload Document</h2>
      </div>
      <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-border bg-muted/35 p-4 text-center">
        <Upload className="mb-2 h-6 w-6 text-muted-foreground" />
        <span className="text-sm font-medium">Drop image, PDF, or text sample</span>
        <span className="text-xs text-muted-foreground">PNG, JPG, PDF, TXT</span>
        <input
          className="hidden"
          type="file"
          accept="image/*,.pdf,.txt"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            setPreview(URL.createObjectURL(file));
            upload.mutate(file);
          }}
        />
      </label>
      {preview && <iframe className="mt-4 h-48 w-full rounded-md border border-border bg-white" src={preview} title="Document preview" />}
      {upload.isPending && <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Processing OCR and extraction</p>}
      {upload.isError && <p className="mt-3 text-sm text-red-700">{upload.error.message}</p>}
    </Card>
  );
}

function SearchPanel({ query, status, setQuery, setStatus }: { query: string; status: string; setQuery: (value: string) => void; setStatus: (value: string) => void }) {
  return (
    <Card className="p-4">
      <div className="mb-4 flex items-center gap-2">
        <Search className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">Search & Filter</h2>
      </div>
      <div className="space-y-3">
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Work order, machine, employee, text" />
        <Select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All records</option>
          <option value="needs_review">Needs review</option>
          <option value="approved">Approved</option>
        </Select>
      </div>
    </Card>
  );
}

function HistoryPanel({ documents, selected, setSelected, isLoading }: { documents: DocumentUpload[]; selected: DocumentUpload | null; setSelected: (doc: DocumentUpload) => void; isLoading: boolean }) {
  return (
    <Card className="p-4">
      <div className="mb-4 flex items-center gap-2">
        <History className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">Document History</h2>
      </div>
      <div className="max-h-[520px] space-y-2 overflow-auto pr-1">
        {isLoading && <p className="text-sm text-muted-foreground">Loading history...</p>}
        {documents.map((doc) => (
          <button
            key={doc.id}
            onClick={() => setSelected(doc)}
            className={`w-full rounded-md border p-3 text-left transition ${selected?.id === doc.id ? "border-primary bg-teal-50" : "border-border bg-white hover:bg-muted/40"}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{doc.filename}</p>
                <p className="text-xs text-muted-foreground">{new Date(doc.created_at).toLocaleString()}</p>
              </div>
              <Badge tone={doc.record?.review_status === "approved" ? "success" : "warning"}>{doc.record?.review_status ?? "queued"}</Badge>
            </div>
            <p className="mt-2 truncate text-xs text-muted-foreground">{doc.record?.work_order_number ?? "No work order detected"}</p>
          </button>
        ))}
        {!isLoading && documents.length === 0 && <p className="text-sm text-muted-foreground">No documents yet.</p>}
      </div>
    </Card>
  );
}

function Dashboard({ analytics }: { analytics?: Analytics }) {
  const stats = [
    ["Uploads", analytics?.total_uploads ?? 0],
    ["Needs Review", analytics?.needs_review ?? 0],
    ["Validation Failures", analytics?.validation_failures ?? 0],
    ["Total Quantity", analytics?.total_quantity ?? 0]
  ];

  return (
    <section>
      <div className="mb-3 flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">Analytics Dashboard</h2>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(([label, value]) => (
          <Card key={label} className="p-4">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-2 text-2xl font-semibold">{value}</p>
          </Card>
        ))}
      </div>
      <div className="mt-3 grid gap-3 xl:grid-cols-3">
        <MiniChart title="Shift Summary" data={analytics?.shift_summary ?? {}} />
        <MiniChart title="Quantity By Shift" data={analytics?.quantity_by_shift ?? {}} />
        <MiniChart title="Machine Summary" data={analytics?.machine_summary ?? {}} />
      </div>
    </section>
  );
}

function MiniChart({ title, data }: { title: string; data: Record<string, number> }) {
  const max = Math.max(...Object.values(data), 1);
  return (
    <Card className="p-4">
      <p className="mb-3 text-sm font-medium">{title}</p>
      <div className="space-y-2">
        {Object.entries(data).slice(0, 6).map(([label, value]) => (
          <div key={label}>
            <div className="mb-1 flex justify-between text-xs">
              <span>{label}</span>
              <span>{value}</span>
            </div>
            <div className="h-2 rounded-full bg-muted">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.max((value / max) * 100, 6)}%` }} />
            </div>
          </div>
        ))}
        {Object.keys(data).length === 0 && <p className="text-sm text-muted-foreground">No data yet.</p>}
      </div>
    </Card>
  );
}

function ReviewPanel({ document, onSaved }: { document: DocumentUpload | null; onSaved: () => void }) {
  const [draft, setDraft] = useState<OperationalRecord | null>(null);
  const [notes, setNotes] = useState("");
  const queryClient = useQueryClient();

  useEffect(() => {
    setDraft(document?.record ?? null);
    setNotes(document?.record?.reviewer_notes ?? "");
  }, [document?.id]);

  const save = useMutation({
    mutationFn: () => {
      if (!draft) throw new Error("No record selected");
      return updateRecord(draft, notes);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      onSaved();
    }
  });

  if (!document || !draft) {
    return (
      <Card className="p-6 text-center">
        <FileSearch className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
        <p className="font-medium">Upload or select a document to review.</p>
      </Card>
    );
  }

  const errorsByField = new Map(draft.validation_errors.map((error) => [error.field, error.message]));

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">Human Review</h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{document.filename}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={draft.review_status === "approved" ? "success" : "warning"}>{draft.review_status}</Badge>
          <Badge tone={draft.overall_confidence >= 0.78 ? "success" : "warning"}>{Math.round(draft.overall_confidence * 100)}% confidence</Badge>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div>
          <div className="grid gap-3 md:grid-cols-2">
            {fields.map((field) => (
              <label key={field} className="space-y-1">
                <span className="flex items-center justify-between text-sm font-medium">
                  {labelFor(field)}
                  <span className={confidenceClass(draft.field_confidence[field] ?? 0)}>{Math.round((draft.field_confidence[field] ?? 0) * 100)}%</span>
                </span>
                <Input
                  value={(draft[field] as string | number | null) ?? ""}
                  type={field.includes("quantity") || field.includes("time") ? "number" : "text"}
                  onChange={(event) => setDraft({ ...draft, [field]: field.includes("quantity") || field.includes("time") ? Number(event.target.value) : event.target.value })}
                />
                {errorsByField.has(field) && <p className="flex gap-1 text-xs text-red-700"><AlertTriangle className="h-3 w-3 shrink-0" />{errorsByField.get(field)}</p>}
              </label>
            ))}
          </div>

          <label className="mt-4 block space-y-1">
            <span className="text-sm font-medium">Reviewer Notes</span>
            <Textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Correction notes, exception reason, production context" />
          </label>

          <div className="mt-4 flex flex-wrap gap-2">
            <Button disabled={save.isPending} onClick={() => save.mutate()}>
              {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Save Reviewed Record
            </Button>
            {save.isSuccess && <span className="self-center text-sm text-emerald-700">Saved</span>}
          </div>
        </div>

        <aside className="space-y-3">
          <Card className="bg-muted/25 p-4 shadow-none">
            <p className="mb-2 text-sm font-medium">Extracted Text</p>
            <p className="max-h-48 overflow-auto whitespace-pre-wrap text-sm text-muted-foreground">{document.extracted_text}</p>
          </Card>
          <Card className="bg-muted/25 p-4 shadow-none">
            <p className="mb-2 text-sm font-medium">Validation</p>
            <div className="space-y-2">
              {draft.validation_errors.map((error, index) => (
                <p key={`${error.field}-${index}`} className="rounded-md bg-red-50 p-2 text-sm text-red-800">{error.field}: {error.message}</p>
              ))}
              {draft.validation_errors.length === 0 && <p className="text-sm text-emerald-700">No validation issues detected.</p>}
            </div>
          </Card>
        </aside>
      </div>
    </Card>
  );
}

function labelFor(field: keyof OperationalRecord) {
  return String(field).replace(/_/g, " ").replace(/\b\w/g, (char: string) => char.toUpperCase());
}

function confidenceClass(score: number) {
  if (score >= 0.78) return "text-xs font-semibold text-emerald-700";
  if (score >= 0.55) return "text-xs font-semibold text-amber-700";
  return "text-xs font-semibold text-red-700";
}

export default App;
