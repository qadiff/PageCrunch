#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PageCrunch Spider

A configurable Scrapy spider that crawls specified website subtrees with URL deduplication.
Optimized for AI data source collection.
"""

import logging
import hashlib
import sqlite3
import os
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

logger = logging.getLogger(__name__)

class URLTracker:
    """Tracks visited URLs using SQLite to avoid duplicates."""
    
    def __init__(self, db_path='pagecrunch_urls.db'):
        """Initialize the URL tracker with a SQLite database."""
        self.db_path = db_path
        self.in_memory = db_path == ':memory:'
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        create_table = not self.in_memory and not os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('PRAGMA journal_mode = WAL')  # Better concurrent access
        
        if create_table or self.in_memory:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS visited_urls (
                    url TEXT PRIMARY KEY,
                    content_hash TEXT,
                    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON visited_urls(content_hash)')
            self.conn.commit()
            logger.info(f"Created URL tracking database at {self.db_path}")
    
    def has_visited(self, url):
        """Check if a URL has been visited before."""
        cursor = self.conn.execute('SELECT 1 FROM visited_urls WHERE url = ?', (url,))
        return cursor.fetchone() is not None
    
    def mark_visited(self, url, content_hash):
        """Mark a URL as visited with its content hash."""
        try:
            self.conn.execute(
                'INSERT OR REPLACE INTO visited_urls (url, content_hash, visited_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                (url, content_hash)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error recording visited URL {url}: {e}")
    
    def has_identical_content(self, content_hash):
        """Check if we've seen identical content before (helps detect duplicate content at different URLs)."""
        cursor = self.conn.execute('SELECT url FROM visited_urls WHERE content_hash = ? LIMIT 1', (content_hash,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info(f"Closed URL tracking database at {self.db_path}")

class PageCrunchSpider(CrawlSpider):
    """
    Spider that crawls specified website subtrees and extracts content.
    Uses SQLite to track visited URLs for deduplication.
    
    Parameters:
        start_url: URL to start crawling from
        domain: Allowed domain to crawl
        path_prefix: URL path prefix to restrict crawling to a subtree
        db_path: Path to SQLite database for URL tracking (default: pagecrunch_urls.db)
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
        # Disable built-in duplication filter to use our custom SQLite-based solution
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',  
    }
    
    def __init__(self, start_url=None, domain=None, path_prefix=None, db_path='pagecrunch_urls.db', *args, **kwargs):
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
        
        # Initialize URL tracker
        self.url_tracker = URLTracker(db_path)
        
        logger.info(f"Starting crawl at: {start_url}")
        logger.info(f"Allowed domains: {self.allowed_domains}")
        logger.info(f"Using URL database: {db_path}")
        
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
                follow=True,
                process_links='process_links'  # Use our link processor for filtering
            ),
        )
        
        # Required for CrawlSpider
        self._compile_rules()
    
    def process_links(self, links):
        """Filter out already visited links before crawling."""
        filtered_links = []
        for link in links:
            if not self.url_tracker.has_visited(link.url):
                filtered_links.append(link)
            else:
                logger.debug(f"Skipping already visited URL: {link.url}")
        
        logger.info(f"Found {len(links)} links, {len(filtered_links)} new")
        return filtered_links
    
    def parse_start_url(self, response):
        """Process the start URL."""
        logger.info(f"Processing start URL: {response.url}")
        return self.parse_item(response)
    
    def parse_item(self, response):
        """Extract data from pages."""
        url = response.url
        logger.info(f"Processing page: {url}")
        
        # Skip non-HTML responses
        if not response.headers.get('Content-Type', b'').startswith(b'text/html'):
            return
        
        # Calculate content hash
        html_content = response.body
        content_hash = hashlib.sha256(html_content).hexdigest()
        
        # Check for duplicate content at different URLs
        duplicate_url = self.url_tracker.has_identical_content(content_hash)
        if duplicate_url:
            logger.info(f"Found duplicate content: {url} matches {duplicate_url}")
            # Still mark as visited but don't yield the item
            self.url_tracker.mark_visited(url, content_hash)
            return
        
        # Mark URL as visited
        self.url_tracker.mark_visited(url, content_hash)
        
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
            'url': url,
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
        # Get stats
        pages_crawled = self.crawler.stats.get_value('item_scraped_count') or 0
        
        # Close URL tracker database
        self.url_tracker.close()
        
        logger.info(f"Spider closed: {reason}. Total pages crawled: {pages_crawled}")

# For direct execution (testing only)
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    
    process = CrawlerProcess(get_project_settings())
    process.crawl(PageCrunchSpider, 
                 start_url='https://docs.astro.build/en/getting-started/',
                 domain='docs.astro.build')
    process.start()