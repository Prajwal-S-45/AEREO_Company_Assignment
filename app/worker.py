from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import uuid
from .database import get_db
from .services import generate_certificate, utc_now

executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="certificate-worker")


def process_one(job_id: str, certificate_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM certificates WHERE id=? AND job_id=?", (certificate_id, job_id)).fetchone()
    if not row:
        return

    try:
        # Explicit test hook: a recipient named [FAIL] exercises isolated failure handling.
        if row["recipient_name"].strip().upper() == "[FAIL]":
            raise RuntimeError("Simulated certificate generation failure")
        path = generate_certificate(
            certificate_id=certificate_id,
            recipient_name=row["recipient_name"],
            course_name=row["course_name"],
            event_date=row["event_date"],
        )
        with get_db() as conn:
            conn.execute("UPDATE certificates SET status='completed', file_path=? WHERE id=?", (str(path), certificate_id))
            conn.execute("UPDATE jobs SET successful=successful+1 WHERE id=?", (job_id,))
    except Exception as exc:
        with get_db() as conn:
            conn.execute("UPDATE certificates SET status='failed', error_message=? WHERE id=?", (str(exc), certificate_id))
            conn.execute("UPDATE jobs SET failed=failed+1 WHERE id=?", (job_id,))
    finally:
        with get_db() as conn:
            job = conn.execute("SELECT total, successful, failed FROM jobs WHERE id=?", (job_id,)).fetchone()
            if job and job["successful"] + job["failed"] >= job["total"]:
                conn.execute("UPDATE jobs SET status='completed', completed_at=? WHERE id=?", (utc_now(), job_id))


def start_job(job_id: str):
    with get_db() as conn:
        rows = conn.execute("SELECT id FROM certificates WHERE job_id=?", (job_id,)).fetchall()
        conn.execute("UPDATE jobs SET status='processing' WHERE id=?", (job_id,))
    for row in rows:
        executor.submit(process_one, job_id, row["id"])
