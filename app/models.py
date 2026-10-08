from dataclasses import dataclass
from typing import Optional

@dataclass
class Recipient:
    name: str
    email: Optional[str]

@dataclass
class CertificateRequest:
    course_name: str
    event_date: str
    recipients: list[Recipient]
