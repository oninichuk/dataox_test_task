from django.core.management.base import BaseCommand
from datetime import timedelta
from main_app.utils import collect_ft_articles_primary_data, FTParserManager
from main_app.models import Article

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        period = timedelta(hours=1) if Article.objects.all()[:1].exists() else timedelta(days=30)
        
        # Get primary data(url, html) of relevant articles
        primary_articles = collect_ft_articles_primary_data(period, True)

        if primary_articles:
            parser_manager = FTParserManager(primary_articles)
            # Parsing articles web pages and saving retrieved data in DB
            parser_manager.run_all_processes()
    
        self.stdout.write('end')
