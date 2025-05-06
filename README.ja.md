# 🇯🇵 日本語 README

**PageCrunch は、ウェブサイトの特定ディレクトリ配下のみをクローリングし、AI ワークフローで扱いやすい JSONL 形式にまとめるワンファイル Scrapy スパイダーです。**

---

## ✨ 特長

| 機能                  | 説明                                                   |
| ------------------- | ---------------------------------------------------- |
| サブツリー限定クロール         | ドメインとパスプレフィクス（例: `/blog/`）の両方で制限し、必要なページだけ取得します。     |
| JSON Lines 出力       | 1 行 1 ページでストリーム処理や大規模 RAG に最適。                       |
| 単一ファイル実行            | `scrapy runspider page_crunch.py` だけで OK、プロジェクト生成不要。 |
| Robots 尊重 & 丁寧なクロール | `robots.txt` を遵守し、待機時間や並列数を調整可能。                     |
| カスタマイズ簡単            | 引数や Spider 属性でほぼすべて設定できます。                           |

---

## 📦 インストール

### 前提

* Python 3.9 以上
* pip / venv (`sudo apt install python3-pip python3-venv`)
* ターゲットサイトへアクセスできるネットワーク

```bash
# 任意のディレクトリにコピー
mkdir pagecrunch && cd pagecrunch
cp /path/to/page_crunch.py .

# 仮想環境（推奨）
python3 -m venv .venv
source .venv/bin/activate

# Scrapy インストール
pip install --upgrade pip scrapy
```

---

## 🚀 使い方

```bash
# 例: https://example.com/sometips/ 配下をクロール → corpus.jsonl
scrapy runspider page_crunch.py \
  -a start_url=https://example.com/sometips/ \
  -a allowed_domain=example.com \
  -a path_prefix=https://example.com/sometips/ \
  -s FEEDS=corpus.jsonl:jsonlines
```

### 出力 (JSONL)

```jsonc
{"url":"https://example.com/sometips/foo","title":"Foo Tips","html":"<html>…"}
{"url":"https://example.com/sometips/bar","title":"Bar Tricks","html":"<html>…"}
```

---

## ⚙️ Spider 引数

| 引数               | デフォルト           | 説明                                           |
| ---------------- | --------------- | -------------------------------------------- |
| `start_url`      | (必須)            | クロール開始 URL（サブツリーのルート）。                       |
| `allowed_domain` | (自動推定)          | ドメイン制限。例: `example.com`。                     |
| `path_prefix`    | `start_url` と同じ | この文字列で始まる URL のみ追跡。                          |
| `download_delay` | `0.3`           | リクエスト間の待機秒数 (`-s DOWNLOAD_DELAY=0.1` で変更可)。  |
| `concurrency`    | `8`             | 同時リクエスト数 (`-s CONCURRENT_REQUESTS=16` で変更可)。 |

---

## 🛠 開発メモ

* **WSL での高速化** – Windows ドライブ (`/mnt/c`) ではなく Linux 側 (`~/projects/pagecrunch`) に配置すると I/O が速くなります。
* **拡張** – `yield` 部分を変更して Markdown 抽出やメタデータ付与を行えます。

---

## 🤝 コントリビュート

1. Fork → ブランチ作成 → PR
2. 可能ならテスト追加
3. `flake8` / `black` で整形

---

## 📄 ライセンス

本プロジェクトは Apache License 2.0 の下で提供されます。詳細は英語版 README のライセンス条項をご覧ください。

---

## 📫 お問い合わせ

* **会社名**: Qadiff LLC
* **Web**: [https://qadiff.com](https://qadiff.com)
* **Twitter**: @QadiffTech

Happy crawling! 🕷️
