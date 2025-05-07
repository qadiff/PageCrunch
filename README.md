# PageCrunch

**Lightning‑fast subtree web scraper that distills any section of a website into clean JSONL ready for AI pipelines, with built-in URL deduplication.**

---

## ✨ Features

| Capability             | Description                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| Targeted crawl         | Restrict by domain **and** path prefix (e.g. `/blog/`) so you collect only what you need.      |
| JSON Lines output      | One page per line—perfect for stream processing, embeddings, and large‑scale RAG.              |
| Single‑file Spider     | Run with a single command: `scrapy runspider page_crunch.py`. No project scaffolding required. |
| Robots‑aware & polite  | Respects `robots.txt`; configurable `DOWNLOAD_DELAY`, concurrency, and User‑Agent.             |
| URL deduplication      | Built-in SQLite tracking to avoid duplicate URLs and content, perfect for AI training data.    |
| Content hash tracking  | Detects duplicate content at different URLs using SHA-256 hashing.                             |
| Persistent tracking    | Database persists between runs, so subsequent crawls won't revisit previously scraped URLs.    |
| Easy to tweak          | All knobs exposed as Spider attributes or CLI `-a` arguments.                                  |

---

## 📦 Installation

### Prerequisites

* Python ≥ 3.9
* pip & venv (`sudo apt install python3-pip python3-venv` on Debian/Ubuntu/WSL)
* Internet connection to fetch the target site 😉

```bash
# Clone (or copy) the repo
mkdir pagecrunch && cd pagecrunch
cp /path/to/page_crunch.py .

# Create an isolated environment (strongly recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install Scrapy (and any extras you add later)
pip install --upgrade pip scrapy
```

---

## 🚀 Usage

```bash
# Basic: crawl https://example.com/sometips/ and descendants → corpus.jsonl
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/sometips/ \
  -a domain=example.com \
  -a db_path=example_urls.db \
  -o corpus.jsonl
```

### Output format (JSONL)

```jsonc
{"url":"https://example.com/sometips/foo","title":"Foo Tips","content":"Main content text...","content_hash":"a1b2c3...","crawled_at":"2025-05-07T06:45:12.345678","status":200,"length":12345}
{"url":"https://example.com/sometips/bar","title":"Bar Tricks","content":"More content text...","content_hash":"d4e5f6...","crawled_at":"2025-05-07T06:45:15.678901","status":200,"length":6789}
```

Each line is an independent JSON object—perfect for piping into vector DB loaders or further markdown conversion scripts.

### URL Tracking Database

PageCrunch creates and maintains a SQLite database for URL tracking. The database has these key features:

* Stores each visited URL with content hash and timestamp
* Prevents revisiting the same URL in subsequent runs
* Detects duplicate content at different URLs
* Uses Write-Ahead Logging (WAL) for better performance

You can query the database directly:

```bash
sqlite3 example_urls.db "SELECT url, visited_at FROM visited_urls ORDER BY visited_at DESC LIMIT 10;"
```

---

## ⚙️ Spider Arguments

| Argument         | Default             | Description                                                             |
| ---------------- | ------------------- | ----------------------------------------------------------------------- |
| `start_url`      | (required)          | Seed URL where crawling begins (should point to the subtree root).      |
| `domain`         | (required)          | Domain to confine crawling, e.g. `example.com`.                         |
| `path_prefix`    | same as `start_url` | Absolute prefix; only URLs that start with this string are followed.    |
| `db_path`        | `pagecrunch_urls.db` | Path to SQLite database for URL tracking. Use `:memory:` for in-memory. |
| `download_delay` | `0.5`               | Seconds to wait between requests. Override via `-s DOWNLOAD_DELAY=0.1`. |
| `concurrency`    | `8`                 | Parallel requests. Override via `-s CONCURRENT_REQUESTS=16`.            |

---

## 🔍 Advanced Use Cases

### In-Memory URL Tracking

For temporary crawls without persistent URL tracking:

```bash
scrapy runspider page_crunch.py \
  -a start_url=https://docs.example.com/api/ \
  -a domain=docs.example.com \
  -a db_path=:memory: \
  -o api_docs.jsonl
```

### Content Deduplication Analysis

To analyze how much duplicate content exists on a site:

```bash
sqlite3 example_urls.db "SELECT content_hash, COUNT(*) as num_duplicates FROM visited_urls GROUP BY content_hash HAVING COUNT(*) > 1 ORDER BY num_duplicates DESC;"
```

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss substantial changes.

1. Fork ‑> Feature branch ‑> PR
2. Add test cases where practical
3. Ensure `flake8` / `black` pass

---

## 📄 License

```
Copyright 2025 Qadiff LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 📫 Contact

* **Company**: Qadiff LLC
* **Website**: [https://qadiff.com](https://qadiff.com)
* **Twitter**: @Qadiff

Happy crawling! 🕷️