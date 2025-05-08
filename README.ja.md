# PageCrunch

**AI データソース向け高性能ウェブクローラー：特定のセクションを効率的にクロールし、AI トレーニング用の JSONL 形式で出力、HTML から Markdown への変換機能付き**

---

## ✨ 主な機能

| 機能               | 説明                                                              |
|-------------------|-----------------------------------------------------------------|
| ターゲット指定クローリング | ドメインとパスプレフィックスを指定して特定のセクションのみを収集                   |
| コンテンツ変更検出     | SHA-256 ハッシュと SQLite を使用した効率的な重複検出と変更追跡             |
| 単一ファイルスパイダー  | `scrapy runspider page_crunch.py` で実行。プロジェクト構造不要           |
| ロボット排除プロトコル対応 | robots.txt と各種メタタグを適切に処理。PrimeDirective によるアクセス制御   |
| HTML から Markdown への変換 | 収集した HTML コンテンツをカスタマイズ可能なオプションでクリーンな Markdown 形式に変換 |
| コンテンツ抽出モード   | 自動コンテンツ検出またはフル body 抽出を選択可能                         |
| エラー耐性          | DNS ルックアップの問題やその他のネットワーク問題に対する堅牢なエラー処理         |
| 高度なカスタマイズ     | スパイダー属性または CLI 引数として公開される様々なパラメータ                |

---

## 📦 インストール

### 要件

* Python ≥ 3.9
* pip & venv（Debian/Ubuntu/WSL では `sudo apt install python3-pip python3-venv`）
* 対象サイトへのインターネット接続 😉

```bash
# クローン（またはコピー）
mkdir pagecrunch && cd pagecrunch
cp /path/to/page_crunch.py .
cp /path/to/html_to_markdown.py .

# 仮想環境の作成（強く推奨）
python3 -m venv .venv
source .venv/bin/activate

# Scrapy と関連パッケージのインストール
pip install --upgrade pip scrapy html2text
```

テスト実行用の追加パッケージ：

```bash
pip install coverage pytest pytest-cov
```

---

## 🚀 使用方法

```bash
# 基本: Astro ドキュメントサイトをクロール → example.jsonl
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/ \
  -a domain=example.com \
  -o example.jsonl
```

### Markdown 変換を使用

```bash
# クロール中に HTML を Markdown に変換
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/ \
  -a domain=example.com \
  -a convert_markdown=true \
  -o astro_markdown.jsonl
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
  -a content_mode=auto \
  -a convert_markdown=true \
  -a markdown_heading=atx \
  -a markdown_preserve_images=true \
  -a markdown_ignore_links=false \
  -a prime_directive=true \
  -o output.jsonl
```

### 出力形式（JSONL）

#### 基本出力（Markdown 変換なし）

```jsonc
{
  "url": "https://example.com/page",
  "title": "ページタイトル",
  "meta_description": "メタ説明",
  "content": "抽出されたメインコンテンツ",
  "content_hash": "SHA-256 ハッシュ値",
  "crawled_at": "2025-05-07T13:44:35.675979",
  "status": 200,
  "length": 151394,
  "robots_meta": "",
  "content_status": "new"  // new, updated, unchanged
}
```

#### Markdown 変換あり

```jsonc
{
  "url": "https://example.com/page",
  "title": "ページタイトル",
  "meta_description": "メタ説明",
  "content": "抽出されたメイン HTML コンテンツ",
  "content_hash": "SHA-256 ハッシュ値",
  "crawled_at": "2025-05-07T13:44:35.675979",
  "status": 200,
  "length": 151394,
  "robots_meta": "",
  "content_status": "new",
  "markdown_content": "# ページタイトル\n\n変換された markdown コンテンツ",
  "markdown_hash": "Markdown コンテンツの SHA-256 ハッシュ",
  "markdown_length": 8976
}
```

各行は独立した JSON オブジェクトになっており、ベクトルデータベースや AI トレーニングパイプラインへの読み込みに最適です。

### URL 追跡データベース

PageCrunch は URL 追跡用の SQLite データベースを作成・維持します。データベースには以下の主要機能があります：

