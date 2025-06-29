import uuid
import shutil
from pathlib import Path
from typing import Optional
import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from app.tasks.process_video import process_video_task
from app.models.upload_response import UploadResponse
from app.config import Config

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "as": "Assamese",
    "az": "Azerbaijani",
    "ba": "Bashkir",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bo": "Tibetan",
    "br": "Breton",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fo": "Faroese",
    "fr": "French",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "ht": "Haitian Creole",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "la": "Latin",
    "lb": "Luxembourgish",
    "ln": "Lingala",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Myanmar",
    "ne": "Nepali",
    "nl": "Dutch",
    "nn": "Norwegian Nynorsk",
    "no": "Norwegian",
    "oc": "Occitan",
    "pa": "Punjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sa": "Sanskrit",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sn": "Shona",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "tk": "Turkmen",
    "tl": "Tagalog",
    "tr": "Turkish",
    "tt": "Tatar",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zh": "Chinese"
}

SUPPORTED_MODELS = ["openai-whisper", "faster-whisper"]

def validate_video_file(file: UploadFile) -> bool:
    """Validate uploaded video file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size and file.size > Config.get_max_file_size():
        return False
    
    return True

def validate_language(language: str) -> bool:
    """Validate target language code"""
    return language in SUPPORTED_LANGUAGES

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for translation"""
    return {
        "languages": SUPPORTED_LANGUAGES,
        "count": len(SUPPORTED_LANGUAGES),
        "default": "tr"
    }

@router.get("/models")
async def get_supported_models():
    """Desteklenen transkripsiyon modellerini döndürür."""
    return {"models": SUPPORTED_MODELS, "default": "openai-whisper"}

@router.post("/", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    target_language: str = Form("tr"),
    model: str = Form("openai-whisper")
):
    """
    Video dosyası yükle ve işleme başlat (altyazı çıkarma, çeviri, hardsub).

    - **Amaç:** Kullanıcıdan bir video dosyası alır, hedef dil ve model seçimiyle işleme başlatır.
    - **Parametreler:**
        - **file**: Yüklenecek video dosyası (mp4, avi, mov, mkv, wmv, flv, webm)
        - **target_language**: Hedef dil kodu (örn: "tr", "en", "es")
        - **model**: Kullanılacak transkripsiyon modeli ("openai-whisper" veya "faster-whisper")
    - **Yanıt:**
        - video_id: Yüklenen videoya ait UUID
        - filename: Dosya adı
        - target_language: Hedef dil kodu
        - language_name: Hedef dilin adı
        - status: "uploaded"
        - task_id: Arka planda başlatılan işin Celery task id'si
        - model: Seçilen model
        - supported_models: Desteklenen modellerin listesi
    - **Örnek İstek:**
        ```bash
        curl -X POST "http://localhost:8082/api/v1/upload/" \
          -F "file=@video.mp4" \
          -F "target_language=tr" \
          -F "model=faster-whisper"
        ```
    - **Örnek Yanıt:**
        ```json
        {
          "video_id": "550e8400-e29b-41d4-a716-446655440000",
          "filename": "video.mp4",
          "target_language": "tr",
          "language_name": "Turkish",
          "status": "uploaded",
          "task_id": "task-123",
          "model": "faster-whisper",
          "supported_models": ["openai-whisper", "faster-whisper"]
        }
        ```
    - **Hata Kodları:**
        - 400: Geçersiz dosya, dil kodu veya model
        - 413: Dosya boyutu limiti aşıldı
        - 500: Sunucu hatası
    """
    logger.info(f"Received upload request for file: {file.filename} with target language: {target_language} and model: {model}")
    if model not in SUPPORTED_MODELS:
        raise HTTPException(status_code=400, detail=f"Model '{model}' is not supported. Supported: {SUPPORTED_MODELS}")
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Save file with video ID
        file_extension = Path(file.filename).suffix if file.filename else ".mp4"
        file_path = uploads_dir / f"{video_id}{file_extension}"
        
        logger.info(f"Saving file {file.filename} as {file_path} for language {target_language}")
        
        # Read file content and save
        content = await file.read()
        
        # Validate file size
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if len(content) > Config.get_max_file_size():
            raise HTTPException(
                status_code=413, 
                detail=f"File size {len(content) / (1024*1024):.2f}MB exceeds limit {Config.get_max_file_size() / (1024*1024):.2f}MB"
            )
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Verify file was saved correctly
        if not file_path.exists() or file_path.stat().st_size != len(content):
            raise HTTPException(status_code=500, detail="Failed to save file correctly")
        
        logger.info(f"File saved successfully: {file_path} ({len(content)} bytes)")
        
        # Start Celery task
        logger.info(f"Starting Celery task for video {video_id} with language {target_language} and model {model}")
        task = process_video_task.delay(video_id, str(file_path), target_language, model)
        logger.info(f"Celery task started: {task.id}")
        
        # Get language name
        language_name = SUPPORTED_LANGUAGES.get(target_language, "Unknown")
        
        return UploadResponse(
            video_id=video_id,
            filename=file.filename,
            target_language=target_language,
            language_name=language_name,
            status="uploaded",
            task_id=task.id,
            model=model,
            supported_models=SUPPORTED_MODELS
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/health")
async def health_check():
    """
    API ve dosya yükleme servisinin sağlık durumunu kontrol et.
    
    - **Amaç:** API'nin ve yükleme klasörünün erişilebilir ve sağlıklı olup olmadığını kontrol eder.
    - **Yanıt:**
        - status: API'nin genel durumu ("healthy" veya "unhealthy")
        - upload_dir: Yükleme klasörünün yolu
        - supported_languages_count: Desteklenen dil sayısı
        - max_file_size_mb: Maksimum dosya boyutu (MB)
    - **Örnek İstek:**
        curl -X GET "http://localhost:8082/api/v1/upload/health"
    - **Örnek Yanıt:**
        {
          "status": "healthy",
          "upload_dir": "uploads",
          "supported_languages_count": 100,
          "max_file_size_mb": 500
        }
    """
    return {
        "status": "healthy", 
        "upload_dir": str(UPLOAD_DIR),
        "supported_languages_count": len(SUPPORTED_LANGUAGES),
        "max_file_size_mb": Config.get_max_file_size() / (1024 * 1024)
    } 