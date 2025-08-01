from datetime import datetime, timezone, timedelta
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from typing import Union
import asyncio
import aiohttp
from main_app.models import Article
import json
import logging
import math
import os

# Retrieve articles primary data in Financial Times list pages. 
# By default it will retrieve only URLs, optionally it can retrieve corresponing articles pages HTML
def collect_ft_articles_primary_data(period: timedelta, get_html=False) -> Union[list, bool]:
    # All collected articles which match requested period
    all_articles = []

    # Get an instance of a logger
    logger = logging.getLogger('main_app') 

    # Initializing selenium driver
    options = Options()
    options.add_argument('--headless')

    # YOU CAN OPTIONALLY PASTE YOUR OWN PROXY AND UNCOMMENT FOLLOWING
    # options.add_argument(f'--proxy-server=http://47.236.163.74:8080')

    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options = options
    )
    wait = WebDriverWait(driver, 20)

    # Current number of Financial times articles page 
    current_page = 1

    logger.info('Fetching articles has started')

    # Variables which will be used for interupting search # check if search is finished(or gained time limit) 
    search_time_limit = int(os.getenv('COLLECT_PR_ARTICLES_TIME_LIMIT'))
    is_end = False
    start_time = datetime.now(timezone.utc)

    # Calculating min publish datetime of relevant articles 
    min_publish_datetime = start_time - period

    while not is_end and (datetime.now(timezone.utc) - start_time).total_seconds() <= search_time_limit:
        articles = []

        # Variables which implement resending request
        attempts = 0
        success_request = False

        while not success_request and attempts < 3:
            try:
                driver.get(f'https://www.ft.com/world?page={current_page}')

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stream__pagination")))
                # Confirming successful attempt
                success_request = True

                # Processing response html
                page_html = re.sub(r'(?:\r\n|\n)+', ' ', driver.page_source)
                # Retrieving specific data of every article (publish datetime, url) 
                matches = list(re.finditer(r'<div data-o-grid-colspan="12 L3">.*?<time data-o-component.*?datetime="((?:[0-9]{4})\-(?:[0-9]{2})\-(?:[0-9]{2})T(?:[0-9]{2})\:(?:[0-9]{2})\:(?:[0-9]{2})).*?<div data-o-grid-colspan="12 L9">.*?<div class="o-teaser__heading".*?<a.*?href\=\"(.+?)\".*?<\/div>',
                                            page_html))
                
                # Handling situation when regular expression didn't retrieve articles
                if len(matches) == 0:
                    logger.info(f'Couldn\'t retrieve articles from page using regular expression. Fetching articles has finished')
                    driver.quit()
                    return False
                
                for match in matches:
                    publish_datetime = datetime.strptime(f'{match.group(1)}+0000', "%Y-%m-%dT%H:%M:%S%z")
                    # Filtering articles which match requested period
                    if publish_datetime >= min_publish_datetime:
                        # Filtering articles which are not premium
                        if 'o-labels o-labels--premium o-labels--content-premium' not in match.group(0):
                            article_url = f'https://www.ft.com{match.group(2)}'

                            # Check if we need to get article html
                            if get_html:
                                # GET ARTICLE PAGE
                                # Variables which implement resending request
                                article_attempts = 0
                                article_success = False
                                
                                while not article_success and article_attempts < 3:
                                    try: 
                                        driver.get(article_url)
                                        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'footer')))
                                        article_success = True
                                        # Add retrieved html of article
                                        articles.append({'url': article_url, 'html': driver.page_source})
                                    except WebDriverException as e:
                                        article_attempts += 1
                                        if article_attempts < 3:
                                            # Make pause before next attempt
                                            time.sleep(3)
                                        if article_attempts == 3:
                                            logger.info(f'Request "{article_url}" has failed(3 attempts). Exception: {e}')
                            else:
                                # Collect only article url
                                articles.append(article_url)
                    else:
                        # If we found at least one not relevant article then we stop search 
                        is_end = True
                        break
                
                # Add ready articles of current page to general dictionary
                all_articles.extend(articles)

                if not is_end: # Incrementing current page in case if search continues
                    current_page += 1

            except WebDriverException as e:
                attempts += 1
                if attempts < 3:
                    # Make pause before next attempt
                    time.sleep(3)
                if attempts == 3:
                    # Forcing interuption
                    logger.info(f'Request "https://www.ft.com/world?page={current_page}" has failed(3 attempts). Exception: {e}')
                    driver.quit()
                    # Return articles which we retrieved before connection error
                    all_articles.extend(articles)
                    logger.info(f'Fetched {len(all_articles)} articles. Fetching articles has finished')
                    return all_articles
                
            except Exception as e:
                # Forcing interuption, notify about unknown problem
                logger.info(f'Something gone wrong. Exception: {e}. Fetching articles has finished')
                # Stop all processes
                driver.quit()
                return False
    
    driver.quit()
    logger.info(f'Fetched {len(all_articles)} articles. Fetching articles has finished')
    return all_articles

