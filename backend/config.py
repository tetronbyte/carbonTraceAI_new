import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    MONGO_URL: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.environ.get("DB_NAME", "carbontraceai")
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "carbontraceai-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "*")
    EMERGENT_LLM_KEY: str = os.environ.get("EMERGENT_LLM_KEY", "")
    UPLOAD_DIR: str = str(ROOT_DIR / "uploads")
    REPORTS_DIR: str = str(ROOT_DIR / "generated_reports")
    TEMPLATES_DIR: str = str(ROOT_DIR / "templates")

settings = Settings()
