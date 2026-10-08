from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RecipientInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not any(ch.isalpha() for ch in value):
            raise ValueError("name must contain alphabetic characters")
        return value

class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    course_name: str = Field(..., min_length=2, max_length=200)
    event_date: date
    recipients: list[RecipientInput] = Field(..., min_length=1, max_length=10000)

    @field_validator("course_name")
    @classmethod
    def validate_course_name(cls, value: str) -> str:
        return " ".join(value.split())

class JobCreatedResponse(BaseModel):
    job_id: str
    status: str
    total: int

class CertificateResult(BaseModel):
    id: str
    recipient_name: str
    recipient_email: str | None
    status: str
    download_url: str | None = None
    error: str | None = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total: int
    successful: int
    failed: int
    progress_percent: float
    certificates: list[CertificateResult]
