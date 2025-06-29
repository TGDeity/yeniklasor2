from fastapi import APIRouter
from .endpoints import upload, status, config

router = APIRouter()
router.include_router(upload.router, prefix="/upload", tags=["Upload"])
router.include_router(status.router, prefix="/status", tags=["Status"])
router.include_router(config.router, prefix="/config", tags=["Config"])