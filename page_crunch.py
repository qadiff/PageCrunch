#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PageCrunch: Web crawler for AI data sources
A specialized crawler for efficiently collecting data in JSONL format for AI model training

PageCrunch: AI データソース向けウェブクローラー
AI モデル訓練用のデータを JSONL 形式で効率的に収集するための特化型クローラー
"""

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.exceptions import NotConfigured
import sqlite3
import hashlib
import json
import os
import datetime
import logging
import re
from urllib.parse import urlparse, urljoin
from w3lib.url import url_query_cleaner


class PageCrunchSpider(CrawlSpider):
    name = 'page_crunch'
    
    def __init__(self, start_url=None, domain=None, ignore_subdomains='true',
                 refresh_mode='auto', refresh_days=7, db_path=None, 
                 path_prefix=None, output_cache='true', content_mode='auto', **kwargs):
        """
        Initialization method
        
        Args:
            start_url (str): Starting URL for crawling
            domain (str): Allowed domain
            ignore_subdomains (str): Whether to treat subdomains as the same domain (true/false)
            refresh_mode (str): auto/force/none - Re-crawling behavior settings
            refresh_days (int): Day threshold for re-crawling
            db_path (str): Path to URL tracking database
            path_prefix (str): If specified, only crawl URLs that match this path prefix
            output_cache (str): Whether to output cached pages as well (true/false)
            content_mode (str): Content extraction mode (auto/body) - auto for automatic selection, body to get the entire body tag
            **kwargs: Additional parameters

        初期化メソッド
        
        Args:
            start_url (str): クロール開始 URL
            domain (str): 許可ドメイン
            ignore_subdomains (str): サブドメインを同じドメインとして扱うか (true/false)
            refresh_mode (str): auto/force/none - 再クロール動作の設定
            refresh_days (int): 再クロールの日数閾値
            db_path (str): URL 追跡データベースのパス
            path_prefix (str): 指定した場合、このパスプレフィックスに一致するURLのみをクロール
            output_cache (str): キャッシュされたページも出力するか (true/false)
            content_mode (str): コンテンツ抽出モード (auto/body) - autoは自動選択、bodyはbodyタグ全体を取得
            **kwargs: 追加のパラメータ
        """

        # Check required parameters
        # 必須パラメータのチェック
        if not start_url:
            raise NotConfigured('start_url is required')
        if not domain:
            parsed_url = urlparse(start_url)
            domain = parsed_url.netloc
        
        # Parameter settings
        # パラメータの設定
        self.start_urls = [start_url]
        self.allowed_domains = [domain]
        self.ignore_subdomains = ignore_subdomains.lower() == 'true'
        self.refresh_mode = refresh_mode.lower()
        self.refresh_days = int(refresh_days)
        self.path_prefix = path_prefix
        self.output_cache = output_cache.lower() == 'true'
        self.content_mode = content_mode.lower()
        self.prime_directive = kwargs.get('prime_directive', 'true').lower() == 'true'
        
        # Log level settings (change from INFO -> WARN to suppress log output)
        # ログレベル設定（INFO -> WARN に変更してログ出力を抑制）
        logging.getLogger('scrapy').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('twisted').setLevel(logging.WARNING)
        
        # Keep our own logger at INFO level
        # 自分自身のロガーは INFO レベルを維持
        self.log_level = logging.INFO
        
        # Domain settings processing
        # ドメイン設定の処理
        self.top_domain = self._get_top_domain(domain)
        if self.ignore_subdomains:
            self.allowed_domains = [self.top_domain]
        
        # Database settings
        # データベース設定
        self.db_path = db_path or f"{domain.replace('.', '_')}_urls.db"
        
        # Link extraction settings
        # リンク抽出設定
        self.link_extractor = LinkExtractor(allow_domains=self.allowed_domains)
        
        # CrawlSpiderのルールをオーバーライド（空にする）
        self.rules = ()
        
        # Initialize parent class
        # 親クラスの初期化を最後に行う
        super(PageCrunchSpider, self).__init__(**kwargs)
        
        # Database setup
        # データベースのセットアップ
        self.setup_database()
        
        self.log(f"Spider initialized with parameters:", self.log_level)
        self.log(f"  start_url: {start_url}", self.log_level)
        self.log(f"  domain: {domain}", self.log_level)
        self.log(f"  ignore_subdomains: {self.ignore_subdomains}", self.log_level)
        self.log(f"  refresh_mode: {self.refresh_mode}", self.log_level)
        self.log(f"  refresh_days: {self.refresh_days}", self.log_level)
        self.log(f"  db_path: {self.db_path}", self.log_level)
        self.log(f"  path_prefix: {self.path_prefix}", self.log_level)
        self.log(f"  output_cache: {self.output_cache}", self.log_level)
        self.log(f"  content_mode: {self.content_mode}", self.log_level)
    
    def _get_top_domain(self, domain):
        """
        ドメインの最上位部分を取得
        
        Args:
            domain (str): ドメイン名
            
        Returns:
            str: トップレベルドメイン
        """
        parts = domain.split('.')
        if len(parts) > 2:
            # If it contains subdomains, return only the main domain and TLD
            # サブドメインを含む場合は、メインドメインと TLD のみを返す
            return '.'.join(parts[-2:])
        return domain
    
    def _is_valid_path(self, url):
        """
        URLがpath_prefixに一致するかチェック
        
        Args:
            url (str): チェックするURL
            
        Returns:
            bool: パスが一致するか
        """
        if not self.path_prefix:
            return True  # If path_prefix is not specified, allow all URLs
            
        return url.startswith(self.path_prefix)
    
    def setup_database(self):
        """
        URL 追跡データベースをセットアップ
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create a table to track crawled URLs
        # クロール済み URL を追跡するテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawled_urls (
            url TEXT PRIMARY KEY,
            content_hash TEXT,
            first_crawled_at TIMESTAMP,
            last_crawled_at TIMESTAMP,
            change_count INTEGER DEFAULT 0,
            status INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
        self.log(f"Database setup completed: {self.db_path}", self.log_level)
    
    def should_crawl_url(self, url):
        """
        Determine if URL should be crawled

        Args:
            url (str): URL to check
            
        Returns:
            tuple: (should crawl, existing hash, last crawled at, status)
        
        URL をクロールすべきかを判断
        
        Args:
            url (str): チェックする URL
            
        Returns:
            tuple: (クロールすべきか, 既存のハッシュ値, last_crawled_at, status)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT content_hash, last_crawled_at, status FROM crawled_urls WHERE url = ?", (url,))
        result = cursor.fetchone()
        conn.close()
        
        # Uncrawled URL
        # 未クロールの URL
        if not result:
            return True, None, None, None
        
        existing_hash, last_crawled_str, status = result
        
        # Refresh mode based judgment
        # リフレッシュモードに基づいて判断
        if self.refresh_mode == 'force':
            return True, existing_hash, last_crawled_str, status
        elif self.refresh_mode == 'none':
            return False, existing_hash, last_crawled_str, status
        elif self.refresh_mode == 'auto':
            last_crawled = datetime.datetime.fromisoformat(last_crawled_str)
            days_since_crawl = (datetime.datetime.now() - last_crawled).days
            return days_since_crawl >= self.refresh_days, existing_hash, last_crawled_str, status
        
        # Default is not to crawl
        # デフォルトはクロールしない
        return False, existing_hash, last_crawled_str, status
    
    def update_url_database(self, url, content_hash, status):
        """
        Update the URL database

        Args:
            url (str): URL to update
            content_hash (str): Content hash
            status (int): HTTP status code
        
        URL データベースを更新
        
        Args:
            url (str): 更新する URL
            content_hash (str): コンテンツのハッシュ値
            status (int): HTTP ステータスコード
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute("SELECT content_hash, change_count FROM crawled_urls WHERE url = ?", (url,))
        result = cursor.fetchone()
        
        if not result:
            # New URL
            # 新規 URL の場合
            cursor.execute(
                "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
                (url, content_hash, now, now, 0, status)
            )
        else:
            existing_hash, change_count = result
            # Hash changed
            # ハッシュが変わった場合は変更回数を増やす
            if existing_hash != content_hash:
                change_count += 1
            
            cursor.execute(
                "UPDATE crawled_urls SET content_hash = ?, last_crawled_at = ?, change_count = ?, status = ? WHERE url = ?",
                (content_hash, now, change_count, status, url)
            )
        
        conn.commit()
        conn.close()
    
    def calculate_content_hash(self, content):
        """
        Calculate the content hash

        Args:
            content (str): Content to hash
            
        Returns:
            str: SHA-256 hash value

        コンテンツのハッシュ値を計算
        
        Args:
            content (str): ハッシュ化するコンテンツ
            
        Returns:
            str: SHA-256 ハッシュ値
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def _is_same_domain(self, url):
        """
        Check if URL belongs to the allowed domain

        Args:
            url (str): URL to check
            
        Returns:
            bool: Whether it belongs to the same domain
        
        URL が許可されたドメインに属しているかチェック
        
        Args:
            url (str): チェックする URL
            
        Returns:
            bool: 同一ドメインに属しているか
        """
        parsed_url = urlparse(url)
        url_domain = parsed_url.netloc
        
        if self.ignore_subdomains:
            url_top_domain = self._get_top_domain(url_domain)
            return url_top_domain == self.top_domain
        else:
            return url_domain in self.allowed_domains
    
    def _is_robots_allowed(self, response):
        """
        Check if crawling is allowed by the robots meta tag

        Args:
            response (Response): Response object
            
        Returns:
            bool: Whether crawling is allowed

        robots メタタグでクロールが許可されているかチェック
        
        Args:
            response (Response): レスポンスオブジェクト
            
        Returns:
            bool: クロールが許可されているか
        """
        if not self.prime_directive:
            return True
        
        robots_meta = response.xpath('//meta[@name="robots"]/@content').get()
        if robots_meta:
            if 'noindex' in robots_meta.lower():
                self.log(f"Skipping {response.url} due to robots meta noindex", logging.DEBUG)
                return False
        
        return True
    
    def extract_content(self, response):
        """
        Extract the main content

        Args:
            response (Response): Response object
            
        Returns:
            str: Extracted main content

        メインコンテンツを抽出
        
        Args:
            response (Response): レスポンスオブジェクト
            
        Returns:
            str: 抽出されたメインコンテンツ
        """
        # コンテンツモードがbodyの場合は、bodyタグ全体を取得
        if self.content_mode == 'body':
            body_content = response.xpath('//body').get()
            if body_content:
                return self._clean_html(body_content)
            return self._clean_html(response.text)
            
        # コンテンツモードがautoまたはその他の場合は、通常の抽出ロジックを使用
        # コンテンツ抽出の優先順位
        # 1. main タグ
        # 2. article タグ
        # 3. .content または #content
        # 4. .main または #main
        # 5. body タグ（最後の手段）
        
        main_content = response.xpath('//main').get()
        if main_content:
            return self._clean_html(main_content)
        
        article_content = response.xpath('//article').get()
        if article_content:
            return self._clean_html(article_content)
        
        content_div = response.css('.content, #content').get()
        if content_div:
            return self._clean_html(content_div)
        
        main_div = response.css('.main, #main').get()
        if main_div:
            return self._clean_html(main_div)
        
        # 最後の手段として body コンテンツを使用
        body_content = response.xpath('//body').get()
        if body_content:
            return self._clean_html(body_content)
        
        # 何も見つからない場合は HTML 全体を返す
        return self._clean_html(response.text)
    
    def _clean_html(self, html):
        """
        Remove scripts and styles from HTML

        Args:
            html (str): Original HTML
            
        Returns:
            str: Cleaned HTML

        HTML からスクリプトやスタイルを削除
        
        Args:
            html (str): 元の HTML
            
        Returns:
            str: クリーンアップされた HTML
        """
        # script と style タグを削除
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL)
        
        # コメントを削除
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # 連続する空白を削除
        html = re.sub(r'\s+', ' ', html)
        
        return html.strip()
    
    def get_content_status(self, current_hash, previous_hash):
        """
        Determine the content status

        Args:
            current_hash (str): Current hash value
            previous_hash (str): Previous hash value
            
        Returns:
            str: new, updated, or unchanged

        コンテンツの状態を判定
        
        Args:
            current_hash (str): 現在のハッシュ値
            previous_hash (str): 以前のハッシュ値
            
        Returns:
            str: new, updated, または unchanged
        """
        if not previous_hash:
            return "new"
        elif current_hash != previous_hash:
            return "updated"
        else:
            return "unchanged"
    
    def start_requests(self):
        """
        Generate crawl start requests
        クロール開始リクエストを生成
        """
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse_item, dont_filter=True)
    
    def parse_item(self, response):
        """
        Process the page
        ページの処理
        """
        url = response.url
        url_clean = url_query_cleaner(url)
        
        # Skip if robots meta tag does not allow
        # robots メタタグが許可しない場合はスキップ
        if not self._is_robots_allowed(response):
            self.log(f"Skipping {url} due to robots restrictions", self.log_level)
            return
            
        # Check path_prefix restriction
        # path_prefix 制限をチェック
        if not self._is_valid_path(url_clean):
            self.log(f"Skipping {url} due to path_prefix restrictions", self.log_level)
            return
        
        # Extract content and calculate hash
        # コンテンツの抽出とハッシュ計算
        content = self.extract_content(response)
        content_hash = self.calculate_content_hash(content)
        
        # Get title and meta description
        # タイトルとメタ説明の取得
        title = response.css('title::text').get() or ""
        meta_description = response.xpath('//meta[@name="description"]/@content').get() or ""
        
        # Get robots meta tag information
        # robots メタタグ情報
        robots_meta = response.xpath('//meta[@name="robots"]/@content').get() or ""
        
        # Get content status
        # 既存のハッシュ値を取得
        should_crawl, previous_hash, last_crawled_at, status = self.should_crawl_url(url_clean)
        
        # Get content status
        # コンテンツステータス
        content_status = self.get_content_status(content_hash, previous_hash)
        
        # Generate results for JSONL output regardless of whether to crawl
        # クロールするかどうかに関わらず、JSONLに出力するための結果を生成
        if not should_crawl and previous_hash and self.output_cache:
            # Output information from cache if already crawled and not re-crawling
            # すでにクロール済みで再クロールしない場合はキャッシュから情報を出力
            self.log(f"Using cached data for {url}", self.log_level)
            yield {
                "url": url_clean,
                "title": title.strip(),
                "meta_description": meta_description.strip(),
                "content": content,
                "content_hash": previous_hash,
                "crawled_at": last_crawled_at,
                "status": status,
                "length": len(content),
                "robots_meta": robots_meta,
                "content_status": content_status
            }
        elif should_crawl or not previous_hash:
            # Update DB and then output if new or update needed
            # Update URL database
            # 新規または更新が必要な場合はDBを更新してから出力
            # URL データベースの更新
            self.update_url_database(url_clean, content_hash, response.status)
            
            # 結果の生成
            yield {
                "url": url_clean,
                "title": title.strip(),
                "meta_description": meta_description.strip(),
                "content": content,
                "content_hash": content_hash,
                "crawled_at": datetime.datetime.now().isoformat(),
                "status": response.status,
                "length": len(content),
                "robots_meta": robots_meta,
                "content_status": content_status
            }
        
        # Extract links and request next pages
        # リンクの抽出と次のページのリクエスト
        links = self.link_extractor.extract_links(response)
        for link in links:
            # Check nofollow
            # nofollow チェック（prime_directive が有効な場合）
            if self.prime_directive and 'nofollow' in (link.attrs.get('rel', '') if hasattr(link, 'attrs') else getattr(link, 'rel', '')):
                continue
                
            link_url = link.url
            
            # Remove query parameters
            # クエリパラメータを削除したクリーンな URL
            clean_url = url_query_cleaner(link_url)
            
            # Check if same domain
            # 同一ドメインチェック
            if not self._is_same_domain(clean_url):
                continue
                
            # Check if it should be crawled
            # クロールすべきかチェック
            should_crawl, _, _, _ = self.should_crawl_url(clean_url)
            if should_crawl:
                yield scrapy.Request(link_url, callback=self.parse_item)
    
    def closed(self, reason):
        """
        Process when the crawler is closed
        クローラー終了時の処理
        """
        self.log(f"Spider closed: {reason}", self.log_level)
        
        # Display crawl statistics
        # クロール統計情報の表示
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM crawled_urls")
        total_urls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crawled_urls WHERE change_count > 0")
        changed_urls = cursor.fetchone()[0]
        
        self.log(f"Total crawled URLs: {total_urls}", self.log_level)
        self.log(f"URLs with changes: {changed_urls}", self.log_level)
        
        conn.close()
