# PageCrunch

**High-performance web crawler for AI data sources: Efficiently crawls specific sections and outputs in JSONL format for AI training, with HTML to Markdown conversion capabilities**

---

## ✨ Key Features

| Feature             | Description                                                                  |
|---------------------|------------------------------------------------------------------------------|
| Targeted Crawling   | Specify domains and path prefixes to collect only specific sections          |
| Content Change Detection | Efficient duplicate detection and change tracking using SHA-256 hash and SQLite |
| Single-file Spider  | Run with `scrapy runspider page_crunch.py`. No project structure needed      |
| Robots Protocol Support | Properly handles robots.txt and various meta tags. Access control with PrimeDirective |
| HTML to Markdown Conversion | Convert collected HTML content to clean Markdown format with customizable options |
| Content Extraction Mode | Choose between automatic content detection or full body extraction |
| Error Resilience | Robust error handling for DNS lookup issues and other network problems |
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
cp /path/to/html_to_markdown.py .

# Create virtual environment (strongly recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install Scrapy and related packages
pip install --upgrade pip scrapy html2text
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
  -a start_url=https://example.com/ \
  -a domain=examlpe.com \
  -o example.jsonl
```

### With Markdown Conversion

```bash
# Convert HTML to Markdown while crawling
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/ \
  -a domain=example.com \
  -a convert_markdown=true \
  -o example.jsonl
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
  -a content_mode=auto \
  -a convert_markdown=true \
  -a markdown_heading=atx \
  -a markdown_preserve_images=true \
  -a markdown_ignore_links=false \
  -o output.jsonl
```

### Output Format (JSONL)

#### Basic Output (without Markdown conversion)

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

#### With Markdown Conversion

```jsonc
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "meta_description": "Meta Description",
  "content": "Extracted Main HTML Content",
  "content_hash": "SHA-256 Hash Value",
  "crawled_at": "2025-05-07T13:44:35.675979",
  "status": 200,
  "length": 151394,
  "robots_meta": "",
  "content_status": "new",
  "markdown_content": "# Page Title\n\nConverted markdown content",
  "markdown_hash": "SHA-256 Hash of Markdown Content",
  "markdown_length": 8976
}
```

Each line is an independent JSON object - perfect for loading into vector databases or AI training pipelines.

### URL Tracking Database

PageCrunch creates and maintains a SQLite database for URL tracking. The database has these key features:

* Stores each visited URL with content hash, markdown hash, and timestamp
* Prevents revisiting the same URL in subsequent runs
* Detects duplicate content at different URLs
* Tracks content changes over time

You can query the database directly:

```bash
sqlite3 example_urls.db "SELECT url, last_crawled_at, change_count FROM crawled_urls ORDER BY last_crawled_at DESC LIMIT 10;"
```

---

## ⚙️ Spider Parameters

### Basic Parameters

| Parameter         | Default       | Description                                                |
|-------------------|--------------|------------------------------------------------------------|
| `start_url`       | (required)    | Starting URL for crawling (specify the subtree root)       |
| `domain`          | (required)    | Target domain for crawling (e.g., example.com)             |
| `ignore_subdomains` | `true`     | Whether to treat subdomains as the same domain              |
| `refresh_mode`    | `auto`        | Re-crawling behavior: auto/force/none                      |
| `refresh_days`    | `7`           | Threshold days for automatic re-crawling                   |
| `db_path`         | (auto-generated) | Path to SQLite database for URL tracking                |
| `path_prefix`     | `null`        | Only crawl URLs matching this path prefix                  |
| `output_cache`    | `true`        | Whether to output cached pages in results                  |
| `content_mode`    | `auto`        | Content extraction mode: auto/body                         |

### Markdown Conversion Parameters

| Parameter                   | Default | Description                                        |
|----------------------------|---------|----------------------------------------------------|
| `convert_markdown`           | `false` | Whether to convert HTML to Markdown               |
| `markdown_heading`           | `atx`   | Heading style: atx (#) or setext (===)           |
| `markdown_preserve_images`   | `true`  | Whether to preserve image references             |
| `markdown_preserve_tables`   | `true`  | Whether to preserve table structure              |
| `markdown_ignore_links`      | `false` | Whether to ignore links in output                |
| `markdown_code_highlighting` | `true`  | Whether to preserve code highlighting hints      |

---

## 🔍 Content Extraction Modes

PageCrunch offers two content extraction modes:

1. `auto` (default): Intelligently extracts the main content using this priority:
   - `<main>` tag
   - `<article>` tag
   - `.content` or `#content` element
   - `.main` or `#main` element
   - `<body>` tag (as a last resort)

2. `body`: Extracts the entire `<body>` tag content

Regardless of the mode, scripts, styles, and HTML comments are always removed.

## 📝 HTML to Markdown Conversion

When `convert_markdown=true`, PageCrunch converts the extracted HTML content to clean Markdown format using the `html2text` library with enhanced pre/post-processing for better results.

Key features of the Markdown converter:

- Heading style options: ATX (#) or Setext (===)
- Proper code block formatting with language hints
- Table formatting preservation
- Image and link handling options
- Special handling for code highlighting

---

## 🛠 Development Notes

* **Performance** – When running in WSL, place the project in your Linux home (`~/projects/pagecrunch`) rather than `/mnt/c/...` for faster I/O.
* **Extensions** – You can add custom content extraction or metadata processing.
* **Error Handling** - The crawler includes robust error handling for DNS lookup issues and other network problems, allowing it to continue crawling even when some URLs are inaccessible.

### Running Tests

Running unit tests:

```bash
python run_tests.py
```

This will also generate a coverage report.

---

### Overview

`split_markdown.py` is a command-line tool that splits large Markdown files into smaller chunks based on a specified size. This can be useful for managing oversized documentation, breaking down large blog posts, or handling any Markdown file that has become too large.

### Features

- Split Markdown files based on specified size
- Customizable output file prefix
- Support for various size units (KB, MB, GB)
- Option to specify output directory
- Linux-style command-line arguments

### Requirements

- Python 3.6 or higher

### Installation

1. Download the script:
   ```bash
   wget https://path/to/split_markdown.py
   ```

2. Make it executable:
   ```bash
   chmod +x split_markdown.py
   ```

### Usage

Basic usage:
```bash
./split_markdown.py -i your_large_file.md
```

All options:
```bash
./split_markdown.py -i your_large_file.md -s 500k -p chapter_ -o output_folder
```

### Command-line Arguments

| Argument | Long Form | Description | Default |
|----------|-----------|-------------|---------|
| `-i` | `--input` | Input file to split (required) | N/A |
| `-s` | `--size` | Split size (e.g., 500k, 1m, 2g) | 1m |
| `-p` | `--prefix` | Output file prefix | part_ |
| `-o` | `--output-dir` | Output directory | Current directory |

Size units:
- `k`: Kilobytes (1024 bytes)
- `m`: Megabytes (1024 kilobytes)
- `g`: Gigabytes (1024 megabytes)
- `b`: Bytes
- No unit: Bytes

### Examples

Split a file into 500KB chunks:
```bash
./split_markdown.py -i document.md -s 500k
```

Split a file into 2MB chunks with a custom prefix:
```bash
./split_markdown.py -i document.md -s 2m -p section_
```

Split a file and save chunks to a specific directory:
```bash
./split_markdown.py -i document.md -o ./split_files
```

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