class AsyncRequestsManager:
    def __init__(self, urls: list[str]):
        self.threads_number = int(os.getenv('ASYNC_REQUESTS_THREADS'))
        self.logger = logging.getLogger('main_app')
        self.urls: list[str] = urls
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # PROVIDE YOUR OWN PROXY
        #self.proxy = '47.236.163.74:8080'

        self.results: list[dict] = []

    def run_all_requests(self):
        asyncio.run(self.fetch_all())

    async def fetch_all(self):
        self.logger.info(f'Getting html pages of articles has started')
        urls_length = len(self.urls)
        # Calculate actual number of threads
        threads_number = urls_length if urls_length < self.threads_number else self.threads_number
        # Number of iterations for creating threads
        approaches = math.ceil(urls_length/threads_number)

        # Sending requests simultaneously
        for i in range(approaches):
            start_index = i * threads_number
            slice_end = (i + 1) * threads_number
            slice_urls = self.urls[start_index:slice_end]
            tasks = [self.fetch(url) for url in slice_urls]
            current_results = await asyncio.gather(*tasks)
            self.results.extend(current_results)
        self.logger.info(f'Getting html pages of articles has finished')
            
    async def fetch(self, url) -> dict:
        attempts = 0

        while attempts < 3:
            try:
                async with aiohttp.ClientSession() as session:
                    # YOU CAN ADD ADDITIONAL ARGUMENT proxy=f"https://{self.proxy} WITH YOUR OWN PROXY
                    async with session.get(url, timeout=10, headers=self.headers) as response: 
                        html = await response.text()
                        return {'url': url, 'html': html}
            except Exception as e:
                attempts += 1
                if attempts < 3:
                    # Make pause before next attempt
                    await asyncio.sleep(3)
                if attempts == 3:
                    self.logger.info(f'Request has failed(3 attempts). Exception: {e}')
        return {'url': url, 'html': False}
    
