from contextlib import asynccontextmanager
from datetime import date
import uuid
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from .database import init_db, get_db
from .schemas import GenerationRequest, JobCreatedResponse, JobStatusResponse
from .services import utc_now
from .worker import start_job

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0",
    description="Generate and track certificates for many recipients in one request.",
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/generation-jobs", response_model=JobCreatedResponse, status_code=202)
def create_generation_job(payload: GenerationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    now = utc_now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO jobs(id,status,total,successful,failed,created_at) VALUES(?,?,?,?,?,?)",
            (job_id, "queued", len(payload.recipients), 0, 0, now),
        )
        for recipient in payload.recipients:
            certificate_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO certificates(id,job_id,recipient_name,recipient_email,course_name,event_date,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (certificate_id, job_id, recipient.name, str(recipient.email) if recipient.email else None,
                 payload.course_name, payload.event_date.isoformat(), "queued", now),
            )
    background_tasks.add_task(start_job, job_id)
    return JobCreatedResponse(job_id=job_id, status="queued", total=len(payload.recipients))

@app.get("/api/v1/generation-jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    with get_db() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        certificates = conn.execute(
            "SELECT id,recipient_name,recipient_email,status,error_message FROM certificates WHERE job_id=? ORDER BY created_at",
            (job_id,),
        ).fetchall()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    results = []
    for cert in certificates:
        results.append({
            "id": cert["id"],
            "recipient_name": cert["recipient_name"],
            "recipient_email": cert["recipient_email"],
            "status": cert["status"],
            "download_url": f"/api/v1/certificates/{cert['id']}/download" if cert["status"] == "completed" else None,
            "error": cert["error_message"],
        })
    processed = job["successful"] + job["failed"]
    progress = round(processed / job["total"] * 100, 2) if job["total"] else 100.0
    return JobStatusResponse(
        job_id=job_id, status=job["status"], total=job["total"], successful=job["successful"],
        failed=job["failed"], progress_percent=progress, certificates=results,
    )

@app.get("/api/v1/certificates/{certificate_id}/download")
def download_certificate(certificate_id: str):
    with get_db() as conn:
        cert = conn.execute("SELECT * FROM certificates WHERE id=?", (certificate_id,)).fetchone()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert["status"] != "completed" or not cert["file_path"]:
        raise HTTPException(status_code=409, detail=f"Certificate is {cert['status']}")
    from pathlib import Path
    path = Path(cert["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Generated certificate file is missing")
    return FileResponse(path, media_type="application/pdf", filename=f"{cert['recipient_name']}_certificate.pdf")

@app.get("/api/v1/generation-jobs/{job_id}/certificates")
def list_job_certificates(job_id: str):
    with get_db() as conn:
        job = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
        rows = conn.execute(
            "SELECT id,recipient_name,recipient_email,status,error_message FROM certificates WHERE job_id=? ORDER BY created_at",
            (job_id,),
        ).fetchall()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return [{
        "id": row["id"],
        "recipient_name": row["recipient_name"],
        "recipient_email": row["recipient_email"],
        "status": row["status"],
        "download_url": f"/api/v1/certificates/{row['id']}/download" if row["status"] == "completed" else None,
        "error": row["error_message"],
    } for row in rows]
