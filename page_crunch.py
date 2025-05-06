#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PageCrunch Spider

A configurable Scrapy spider that crawls specified website subtrees.
"""

import logging
import hashlib
from urllib.parse import urlparse
from datetime import datetime

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

logger = logging.getLogger(__name__)

class PageCrunchSpider(CrawlSpider):
    """
    Spider that crawls specified website subtrees and extracts content.
    
    Parameters:
        start_url: URL to start crawling from
        domain: Allowed domain to crawl
        path_prefix: URL path prefix to restrict crawling to a subtree
    """
    name = 'pagecrunch'
    
    # Define empty rules tuple (will be set in __init__)
    rules = ()
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'PageCrunch/1.0 (+https://example.com/pagecrunch-bot)',
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 0.5,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_DIR': 'cache/http',
        'HTTPCACHE_EXPIRATION_SECS': 86400,  # 24 hours
        'FEED_EXPORT_ENCODING': 'utf-8',
        'LOG_LEVEL': 'INFO',
        'CLOSESPIDER_PAGECOUNT': 10000,  # Safety limit
        'CLOSESPIDER_TIMEOUT': 7200,     # 2 hours max
    }
    
    def __init__(self, start_url=None, domain=None, path_prefix=None, *args, **kwargs):
        # Initialize parent
        super(PageCrunchSpider, self).__init__(*args, **kwargs)
        
        # Validate required parameters
        if not start_url or not domain:
            raise CloseSpider("Missing required parameter: start_url and domain must be provided")
        
        # Extract proper domain from start_url if needed
        parsed_url = urlparse(start_url)
        if 'docs.astro.build' in parsed_url.netloc and domain == 'astro.build':
            domain = 'docs.astro.build'
            logger.info(f"Adjusted domain to: {domain}")
        
        # Set spider attributes
        self.start_urls = [start_url]
        self.allowed_domains = [domain]
        self.path_prefix = path_prefix or start_url
        
        logger.info(f"Starting crawl at: {start_url}")
        logger.info(f"Allowed domains: {self.allowed_domains}")
        
        # Define crawl rules - allow all paths within domain
        self.rules = (
            Rule(
                LinkExtractor(
                    # Empty allow means allow all paths
                    allow=(),
                    # File extensions to skip
                    deny_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 
                                    'xls', 'xlsx', 'zip', 'tar', 'gz', 'mp3', 'mp4', 'mov', 'avi'],
                    # Patterns to skip
                    deny=(
                        r'/search/',            # Avoid search pages
                        r'/login/',             # Avoid login pages
                        r'/logout/',            # Avoid logout pages
                        r'.*(\?|&)page=\d+.*',  # Avoid pagination
                        r'.*(\?|&)sort=.*',     # Avoid sort parameters
                    ),
                ),
                callback='parse_item',
                follow=True
            ),
        )
        
        # Required for CrawlSpider
        self._compile_rules()
    
    def parse_start_url(self, response):
        """Process the start URL."""
        logger.info(f"Processing start URL: {response.url}")
        return self.parse_item(response)
    
    def parse_item(self, response):
        """Extract data from pages."""
        logger.info(f"Processing page: {response.url}")
        
        # Skip non-HTML responses
        if not response.headers.get('Content-Type', b'').startswith(b'text/html'):
            return
        
        # Calculate content hash
        html_content = response.body
        content_hash = hashlib.sha256(html_content).hexdigest()
        
        # Extract title with fallbacks
        title = response.css('title::text').get() or response.css('h1::text').get() or ''
        
        # Extract main content with various fallback strategies
        main_content = ' '.join(response.css('main p::text, article p::text').getall())
        if not main_content:
            main_content = ' '.join(response.css('div.content p::text, div#content p::text').getall())
        if not main_content:
            main_content = ' '.join(response.css('p::text').getall())
        
        # Meta description
        meta_desc = response.css('meta[name="description"]::attr(content)').get() or ''
        
        yield {
            'url': response.url,
            'title': title.strip(),
            'meta_description': meta_desc.strip(),
            'content': main_content.strip(),
            'content_hash': content_hash,
            'crawled_at': datetime.now().isoformat(),
            'status': response.status,
            'length': len(html_content),
        }
        
    def closed(self, reason):
        """Called when spider is closed."""
        logger.info(f"Spider closed: {reason}. Total pages crawled: {self.crawler.stats.get_value('item_scraped_count') or 0}")

# For direct execution (testing only)
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    
    process = CrawlerProcess(get_project_settings())
    process.crawl(PageCrunchSpider, 
                 start_url='https://docs.astro.build/en/getting-started/',
                 domain='docs.astro.build')
    process.start()