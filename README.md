# PageCrunch

**High-performance web crawler for AI data sources: Efficiently crawls specific sections and outputs in JSONL format for AI training**

---

## ✨ Key Features

| Feature             | Description                                                                  |
|---------------------|------------------------------------------------------------------------------|
| Targeted Crawling   | Specify domains and path prefixes to collect only specific sections          |
| Content Change Detection | Efficient duplicate detection and change tracking using SHA-256 hash and SQLite |
| Single-file Spider  | Run with `scrapy runspider page_crunch.py`. No project structure needed      |
| Robots Protocol Support | Properly handles robots.txt and various meta tags. Access control with PrimeDirective |
| Advanced Customization | Various parameters exposed as spider attributes or CLI arguments          |

---

## 📦 Installation

### Requirements

* Python ≥ 3.9
* pip & venv (`sudo apt install python3-pip python3-venv` on Debian/Ubuntu/WSL)
* Internet connection to the target site 😉

```bash
# Clone (or copy)
mkdir pagecrunch && cd pagecrunch
cp /path/to/page_crunch.py .

# Create virtual environment (strongly recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install Scrapy and related packages
pip install --upgrade pip scrapy
```

Additional packages for running tests:

```bash
pip install coverage pytest pytest-cov
```

---

## 🚀 Usage

```bash
# Basic: Crawl Astro documentation site → astro.jsonl
scrapy runspider page_crunch.py \
  -a start_url=https://docs.astro.build/en/getting-started/ \
  -a domain=astro.build \
  -o astro.jsonl
```

### Detailed Options

```bash
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/blog/ \
  -a domain=example.com \
  -a ignore_subdomains=true \
  -a refresh_mode=auto \
  -a refresh_days=7 \
  -a db_path=example_urls.db \
  -a prime_directive=true \
  -o output.jsonl
```

### Output Format (JSONL)

```jsonc
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "meta_description": "Meta Description",
  "content": "Extracted Main Content",
  "content_hash": "SHA-256 Hash Value",
  "crawled_at": "2025-05-07T13:44:35.675979",
  "status": 200,
  "length": 151394,
  "robots_meta": "",
  "content_status": "new"  // new, updated, unchanged
}
```

Each line is an independent JSON object - perfect for loading into vector databases or AI training pipelines.

---

## ⚙️ Spider Parameters

| Parameter         | Default       | Description                                                |
|-------------------|--------------|------------------------------------------------------------|
| `start_url`       | (required)    | Starting URL for crawling (specify the subtree root)       |
| `domain`          | (required)    | Target domain for crawling (e.g., example.com)             |
| `ignore_subdomains` | `true`     | Whether to treat subdomains as the same domain              |
| `refresh_mode`    | `auto`        | Re-crawling behavior: auto/force/none                      |
| `refresh_days`    | `7`           | Threshold days for automatic re-crawling                   |
| `db_path`         | (auto-generated) | Path to SQLite database for URL tracking                |
| `prime_directive` | `true`        | Enable/disable strict adherence to robots exclusion protocol |

---

## 🛠 Development Notes

* **Performance** – When running in WSL, place the project in your Linux home (`~/projects/pagecrunch`) rather than `/mnt/c/...` for faster I/O.
* **Extensions** – You can add custom content extraction or metadata processing.

### Running Tests

Running unit tests:

```bash
python run_tests.py
```

This will also generate a coverage report.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss.

1. Fork → Feature branch → PR
2. Add practical test cases
3. Pass code style checks (flake8/black)

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
