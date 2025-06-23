#!/usr/bin/env python3
"""
Debug script for video processing issues
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_system_resources():
    """Check system resources"""
    logger.info("=== System Resources ===")
    
    # CPU
    try:
        cpu_count = os.cpu_count()
        logger.info(f"CPU cores: {cpu_count}")
    except:
        logger.warning("Could not get CPU info")
    
    # Memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        logger.info(f"Memory: {memory.total / (1024**3):.2f} GB total, {memory.available / (1024**3):.2f} GB available")
    except:
        logger.warning("Could not get memory info")
    
    # Disk
    try:
        disk = psutil.disk_usage('/')
        logger.info(f"Disk: {disk.free / (1024**3):.2f} GB free out of {disk.total / (1024**3):.2f} GB")
    except:
        logger.warning("Could not get disk info")

def check_gpu():
    """Check GPU availability"""
    logger.info("=== GPU Check ===")
    
    # Check CUDA environment
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    logger.info(f"CUDA_VISIBLE_DEVICES: {cuda_visible}")
    
    # Check if nvidia-smi is available
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("nvidia-smi available")
            # Extract GPU info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'NVIDIA-SMI' in line or 'Driver Version' in line:
                    logger.info(line.strip())
        else:
            logger.warning("nvidia-smi not available or failed")
    except Exception as e:
        logger.warning(f"Could not run nvidia-smi: {e}")

def check_docker_services():
    """Check Docker services status"""
    logger.info("=== Docker Services ===")
    
    try:
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Docker services status:")
            logger.info(result.stdout)
        else:
            logger.error("Failed to get Docker services status")
    except Exception as e:
        logger.error(f"Could not check Docker services: {e}")

def check_celery_workers():
    """Check Celery workers"""
    logger.info("=== Celery Workers ===")
    
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "worker", 
            "celery", "-A", "app.core.celery_app.celery_app", "inspect", "ping"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("Celery workers are responding")
            logger.info(result.stdout)
        else:
            logger.error("Celery workers not responding")
            logger.error(result.stderr)
    except Exception as e:
        logger.error(f"Could not check Celery workers: {e}")

def check_redis():
    """Check Redis connection"""
    logger.info("=== Redis Check ===")
    
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "redis", 
            "redis-cli", "ping"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "PONG" in result.stdout:
            logger.info("Redis is responding")
        else:
            logger.error("Redis not responding")
    except Exception as e:
        logger.error(f"Could not check Redis: {e}")

def check_logs():
    """Check recent logs"""
    logger.info("=== Recent Logs ===")
    
    log_files = [
        "logs/app_*.log",
        "logs/celery_*.log"
    ]
    
    for pattern in log_files:
        for log_file in Path(".").glob(pattern):
            if log_file.exists():
                logger.info(f"Recent logs from {log_file}:")
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-10:]:  # Last 10 lines
                            logger.info(line.strip())
                except Exception as e:
                    logger.error(f"Could not read {log_file}: {e}")

def check_video_files():
    """Check uploaded video files"""
    logger.info("=== Video Files ===")
    
    upload_dir = Path("uploads")
    if upload_dir.exists():
        files = list(upload_dir.glob("*"))
        logger.info(f"Found {len(files)} files in uploads directory")
        for file in files:
            size_mb = file.stat().st_size / (1024 * 1024)
            logger.info(f"  {file.name}: {size_mb:.2f} MB")
    else:
        logger.warning("Uploads directory does not exist")

def check_status_files():
    """Check status files"""
    logger.info("=== Status Files ===")
    
    status_dir = Path("status")
    if status_dir.exists():
        files = list(status_dir.glob("*.json"))
        logger.info(f"Found {len(files)} status files")
        for file in files:
            try:
                with open(file, 'r') as f:
                    status = json.load(f)
                    logger.info(f"  {file.stem}: {status.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Could not read {file}: {e}")
    else:
        logger.warning("Status directory does not exist")

def main():
    """Run all checks"""
    logger.info("Starting video processing debug check...")
    
    check_system_resources()
    check_gpu()
    check_docker_services()
    check_redis()
    check_celery_workers()
    check_video_files()
    check_status_files()
    check_logs()
    
    logger.info("Debug check completed!")

if __name__ == "__main__":
    main() 