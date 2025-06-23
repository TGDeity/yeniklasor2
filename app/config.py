import os
import json
from typing import Dict, Any
from pathlib import Path

RUNTIME_CONFIG_PATH = Path(__file__).parent / "config_runtime.json"

class Config:
    """System configuration for video processing"""
    
    # Timeout settings (in seconds)
    FFMPEG_TIMEOUT = int(os.getenv("FFMPEG_TIMEOUT", 1800))  # 30 minutes default
    WHISPER_TIMEOUT = int(os.getenv("WHISPER_TIMEOUT", 600))  # 10 minutes default
    TRANSLATION_TIMEOUT = int(os.getenv("TRANSLATION_TIMEOUT", 300))  # 5 minutes default
    UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", 120))  # 2 minutes default
    
    # Resource limits
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", 2))
    GPU_MEMORY_LIMIT = int(os.getenv("GPU_MEMORY_LIMIT", 8 * 1024 * 1024 * 1024))  # 8GB
    
    # Performance settings
    ENABLE_GPU_ACCELERATION = os.getenv("ENABLE_GPU_ACCELERATION", "true").lower() == "true"
    ENABLE_MODEL_CACHING = os.getenv("ENABLE_MODEL_CACHING", "true").lower() == "true"
    ENABLE_BATCH_PROCESSING = os.getenv("ENABLE_BATCH_PROCESSING", "true").lower() == "true"
    
    # Cleanup settings
    AUTO_CLEANUP_TEMP_FILES = os.getenv("AUTO_CLEANUP_TEMP_FILES", "true").lower() == "true"
    CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", 3600))  # 1 hour
    MAX_STORAGE_AGE = int(os.getenv("MAX_STORAGE_AGE", 7 * 24 * 3600))  # 7 days
    
    @staticmethod
    def get_runtime_config() -> dict:
        if RUNTIME_CONFIG_PATH.exists():
            with open(RUNTIME_CONFIG_PATH, "r") as f:
                return json.load(f)
        return {"max_file_size_mb": 500}

    @staticmethod
    def set_runtime_config(data: dict):
        with open(RUNTIME_CONFIG_PATH, "w") as f:
            json.dump(data, f)

    @classmethod
    def get_max_file_size(cls) -> int:
        cfg = cls.get_runtime_config()
        return int(cfg.get("max_file_size_mb", 500)) * 1024 * 1024

    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings"""
        settings = {
            "timeouts": {
                "ffmpeg": cls.FFMPEG_TIMEOUT,
                "whisper": cls.WHISPER_TIMEOUT,
                "translation": cls.TRANSLATION_TIMEOUT,
                "upload": cls.UPLOAD_TIMEOUT
            },
            "resources": {
                "max_file_size_mb": cls.get_runtime_config().get("max_file_size_mb", 500),
                "max_concurrent_tasks": cls.MAX_CONCURRENT_TASKS,
                "gpu_memory_limit_gb": cls.GPU_MEMORY_LIMIT // (1024 * 1024 * 1024)
            },
            "performance": {
                "enable_gpu_acceleration": cls.ENABLE_GPU_ACCELERATION,
                "enable_model_caching": cls.ENABLE_MODEL_CACHING,
                "enable_batch_processing": cls.ENABLE_BATCH_PROCESSING
            },
            "cleanup": {
                "auto_cleanup_temp_files": cls.AUTO_CLEANUP_TEMP_FILES,
                "cleanup_interval_seconds": cls.CLEANUP_INTERVAL,
                "max_storage_age_days": cls.MAX_STORAGE_AGE // (24 * 3600)
            }
        }
        return settings
    
    @staticmethod
    def str_to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        return str(value).strip().lower() in ("true", "1", "yes", "on")

    @classmethod
    def update_setting(cls, setting_path: str, value: Any) -> bool:
        """Update a configuration setting"""
        try:
            # Parse setting path (e.g., "timeouts.ffmpeg")
            parts = setting_path.split(".")
            if len(parts) != 2:
                return False
            category, setting = parts
            if category == "timeouts":
                if setting == "ffmpeg":
                    cls.FFMPEG_TIMEOUT = int(value)
                elif setting == "whisper":
                    cls.WHISPER_TIMEOUT = int(value)
                elif setting == "translation":
                    cls.TRANSLATION_TIMEOUT = int(value)
                elif setting == "upload":
                    cls.UPLOAD_TIMEOUT = int(value)
            elif category == "resources":
                if setting == "max_file_size_mb":
                    cfg = cls.get_runtime_config()
                    cfg["max_file_size_mb"] = int(value)
                    cls.set_runtime_config(cfg)
                    return True
                elif setting == "max_concurrent_tasks":
                    cls.MAX_CONCURRENT_TASKS = int(value)
                elif setting == "gpu_memory_limit_gb":
                    cls.GPU_MEMORY_LIMIT = int(value) * 1024 * 1024 * 1024
            elif category == "performance":
                if setting == "enable_gpu_acceleration":
                    cls.ENABLE_GPU_ACCELERATION = cls.str_to_bool(value)
                elif setting == "enable_model_caching":
                    cls.ENABLE_MODEL_CACHING = cls.str_to_bool(value)
                elif setting == "enable_batch_processing":
                    cls.ENABLE_BATCH_PROCESSING = cls.str_to_bool(value)
            elif category == "cleanup":
                if setting == "auto_cleanup_temp_files":
                    cls.AUTO_CLEANUP_TEMP_FILES = cls.str_to_bool(value)
                elif setting == "cleanup_interval_seconds":
                    cls.CLEANUP_INTERVAL = int(value)
                elif setting == "max_storage_age_days":
                    cls.MAX_STORAGE_AGE = int(value) * 24 * 3600
            return True
        except (ValueError, TypeError):
            return False 