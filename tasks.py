# tasks.py
from celery import Celery
import os
from models import Resume, get_db
from sqlalchemy.orm import Session

celery = Celery(
    'resume_analyzer',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)
