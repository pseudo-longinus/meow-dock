import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Literal

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Response
from contextlib import asynccontextmanager
# Import shared libraries
from meowdock.library.browser import (
    init_logger,
    extract_main_content,
    abort_resource,
    get_moderate_resources,
    find_chromium,
    get_cookies
)
import json


USER_DATA_DIR = os.getenv('CHROME_USER_DATA_PATH', 'chrome_data/')


@dataclass
class FetchOptions:
    """Fetch options configuration"""

    timeout: int = 30000  # Timeout (milliseconds)
    waitUntil: Literal['load', 'domcontentloaded', 'networkidle', 'commit'] = 'load'
    extractContent: bool = True  # Whether to extract main content
    maxLength: Optional[int] = None  # Maximum length of returned content
    returnHtml: bool = False  # Whether to return HTML (otherwise return extracted text)
    waitForNavigation: bool = False  # Whether to wait for additional navigation
    navigationTimeout: int = 10000  # Navigation timeout
    disableMedia: bool = True  # Whether to disable media resources
    debug: bool = False  # Debug mode


@dataclass
class FetchResult:
    """Fetch result"""

    success: bool = False
    content: str = ""
    error: Optional[str] = None
    index: Optional[int] = None
    url: Optional[str] = None
    link: Optional[str] = None  # Real link after redirection


class Fetcher:
    """Web content fetcher"""
    def __init__(self, context: BrowserContext = None):
        init_logger()  # Initialize logger using shared library
        self.default_block_resources = get_moderate_resources()
        self.injected_context = context

    @asynccontextmanager
    async def get_browser_context(self, headless=True):
        try:
            if self.injected_context:
                yield self.injected_context
            else:
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(
                    headless=headless,
                    executable_path=find_chromium,
                    args=['--disable-blink-features=AutomationControlled'],
                )
                context = await browser.new_context()
                await context.add_cookies(get_cookies())
                yield context
        finally:
            if self.injected_context:
                ...
            else:
                if context: await context.close()
                if browser: await browser.close()
                if playwright: await playwright.stop()

    async def _fetch_url(
        self, url: str, options: FetchOptions, index: Optional[int] = None
    ) -> FetchResult:
        """Fetch content from a single URL"""
        result = FetchResult(index=index, url=url)
        try:
            async with self.get_browser_context(headless=not options.debug) as context:
                # Set up route interception to block unnecessary resources
                if options.disableMedia:
                    await context.route(
                        "**/*", lambda route: abort_resource(route, self.default_block_resources)
                    )

                page = await context.new_page()

                # Listen for requests, record redirects
                final_url = url

                async def handle_response(response):
                    nonlocal final_url
                    if response.request.url == url or response.url == url:
                        if response.status >= 300 and response.status < 400:
                            # Get redirect target
                            location = response.headers.get("location")
                            if location:
                                if location.startswith("/"):
                                    # Handle relative URLs
                                    from urllib.parse import urlparse

                                    parsed = urlparse(url)
                                    final_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                                else:
                                    final_url = location

                page.on("response", handle_response)

                # Visit URL
                response = await page.goto(
                    url,
                    timeout=options.timeout,
                    wait_until=options.waitUntil,
                )

                # Check response status
                if not response:
                    raise Exception("No response received")

                if response.status >= 400 and response.status not in [403, 429, 503]:
                    raise Exception(f"HTTP error: {response.status}")

                try:
                    await page.wait_for_function("document.readyState === 'complete'", timeout=10000)
                except TimeoutError:
                    raise Exception(f"HTTP error: {response.status}.")

                # Get final URL (actual URL after redirection)
                current_url = page.url
                result.link = current_url if current_url != url else final_url

                # Wait for additional navigation
                if options.waitForNavigation:
                    try:
                        await page.wait_for_load_state(
                            "networkidle", timeout=options.navigationTimeout
                        )
                        # Update to final URL after navigation
                        result.link = page.url
                    except Exception as e:
                        logging.warning(f"Wait for additional navigation timed out: {str(e)}")

                # Get page content
                html = await page.content()

                if response.status >= 400:
                    lhtml = html.lower()
                    if len(html) < 3000 or (len(html) < 5000
                            and ('Access Denied' in lhtml or 'error' in lhtml)):
                        raise Exception(
                            f"HTTP error: {response.status}! {len(html)}")
                # Process content
                if options.extractContent:
                    content = await extract_main_content(
                        html
                    )  # Extract content using shared library
                else:
                    content = (
                        html
                        if options.returnHtml
                        else await page.evaluate('document.body.innerText')
                    )

                # Limit content length
                if options.maxLength and len(content) > options.maxLength:
                    content = content[: options.maxLength]


                result.success = True
                result.content = content

        except Exception as e:
            logging.error(f"Fetch failed ({url}): {str(e)}")
            result.error = str(e)

        return result

    async def fetch(
        self, urls: Union[str, List[str]], options: Optional[FetchOptions] = None
    ) -> Union[FetchResult, List[FetchResult]]:
        """Fetch content from one or more URLs"""
        # Set default options
        if options is None:
            options = FetchOptions()

        # Handle single URL
        if isinstance(urls, str):
            return await self._fetch_url(urls, options)

        # Handle multiple URLs
        tasks = []
        for i, url in enumerate(urls):
            tasks.append(self._fetch_url(url, options, i))

        results = await asyncio.gather(*tasks)
        return results

    def fetch_sync(
        self, urls: Union[str, List[str]], options: Optional[FetchOptions] = None
    ) -> Union[FetchResult, List[FetchResult]]:
        """Synchronously fetch URL content (uses async internally)"""
        return asyncio.run(self.fetch(urls, options))
