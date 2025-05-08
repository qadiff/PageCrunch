import html2text
import re
from typing import Optional

class HtmlToMarkdownConverter:
    """
    HTML to Markdown conversion utility for PageCrunch
    Uses html2text library for efficient and reliable conversion
    
    HTMLからMarkdownへの変換ユーティリティ
    効率的で信頼性の高い変換のためにhtml2textライブラリを使用
    """
    
    def __init__(self, base_url: Optional[str] = None, 
                 heading_style: str = "atx", 
                 preserve_images: bool = True,
                 preserve_tables: bool = True,
                 ignore_links: bool = False,
                 code_highlighting: bool = True):
        """
        Initialize the HTML to Markdown converter
        
        Args:
            base_url (str, optional): Base URL for relative links
            heading_style (str): ATX (#) or Setext (===) heading style
            preserve_images (bool): Whether to preserve image references
            preserve_tables (bool): Whether to preserve table structure
            ignore_links (bool): Whether to ignore links in output
            code_highlighting (bool): Whether to preserve code highlighting hints
        
        HTMLからMarkdownへのコンバーターを初期化
        
        Args:
            base_url (str, optional): 相対リンクのベースURL
            heading_style (str): ATX (#) or Setext (===) 見出しスタイル
            preserve_images (bool): 画像参照を保持するか
            preserve_tables (bool): テーブル構造を保持するか
            ignore_links (bool): リンクを無視するか
            code_highlighting (bool): コードハイライト情報を保持するか
        """
        self.base_url = base_url
        self.heading_style = heading_style
        self.preserve_images = preserve_images
        self.preserve_tables = preserve_tables
        self.ignore_links = ignore_links
        self.code_highlighting = code_highlighting
        
        # Configure the html2text converter
        self._configure_converter()
    
    def _configure_converter(self):
        """
        Configure the html2text converter based on settings
        
        設定に基づいて html2text コンバーターを設定
        """
        self.converter = html2text.HTML2Text()
        
        # Basic configuration
        self.converter.unicode_snob = True  # Use Unicode instead of ASCII
        self.converter.body_width = 0  # No text wrapping
        
        # Image handling
        self.converter.ignore_images = not self.preserve_images
        
        # Link handling
        self.converter.ignore_links = self.ignore_links
        self.converter.protect_links = not self.ignore_links
        self.converter.skip_internal_links = False
        self.converter.inline_links = True
        
        # Table handling
        self.converter.ignore_tables = not self.preserve_tables
        self.converter.pad_tables = self.preserve_tables
        
        # Heading style
        self.converter.use_setext = self.heading_style.lower() == "setext"
        
        # Base URL for relative links
        if self.base_url:
            self.converter.baseurl = self.base_url
        
        # Force emphasis with asterisks instead of underscores
        self.converter.emphasis_mark = '*'
        self.converter.strong_mark = '**'
    
    def convert(self, html_content: str) -> str:
        """
        Convert HTML to Markdown
        
        Args:
            html_content (str): HTML content to convert
            
        Returns:
            str: Converted Markdown content
        
        HTMLをMarkdownに変換
        
        Args:
            html_content (str): 変換するHTMLコンテンツ
            
        Returns:
            str: 変換されたMarkdownコンテンツ
        """
        if not html_content:
            return ""
        
        # Pre-processing: enhance code blocks if highlighting is enabled
        if self.code_highlighting:
            html_content = self._preprocess_code_blocks(html_content)
        
        # Convert HTML to Markdown using html2text
        markdown = self.converter.handle(html_content)
        
        # Post-processing to improve the output
        markdown = self._postprocess_markdown(markdown)
        
        return markdown
    
    def _preprocess_code_blocks(self, html_content: str) -> str:
        """
        Preprocess HTML to better handle code blocks with language hints
        
        Args:
            html_content (str): HTML content
            
        Returns:
            str: Preprocessed HTML content
        
        言語ヒントを持つコードブロックをより適切に処理するためのHTML前処理
        
        Args:
            html_content (str): HTMLコンテンツ
            
        Returns:
            str: 前処理されたHTMLコンテンツ
        """
        # Handle code blocks with language hints by adding a special marker
        # <pre><code class="language-xyz"> -> <pre lang="xyz"><code>
        pattern = r'<pre><code\s+class=["\'](language-|lang-)(\w+)["\']>(.*?)</code></pre>'
        
        def code_replacement(match):
            language = match.group(2)
            code_content = match.group(3)
            # Format that html2text will convert to ```language
            return f'<pre lang="{language}"><code>{code_content}</code></pre>'
            
        html_content = re.sub(pattern, code_replacement, html_content, flags=re.DOTALL)
        
        return html_content
    
    def _postprocess_markdown(self, markdown: str) -> str:
        """
        Post-process the Markdown to improve formatting
        
        Args:
            markdown (str): Raw Markdown from html2text
            
        Returns:
            str: Refined Markdown content
        
        マークダウン出力を改善するための後処理
        
        Args:
            markdown (str): html2textから生成された生のMarkdown
            
        Returns:
            str: 整形されたMarkdownコンテンツ
        """
        # Remove excessive newlines (more than 2 consecutive)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Ensure fenced code blocks have proper syntax highlighting
        if self.code_highlighting:
            # Match pre blocks that might contain language info
            pattern = r'```\s*(\w+)?\n(.*?)\n```'
            
            def format_code_block(match):
                language = match.group(1) or ''
                code = match.group(2)
                return f'```{language}\n{code}\n```'
                
            markdown = re.sub(pattern, format_code_block, markdown, flags=re.DOTALL)
        
        # Convert angle-bracketed URLs to normal URLs
        # [Link Text](<https://example.com>) -> [Link Text](https://example.com)
        if not self.ignore_links:
            markdown = re.sub(r'\[([^\]]+)\]\(<([^>]+)>\)', r'[\1](\2)', markdown)
        
        # Convert emphasis with underscores to asterisks for consistency
        markdown = re.sub(r'_([^_\n]+?)_', r'*\1*', markdown)
        markdown = re.sub(r'__([^_\n]+?)__', r'**\1**', markdown)
        
        return markdown.strip()


