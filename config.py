import os

ADMISSION_URL = "https://www.nit.ac.in/admission/index.php"
BASE_DOMAIN = "www.nit.ac.in"

DOWNLOAD_DIR = "downloads"
PDF_DIR = os.path.join(DOWNLOAD_DIR, "pdfs")
RAW_DIR = os.path.join(DOWNLOAD_DIR, "raw")
UNSTRUCTURED_DATA_JSON = "unstructured_admission_data.json"
AUDIT_LOG_JSON = "query_audit_log.json"

# Dense neural embedding threshold
DEFAULT_CONFIDENCE_THRESHOLD = 0.58

# Google Gemini API Settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
