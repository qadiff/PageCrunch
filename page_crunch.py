#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
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
    name = 'page_crunch'
    
    def __init__(self, start_url=None, domain=None, ignore_subdomains='true',
                 refresh_mode='auto', refresh_days=7, db_path=None, 
                 prime_directive='true', *args, **kwargs):
        """
        初期化メソッド
        
        Args:
            start_url (str): クロール開始 URL
            domain (str): 許可ドメイン
            ignore_subdomains (str): サブドメインを同じドメインとして扱うか (true/false)
            refresh_mode (str): auto/force/none - 再クロール動作の設定
            refresh_days (int): 再クロールの日数閾値
            db_path (str): URL 追跡データベースのパス
            prime_directive (str): ロボット排除プロトコルを遵守するか (true/false)
        """
        # 必須パラメータのチェック
        if not start_url:
            raise NotConfigured('start_url is required')
        if not domain:
            parsed_url = urlparse(start_url)
            domain = parsed_url.netloc
        
        # パラメータの設定
        self.start_urls = [start_url]
        self.allowed_domains = [domain]
        self.ignore_subdomains = ignore_subdomains.lower() == 'true'
        self.refresh_mode = refresh_mode.lower()
        self.refresh_days = int(refresh_days)
        self.prime_directive = prime_directive.lower() == 'true'
        
        # ドメイン設定の処理
        self.top_domain = self._get_top_domain(domain)
        if self.ignore_subdomains:
            self.allowed_domains = [self.top_domain]
            
        # データベース設定
        self.db_path = db_path or f"{domain.replace('.', '_')}_urls.db"
        
        # リンク抽出設定
        self.link_extractor = LinkExtractor(allow_domains=self.allowed_domains)
        
        # CrawlSpiderのルールをオーバーライド（空にする）
        self.rules = ()
        
        # 親クラスの初期化を最後に行う
        super(PageCrunchSpider, self).__init__(*args, **kwargs)
        
        # データベースのセットアップ
        self.setup_database()
        
        # ログメッセージ
        self.log(f"Spider initialized with parameters:", logging.INFO)
        self.log(f"  start_url: {start_url}", logging.INFO)
        self.log(f"  domain: {domain}", logging.INFO)
        self.log(f"  ignore_subdomains: {self.ignore_subdomains}", logging.INFO)
        self.log(f"  refresh_mode: {self.refresh_mode}", logging.INFO)
        self.log(f"  refresh_days: {self.refresh_days}", logging.INFO)
        self.log(f"  db_path: {self.db_path}", logging.INFO)
        self.log(f"  prime_directive: {self.prime_directive}", logging.INFO)
    
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
            # サブドメインを含む場合は、メインドメインと TLD のみを返す
            return '.'.join(parts[-2:])
        return domain
    
    def setup_database(self):
        """
        URL 追跡データベースをセットアップ
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        self.log(f"Database setup completed: {self.db_path}", logging.INFO)
    
    def should_crawl_url(self, url):
        """
        URL をクロールすべきかを判断
        
        Args:
            url (str): チェックする URL
            
        Returns:
            tuple: (クロールすべきか, 既存のハッシュ値)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT content_hash, last_crawled_at FROM crawled_urls WHERE url = ?", (url,))
        result = cursor.fetchone()
        conn.close()
        
        # 未クロールの URL
        if not result:
            return True, None
        
        existing_hash, last_crawled_str = result
        
        # リフレッシュモードに基づいて判断
        if self.refresh_mode == 'force':
            return True, existing_hash
        elif self.refresh_mode == 'none':
            return False, existing_hash
        elif self.refresh_mode == 'auto':
            last_crawled = datetime.datetime.fromisoformat(last_crawled_str)
            days_since_crawl = (datetime.datetime.now() - last_crawled).days
            return days_since_crawl >= self.refresh_days, existing_hash
        
        # デフォルトはクロールしない
        return False, existing_hash
    
    def update_url_database(self, url, content_hash, status):
        """
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
            # 新規 URL の場合
            cursor.execute(
                "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
                (url, content_hash, now, now, 0, status)
            )
        else:
            existing_hash, change_count = result
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
        メインコンテンツを抽出
        
        Args:
            response (Response): レスポンスオブジェクト
            
        Returns:
            str: 抽出されたメインコンテンツ
        """
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
        クロール開始リクエストを生成
        """
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse_item, dont_filter=True)
    
    def parse_item(self, response):
        """
        ページの処理
        """
        url = response.url
        url_clean = url_query_cleaner(url)
        
        # robots メタタグが許可しない場合はスキップ
        if not self._is_robots_allowed(response):
            self.log(f"Skipping {url} due to robots restrictions", logging.INFO)
            return
        
        # コンテンツの抽出
        content = self.extract_content(response)
        content_hash = self.calculate_content_hash(content)
        
        # タイトルとメタ説明の取得
        title = response.css('title::text').get() or ""
        meta_description = response.xpath('//meta[@name="description"]/@content').get() or ""
        
        # robots メタタグ情報
        robots_meta = response.xpath('//meta[@name="robots"]/@content').get() or ""
        
        # 既存のハッシュ値を取得
        _, previous_hash = self.should_crawl_url(url_clean)
        
        # コンテンツステータス
        content_status = self.get_content_status(content_hash, previous_hash)
        
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
        
        # リンクの抽出と次のページのリクエスト
        links = self.link_extractor.extract_links(response)
        for link in links:
            # nofollow チェック（prime_directive が有効な場合）
            if self.prime_directive and 'nofollow' in (link.attrs.get('rel', '') if hasattr(link, 'attrs') else getattr(link, 'rel', '')):
                continue
                
            link_url = link.url
            
            # クエリパラメータを削除したクリーンな URL
            clean_url = url_query_cleaner(link_url)
            
            # 同一ドメインチェック
            if not self._is_same_domain(clean_url):
                continue
                
            # クロールすべきかチェック
            should_crawl, _ = self.should_crawl_url(clean_url)
            if should_crawl:
                yield scrapy.Request(link_url, callback=self.parse_item)
    
    def closed(self, reason):
        """
        クローラー終了時の処理
        """
        self.log(f"Spider closed: {reason}", logging.INFO)
        
        # クロール統計情報の表示
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM crawled_urls")
        total_urls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crawled_urls WHERE change_count > 0")
        changed_urls = cursor.fetchone()[0]
        
        self.log(f"Total crawled URLs: {total_urls}", logging.INFO)
        self.log(f"URLs with changes: {changed_urls}", logging.INFO)
        
        conn.close()
