from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import requests
import os
from datetime import datetime
from config import Config
from monitoring import ResourceMonitor
from app.services.storage_service import cleanup_temp_files

app = FastAPI(title="Video Processing Admin Panel")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8082/api/v1")

# Initialize monitoring
monitor = ResourceMonitor()

def get_api_data(endpoint: str):
    """Get data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def get_video_statuses():
    """Get video processing statuses"""
    try:
        status_dir = Path("../status")
        if not status_dir.exists():
            return []
        
        statuses = []
        for file in status_dir.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    status = json.load(f)
                    status['file'] = file.name
                    status['modified'] = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    statuses.append(status)
            except Exception as e:
                print(f"Error reading {file}: {e}")
        
        return sorted(statuses, key=lambda x: x.get('modified', ''), reverse=True)
    except Exception as e:
        print(f"Error getting statuses: {e}")
        return []

@app.get("/", response_class=HTMLResponse)
async def admin_home(request: Request):
    """Admin panel home page"""
    try:
        # Get system health
        health_data = get_api_data("status/system/health")
        
        # Get video statuses
        video_statuses = get_video_statuses()
        
        # Get active tasks
        active_tasks = get_api_data("status/tasks/active")
        
        # Get supported languages
        languages = get_api_data("upload/languages")
        
        # Get system resources
        system_resources = monitor.get_system_resources()
        
        # Get service status
        service_status = monitor.get_service_status()
        
        # Get storage info
        storage_info = monitor.get_storage_info()
        
        # Get performance metrics
        performance_metrics = monitor.get_performance_metrics()
        
        # Get configuration
        config_settings = Config.get_all_settings()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "health": health_data,
            "videos": video_statuses,
            "active_tasks": active_tasks,
            "languages": languages,
            "system_resources": system_resources,
            "service_status": service_status,
            "storage_info": storage_info,
            "performance_metrics": performance_metrics,
            "config_settings": config_settings,
            "api_url": API_BASE_URL
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": str(e),
            "health": {"error": "Failed to load"},
            "videos": [],
            "active_tasks": {"error": "Failed to load"},
            "languages": {"error": "Failed to load"},
            "system_resources": {"error": "Failed to load"},
            "service_status": {"error": "Failed to load"},
            "storage_info": {"error": "Failed to load"},
            "performance_metrics": {"error": "Failed to load"},
            "config_settings": {"error": "Failed to load"},
            "api_url": API_BASE_URL
        })

@app.get("/api/health")
async def api_health():
    """API health check"""
    return get_api_data("status/system/health")

@app.get("/api/videos")
async def api_videos():
    """Get video statuses"""
    return {"videos": get_video_statuses()}

@app.get("/api/tasks")
async def api_tasks():
    """Get active tasks"""
    return get_api_data("status/tasks/active")

@app.get("/api/languages")
async def api_languages():
    """Get supported languages"""
    return get_api_data("upload/languages")

@app.get("/api/system/resources")
async def api_system_resources():
    """Get system resources"""
    return monitor.get_system_resources()

@app.get("/api/system/services")
async def api_service_status():
    """Get service status"""
    return monitor.get_service_status()

@app.get("/api/system/storage")
async def api_storage_info():
    """Get storage information"""
    return monitor.get_storage_info()

@app.get("/api/system/performance")
async def api_performance_metrics():
    """Get performance metrics"""
    return monitor.get_performance_metrics()

@app.get("/api/config")
async def api_config():
    """Get current configuration"""
    return Config.get_all_settings()

@app.post("/api/config/update")
async def api_update_config(request: Request):
    """Update configuration setting"""
    try:
        data = await request.json()
        setting_path = data.get("setting_path")
        value = data.get("value")
        
        if not setting_path or value is None:
            raise HTTPException(status_code=400, detail="setting_path and value are required")
        
        success = Config.update_setting(setting_path, value)
        if success:
            return {"message": f"Setting {setting_path} updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid setting or value")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a task"""
    try:
        response = requests.delete(f"{API_BASE_URL}/status/tasks/{task_id}", timeout=10)
        if response.status_code == 200:
            return {"message": f"Task {task_id} cancelled successfully"}
        else:
            return {"error": f"Failed to cancel task: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error cancelling task: {str(e)}"}

@app.post("/api/system/cleanup", summary="Tüm videolar için manuel temizlik başlat", response_description="Temizlik sonucu")
async def api_cleanup():
    """
    Tüm videolar için manuel temizlik başlatır.
    - uploads, outputs ve status klasörlerindeki ilgili dosyaları siler.
    - Her video_id için temizlik yapılır.
    - Başarılı ve başarısız video_id listesi döner.

    **Response örneği:**
    {
      "message": "Cleanup completed for 3 videos.",
      "cleaned": ["videoid1", "videoid2"],
      "failed": [{"video_id": "videoid3", "error": "Açıklama"}]
    }
    """
    try:
        status_dir = Path("status")
        video_ids = [f.stem for f in status_dir.glob("*.json")]
        cleaned = []
        failed = []
        for vid in video_ids:
            try:
                cleanup_temp_files(vid)
                cleaned.append(vid)
            except Exception as e:
                failed.append({"video_id": vid, "error": str(e)})
        return {"message": f"Cleanup completed for {len(cleaned)} videos.", "cleaned": cleaned, "failed": failed}
    except Exception as e:
        return {"error": f"Cleanup failed: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "admin_panel"}