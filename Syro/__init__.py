# Make sure Celery is imported when Django starts (optional)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception:
    # Celery is optional - app will work without it using synchronous processing
    celery_app = None
    __all__ = tuple()
