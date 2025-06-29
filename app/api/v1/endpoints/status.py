from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json
import psutil
import os
import subprocess
import redis
from app.core.celery_app import celery_app
from app.services.storage_service import get_storage_info, cleanup_temp_files
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

STATUS_DIR = Path("status")
STATUS_DIR.mkdir(exist_ok=True)

def _get_gpu_info():
    """Get GPU information using nvidia-smi if available."""
    try:
        # Check if nvidia-smi is in PATH
        subprocess.check_output("which nvidia-smi", shell=True)
        
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            name, mem_total, mem_used, util, temp = line.split(', ')
            gpus.append({
                "name": name.strip(),
                "memory_total_mb": int(mem_total),
                "memory_used_mb": int(mem_used),
                "utilization_percent": int(util),
                "temperature_celsius": int(temp)
            })
        return {"available": True, "gpus": gpus}
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # nvidia-smi not found or failed to run
        return {"available": False, "error": "nvidia-smi not found or failed"}
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching GPU info: {e}")
        return {"available": False, "error": str(e)}

@router.get("/{video_id}")
def check_status(video_id: str):
    """
    # /api/v1/status/{video_id} [GET]
    # Kullanım amacı: Belirli bir video işinin durumunu (işleniyor, tamamlandı, hata) sorgulamak için kullanılır.
    
    Bir videonun işlenme durumunu sorgula.
    
    - **Amaç:** Belirli bir video_id için işleme durumunu (processing, completed, failed) ve ilerlemeyi döner.
    - **Parametreler:**
        - **video_id**: Video işinin UUID'si (path parametresi)
    - **Yanıt:**
        - video_id: Sorgulanan video id
        - status: İşleme durumu
        - progress: Yüzde ilerleme (opsiyonel)
        - error: Hata mesajı (opsiyonel)
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/550e8400-e29b-41d4-a716-446655440000"
    - **Örnek Yanıt:**
        {
          "video_id": "550e8400-e29b-41d4-a716-446655440000",
          "status": "processing",
          "progress": 40
        }
    - **Hata Kodları:**
        - 404: Video bulunamadı
        - 500: Sunucu hatası
    """
    try:
        status_file = STATUS_DIR / f"{video_id}.json"
        if not status_file.exists():
            return {"video_id": video_id, "status": "not_found", "message": "Video ID not found"}
        
        with open(status_file, "r") as f:
            status = json.load(f)
            
        logger.info(f"Status check for video {video_id}: {status.get('status', 'unknown')}")
        return status
        
    except Exception as e:
        logger.error(f"Error checking status for video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking video status")

@router.get("/download/{video_id}")
def download_video(video_id: str):
    """
    # /api/v1/status/download/{video_id} [GET]
    # Kullanım amacı: İşlenmiş videoyu indirmek için kullanılır.
    
    İşlenmiş videoyu indir.
    
    - **Amaç:** Belirli bir video_id için işlenmiş video dosyasını (mp4) döner.
    - **Parametreler:**
        - **video_id**: Video işinin UUID'si (path parametresi)
    - **Yanıt:**
        - Başarılı: video/mp4 dosyası
        - Hata: JSON hata mesajı
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/download/550e8400-e29b-41d4-a716-446655440000" -o "output.mp4"
    - **Hata Kodları:**
        - 404: Video bulunamadı
        - 500: Sunucu hatası
    """
    try:
        # Get storage info
        storage_info = get_storage_info(video_id)
        
        if "error" in storage_info:
            raise HTTPException(status_code=404, detail=storage_info["error"])
        
        # Find the video file
        storage_dir = Path("storage") / video_id
        video_files = list(storage_dir.glob("*.mp4"))
        
        if not video_files:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        video_file = video_files[0]  # Get the first MP4 file
        
        logger.info(f"Downloading video {video_id}: {video_file}")
        
        return FileResponse(
            path=str(video_file),
            filename=video_file.name,
            media_type="video/mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading video")

