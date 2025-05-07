# PageCrunch

**ウェブサイトの特定セクションを高速クロールし、URL 重複排除機能付きで AI データソースに最適な JSONL 形式で出力するスパイダー**

---

## ✨ 特長

| 機能                | 説明                                                       |
| ------------------- | ---------------------------------------------------------- |
| サブツリー限定クロール | ドメインとパスプレフィクス（例: `/blog/`）の両方で制限し、必要なページだけ取得。 |
| JSON Lines 出力     | 1行1ページ形式でストリーム処理、埋め込み、大規模RAGに最適。      |
| 単一ファイル実行      | `scrapy runspider page_crunch.py` だけで実行可能。プロジェクト生成不要。 |
| Robots 対応 & 丁寧なクロール | `robots.txt` を遵守し、待機時間や並列数を調整可能。          |
| URL 重複排除         | SQLite データベースによる URL およびコンテンツの重複回避。AI トレーニングデータに最適。 |
| コンテンツハッシュ追跡  | SHA-256 ハッシュを使用して異なる URL の重複コンテンツを検出。   |
| 永続的追跡           | データベースは実行間で保持され、過去にクロールした URL を再訪問しない。 |
| カスタマイズ簡単      | 引数や Spider 属性でほぼすべて設定可能。                      |

---

## 📦 インストール

### 前提条件

* Python 3.9 以上
* pip / venv (`sudo apt install python3-pip python3-venv` on Debian/Ubuntu/WSL)
* ターゲットサイトへアクセスできるネットワーク環境

```bash
# リポジトリをクローンまたはコピー
mkdir pagecrunch && cd pagecrunch
cp /path/to/page_crunch.py .

# 仮想環境の作成（強く推奨）
python3 -m venv .venv
source .venv/bin/activate

# Scrapy のインストール
pip install --upgrade pip scrapy
```

---

## 🚀 使い方

```bash
# 基本: https://example.com/sometips/ 配下をクロールして corpus.jsonl に出力
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/sometips/ \
  -a domain=example.com \
  -a db_path=example_urls.db \
  -o corpus.jsonl
```

### 出力形式 (JSONL)

```jsonc
{"url":"https://example.com/sometips/foo","title":"Foo Tips","content":"メインコンテンツテキスト...","content_hash":"a1b2c3...","crawled_at":"2025-05-07T06:45:12.345678","status":200,"length":12345}
{"url":"https://example.com/sometips/bar","title":"Bar Tricks","content":"さらにコンテンツテキスト...","content_hash":"d4e5f6...","crawled_at":"2025-05-07T06:45:15.678901","status":200,"length":6789}
```

各行は独立した JSON オブジェクトで、ベクターDB ローダーや追加の Markdown 変換スクリプトへのパイプに最適です。

### URL 追跡データベース

PageCrunch は URL 追跡用の SQLite データベースを作成・管理します。このデータベースには以下の特徴があります：

* 訪問済み URL をコンテンツハッシュとタイムスタンプと共に保存
* 後続の実行で同じ URL を再訪問しないよう防止
* 異なる URL での重複コンテンツを検出
* Write-Ahead Logging (WAL) を使用してパフォーマンスを向上

データベースは直接クエリ可能です：

```bash
sqlite3 example_urls.db "SELECT url, visited_at FROM visited_urls ORDER BY visited_at DESC LIMIT 10;"
```

---

## ⚙️ Spider 引数

| 引数             | デフォルト           | 説明                                           |
| ---------------- | ------------------- | ---------------------------------------------- |
| `start_url`      | (必須)               | クロール開始 URL（サブツリーのルート）。        |
| `domain`         | (必須)               | ドメイン制限（例: `example.com`）。            |
| `path_prefix`    | `start_url` と同じ   | この文字列で始まる URL のみ追跡。              |
| `db_path`        | `pagecrunch_urls.db` | URL 追跡用SQLiteデータベースのパス。`:memory:` でインメモリ使用。 |
| `download_delay` | `0.5`               | リクエスト間の待機秒数 (`-s DOWNLOAD_DELAY=0.1` で変更可)。 |
| `concurrency`    | `8`                 | 同時リクエスト数 (`-s CONCURRENT_REQUESTS=16` で変更可)。 |

---

## 🔍 高度な使用例

### インメモリ URL 追跡

永続的な URL 追跡が不要な一時的なクロールの場合：

```bash
scrapy runspider page_crunch.py \
  -a start_url=https://docs.example.com/api/ \
  -a domain=docs.example.com \
  -a db_path=:memory: \
  -o api_docs.jsonl
```

### コンテンツ重複分析

サイト上の重複コンテンツの量を分析するには：

```bash
sqlite3 example_urls.db "SELECT content_hash, COUNT(*) as num_duplicates FROM visited_urls GROUP BY content_hash HAVING COUNT(*) > 1 ORDER BY num_duplicates DESC;"
```

---

## 🛠 開発メモ

* **パフォーマンス** – WSL で実行する場合は、Windows ドライブ（`/mnt/c/...`）ではなく Linux ホーム（`~/projects/pagecrunch`）にプロジェクトを配置すると I/O が高速化します。
* **データベースメンテナンス** – 大規模クロールでは、定期的なバキューム処理を検討：`sqlite3 example_urls.db "VACUUM;"`
* **拡張** – `yield` 部分を変更して、可読性/Markdown 抽出やメタデータ強化を行うことができます。

---

## 🤝 コントリビュート

プルリクエスト歓迎です！大きな変更を加える前に、まずイシューを開いて議論してください。

1. Fork → ブランチ作成 → PR
2. 可能な場合はテストケースを追加
3. `flake8` / `black` のパスを確認

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

## 📫 お問い合わせ

* **会社名**: Qadiff LLC
* **Web**: [https://qadiff.com](https://qadiff.com)
* **Twitter**: @Qadiff

Happy crawling! 🕷️