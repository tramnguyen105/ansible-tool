from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


settings = get_settings()
celery_app = Celery('ansible_tool', broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = 'UTC'
celery_app.conf.imports = (
    'app.modules.jobs.tasks',
    'app.modules.schedules.service',
)
celery_app.conf.beat_schedule = {
    'dispatch-due-schedules': {
        'task': 'app.modules.schedules.service.dispatch_due_schedules',
        'schedule': 60.0,
    }
}
celery_app.autodiscover_tasks(['app.modules.jobs'])
