import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger
import sys

# Workspace Root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    SQLITE_DB_PATH: str = "data/resume_intelligence.db"
    CHROMA_DB_PATH: str = "data/chroma"
    LOG_LEVEL: str = "INFO"

    # Settings config to read from .env file
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure absolute paths
sqlite_db_abs = ROOT_DIR / settings.SQLITE_DB_PATH
chroma_db_abs = ROOT_DIR / settings.CHROMA_DB_PATH
runtime_dir_abs = ROOT_DIR / "runtime"
data_dir_abs = ROOT_DIR / "data"

# Create directories
data_dir_abs.mkdir(parents=True, exist_ok=True)
sqlite_db_abs.parent.mkdir(parents=True, exist_ok=True)
chroma_db_abs.mkdir(parents=True, exist_ok=True)
runtime_dir_abs.mkdir(parents=True, exist_ok=True)

# Configure Loguru Logging
logger.remove()  # Remove default handler

# Custom log formatter to display stage clearly if bound
def custom_formatter(record):
    stage = record["extra"].get("stage", "SYSTEM")
    record["extra"]["stage_upper"] = f"[{stage.upper()}]"
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[stage_upper]: <10}</cyan> | "
        "<level>{message}</level>\n"
    )

logger.add(
    sys.stderr,
    format=custom_formatter,
    level=settings.LOG_LEVEL,
    colorize=True
)

logger.add(
    str(runtime_dir_abs / "app.log"),
    format=custom_formatter,
    level="DEBUG",
    rotation="10 MB",
    retention="10 days"
)

# Set Tesseract command path if defined and exists (on Windows)
if settings.TESSERACT_CMD:
    import pytesseract
    # Try setting if it exists, otherwise log warning
    if os.path.exists(settings.TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    else:
        logger.bind(stage="SYSTEM").warning(
            f"Tesseract executable not found at specified path: {settings.TESSERACT_CMD}. "
            "OCR may fail if tesseract is not in the system PATH."
        )

logger.bind(stage="SYSTEM").info("Configuration initialized successfully.")
