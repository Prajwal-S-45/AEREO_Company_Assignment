import time


def wait_for_completion(client, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/v1/generation-jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            return data
        time.sleep(0.05)
    raise AssertionError("Job did not complete in time")


def test_create_generation_job(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Python Backend Engineering",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Alice Johnson", "email": "alice@example.com"}, {"name": "Bob Smith"}],
    })
    assert response.status_code == 202
    body = response.json()
    assert body["total"] == 2
    assert body["status"] == "queued"


def test_input_validation(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "X",
        "event_date": "not-a-date",
        "recipients": [{"name": "1", "email": "bad-email"}],
    })
    assert response.status_code == 422


def test_certificate_generation_and_retrieval(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "FastAPI Workshop",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Jane Doe", "email": "jane@example.com"}],
    })
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["successful"] == 1
    assert job["failed"] == 0
    cert = job["certificates"][0]
    download = client.get(cert["download_url"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")


def test_job_status_and_progress(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Testing",
        "event_date": "2026-10-08",
        "recipients": [{"name": "One Person"}, {"name": "Two Person"}],
    })
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["progress_percent"] == 100.0
    assert job["successful"] == 2
    assert len(job["certificates"]) == 2


def test_individual_failure_does_not_stop_other_certificates(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Resilience Testing",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Good Person"}, {"name": "[FAIL]"}, {"name": "Another Person"}],
    })
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["successful"] == 2
    assert job["failed"] == 1
    failed = [c for c in job["certificates"] if c["status"] == "failed"][0]
    assert "Simulated certificate generation failure" in failed["error"]


def test_retrieve_job_certificates(client):
    response = client.post("/api/v1/generation-jobs", json={
        "course_name": "Certificate API",
        "event_date": "2026-10-08",
        "recipients": [{"name": "Recipient One"}],
    })
    job_id = response.json()["job_id"]
    wait_for_completion(client, job_id)
    response = client.get(f"/api/v1/generation-jobs/{job_id}/certificates")
    assert response.status_code == 200
    assert len(response.json()) == 1
