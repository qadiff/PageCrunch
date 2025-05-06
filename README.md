# PageCrunch

**Lightning‑fast subtree web scraper that distills any section of a website into clean JSONL ready for AI pipelines.**

---

## ✨ Features

| Capability            | Description                                                                                    |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| Targeted crawl        | Restrict by domain **and** path prefix (e.g. `/blog/`) so you collect only what you need.      |
| JSON Lines output     | One page per line—perfect for stream processing, embeddings, and large‑scale RAG.              |
| Single‑file Spider    | Run with a single command: `scrapy runspider page_crunch.py`. No project scaffolding required. |
| Robots‑aware & polite | Respects `robots.txt`; configurable `DOWNLOAD_DELAY`, concurrency, and User‑Agent.             |
| Easy to tweak         | All knobs exposed as Spider attributes or CLI `-a` arguments.                                  |

---

## 📦 Installation

### Prerequisites

* Python ≥ 3.9
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
  -a allowed_domain=example.com \
  -a path_prefix=https://example.com/sometips/ \
  -s FEEDS=corpus.jsonl:jsonlines
```

### Output format (JSONL)

```jsonc
{"url":"https://example.com/sometips/foo","title":"Foo Tips","html":"<html>…"}
{"url":"https://example.com/sometips/bar","title":"Bar Tricks","html":"<html>…"}
```

Each line is an independent JSON object—perfect for piping into vector DB loaders or further markdown conversion scripts.

---

## ⚙️ Spider Arguments

| Argument         | Default             | Description                                                             |
| ---------------- | ------------------- | ----------------------------------------------------------------------- |
| `start_url`      | (required)          | Seed URL where crawling begins (should point to the subtree root).      |
| `allowed_domain` | (derived)           | Domain to confine crawling, e.g. `example.com`.                         |
| `path_prefix`    | same as `start_url` | Absolute prefix; only URLs that start with this string are followed.    |
| `download_delay` | `0.3`               | Seconds to wait between requests. Override via `-s DOWNLOAD_DELAY=0.1`. |
| `concurrency`    | `8`                 | Parallel requests. Override via `-s CONCURRENT_REQUESTS=16`.            |

---

## 🛠 Development notes

* **Performance** – Running under WSL? Place the project inside your Linux home (`~/projects/pagecrunch`) rather than `/mnt/c/...` for faster I/O.
* **Extending** – Swap the `yield` block for readability/markdown extraction or metadata enrichment as needed.

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

* **Company**: Qadiff LLC
* **Website**: [https://qadiff.com](https://qadiff.com)
* **Twitter**: @QadiffTech

Happy crawling! 🕷️

