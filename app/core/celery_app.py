from celery import Celery
from app.core.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    "app",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=["app.tasks.process_video"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    broker_connection_retry_on_startup=True,
    
    # Task routing
    task_routes={
        'app.tasks.process_video.process_video_task': {'queue': 'video_processing'}
    },
    
    # Queue settings
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'video_processing': {
            'exchange': 'video_processing',
            'routing_key': 'video_processing',
        }
    },
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': "mymaster",
        'visibility_timeout': 3600,
    },
    
    # Beat settings (for scheduled tasks if needed)
    beat_schedule={},
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Force import of task modules to register with Celery
from app.tasks import process_video

logger.info("Celery app configured successfully")
