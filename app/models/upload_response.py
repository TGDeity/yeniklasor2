from pydantic import BaseModel, Field

class UploadResponse(BaseModel):
    """
    Video yükleme işlemi sonrası dönen yanıt modeli.
    """
    video_id: str = Field(..., description="Yüklenen videoya ait benzersiz kimlik (UUID)", example="550e8400-e29b-41d4-a716-446655440000")
    filename: str = Field(..., description="Yüklenen dosyanın orijinal adı", example="video.mp4")
    target_language: str = Field(..., description="Hedef dil kodu", example="tr")
    language_name: str = Field(..., description="Hedef dilin tam adı", example="Turkish")
    status: str = Field(..., description="Yükleme ve işleme durumu", example="uploaded")
    task_id: str = Field(..., description="Arka planda başlatılan Celery görevinin kimliği", example="task-123")

    class Config:
        schema_extra = {
            "example": {
                "video_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "video.mp4",
                "target_language": "tr",
                "language_name": "Turkish",
                "status": "uploaded",
                "task_id": "task-123"
            }
        } 