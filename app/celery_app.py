from celery import Celery
 
celery_app = Celery(
    "lisa",
    broker="redis://localhost:6379/0",   # Update if your Redis is elsewhere
    backend="redis://localhost:6379/0"
) 