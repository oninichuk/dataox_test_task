import os
from celery import Celery
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraping_project.settings')

app = Celery('main_app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()