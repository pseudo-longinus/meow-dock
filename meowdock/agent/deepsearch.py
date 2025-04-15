import asyncio
from typing import List, Optional, Dict, Any, Union, cast
import json

from ..cmd.search.scrapers.scraper_factory import get_scraper
from ..cmd.search.scrapers import ScrapeRequest, SearchResult
from meowdock.cmd.fetch import Fetcher, FetchOptions, FetchResult
from meowdock.cmd.execute.executors.executors_factory import get_executor
from meowdock.library.browser import find_chromium, get_cookies
from playwright.async_api import async_playwright, BrowserContext
import pathlib
import os


USER_DATA_DIR = pathlib.Path(os.getenv('CHROME_USER_DATA_PATH', "chrome_data/")).resolve()


async def _search_one_engine(
    engine: str, query: str, count: int = 5, **kwargs
) -> List[SearchResult]:
    """Search using a specified search engine"""
    try:
        scraper = get_scraper(engine, **kwargs)
        request = ScrapeRequest(
            term=query,
            count=count,
            **{
                k: v
                for k, v in kwargs.items()
                if k in ['domain', 'sleep', 'proxy', 'language', 'geo', 'filters']
            },
        )
        return await scraper.scrape(request)
    except Exception as e:
        print(f"Search engine {engine} error: {str(e)}")
        return []


async def _fetch_content_for_url(
    fetcher: Fetcher, url: str, options: FetchOptions
) -> Optional[str]:
    """Get content from a single URL"""
    try:
        # When fetching a single URL string, the result is a FetchResult object
        result = await fetcher.fetch(url, options)
        # Since we know we're passing a single URL, we can safely cast
        single_result = cast(FetchResult, result)
        if single_result and single_result.success and single_result.content:
            return single_result.content
    except Exception as e:
        print(f"Failed to fetch URL content {url}: {str(e)}")
    return None


async def _fetch_contents(urls: List[str]) -> Dict[str, str]:
    """Concurrently fetch content from multiple URLs"""
    url_to_content = {}
    if not urls:
        return url_to_content

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=find_chromium(),
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        await context.add_cookies(get_cookies())
        # Create a single Fetcher instance and FetchOptions instance
        fetcher = Fetcher(context)
        options = FetchOptions(
            timeout=30000,
            extractContent=True,
            disableMedia=True,
            returnHtml=False,
        )

        # Use a separate task list and reuse the fetcher instance
        tasks = [_fetch_content_for_url(fetcher, url, options) for url in urls]
        contents = await asyncio.gather(*tasks)

    # Build a mapping from URL to content
    for i, content in enumerate(contents):
        if content:
            url_to_content[urls[i]] = content

    return url_to_content


async def _search_multi_engine(
    query: str, engines: List[str] = ["baidu", "bing"], count_per_engine: int = 5, **kwargs
) -> List[Dict[str, Any]]:
    """
    Perform asynchronous search using multiple search engines and merge results

    Args:
        query: Search query
        engines: List of search engines to use
        count_per_engine: Number of results to get from each engine
        **kwargs: Additional parameters to pass to search engines

    Returns:
        List of merged search results
    """
    tasks = []
    for engine in engines:
        task = _search_one_engine(engine, query, count_per_engine, **kwargs)
        tasks.append(task)

    results_per_engine = await asyncio.gather(*tasks)

    # Collect all URLs
    all_links = []
    url_to_result = {}  # Used to track the relationship between URLs and search results
    for engine_idx, engine_results in enumerate(results_per_engine):
        for result in engine_results:
            if result.link and result.link not in url_to_result:
                all_links.append(result.link)
                url_to_result[result.link] = {"engine": engines[engine_idx], "result": result}

    # Fetch content for all URLs
    url_to_content = await _fetch_contents(all_links)

    # Merge and format results
    all_results = []
    rank = 1

    # Interleave results from each engine
    max_results = max((len(results) for results in results_per_engine), default=0)
    for i in range(max_results):
        for engine_idx, engine_results in enumerate(results_per_engine):
            if i < len(engine_results):
                result = engine_results[i]
                # Prioritize fetched content, fallback to snippet if not available
                content = url_to_content.get(result.link, result.snippet or "")

                all_results.append(
                    {
                        "rank": rank,
                        "engine": engines[engine_idx],
                        "url": result.link,
                        "title": result.title,
                        "content": content,
                    }
                )
                rank += 1

    return all_results


def format_results_as_markdown(results: List[Dict[str, Any]]) -> str:
    """Format search results as Markdown text for better formatting and readability"""
    if not results:
        return "No search results found"

    markdown_lines = []

    for result in results:
        # Add horizontal rule (except for the first result)
        if result != results[0]:
            markdown_lines.append("---")

        # Add ranking with bold formatting
        markdown_lines.append(f"- **rank: {result['rank']}**")

        # Use markdown link format for URLs
        url = result['url']
        title = result['title']
        markdown_lines.append(f"  **url:** [{title}]({url})")

        # Content processing: truncate long content, add formatting
        content = result['content']
        if content:
            markdown_lines.append(f"  **content:**\n  {content}")
        else:
            markdown_lines.append(f"  **content:** _(No content)_")

        # Add extra line for readability
        markdown_lines.append("")

    return "\n\n".join(markdown_lines)


def deepsearch(
    query: str,
    engines: Union[List[str], str] = ["baidu", "bing"],
    count: int = 10,
    executor: str = "yuanbao",
    **kwargs,
) -> str:
    """
    Perform deep search, combining results from multiple search engines and process results with specified executor

    Args:
        query: Search query
        engines: Search engine or list of engines to use
        count: Total number of results to get
        executor: Executor for processing results, default is 'yuanbao'
        **kwargs: Additional search parameters

    Returns:
        Formatted search results
    """
    if isinstance(engines, str):
        engines = [engines]
    executor_instance = get_executor(executor)
    # Calculate number of results needed from each engine
    count_per_engine = count // len(engines) + 1

    # Execute asynchronous search
    results = asyncio.run(
        _search_multi_engine(query, engines=engines,
                             count_per_engine=count_per_engine, **kwargs)
    )

    # Limit the number of results
    results = results[:count]

    # Format results as Markdown
    markdown_results = format_results_as_markdown(results)

    # If an executor is specified, pass the query and results to the executor
    combined_prompt = f"Please answer the question based on the following search results:\n\nQuestion: {query}\n\nSearch Results:\n{markdown_results}"
    result = asyncio.run(executor_instance.execute(combined_prompt))
    return result if result is not None else markdown_results

    # If no executor is specified or the executor is not supported, return the Markdown results directly
    return markdown_results
