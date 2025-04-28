"""
Content extraction utility module

Provides utility functions for extracting main content from HTML.
"""

import re
from typing import Optional

import html2text
from readability import Document
from playwright.async_api._generated import Page
import markdownify


async def extract_main_content(html: str, filter_pattern: Optional[str] = None) -> str:
    """
    Extract the main content of the page.

    Args:
        html: HTML content
        filter_pattern: Regex pattern for filtering, default is None (no filtering)

    Returns:
        Extracted main content text
    """
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.body_width = 0

    doc = Document(html, min_text_length=15)
    content = h.handle(doc.summary())

    # Apply filtering (if a pattern is provided)
    if filter_pattern:
        pattern = re.compile(filter_pattern)
        content = pattern.sub("", content)

    return content


async def extract_chinese_content(html: str) -> str:
    """
    Extract and retain Chinese content from the page.

    Retain Chinese characters, Chinese punctuation, numbers, and newlines; filter out other characters.

    Args:
        html: HTML content

    Returns:
        Extracted Chinese content text
    """
    # Filtering pattern for Chinese characters, punctuation, numbers, and newlines
    filter_pattern = r"[^\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef0-9\n\r%]"

    return await extract_main_content(html, filter_pattern)


async def extract_page_content(
    page: Page,
    min_text_length=25,
    locator: Optional[str] = None
) -> str:
    """
    Extract the main content of the page. Will also enter iframes.

    Args:
        page: HTML content
        min_text_length: minimum text length for content extraction
        locator:
    Returns:
        Extracted main content text
    """
    html = await page.content()
    pat = re.compile(r'\[\[\[(.*?)\]\]\]', flags=re.DOTALL)
    raw_mo = re.findall(pat, html)
    matches = [mo for mo in raw_mo if len(mo) > min_text_length]
    if len(matches) == 0: return ''
    len_matches = list(map(len, matches))
    final_match = matches[len_matches.index(max(len_matches))]
    md = markdownify.markdownify(final_match)
    def shorten(match):
        s = match.group(0)
        return s[:10] + '...' + s[-5:]
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = re.sub(r' {3,}', '  ', md)
    md = re.sub(r'[a-zA-Z0-9_]{20,}', shorten, md)
    return md
