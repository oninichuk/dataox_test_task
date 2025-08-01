from django.test import TestCase
from main_app.utils import collect_ft_articles_primary_data, AsyncRequestsManager, FTParserManager
from datetime import timedelta

# Create your tests here.

class ArticleTestCase(TestCase):
    def setUp(self):
        self.test_article_data = {
                                'title': 'Evercore buys London’s elite M&amp;A boutique Robey Warshaw for $196mn',
                                'image_url': 'https://www.ft.com/__origami/service/image/v2/images/raw/https%3A%2F%2Fd1e00ek4ebabms.cloudfront.net%2Fproduction%2Fb96c17ec-74ea-47b2-b635-fe3bc882d8a4.jpg?source=next-article&amp;fit=scale-down&amp;quality=highest&amp;width=700&amp;dpr=1',
        }

    def test_collect_ft_articles_primary_data(self):
        # Get primary data(url, html) of relevant articles
        primary_articles = collect_ft_articles_primary_data(timedelta(hours=1), True)
        self.assertTrue(primary_articles is not False, 'Some exception was thrown, please check logs')

        if primary_articles:
            print(f'Found {len(primary_articles)} articles')
            self.assertTrue(isinstance(primary_articles[0]['url'], str) and primary_articles[0]['url'].find('http') == 0, 'Didn\'t retrieve article URL')
            self.assertTrue(isinstance(primary_articles[0]['html'], str) and primary_articles[0]['html'].find('<body') > -1, 'Didn\'t retrieve article HTML')

    def test_async_requests_manager(self):
        # Collect urls of relevant articles from FT list pages
        articles_urls = collect_ft_articles_primary_data(timedelta(hours=1))

        if articles_urls:
            print(f'Found {len(articles_urls)} articles')
            requests_manager = AsyncRequestsManager(articles_urls)
            # Get articles web pages
            requests_manager.run_all_requests()

            if requests_manager.results:
                self.assertTrue(isinstance(requests_manager.results[0]['url'], str) and requests_manager.results[0]['url'].find('http') == 0, 'Didn\'t retrieve article URL')
                self.assertTrue(isinstance(requests_manager.results[0]['html'], str) and requests_manager.results[0]['html'].find('<body') > -1, 'Didn\'t retrieve article HTML')

    def test_parser_manager(self):
        try:
            with open('main_app/test_articles/article1.html', 'r') as file1:
                article1 = file1.read()
                parser_manager = FTParserManager([{'url':'https://ft.com/content/specific_article', 'html': article1}])
                # Parsing and saving article
                parser_manager.run_all_processes()
                ready_data = parser_manager.results
                # Comparing retrieved data with real data
                statement = (ready_data and ready_data[0]['article'] and ready_data[0]['article'].title == self.test_article_data['title'] and ready_data[0]['article'].image_url == self.test_article_data['image_url'])
                self.assertTrue(statement, 'Parsing and saving article has failed')
        except Exception as e:
            self.assertTrue(False, f"Could not open test article file. Exception: {e}")