import psutil
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import requests
from datetime import datetime, timedelta

class ResourceMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.api_base_url = os.getenv("API_BASE_URL", "http://api:8082/api/v1")
    
    def _get_from_api(self, endpoint: str) -> Dict[str, Any]:
        """Helper function to get data from the main API."""
        try:
            response = requests.get(f"{self.api_base_url}/{endpoint}", timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage from the main API."""
        return self._get_from_api("status/system/resources")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services from the main API."""
        health_data = self._get_from_api("status/system/health")
        if "error" in health_data:
            # Return a default error structure if the health endpoint is unreachable
            return {
                "api": {"status": "unreachable", "error": health_data["error"]},
                "redis": {"status": "unknown"},
                "celery": {"status": "unknown"}
            }
        
        # The API is implicitly healthy if we get a response
        services = {"api": {"status": "healthy"}}
        
        # Extract service statuses from the response
        api_services = health_data.get("services", {})
        services["redis"] = api_services.get("redis", {"status": "unknown"})
        services["celery"] = api_services.get("celery", {"status": "unknown"})

        return services
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of active tasks"""
        try:
            response = requests.get(f"{self.api_base_url}/status/tasks/active", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("active_tasks", [])
            else:
                return []
        except Exception:
            return []
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage directory information"""
        try:
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
        except Exception as e:
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics over time"""
        try:
            # Get recent logs for analysis
            log_dir = Path("logs")
            log_files = sorted(log_dir.glob("app_*.log"), reverse=True)
            if not log_files:
                return {"error": "Log file not found"}
            log_file = log_files[0]
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # Analyze recent activity
                recent_lines = lines[-100:]  # Last 100 lines
                # Count different types of operations
                metrics = {
                    "upload_count": len([l for l in recent_lines if "upload" in l.lower()]),
                    "processing_count": len([l for l in recent_lines if "processing" in l.lower()]),
                    "error_count": len([l for l in recent_lines if "error" in l.lower()]),
                    "success_count": len([l for l in recent_lines if "completed" in l.lower()]),
                    "total_operations": len(recent_lines)
                }
                return metrics
            else:
                return {"error": "Log file not found"}
        except Exception as e:
            return {"error": str(e)} 