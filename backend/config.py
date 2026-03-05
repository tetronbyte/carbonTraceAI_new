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
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "*")
    
    # Ollama Cloud API
    OLLAMA_API_KEY: str = os.environ.get("OLLAMA_API_KEY", "")
    OLLAMA_HOST: str = "https://ollama.com"
    VLM_MODEL: str = "kimi-k2.5:cloud"  # Vision Language Model for invoice parsing
    LLM_MODEL: str = "kimi-k2.5:cloud"  # LLM for text generation (using kimi instead of deepseek due to response issues)
    
    # File paths
    UPLOAD_DIR: str = str(ROOT_DIR / "uploads")
    REPORTS_DIR: str = str(ROOT_DIR / "generated_reports")
    TEMPLATES_DIR: str = str(ROOT_DIR / "templates")

settings = Settings()
