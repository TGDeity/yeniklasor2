import enum
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import Config

logger = logging.getLogger(__name__)

class Status(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def update_status(video_id: str, status: Status, details: Optional[Dict[str, Any]] = None) -> None:
    """Update the status of a video processing task"""
    try:
        status_file = Config.STATUS_DIR / f"{video_id}.json"
        status_data = {
            "video_id": video_id,
            "status": status.value
        }
        if details:
            status_data.update(details)
            
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
            
        logger.info(f"Video {video_id} status updated to {status.value}")
        if details:
            logger.info(f"Details: {details}")
    except Exception as e:
        logger.error(f"Failed to update status for video {video_id}: {str(e)}") 