from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CERTIFICATES_DIR = STORAGE_DIR / "certificates"
DB_PATH = STORAGE_DIR / "certificates.db"
TEMPLATE_PATH = BASE_DIR / "app" / "templates" / "certificate_template.html"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
