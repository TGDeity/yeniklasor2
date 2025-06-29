import os
from pathlib import Path

class Config:
    # Storage settings
    STORAGE_PATH = os.getenv("STORAGE_PATH", "storage")
    
    # Model settings
    MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "model_cache")
    ENABLE_MODEL_CACHING = os.getenv("ENABLE_MODEL_CACHING", "true").lower() == "true"
    MODEL_CACHE_TTL = int(os.getenv("MODEL_CACHE_TTL", "1800"))  # 30 minutes
    
    # Celery settings
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8082"))
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUTS_DIR = BASE_DIR / "outputs"
    STATUS_DIR = BASE_DIR / "status"
    STORAGE_DIR = BASE_DIR / STORAGE_PATH
    
    # Create directories if they don't exist
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    # File size limits
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(500 * 1024 * 1024)))  # 500MB 