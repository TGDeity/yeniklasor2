import shutil
from pathlib import Path
import logging
import os
from app.core.config import Config

logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)

def upload_to_storage(file_path: str, video_id: str) -> dict:
    """Upload processed video to storage"""
    logger.info(f"Starting storage upload for video {video_id}")
    
    try:
        # Ensure input file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create storage directory structure
        video_storage_dir = STORAGE_DIR / video_id
        video_storage_dir.mkdir(exist_ok=True)
        
        # Copy file to storage
        source_path = Path(file_path)
        destination_path = video_storage_dir / source_path.name
        
        logger.info(f"Copying {source_path} to {destination_path}")
        shutil.copy2(source_path, destination_path)
        
        # Verify copy was successful
        if not destination_path.exists():
            raise RuntimeError("File copy failed")
        
        # Get file size
        file_size = destination_path.stat().st_size / (1024 * 1024)  # MB
        
        # Create metadata file
        metadata = {
            "video_id": video_id,
            "filename": source_path.name,
            "size_mb": round(file_size, 2),
            "storage_path": str(destination_path),
            "upload_timestamp": str(Path(file_path).stat().st_mtime)
        }
        
        metadata_path = video_storage_dir / "metadata.json"
        import json
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Storage upload completed for video {video_id}: {file_size:.2f} MB")
        
        return {
            "video_id": video_id,
            "filename": source_path.name,
            "size_mb": round(file_size, 2),
            "storage_url": f"/storage/{video_id}/{source_path.name}",
            "download_url": f"/api/v1/status/download/{video_id}",
            "status": "uploaded"
        }
        
    except Exception as e:
        logger.error(f"Storage upload failed for video {video_id}: {str(e)}")
        raise

def get_storage_info(video_id: str) -> dict:
    """Get storage information for a video"""
    try:
        video_storage_dir = STORAGE_DIR / video_id
        if not video_storage_dir.exists():
            return {"error": "Video not found in storage"}
        
        metadata_path = video_storage_dir / "metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path, "r") as f:
                return json.load(f)
        else:
            # Fallback: scan directory
            files = list(video_storage_dir.glob("*"))
            return {
                "video_id": video_id,
                "files": [f.name for f in files if f.is_file()],
                "status": "found"
            }
            
    except Exception as e:
        logger.error(f"Error getting storage info for video {video_id}: {str(e)}")
        return {"error": str(e)}

def cleanup_temp_files(video_id: str):
    """Clean up temporary files after successful storage"""
    try:
        uploads_dir = Path("uploads")
        patterns = [f"{video_id}_*", f"{video_id}.*"]
        for pattern in patterns:
            for file in uploads_dir.glob(pattern):
                if file.is_file():
                    file.unlink()
                    logger.info(f"Cleaned up upload file: {file}")

        outputs_dir = Path("outputs")
        for pattern in patterns:
            for file in outputs_dir.glob(pattern):
                if file.is_file():
                    file.unlink()
                    logger.info(f"Cleaned up output file: {file}")

        status_file = Path("status") / f"{video_id}.json"
        if status_file.exists():
            status_file.unlink()
            logger.info(f"Cleaned up status file: {status_file}")

    except Exception as e:
        logger.warning(f"Error during cleanup for video {video_id}: {str(e)}")

def cleanup_storage(video_id: str):
    """Clean up temporary files for a video"""
    try:
        # Clean up temporary files
        temp_dir = Path("temp") / video_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary files for video {video_id}")
            
        # Clean up output files
        output_dir = Path("outputs") / video_id
        if output_dir.exists():
            shutil.rmtree(output_dir)
            logger.info(f"Cleaned up output files for video {video_id}")
            
    except Exception as e:
        logger.error(f"Failed to clean up files for video {video_id}: {str(e)}")
        # Don't raise the exception as this is a cleanup task 