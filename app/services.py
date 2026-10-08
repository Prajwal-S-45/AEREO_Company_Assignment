import html
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from . import config


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value).strip("_")
    return cleaned[:80] or "recipient"


def generate_certificate(*, certificate_id: str, recipient_name: str, course_name: str, event_date: str) -> Path:
    """Generate one certificate from the application's single predefined design."""
    config.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    output = config.CERTIFICATES_DIR / f"{certificate_id}.pdf"
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(str(output), pagesize=(page_width, page_height))

    # Decorative border and certificate content form the predefined template.
    c.setStrokeColor(colors.HexColor("#1f2937"))
    c.setLineWidth(3)
    c.rect(28, 28, page_width - 56, page_height - 56)
    c.setStrokeColor(colors.HexColor("#b08d57"))
    c.setLineWidth(1)
    c.rect(40, 40, page_width - 80, page_height - 80)

    c.setFillColor(colors.HexColor("#1f2937"))
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(page_width / 2, page_height - 115, "CERTIFICATE OF COMPLETION")

    c.setFillColor(colors.HexColor("#4b5563"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_width / 2, page_height - 155, "This certificate is proudly presented to")

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 27)
    c.drawCentredString(page_width / 2, page_height - 205, recipient_name)

    c.setFillColor(colors.HexColor("#4b5563"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_width / 2, page_height - 245, "for successfully completing")

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 21)
    c.drawCentredString(page_width / 2, page_height - 285, course_name)

    c.setFillColor(colors.HexColor("#4b5563"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(page_width / 2, 92, f"Event date: {event_date}")
    c.drawCentredString(page_width / 2, 72, f"Certificate ID: {certificate_id}")

    c.setStrokeColor(colors.HexColor("#6b7280"))
    c.line(page_width / 2 - 85, 120, page_width / 2 + 85, 120)
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_width / 2, 105, "Authorized Signature")

    c.showPage()
    c.save()
    return output
