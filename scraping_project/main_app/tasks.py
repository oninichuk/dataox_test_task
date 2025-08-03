from celery import shared_task
from django.core.management import call_command
import os


@shared_task
def fetch_articles():
    call_command(os.getenv("ACTIVE_FETCH_COMMAND"))