* コンテンツハッシュ、Markdown ハッシュ、タイムスタンプとともに訪問した各 URL を保存
* 後続の実行で同じ URL を再訪問することを防止
* 異なる URL での重複コンテンツを検出
* 時間の経過に伴うコンテンツの変更を追跡

データベースに直接クエリを実行できます：

```bash
sqlite3 example_urls.db "SELECT url, last_crawled_at, change_count FROM crawled_urls ORDER BY last_crawled_at DESC LIMIT 10;"
```

---

## ⚙️ スパイダーパラメータ

### 基本パラメータ

| パラメータ        | デフォルト値   | 説明                                                |
|----------------|--------------|----------------------------------------------------|
| `start_url`     | (必須)        | クロール開始 URL（サブツリーのルートを指定）                 |
| `domain`        | (必須)        | クロール対象ドメイン（例：example.com）                  |
| `ignore_subdomains` | `true`   | サブドメインを同じドメインとして扱うかどうか               |
| `refresh_mode`  | `auto`      | 再クロール動作：auto/force/none                       |
| `refresh_days`  | `7`         | 自動再クロールの閾値日数                               |
| `db_path`       | (自動生成)     | URL 追跡用 SQLite データベースのパス                   |
| `path_prefix`   | `null`      | このパスプレフィックスに一致する URL のみをクロール         |
| `output_cache`  | `true`      | キャッシュされたページを結果に出力するかどうか              |
| `content_mode`  | `auto`      | コンテンツ抽出モード：auto/body                        |
| `prime_directive` | `true`    | ロボット排除プロトコルへの厳格な準拠を有効/無効にする        |

### Markdown 変換パラメータ

| パラメータ                    | デフォルト値 | 説明                                      |
|----------------------------|---------|------------------------------------------|
| `convert_markdown`         | `false` | HTML を Markdown に変換するかどうか            |
| `markdown_heading`         | `atx`   | 見出しスタイル：atx (#) または setext (===)     |
| `markdown_preserve_images` | `true`  | 画像参照を保持するかどうか                      |
| `markdown_preserve_tables` | `true`  | テーブル構造を保持するかどうか                    |
| `markdown_ignore_links`    | `false` | 出力でリンクを無視するかどうか                    |
| `markdown_code_highlighting` | `true` | コードハイライトのヒントを保持するかどうか           |

---

## 🔍 コンテンツ抽出モード

PageCrunch は次の2つのコンテンツ抽出モードを提供します：

1. `auto`（デフォルト）：次の優先順位でメインコンテンツをインテリジェントに抽出します：
   - `<main>` タグ
   - `<article>` タグ
   - `.content` または `#content` 要素
   - `.main` または `#main` 要素
   - `<body>` タグ（最後の手段として）

2. `body`：`<body>` タグの内容全体を抽出します

モードに関係なく、スクリプト、スタイル、HTML コメントは常に削除されます。

## 📝 HTML から Markdown への変換

`convert_markdown=true` の場合、PageCrunch は抽出された HTML コンテンツを `html2text` ライブラリと拡張された前処理/後処理を使用して、より良い結果のためのクリーンな Markdown 形式に変換します。

Markdown コンバーターの主な機能：

- 見出しスタイルオプション：ATX (#) または Setext (===)
- 言語ヒント付きの適切なコードブロックフォーマット
- テーブル形式の保持
- 画像とリンクの処理オプション
- コードハイライト用の特別な処理

---

## 🛠 開発ノート

* **パフォーマンス** – WSL で実行する場合、より高速な I/O のために、プロジェクトを `/mnt/c/...` ではなく Linux ホーム（`~/projects/pagecrunch`）に配置してください。
* **拡張機能** – カスタムコンテンツ抽出やメタデータ処理を追加できます。
* **エラー処理** - クローラーには DNS ルックアップの問題やその他のネットワーク問題に対する堅牢なエラー処理が含まれており、一部の URL にアクセスできない場合でもクロールを継続できます。

### テストの実行

単体テストの実行：

```bash
python run_tests.py
```

これにより、カバレッジレポートも生成されます。

---

## 🤝 貢献

プルリクエスト歓迎します！大きな変更については、まず問題を開いて議論してください。

1. フォーク → 機能ブランチ → PR
2. 実用的なテストケースを追加
3. コードスタイルチェック（flake8/black）に合格

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

ハッピークローリング！ 🕷️
