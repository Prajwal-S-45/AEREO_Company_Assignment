# Bulk Certificate Generator

A production-oriented FastAPI backend for creating certificates for many recipients in a single request, tracking each generation, and retrieving generated PDF certificates.

## Assignment coverage

- Python + FastAPI backend
- SQLite relational database
- One predefined certificate design generated as PDF with ReportLab
- Bulk generation in one API request
- Pydantic validation for recipient and request data
- Background processing using a thread pool so the API returns a job ID immediately
- Per-certificate status (`queued`, `processing`, `completed`, `failed`)
- Job-level progress and success/failure counts
- One failed certificate does not stop other recipients
- Certificate download endpoint
- Automated tests for job creation, validation, generation, progress, failure isolation, and retrieval

## Architecture

`POST /generation-jobs` validates the complete request, creates a job and one certificate row per recipient, then schedules background work. A worker processes each certificate independently. The SQLite database is the source of truth for job and certificate state; generated PDFs are stored under `storage/certificates/`.

### Why background processing?

Bulk PDF generation can take longer as recipient count increases. Returning `202 Accepted` with a job ID keeps the HTTP request short and lets the client poll job status. A `ThreadPoolExecutor` with four workers provides bounded concurrency without requiring an external queue for this assignment. In a larger production deployment, the worker layer could be replaced with Celery/RQ + Redis or a managed queue.

## Requirements

- Python 3.10+

## Setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`.

## API usage

### 1. Create a bulk generation job

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generation-jobs" ^
  -H "Content-Type: application/json" ^
  -d "{\"course_name\":\"Python Backend Workshop\",\"event_date\":\"2026-10-08\",\"recipients\":[{\"name\":\"Alice Johnson\",\"email\":\"alice@example.com\"},{\"name\":\"Bob Smith\"}]}"
```

Example response:

```json
{
  "job_id": "<uuid>",
  "status": "queued",
  "total": 2
}
```

### 2. Check job progress

```text
GET /api/v1/generation-jobs/{job_id}
```

The response includes `total`, `successful`, `failed`, `progress_percent`, and the status of every certificate.

### 3. List generated certificates

```text
GET /api/v1/generation-jobs/{job_id}/certificates
```

### 4. Download an individual certificate

```text
GET /api/v1/certificates/{certificate_id}/download
```

The endpoint returns the generated PDF.

## Validation and failure handling

The request validates:

- `course_name`: 2–200 characters
- `event_date`: ISO date
- at least one and at most 10,000 recipients
- recipient name: 2–120 characters and must contain alphabetic characters
- recipient email: optional but validated when supplied
- unknown JSON fields are rejected

Each recipient has an independent database record. If one certificate fails, that recipient is marked `failed` with an error message while the remaining recipients continue. The test suite uses the reserved name `[FAIL]` to deterministically exercise this path without introducing an artificial production failure.

## Testing

Run:

```bash
pytest -q
```

The tests cover:

1. Creating a generation job
2. Input validation
3. Certificate PDF generation and retrieval
4. Job progress/status
5. Individual certificate failure without stopping other work
6. Listing certificates for a job

## Project structure

```text
bulk_certificate_generator/
├── app/
│   ├── main.py              # FastAPI routes and application setup
│   ├── database.py          # SQLite schema and connection helper
│   ├── schemas.py           # Pydantic request/response validation
│   ├── services.py          # PDF certificate generation
│   ├── worker.py            # Background bulk processing
│   ├── config.py            # Paths and configuration
│   └── templates/            # Predefined certificate design reference
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── storage/
│   ├── certificates/
│   └── .gitkeep
├── requirements.txt
├── .gitignore
└── README.md
```

## Design notes / production considerations

- SQLite is appropriate for a self-contained assignment; PostgreSQL would be a better production database for concurrent multi-instance deployment.
- The worker uses bounded concurrency to avoid starting an unbounded thread per recipient.
- Database state is updated after every individual certificate, allowing progress to survive individual failures.
- Generated files use UUIDs rather than user-controlled filenames.
- For very large workloads, the same API/data model can be moved to a durable queue and object storage.
