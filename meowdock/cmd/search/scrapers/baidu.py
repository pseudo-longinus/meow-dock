import asyncio
import logging
import random
import os
from typing import List, Dict, Optional
import re
from urllib.parse import unquote

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Import shared libraries
from meowdock.library.browser import (
    find_chromium,
    check_browser_executable,
    init_logger,
    get_user_agents,
    extract_main_content,
    abort_resource,
    get_strict_resources,
    get_cookies
)

from meowdock.cmd.search.scrapers import (
    SearchScraper,
    ScrapeRequest,
    SearchResult,
    ScrapeResponse,
)
from meowdock.cmd.search.scrapers import BlockedException, ConfigException
from meowdock.cmd.search.scrapers.scraper_factory import register
import json


USER_DATA_DIR = os.getenv('CHROME_USER_DATA_PATH', 'chrome_data/')
cookies = get_cookies()



def _check_config(max_pages: int):
    if max_pages <= 0:
        raise ConfigException("Number of Baidu search pages must be greater than 0")
    return max_pages


@register('baidu')
class BaiduScraper(SearchScraper):
    BASE_URL = "https://www.baidu.com/s?wd={}&pn={}"

    def __init__(self, max_pages: int = 10):
        self.max_pages = _check_config(max_pages)
        self.browser_path = find_chromium()  # Use shared library to find browser
        init_logger()  # Use shared library to initialize logger
        self.user_agents = get_user_agents()  # Use shared library to get user agents
        self.block_resources_set = get_strict_resources()

    def _parse_page(self, results: List[SearchResult], resp: ScrapeResponse) -> None:
        """Parse Baidu search results page"""
        rank = len(results) + 1
        soup = BeautifulSoup(resp.html, "html.parser")

        # Baidu search results are usually in h3 tags under div with id="content_left"
        for result_div in soup.select('#content_left > div'):
            h3_tag = result_div.find('h3')
            if not h3_tag:
                continue

            link_tag = h3_tag.find('a', href=True)
            if not link_tag:
                continue

            link = link_tag['href']
            title = link_tag.get_text().strip()

            # Find summary text - enhanced version
            snippet = ""

            # Try multiple possible summary containers
            snippet_candidates = [
                result_div.find('div', {'class': 'c-abstract'}),
                result_div.find('div', {'class': 'content-right'}),
                result_div.find('div', {'class': 'c-span9'}),
                result_div.find('span', {'class': 'content-right_8Zs40'}),
                # Find content preview box
                result_div.find('div', {'class': 'c-row'}),
                # Generic alternative: search for any paragraph tag
                result_div.find('p'),
            ]

            # Use the first non-None candidate
            for candidate in snippet_candidates:
                if candidate:
                    snippet = candidate.get_text().strip()
                    if snippet:  # Exit if non-empty content is obtained
                        break

            # If all above methods fail, try to get all text under div except h3
            if not snippet:
                # Get all text except h3
                h3s = result_div.find_all('h3')
                for h3 in h3s:
                    h3.decompose()  # Temporarily remove h3 tags from DOM

                full_text = result_div.get_text().strip()
                if full_text:
                    # Only take the first 150 characters as summary
                    snippet = full_text[:150].strip()

            results.append(SearchResult(rank, link, title, snippet))
            rank += 1

    def _paginate(self, term: str, domain: str, language: str, count: int):
        """Generate Baidu search pagination URLs"""
        urls = []
        pages_to_fetch = min(count // 10 + (1 if count % 10 else 0), self.max_pages)

        for page in range(pages_to_fetch):
            # Baidu uses pn parameter for page number, 10 results per page, pn=0 for first page, pn=10 for second page
            pn = page * 10
            urls.append(self.BASE_URL.format(term, pn))

        return urls

    def _check_exceptions(self, res: ScrapeResponse) -> None:
        """Check if blocked by Baidu"""
        if res.status >= 400:
            raise BlockedException("Blocked by Baidu")

        # Check if CAPTCHA appears
        if "verify" in res.html.lower() and "human verification" in res.html:
            raise BlockedException("Baidu requires human verification")

        return

    async def scrape(self, req: ScrapeRequest) -> List[SearchResult]:
        """Execute Baidu search and return results"""
        urls = self._paginate(req.term, req.domain, req.language, req.count)
        results = []

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    executable_path=self.browser_path,
                    args=['--disable-blink-features=AutomationControlled'],
                )
                context = await browser.new_context(user_agent=random.choice(self.user_agents))
                await context.add_cookies(cookies)

                # Set route interception, explicitly pass blocking set
                await context.route(
                    "**/*", lambda route: abort_resource(route, self.block_resources_set)
                )

                for idx, url in enumerate(urls):
                    page = await context.new_page()
                    response = await page.goto(url, wait_until="domcontentloaded")

                    html = await page.content()
                    scrape_response = ScrapeResponse(html, response.status)

                    self._check_exceptions(scrape_response)
                    self._parse_page(results, scrape_response)

                    await page.close()

                    if idx < len(urls) - 1:
                        await asyncio.sleep(req.sleep)

                await browser.close()

            except Exception as e:
                logging.error(f"Baidu search failed: {str(e)}")
                raise

        return results[: req.count]
