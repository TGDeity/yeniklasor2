from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import Config
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    setting_path: str
    value: int

# /api/v1/config [GET]
# Kullanım amacı: Sunucunun çalışma zamanı ve sistem ayarlarını JSON olarak döner. Tüm konfigürasyon ayarlarını görüntülemek için kullanılır.
@router.get("/")
def get_config():
    """
    Tüm konfigürasyon ayarlarını döner.
    
    - **Amaç:** Sunucunun çalışma zamanı ve sistem ayarlarını JSON olarak döner.
    - **Yanıt:**
        - Tüm ayarları içeren bir JSON nesnesi
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/config"
    """
    logger.info("GET /config/ - returning all settings")
    return Config.get_all_settings()

# /api/v1/config/update [POST]
# Kullanım amacı: Belirli bir konfigürasyon ayarını dinamik olarak güncellemek için kullanılır.
@router.post("/update")
async def update_config(req: ConfigUpdateRequest):
    """
    Bir konfigürasyon ayarını dinamik olarak günceller.
    
    - **Amaç:** Belirli bir ayarı (örn: timeout, kaynak limiti) günceller.
    - **Parametreler:**
        - **setting_path**: Güncellenecek ayarın yolu (örn: "timeouts.process_timeout")
        - **value**: Yeni değer
    - **Yanıt:**
        - message: Sonuç mesajı
        - config: Güncel ayarların tamamı
    - **Örnek İstek:**
        curl -X POST "http://localhost:8082/api/v1/config/update" \
          -H "Content-Type: application/json" \
          -d '{"setting_path": "timeouts.process_timeout", "value": 600}'
    """
    logger.info(f"POST /config/update - received: {req}")
    # Log config file before update
    try:
        with open(Config.RUNTIME_CONFIG_PATH, "r") as f:
            before = f.read()
        logger.info(f"Config file before update: {before}")
    except Exception as e:
        logger.warning(f"Could not read config file before update: {e}")
    # Update logic
    setting_path = req.setting_path
    value = req.value
    if not setting_path or value is None:
        logger.error(f"Missing setting_path or value in request: {req}")
        raise HTTPException(status_code=400, detail="setting_path and value are required")
    if setting_path == "resources.max_file_size_mb":
        cfg = Config.get_runtime_config()
        cfg["max_file_size_mb"] = int(value)
        Config.set_runtime_config(cfg)
        logger.info(f"Updated max_file_size_mb to {value}")
    else:
        success = Config.update_setting(setting_path, value)
        if not success:
            logger.error(f"Invalid setting or value: {setting_path}={value}")
            raise HTTPException(status_code=400, detail="Invalid setting or value")
        logger.info(f"Updated {setting_path} to {value}")
    # Log config file after update
    try:
        with open(Config.RUNTIME_CONFIG_PATH, "r") as f:
            after = f.read()
        logger.info(f"Config file after update: {after}")
    except Exception as e:
        logger.warning(f"Could not read config file after update: {e}")
    return {"message": f"Setting {setting_path} updated successfully", "config": Config.get_all_settings()} 