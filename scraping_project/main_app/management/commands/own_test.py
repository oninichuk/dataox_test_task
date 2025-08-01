from django.core.management.base import BaseCommand

#FOR FETCHING URLS
from datetime import datetime, timezone

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        print(f"MY OWN COMMAND. Time: {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