class FTParserManager:
    def __init__(self, html_pages: list[dict]):
        self.threads_number = int(os.getenv('PARSE_ARTICLE_THREADS'))
        self.logger = logging.getLogger('main_app')
        self.patterns = {
                            'title': r'<span class="headline__text".*?>(?:\s|\\t)*?(.+?)(?:\s|\\t)*?<\/span>',
                            'content': r'<article id="article-body".*?>((?:\s|.)+?)<\/article>',
                            'author': r'<a class="o3-editorial-typography-byline-author".*?>(?:\s|\\t)*?(.+?)(?:\s|\\t)*?<\/a>',
                            'published_at': r'<time data-o-component="o-date" class="article-info__timestamp o3-editorial-typography-byline-timestamp o-date" datetime="((?:[0-9]{4})\-(?:[0-9]{2})\-(?:[0-9]{2})T(?:[0-9]{2})\:(?:[0-9]{2})\:(?:[0-9]{2}))',
                            'subtitle': r'<div class="o-topper__standfirst".*?>(?:\s|\\t)*?(.+?)(?:\s|\\t)*?<\/div>',
                            'tags': r'<li class="concept-list__list-item".*?>(?:\s|\\t)*?<a.*?>(?:\s|\\t|\t)*?(.+?)(?:\s|\\t|\t)*?<\/a>',
                            'image_url': r'<div class="main-image".*?>(?:.|\s)*?<img src="(.+?)"',
                            'related_articles': r'<div class="o-teaser__heading".*?>(?:\s|\\t)*?<a .*?href="(.+?)"',
        }
        self.mandatory_patterns = ['title', 'content', 'author', 'published_at']
        self.html_pages = html_pages
        self.results: list[dict] = []

    def parse_and_save_article(self, html_page: dict) -> dict:
        default_response = html_page.copy()
        default_response['article'] = False
        
        if not html_page['html']:
            return default_response

        all_matches = {}
        
        for spattern in ['title', 'content', 'published_at', 'subtitle', 'image_url']:
            all_matches[spattern] = re.search(self.patterns[spattern], html_page['html'])
            if spattern in self.mandatory_patterns and not all_matches[spattern]:
                self.logger.info(f'Mandatory pattern "{spattern}" hasn\'t retrieved value')
                return default_response
        
        for mpattern in ['author', 'tags', 'related_articles']:
            all_matches[mpattern] = list(re.finditer(self.patterns[mpattern], html_page['html']))
            if mpattern in self.mandatory_patterns and len(all_matches[mpattern]) == 0:
                self.logger.info(f'Mandatory pattern "{mpattern}" hasn\'t retrieved value')
                return default_response
            
        # Clean html-tags in content
        content = re.sub(r'<.*?>', '', all_matches['content'].group(1))
        word_count = len(re.split(r'\s+', content))

        authors = json.dumps([match.group(1) for match in all_matches['author']])
        published_at = datetime.strptime(f'{all_matches["published_at"].group(1)}+0000', "%Y-%m-%dT%H:%M:%S%z")
        subtitle = all_matches['subtitle'].group(1) if all_matches['subtitle'] else ''
        tags = json.dumps([match.group(1) for match in all_matches['tags']])
        image_url = all_matches['image_url'].group(1) if all_matches['image_url'] else ''
        related_articles = json.dumps([match.group(1) for match in all_matches['related_articles']])

        try:
            new_article = Article.objects.create(
                                    url=html_page['url'],
                                    title=all_matches['title'].group(1),
                                    content=content,
                                    author=authors,
                                    published_at=published_at,
                                    subtitle=subtitle,
                                    tags=tags,
                                    image_url=image_url,
                                    word_count=word_count,
                                    related_articles=related_articles
            )
            default_response['article'] = new_article
            self.logger.info(f'Article "{new_article.title}" was saved')
        except Exception as e:
            self.logger.info(f'Couldn\'t add new Article record. Exception: {e}')
            return default_response
        
        return default_response 

    async def parse_and_save_all_articles(self):
        self.logger.info(f'Parsing and saving articles has started')
        html_pages_length = len(self.html_pages)
        # Calculate actual number of threads
        threads_number = html_pages_length if html_pages_length < self.threads_number else self.threads_number
        # Number of iterations for creating threads
        approaches = math.ceil(html_pages_length/threads_number)

        # Parsing articles web pages simultaneously
        for i in range(approaches):
            start_index = i * threads_number
            slice_end = (i + 1) * threads_number
            slice_pages = self.html_pages[start_index:slice_end]
            tasks = [asyncio.to_thread(self.parse_and_save_article, html_page) for html_page in slice_pages]
            current_results = await asyncio.gather(*tasks)
            self.results.extend(current_results)
        self.logger.info(f'Parsing and saving articles has finished')

    def run_all_processes(self):
        asyncio.run(self.parse_and_save_all_articles())
            
        
        
    
