from app.core.celery_app import celery_app
from app.services.whisper_service import transcribe_with_openai_whisper, transcribe_with_faster_whisper, cleanup_model_cache
from app.services.translation_service import translate_subtitles, cleanup_translation_cache
from app.services.hardsub_service import burn_subtitles
from app.services.storage_service import upload_to_storage, cleanup_storage
from app.utils.logger import get_logger
from app.config import Config
from pathlib import Path
import json
import traceback
import time
from celery.exceptions import SoftTimeLimitExceeded
from app.core.status import update_status, Status
import os

logger = get_logger(__name__)

def cleanup_models():
    """Clean up old models from cache"""
    try:
        cleanup_model_cache()
        cleanup_translation_cache()
        logger.info("Model cache cleanup completed")
    except Exception as e:
        logger.warning(f"Model cache cleanup failed: {str(e)}")

@celery_app.task(name="app.tasks.process_video.process_video_task", bind=True, time_limit=3600, soft_time_limit=3000)  # 1 hour hard limit, 50 min soft limit
def process_video_task(self, video_id: str, video_path: str, target_language: str = "tr", model: str = "openai-whisper") -> dict:
    """Process video task that handles transcription, translation and subtitle burning"""
    try:
        # Log task start
        logger.info(f"Starting video processing for video_id: {video_id}, path: {video_path}, target language: {target_language}, model: {model}")
        update_status(video_id, Status.PROCESSING)
        
        # Check if video file exists
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            error_msg = f"Video file not found: {video_path}"
            logger.error(error_msg)
            update_status(video_id, Status.FAILED, {"error": error_msg})
            return {"status": "failed", "error": error_msg}
        
        # Check file size
        file_size = video_path.stat().st_size
        if file_size > Config.get_max_file_size():
            error_msg = f"File size {file_size / (1024*1024):.2f}MB exceeds limit {Config.get_max_file_size() / (1024*1024):.2f}MB"
            logger.error(error_msg)
            update_status(video_id, Status.FAILED, {"error": error_msg})
            return {"status": "failed", "error": error_msg}
        
        # Step 1: Transcribe video
        logger.info(f"Starting transcription for video {video_id} with model {model}")
        if model == "faster-whisper":
            srt_path = transcribe_with_faster_whisper(str(video_path), target_lang=target_language)
        else:
            srt_path = transcribe_with_openai_whisper(str(video_path), target_lang=target_language)
        logger.info(f"Transcription completed for video {video_id}: {srt_path}")
        
        # Step 2: Translate subtitles
        logger.info(f"Starting translation for video {video_id}")
        translated_srt = translate_subtitles(srt_path, target_language)
        logger.info(f"Translation completed for video {video_id}: {translated_srt}")
        
        # Step 3: Burn subtitles into video
        logger.info(f"Starting subtitle burning for video {video_id}")
        output_path = burn_subtitles(str(video_path), translated_srt, video_id)
        logger.info(f"Subtitle burning completed for video {video_id}: {output_path}")
        
        # Step 4: Upload to storage
        logger.info(f"Starting upload for video {video_id}")
        storage_info = upload_to_storage(output_path, video_id)
        logger.info(f"Upload completed for video {video_id}: {storage_info}")
        
        # Step 5: Cleanup
        logger.info(f"Starting cleanup for video {video_id}")
        try:
            if Config.AUTO_CLEANUP_TEMP_FILES:
                cleanup_storage(video_id)
                logger.info(f"Cleanup completed for video {video_id}")
            else:
                logger.info(f"Auto cleanup disabled, skipping cleanup for video {video_id}")
        except Exception as e:
            logger.warning(f"Cleanup warning for video {video_id}: {str(e)}")

        # Cleanup models periodically
        cleanup_models()

        # Success
        update_status(video_id, Status.COMPLETED, storage_info)
        return {
            "status": "success",
            "video_id": video_id,
            "storage_info": storage_info
        }

    except SoftTimeLimitExceeded:
        error_msg = f"Processing timeout exceeded (soft limit: {self.soft_time_limit}s)"
        logger.error(f"Timeout for video {video_id}: {error_msg}")
        update_status(video_id, Status.FAILED, {"error": error_msg})
        return {"status": "failed", "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error for video {video_id}: {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        update_status(video_id, Status.FAILED, {"error": error_msg})
        return {"status": "failed", "error": error_msg} 