def extend_pagecruncher_with_markdown(spider, html_content: str, url: Optional[str] = None, 
                                      convert_to_markdown: bool = False, 
                                      markdown_options: Optional[dict] = None) -> dict:
    """
    Helper function to extend PageCrunch with Markdown conversion capability
    
    Args:
        spider: PageCrunchSpider instance
        html_content (str): HTML content to process
        url (str, optional): URL of the content (for relative links)
        convert_to_markdown (bool): Whether to convert HTML to Markdown
        markdown_options (dict, optional): Options for the Markdown converter
        
    Returns:
        dict: Dictionary with original content and Markdown conversion
    
    PageCrunchをMarkdown変換機能で拡張するヘルパー関数
    
    Args:
        spider: PageCrunchSpiderインスタンス
        html_content (str): 処理するHTMLコンテンツ
        url (str, optional): コンテンツのURL（相対リンク用）
        convert_to_markdown (bool): HTMLをMarkdownに変換するかどうか
        markdown_options (dict, optional): Markdownコンバーターのオプション
        
    Returns:
        dict: 元のコンテンツとMarkdown変換を含む辞書
    """
    result = {"html_content": html_content}
    
    if convert_to_markdown:
        options = markdown_options or {}
        converter = HtmlToMarkdownConverter(base_url=url, **options)
        markdown_content = converter.convert(html_content)
        
        # Calculate hash for the Markdown content
        markdown_hash = spider.calculate_content_hash(markdown_content)
        
        result.update({
            "markdown_content": markdown_content,
            "markdown_hash": markdown_hash,
            "markdown_length": len(markdown_content)
        })
    
    return result
