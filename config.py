import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# App configurations
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEFAULT_CSV_PATH = os.environ.get("DEFAULT_CSV_PATH", str(BASE_DIR / "data" / "scores.csv"))

# Directory config
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
UPLOADS_DIR = BASE_DIR / "uploads"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Flask Configuration
FLASK_HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

def validate_config():
    """Simple validator to ensure essential settings are active."""
    errors = []
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is not set in your .env file or environment.")
    return len(errors) == 0, errors
