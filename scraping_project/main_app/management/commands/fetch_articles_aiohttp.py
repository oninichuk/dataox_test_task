from django.core.management.base import BaseCommand
from datetime import timedelta
from main_app.utils import collect_ft_articles_primary_data, AsyncRequestsManager, FTParserManager
from main_app.models import Article

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        period = timedelta(hours=1) if Article.objects.all()[:1].exists() else timedelta(days=30)
        
        # Collect urls of relevant articles from FT list pages
        primary_articles = collect_ft_articles_primary_data(period)

        if primary_articles:
            requests_manager = AsyncRequestsManager(primary_articles)
            # Get articles web pages
            requests_manager.run_all_processes()

            parser_manager = FTParserManager(requests_manager.results)
            # Parsing articles web pages and saving retrieved data in DB
            parser_manager.run_all_processes()
    
        self.stdout.write('end')
        
