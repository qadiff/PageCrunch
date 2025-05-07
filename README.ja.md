# PageCrunch

**AI データソース向け高性能ウェブクローラー：特定セクションを効率的にクロールし、AIトレーニング用にJSONL形式で出力**

---

## ✨ 主な機能

| 機能                | 説明                                                                      |
|---------------------|---------------------------------------------------------------------------|
| ターゲット指定クローリング | ドメインとパスプレフィックスを指定して特定セクションのみを収集                 |
| コンテンツ変更検出     | SHA-256ハッシュとSQLiteを使用した効率的な重複検出と変更追跡                    |
| 単一ファイルスパイダー  | `scrapy runspider page_crunch.py`で実行。プロジェクト構造不要                 |
| ロボット排除対応    | robots.txtと各種metaタグを適切に処理。PrimeDirectiveでアクセス制御               |
| 高度なカスタマイズ性   | 各種パラメータをスパイダー属性またはCLI引数として公開                          |

---

## 📦 インストール

### 必要条件

* Python ≥ 3.9
* pip & venv (`sudo apt install python3-pip python3-venv` on Debian/Ubuntu/WSL)
* クロール対象サイトへのインターネット接続 😉

```bash
# クローン（またはコピー）
mkdir pagecrunch && cd pagecrunch
cp /path/to/page_crunch.py .

# 仮想環境の作成（強く推奨）
python3 -m venv .venv
source .venv/bin/activate

# Scrapyと関連パッケージのインストール
pip install --upgrade pip scrapy
```

テスト実行のための追加パッケージ：

```bash
pip install coverage pytest pytest-cov
```

もしくは

```bash
pip install -r requirements.txt
```

---

## 🚀 使用方法

```bash
# 基本：Astroのドキュメントサイトをクロール → astro.jsonl
scrapy runspider page_crunch.py \
  -a start_url=https://docs.astro.build/en/getting-started/ \
  -a domain=astro.build \
  -o astro.jsonl
```

### 詳細オプション

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

### 出力形式 (JSONL)

```jsonc
{
  "url": "https://example.com/page",
  "title": "ページタイトル",
  "meta_description": "メタ説明",
  "content": "抽出されたメインコンテンツ",
  "content_hash": "SHA-256ハッシュ値",
  "crawled_at": "2025-05-07T13:44:35.675979",
  "status": 200,
  "length": 151394,
  "robots_meta": "",
  "content_status": "new"  // new, updated, unchanged
}
```

各行は独立したJSONオブジェクト。ベクトルDBへの読み込みやAIトレーニングパイプラインに最適です。

---

## ⚙️ スパイダーパラメータ

| パラメータ         | デフォルト      | 説明                                                     |
|-------------------|----------------|----------------------------------------------------------|
| `start_url`       | (必須)          | クロール開始URL（サブツリーのルートを指定）                |
| `domain`          | (必須)          | クロール対象ドメイン（例：example.com）                   |
| `ignore_subdomains` | `true`         | サブドメインを同じドメインとして扱うかどうか              |
| `refresh_mode`    | `auto`         | 再クロールの動作: auto/force/none                         |
| `refresh_days`    | `7`            | 自動再クロールする日数閾値                                |
| `db_path`         | (自動生成)      | URL追跡用SQLiteデータベースのパス                         |
| `prime_directive` | `true`         | ロボット排除プロトコルの厳格な遵守を有効/無効             |

---

## 🛠 開発メモ

* **パフォーマンス** – WSL環境では、プロジェクトをLinuxホーム (`~/projects/pagecrunch`) に配置し、`/mnt/c/...` を避けるとI/Oが高速化します。
* **拡張** – コンテンツ抽出やメタデータ処理を独自に追加できます。

### テスト実行

単体テストの実行:

```bash
python run_tests.py
```

これにより、カバレッジレポートも生成されます。

---

## 🤝 貢献

プルリクエスト歓迎！大きな変更を提案する場合は、まずIssueを開いてください。

1. フォーク → 機能ブランチ → PR
2. 実用的なテストケースを追加
3. コードスタイル（flake8/black）をパスすること

---

## 📄 ライセンス

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

## 📫 連絡先

* **会社**: Qadiff LLC
* **ウェブサイト**: [https://qadiff.com](https://qadiff.com)
* **Twitter**: @Qadiff

Happy crawling! 🕷️