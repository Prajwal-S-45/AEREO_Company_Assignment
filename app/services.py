from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from . import config


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value).strip("_")
    return cleaned[:80] or "recipient"


def _draw_centered_fitted(c: canvas.Canvas, text: str, center_x: float, y: float,
                          font_name: str, max_size: float, min_size: float,
                          max_width: float) -> None:
    size = max_size
    while size > min_size and c.stringWidth(text, font_name, size) > max_width:
        size -= 1
    c.setFont(font_name, size)
    c.drawCentredString(center_x, y, text)


def generate_certificate(*, certificate_id: str, recipient_name: str, course_name: str, event_date: str) -> Path:
    """Generate one certificate from the application's single predefined design."""
    config.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    output = config.CERTIFICATES_DIR / f"{certificate_id}.pdf"
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(str(output), pagesize=(page_width, page_height))

    navy = colors.HexColor("#102a43")
    navy_light = colors.HexColor("#243b53")
    gold = colors.HexColor("#c99a3e")
    gold_light = colors.HexColor("#e8c878")
    cream = colors.HexColor("#fbf8f1")
    slate = colors.HexColor("#52606d")

    # Soft paper background with a layered navy-and-gold frame.
    c.setFillColor(cream)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    c.setStrokeColor(navy)
    c.setLineWidth(7)
    c.rect(25, 25, page_width - 50, page_height - 50, fill=0, stroke=1)
    c.setStrokeColor(gold)
    c.setLineWidth(2)
    c.rect(39, 39, page_width - 78, page_height - 78, fill=0, stroke=1)
    c.setStrokeColor(gold_light)
    c.setLineWidth(1)
    c.rect(47, 47, page_width - 94, page_height - 94, fill=0, stroke=1)

    # Decorative corner accents.
    for x, y, x_direction, y_direction in (
        (47, 47, 1, 1),
        (page_width - 47, 47, -1, 1),
        (47, page_height - 47, 1, -1),
        (page_width - 47, page_height - 47, -1, -1),
    ):
        c.setStrokeColor(gold)
        c.setLineWidth(2)
        c.line(x, y, x + 30 * x_direction, y)
        c.line(x, y, x, y + 30 * y_direction)

    center_x = page_width / 2
    c.setFillColor(gold)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(center_x, page_height - 91, "AEREO LEARNING")

    c.setFillColor(navy)
    _draw_centered_fitted(c, "CERTIFICATE OF COMPLETION", center_x, page_height - 132,
                          "Helvetica-Bold", 30, 22, page_width - 180)
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.line(center_x - 145, page_height - 148, center_x + 145, page_height - 148)

    c.setFillColor(slate)
    c.setFont("Helvetica", 14)
    c.drawCentredString(center_x, page_height - 184, "This certificate is proudly presented to")
    c.setFillColor(navy)
    _draw_centered_fitted(c, recipient_name, center_x, page_height - 230,
                          "Helvetica-Bold", 29, 18, page_width - 190)

    c.setFillColor(gold)
    c.setLineWidth(2)
    c.line(center_x - 120, page_height - 246, center_x + 120, page_height - 246)
    c.setFillColor(slate)
    c.setFont("Helvetica", 14)
    c.drawCentredString(center_x, page_height - 278, "for successfully completing")
    c.setFillColor(navy_light)
    _draw_centered_fitted(c, course_name, center_x, page_height - 319,
                          "Helvetica-Bold", 21, 14, page_width - 220)

    # Centered seal adds a visual focal point without introducing external assets.
    seal_y = 107
    c.setFillColor(navy)
    c.circle(center_x, seal_y, 28, fill=1, stroke=0)
    c.setStrokeColor(gold_light)
    c.setLineWidth(2)
    c.circle(center_x, seal_y, 22, fill=0, stroke=1)
    c.setFillColor(gold_light)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(center_x, seal_y - 5, "A")

    c.setFillColor(slate)
    c.setFont("Helvetica", 10)
    c.drawCentredString(112, 84, f"EVENT DATE  |  {event_date}")
    c.drawCentredString(page_width - 112, 84, f"CERTIFICATE ID  |  {certificate_id}")
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.line(65, 72, 160, 72)
    c.line(page_width - 160, 72, page_width - 65, 72)

    c.showPage()
    c.save()
    return output
