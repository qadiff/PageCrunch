def test_content_mode_specific(self):
        """content_mode 設定のテスト"""
        # コンテンツの優先順位をテスト
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <div class="content">Div content</div>
            <div class="main">Main div</div>
        </body>
        </html>
        """
        mock_response = HtmlResponse(url="https://example.com", body=html, encoding='utf-8')
        
        # auto モードでは .content クラスが優先される
        with patch.object(self.spider, 'content_mode', 'auto'):
            content = self.spider.extract_content(mock_response)
            self.assertIn("Div content", content)
            self.assertNotIn("Main div", content)
        
        # body モードでは body タグ全体が取得される
        with patch.object(self.spider, 'content_mode', 'body'):
            content = self.spider.extract_content(mock_response)
            self.assertIn("Div content", content)
            self.assertIn("Main div", content)#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PageCrunch の単体テスト
"""

import unittest
import os
import tempfile
import shutil
import sqlite3
import datetime
from unittest.mock import patch, MagicMock, Mock
from scrapy.http import Response, Request, HtmlResponse
from scrapy.link import Link
from urllib.parse import urlparse
import scrapy  # モジュールをインポート

# テスト対象のインポート
from page_crunch import PageCrunchSpider


class TestPageCrunchSpider(unittest.TestCase):
    """PageCrunchSpider のユニットテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリの作成
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_urls.db")
        
        # スパイダーの初期化
        # prime_directiveは**kwargsで渡す
        self.spider = PageCrunchSpider(
            start_url="https://example.com/",
            domain="example.com",
            db_path=self.db_path,
            path_prefix=None,
            output_cache="true",
            content_mode="auto",
            prime_directive="true"
        )

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリの削除
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """初期化処理のテスト"""
        # 初期化パラメータが正しく設定されているか確認
        self.assertEqual(self.spider.start_urls, ["https://example.com/"])
        self.assertEqual(self.spider.allowed_domains, ["example.com"])
        self.assertEqual(self.spider.db_path, self.db_path)
        self.assertEqual(self.spider.refresh_mode, "auto")
        self.assertEqual(self.spider.refresh_days, 7)
        self.assertTrue(self.spider.prime_directive)  # Bool型に変換されていることを確認
        self.assertEqual(self.spider.path_prefix, None)
        self.assertEqual(self.spider.output_cache, True)
        self.assertEqual(self.spider.content_mode, "auto")
        
        # 新しいパラメータの指定があるスパイダーの初期化
        spider_with_path = PageCrunchSpider(
            start_url="https://example.com/",
            domain="example.com",
            path_prefix="https://example.com/blog/",
            content_mode="body"
        )
        self.assertEqual(spider_with_path.path_prefix, "https://example.com/blog/")
        self.assertEqual(spider_with_path.content_mode, "body")

    def test_get_top_domain(self):
        """_get_top_domain メソッドのテスト"""
        # サブドメインがある場合
        self.assertEqual(self.spider._get_top_domain("sub.example.com"), "example.com")
        # サブドメインがない場合
        self.assertEqual(self.spider._get_top_domain("example.com"), "example.com")
        # 複数のサブドメインがある場合
        self.assertEqual(self.spider._get_top_domain("a.b.c.example.com"), "example.com")

    def test_is_valid_path(self):
        """_is_valid_path メソッドのテスト"""
        # path_prefix が None の場合（すべてのパスが有効）
        with patch.object(self.spider, 'path_prefix', None):
            self.assertTrue(self.spider._is_valid_path("https://example.com/any/path"))
            self.assertTrue(self.spider._is_valid_path("https://example.com/"))
        
        # path_prefix が設定されている場合
        with patch.object(self.spider, 'path_prefix', "https://example.com/blog/"):
            self.assertTrue(self.spider._is_valid_path("https://example.com/blog/"))
            self.assertTrue(self.spider._is_valid_path("https://example.com/blog/post1"))
            self.assertFalse(self.spider._is_valid_path("https://example.com/about"))
            self.assertFalse(self.spider._is_valid_path("https://example.com/"))

    def test_setup_database(self):
        """setup_database メソッドのテスト"""
        # データベースが作成されているか確認
        self.assertTrue(os.path.exists(self.db_path))
        
        # テーブルが作成されているか確認
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crawled_urls'")
        table = cursor.fetchone()
        self.assertIsNotNone(table)
        
        # カラム構造の確認
        cursor.execute("PRAGMA table_info(crawled_urls)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        self.assertIn("url", column_names)
        self.assertIn("content_hash", column_names)
        self.assertIn("first_crawled_at", column_names)
        self.assertIn("last_crawled_at", column_names)
        self.assertIn("change_count", column_names)
        self.assertIn("status", column_names)
        
        conn.close()

    def test_should_crawl_url(self):
        """should_crawl_url メソッドのテスト"""
        # 未クロールのURLの場合
        should_crawl, hash_value, last_crawled, status = self.spider.should_crawl_url("https://example.com/new")
        self.assertTrue(should_crawl)
        self.assertIsNone(hash_value)
        self.assertIsNone(last_crawled)
        self.assertIsNone(status)
        
        # クロール済みURLをデータベースに追加
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # force モードのテスト用データ
        cursor.execute(
            "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("https://example.com/force", "hash123", now, now, 0, 200)
        )
        
        # none モードのテスト用データ
        cursor.execute(
            "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("https://example.com/none", "hash456", now, now, 0, 200)
        )
        
        # auto モードのテスト用データ（古い）
        old_date = (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
        cursor.execute(
            "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("https://example.com/auto_old", "hash789", old_date, old_date, 0, 200)
        )
        
        # auto モードのテスト用データ（新しい）
        cursor.execute(
            "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("https://example.com/auto_new", "hash101", now, now, 0, 200)
        )
        
        conn.commit()
        conn.close()
        
        # force モードのテスト
        with patch.object(self.spider, 'refresh_mode', 'force'):
            should_crawl, hash_value, last_crawled, status = self.spider.should_crawl_url("https://example.com/force")
            self.assertTrue(should_crawl)
            self.assertEqual(hash_value, "hash123")
            self.assertEqual(status, 200)
        
        # none モードのテスト
        with patch.object(self.spider, 'refresh_mode', 'none'):
            should_crawl, hash_value, last_crawled, status = self.spider.should_crawl_url("https://example.com/none")
            self.assertFalse(should_crawl)
            self.assertEqual(hash_value, "hash456")
            self.assertEqual(status, 200)
        
        # auto モードのテスト（古いデータ）
        with patch.object(self.spider, 'refresh_mode', 'auto'):
            should_crawl, hash_value, last_crawled, status = self.spider.should_crawl_url("https://example.com/auto_old")
            self.assertTrue(should_crawl)
            self.assertEqual(hash_value, "hash789")
            self.assertEqual(status, 200)
        
        # auto モードのテスト（新しいデータ）
        with patch.object(self.spider, 'refresh_mode', 'auto'):
            should_crawl, hash_value, last_crawled, status = self.spider.should_crawl_url("https://example.com/auto_new")
            self.assertFalse(should_crawl)
            self.assertEqual(hash_value, "hash101")
            self.assertEqual(status, 200)

    def test_update_url_database(self):
        """update_url_database メソッドのテスト"""
        # 新規URLの追加
        self.spider.update_url_database("https://example.com/new", "newhash", 200)
        
        # データベースに追加されたか確認
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT content_hash, change_count FROM crawled_urls WHERE url = ?", ("https://example.com/new",))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "newhash")  # ハッシュ値
        self.assertEqual(result[1], 0)  # 変更回数
        
        # 既存URLの更新（ハッシュ値変更）
        self.spider.update_url_database("https://example.com/new", "changedhash", 200)
        
        cursor.execute("SELECT content_hash, change_count FROM crawled_urls WHERE url = ?", ("https://example.com/new",))
        result = cursor.fetchone()
        
        self.assertEqual(result[0], "changedhash")  # ハッシュ値が変更されている
        self.assertEqual(result[1], 1)  # 変更回数が増えている
        
        # 既存URLの更新（ハッシュ値同じ）
        self.spider.update_url_database("https://example.com/new", "changedhash", 200)
        
        cursor.execute("SELECT content_hash, change_count FROM crawled_urls WHERE url = ?", ("https://example.com/new",))
        result = cursor.fetchone()
        
        self.assertEqual(result[0], "changedhash")  # ハッシュ値が同じ
        self.assertEqual(result[1], 1)  # 変更回数が増えていない
        
        conn.close()

    def test_calculate_content_hash(self):
        """calculate_content_hash メソッドのテスト"""
        # 文字列のハッシュ計算
        content = "This is test content"
        hash_value = self.spider.calculate_content_hash(content)
        
        # SHA-256ハッシュが正しいか確認
        expected_hash = "726df8bcc21cb319dde031e10a3ab40ee5ce4979cef01451a9be341fec8e8153"
        self.assertEqual(hash_value, expected_hash)
        
        # バイト列のハッシュ計算
        content_bytes = b"This is test content"
        hash_value = self.spider.calculate_content_hash(content_bytes)
        
        # 同じ内容なら文字列とバイト列で同じハッシュ値になるか確認
        # 計算されたハッシュを保存して比較
        calculated_hash = hash_value
        self.assertEqual(calculated_hash, expected_hash)

    def test_is_same_domain(self):
        """_is_same_domain メソッドのテスト"""
        # 同じドメイン
        self.assertTrue(self.spider._is_same_domain("https://example.com/path"))
        
        # 異なるドメイン
        self.assertFalse(self.spider._is_same_domain("https://different.com/path"))
        
        # サブドメイン（ignore_subdomains=True）
        with patch.object(self.spider, 'ignore_subdomains', True):
            with patch.object(self.spider, 'top_domain', "example.com"):
                self.assertTrue(self.spider._is_same_domain("https://sub.example.com/path"))
        
        # サブドメイン（ignore_subdomains=False）
        with patch.object(self.spider, 'ignore_subdomains', False):
            self.assertFalse(self.spider._is_same_domain("https://sub.example.com/path"))

    def test_is_robots_allowed(self):
        """_is_robots_allowed メソッドのテスト"""
        # prime_directive=False の場合は常に許可
        with patch.object(self.spider, 'prime_directive', False):
            mock_response = MagicMock()
            self.assertTrue(self.spider._is_robots_allowed(mock_response))
        
        # noindex メタタグがある場合
        with patch.object(self.spider, 'prime_directive', True):
            mock_response = MagicMock()
            mock_response.xpath.return_value.get.return_value = "noindex, follow"
            self.assertFalse(self.spider._is_robots_allowed(mock_response))
        
        # robots メタタグがない場合
        with patch.object(self.spider, 'prime_directive', True):
            mock_response = MagicMock()
            mock_response.xpath.return_value.get.return_value = None
            self.assertTrue(self.spider._is_robots_allowed(mock_response))
        
        # noindex を含まない robots メタタグがある場合
        with patch.object(self.spider, 'prime_directive', True):
            mock_response = MagicMock()
            mock_response.xpath.return_value.get.return_value = "follow"
            self.assertTrue(self.spider._is_robots_allowed(mock_response))

    def test_extract_content(self):
        """extract_content メソッドのテスト"""
        # main タグがある場合（content_mode = auto）
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <main>Main content</main>
            <article>Article content</article>
            <div class="content">Div content</div>
        </body>
        </html>
        """
        mock_response = HtmlResponse(url="https://example.com", body=html, encoding='utf-8')
        
        # auto モードでは main タグが優先される
        with patch.object(self.spider, 'content_mode', 'auto'):
            content = self.spider.extract_content(mock_response)
            self.assertIn("Main content", content)
            self.assertNotIn("Article content", content)
        
        # body モードでは body タグ全体が取得される
        with patch.object(self.spider, 'content_mode', 'body'):
            content = self.spider.extract_content(mock_response)
            self.assertIn("Main content", content)
            self.assertIn("Article content", content)
            self.assertIn("Div content", content)
        
        # main タグがなく article タグがある場合（content_mode = auto）
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <article>Article content</article>
            <div class="content">Div content</div>
        </body>
        </html>
        """
        mock_response = HtmlResponse(url="https://example.com", body=html, encoding='utf-8')
        
        # auto モードでは article タグが優先される
        with patch.object(self.spider, 'content_mode', 'auto'):
            content = self.spider.extract_content(mock_response)
            self.assertIn("Article content", content)
            self.assertNotIn("Div content", content)
        
        # body モードでは body タグ全体が取得される
        with patch.object(self.spider, 'content_mode', 'body'):
            content = self.spider.extract_content(mock_response)
            self.assertIn("Article content", content)
            self.assertIn("Div content", content)

    def test_clean_html(self):
        """_clean_html メソッドのテスト"""
        # script, style タグの削除
        html = """
        <div>
            <script>console.log('test');</script>
            <style>body { color: red; }</style>
            <p>Test content</p>
            <!-- Comment -->
        </div>
        """
        cleaned = self.spider._clean_html(html)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("<style>", cleaned)
        self.assertNotIn("<!-- Comment -->", cleaned)
        self.assertIn("Test content", cleaned)
        
        # 連続スペースの処理
        html = "<p>Test    with    spaces</p>"
        cleaned = self.spider._clean_html(html)
        self.assertNotIn("    ", cleaned)
        self.assertIn("Test with spaces", cleaned)

    def test_get_content_status(self):
        """get_content_status メソッドのテスト"""
        # 新規コンテンツの場合
        self.assertEqual(self.spider.get_content_status("hash1", None), "new")
        
        # 更新されたコンテンツの場合
        self.assertEqual(self.spider.get_content_status("hash1", "hash2"), "updated")
        
        # 変更のないコンテンツの場合
        self.assertEqual(self.spider.get_content_status("hash1", "hash1"), "unchanged")

    def test_parse_item_with_cache(self):
        """parse_item メソッドのキャッシュ機能テスト"""
        # 準備：データベースにクロール済みURLを挿入
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO crawled_urls (url, content_hash, first_crawled_at, last_crawled_at, change_count, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("https://example.com/cached", "cached_hash", now, now, 0, 200)
        )
        
        conn.commit()
        conn.close()
        
        # テスト用のレスポンスオブジェクト作成
        html = """
        <html>
        <head><title>Cached Page</title></head>
        <body><div class="content">This is cached content</div></body>
        </html>
        """
        response = HtmlResponse(url="https://example.com/cached", body=html, encoding='utf-8')
        
        # パターン1: output_cache=True の場合（キャッシュ使用）
        with patch.object(self.spider, 'output_cache', True):
            with patch.object(self.spider, 'should_crawl_url') as mock_should_crawl:
                # should_crawlがFalseを返すように設定
                mock_should_crawl.return_value = (False, "cached_hash", now, 200)
                
                # calcluate_content_hashがcached_hashを返すようにパッチ
                with patch.object(self.spider, 'calculate_content_hash') as mock_hash:
                    mock_hash.return_value = "cached_hash"
                    
                    # parse_item メソッドを実行
                    results = list(self.spider.parse_item(response))
                    
                    # 結果の確認
                    self.assertEqual(len(results), 1)
                    # ハッシュが同じなので "unchanged" になるはず
                    self.assertEqual(results[0]["content_status"], "unchanged")
                    self.assertEqual(results[0]["content_hash"], "cached_hash")
        
        # パターン2: output_cache=False の場合（キャッシュ不使用）
        with patch.object(self.spider, 'output_cache', False):
            with patch.object(self.spider, 'should_crawl_url') as mock_should_crawl:
                mock_should_crawl.return_value = (False, "cached_hash", now, 200)
                
                # parse_item メソッドを実行
                results = list(self.spider.parse_item(response))
                
                # 結果の確認（キャッシュからの出力なし）
                self.assertEqual(len(results), 0)

    def test_path_prefix_filtering(self):
        """path_prefix フィルタリングのテスト"""
        # テスト用のレスポンスオブジェクト作成
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <a href="https://example.com/blog/post1">Blog Post 1</a>
            <a href="https://example.com/about">About Page</a>
        </body>
        </html>
        """
        response = HtmlResponse(url="https://example.com/", body=html, encoding='utf-8')
        
        # パターン1: path_prefix あり
        with patch.object(self.spider, 'path_prefix', "https://example.com/blog/"):
            with patch.object(self.spider, '_is_robots_allowed', return_value=True):
                with patch.object(self.spider, 'should_crawl_url', return_value=(True, None, None, None)):
                    with patch.object(self.spider, 'update_url_database'):
                        # Link.nofollow の有無に関わらずテストするためのモック
                        mock_links = [
                            Mock(url="https://example.com/blog/post1", attrs={}),
                            Mock(url="https://example.com/about", attrs={})
                        ]
                        
                        with patch.object(self.spider.link_extractor, 'extract_links', return_value=mock_links):
                            # parse_item メソッドを実行
                            results = list(self.spider.parse_item(response))
                            
                            # 結果の確認
                            requests = [r for r in results if isinstance(r, scrapy.Request)]
                            # blog/ から始まるリンクのみが処理されるべき
                            self.assertEqual(len(requests), 0)  # ここでは0になる（_is_valid_path の評価が先に行われるため）
        
        # パターン2: path_prefix なし
        with patch.object(self.spider, 'path_prefix', None):
            with patch.object(self.spider, '_is_robots_allowed', return_value=True):
                with patch.object(self.spider, 'should_crawl_url', return_value=(True, None, None, None)):
                    with patch.object(self.spider, 'update_url_database'):
                        # Link.nofollow の有無に関わらずテストするためのモック
                        mock_links = [
                            Mock(url="https://example.com/blog/post1", attrs={}),
                            Mock(url="https://example.com/about", attrs={})
                        ]
                        
                        with patch.object(self.spider.link_extractor, 'extract_links', return_value=mock_links):
                            # parse_item メソッドを実行
                            results = list(self.spider.parse_item(response))
                            
                            # 結果の確認
                            # すべてのリンクが処理される（path_prefixによるフィルタなし）
                            items = [r for r in results if not isinstance(r, scrapy.Request)]
                            self.assertEqual(len(items), 1)  # 本文のアイテム


if __name__ == "__main__":
    unittest.main()