@router.get("/system/resources")
def system_resources():
    """
    # /api/v1/status/system/resources [GET]
    # Kullanım amacı: Sunucunun anlık CPU, RAM, disk ve GPU kaynak kullanımını öğrenmek için kullanılır.
    
    Sistem kaynaklarını (CPU, RAM, Disk, GPU) döner.
    
    - **Amaç:** Sunucunun anlık kaynak kullanımını ve GPU durumunu döner.
    - **Yanıt:**
        - cpu_percent, memory_percent, disk_percent, gpu, vb.
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/system/resources"
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_cores": psutil.cpu_count(),
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "gpu": _get_gpu_info(),
        }
    except Exception as e:
        logger.error(f"Error getting system resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting system resources")

@router.get("/system/health")
def system_health():
    """
    # /api/v1/status/system/health [GET]
    # Kullanım amacı: API, Celery worker ve Redis servislerinin sağlık durumunu topluca görmek için kullanılır.
    
    API, Celery worker ve Redis servislerinin sağlık durumunu döner.
    
    - **Amaç:** Tüm altyapı servislerinin sağlık durumunu topluca gösterir.
    - **Yanıt:**
        - overall_status, services (api, celery, redis)
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/system/health"
    """
    # Check Celery worker status with a ping
    celery_status = {"status": "unhealthy", "details": "Could not connect to workers"}
    try:
        ping_response = celery_app.control.ping(timeout=3.0)
        if ping_response:
            # Check if any worker replied
            active_workers = [worker for worker_info in ping_response for worker, info in worker_info.items() if info.get('ok') == 'pong']
            if active_workers:
                celery_status = {"status": "healthy", "workers": active_workers}
            else:
                celery_status = {"status": "unhealthy", "details": "No workers replied to ping"}
        else:
            celery_status = {"status": "unhealthy", "details": "Ping returned empty response"}
    except Exception as e:
        logger.warning(f"Could not get Celery status via ping: {str(e)}")
        # The exception itself means workers are unreachable
        celery_status["details"] = str(e)
        
    # Check Redis connection
    redis_status = {"status": "unhealthy"}
    try:
        # Use the broker URL from Celery config for a direct check
        r = redis.Redis.from_url(celery_app.conf.broker_url, socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        redis_status = {"status": "healthy"}
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {str(e)}")
        redis_status['details'] = str(e)
        
    overall_status = "healthy" if redis_status["status"] == "healthy" and celery_status["status"] == "healthy" else "degraded"

    return {
        "overall_status": overall_status,
        "services": {
            "api": {"status": "healthy"}, # If this endpoint works, API is healthy
            "celery": celery_status,
            "redis": redis_status
        }
    }

@router.get("/tasks/active")
def get_active_tasks():
    """
    # /api/v1/status/tasks/active [GET]
    # Kullanım amacı: Şu anda çalışan (aktif) arka plan görevlerini listelemek için kullanılır.
    
    Aktif (devam eden) arka plan görevlerini listeler.
    
    - **Amaç:** Şu anda çalışan Celery görevlerini listeler.
    - **Yanıt:**
        - active_tasks: Görev listesi
        - count: Görev sayısı
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/tasks/active"
    """
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {"active_tasks": [], "count": 0}
        
        # Flatten active tasks from all workers
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                task_info = {
                    "task_id": task.get("id"),
                    "name": task.get("name"),
                    "worker": worker,
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {}),
                    "time_start": task.get("time_start")
                }
                all_tasks.append(task_info)
        
        return {"active_tasks": all_tasks, "count": len(all_tasks)}
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting active tasks")

@router.delete("/tasks/{task_id}")
def cancel_task(task_id: str):
    """
    # /api/v1/status/tasks/{task_id} [DELETE]
    # Kullanım amacı: Belirli bir arka plan görevini iptal etmek için kullanılır.
    
    Belirli bir arka plan görevini iptal et.
    
    - **Amaç:** Celery'de çalışan bir görevi sonlandırır.
    - **Parametreler:**
        - **task_id**: Celery task id (path parametresi)
    - **Yanıt:**
        - message: Sonuç mesajı
    - **Örnek İstek:**
        curl -X DELETE "http://localhost:8082/api/v1/status/tasks/123"
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Task {task_id} cancelled")
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error cancelling task")

@router.get("/videos")
def list_videos():
    """
    # /api/v1/status/videos [GET]
    # Kullanım amacı: Sistemdeki tüm video işlerinin özetini ve durumunu listelemek için kullanılır.
    
    Tüm video işlerinin durum dosyalarını listeler.
    
    - **Amaç:** Sistemdeki tüm video işlerinin özetini döner.
    - **Yanıt:**
        - videos: Video işlerinin listesi
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/videos"
    """
    try:
        videos = []
        for file in STATUS_DIR.glob("*.json"):
            try:
                with open(file, "r") as f:
                    status = json.load(f)
                status['file'] = file.name
                status['modified'] = file.stat().st_mtime
                # Optionally format modified date
                import datetime
                status['modified'] = datetime.datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                videos.append(status)
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
        # Sort by modified date descending
        videos.sort(key=lambda x: x.get('modified', ''), reverse=True)
        return {"videos": videos}
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail="Error listing videos")

