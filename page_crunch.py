import scrapy

class SomeTipsSpider(scrapy.Spider):
    name = "sometips"

    # ❶ クロール範囲
    start_urls      = ["https://example.com/sometips/"]
    allowed_domains = ["example.com"]
    target_prefix   = "https://example.com/sometips/"

    # ❷ 主要設定（ここで完結）
    custom_settings = {
        # 出力: 1 行 1 レコードの JSONL
        "FEEDS": {"corpus.jsonl": {"format": "jsonlines", "encoding": "utf8"}},
        # マナー
        "DOWNLOAD_DELAY": 0.3,            # 0.3 秒待って次へ
        "CONCURRENT_REQUESTS": 8,
        "LOG_LEVEL": "INFO",
        "USER_AGENT": "Mozilla/5.0 (+https://example.com/bot)"
    }

    def parse(self, response):
        # ❸ パス制限 ― /sometips/ 以外は捨てる
        if not response.url.startswith(self.target_prefix):
            return

        # ❹ ページ本体を保存（必要なら後で本文抽出）
        yield {
            "url":   response.url,
            "title": response.css("title::text").get(default="").strip(),
            "html":  response.text,        # ここを自前で Markdown 化しても OK
        }

        # ❺ 次リンクをたどる
        for href in response.css("a::attr(href)").getall():
            nxt = response.urljoin(href.split("#")[0])
            if nxt.startswith(self.target_prefix):
                yield scrapy.Request(nxt, callback=self.parse)