@router.get("/system/storage")
def system_storage_info():
    """
    # /api/v1/status/system/storage [GET]
    # Kullanım amacı: uploads, outputs, storage ve logs klasörlerinin boyut ve dosya sayısını öğrenmek için kullanılır.
    
    Depolama klasörlerinin (uploads, outputs, storage, logs) boyut ve dosya sayısını döner.
    
    - **Amaç:** Sunucudaki ana klasörlerin doluluk ve dosya sayısı bilgisini verir.
    - **Yanıt:**
        - uploads, outputs, storage, logs
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/system/storage"
    """
    directories = ["uploads", "outputs", "storage", "logs"]
    storage_info = {}
    for dir_name in directories:
        dir_path = Path(dir_name)
        if dir_path.exists():
            total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            file_count = len(list(dir_path.rglob('*')))
            storage_info[dir_name] = {
                "size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "exists": True
            }
        else:
            storage_info[dir_name] = {
                "size_mb": 0,
                "file_count": 0,
                "exists": False
            }
    return storage_info

@router.get("/system/performance")
def system_performance_metrics():
    """
    # /api/v1/status/system/performance [GET]
    # Kullanım amacı: Son 100 log satırından upload, işleme, hata ve başarı sayısını öğrenmek için kullanılır.
    
    Son 100 log satırından performans metriklerini döner.
    
    - **Amaç:** Son işlemlerden upload, işleme, hata ve başarı sayısını verir.
    - **Yanıt:**
        - upload_count, processing_count, error_count, success_count, total_operations
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/status/system/performance"
    """
    log_dir = Path("logs")
    log_files = sorted(log_dir.glob("app_*.log"), reverse=True)
    if not log_files:
        return {"error": "Log file not found"}
    log_file = log_files[0]
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        recent_lines = lines[-100:]
        metrics = {
            "upload_count": len([l for l in recent_lines if "upload" in l.lower()]),
            "processing_count": len([l for l in recent_lines if "processing" in l.lower()]),
            "error_count": len([l for l in recent_lines if "error" in l.lower()]),
            "success_count": len([l for l in recent_lines if "completed" in l.lower()]),
            "total_operations": len(recent_lines)
        }
        return metrics
    except Exception as e:
        return {"error": str(e)}

@router.post("/system/cleanup", summary="Tüm videolar için manuel temizlik başlat", response_description="Temizlik sonucu")
def system_cleanup():
    """
    # /api/v1/status/system/cleanup [POST]
    # Kullanım amacı: uploads ve outputs klasörlerindeki tüm video dosyalarını ve geçici dosyaları topluca temizlemek için kullanılır.
    
    Uploads ve outputs klasörlerindeki tüm video dosyalarını ve ilgili geçici dosyaları temizler.
    
    - **Amaç:** Sunucuda biriken geçici ve çıktı dosyalarını topluca temizler.
    - **Yanıt:**
        - message: Temizlik özeti
        - cleaned: Temizlenen video_id listesi
        - failed: Temizlenemeyen video_id ve hata açıklamaları
    - **Örnek İstek:**
        curl -X POST "http://localhost:8082/api/v1/status/system/cleanup"
    """
    video_ids = set()
    # uploads klasöründen video_id'leri topla
    uploads_dir = Path("uploads")
    for file in uploads_dir.iterdir():
        if file.is_file():
            name = file.stem
            # UUID formatında olanları al
            if len(name) >= 32:
                video_ids.add(name.split('_')[0])
    # outputs klasöründen video_id'leri topla
    outputs_dir = Path("outputs")
    for file in outputs_dir.iterdir():
        if file.is_file():
            name = file.stem
            if len(name) >= 32:
                video_ids.add(name.split('_')[0])
    cleaned = []
    failed = []
    for vid in video_ids:
        try:
            cleanup_temp_files(vid)
            cleaned.append(vid)
        except Exception as e:
            failed.append({"video_id": vid, "error": str(e)})
    return {"message": f"Cleanup completed for {len(cleaned)} videos.", "cleaned": cleaned, "failed": failed} 