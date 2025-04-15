"""
Example: Combining Search and Fetch functionality (direct library usage)

1. Use ScraperFactory to get a Baidu Scraper.
2. Execute search to get SearchResult list.
3. Extract links from search results.
4. Use Fetcher to fetch the content of these links.
5. Print the final results.
"""

import asyncio
import sys
import os
from typing import List

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import required components
from meowdock.cmd.search.scrapers.scraper_factory import get_scraper
from meowdock.cmd.search.scrapers import (
    ScrapeRequest,
    SearchResult,
    BlockedException,
    ConfigException,
)
from meowdock.cmd.fetch.fetcher import Fetcher, FetchOptions, FetchResult


async def main():
    # --- 1. Define parameters ---
    search_query: str = "Autonomous driving technology"  # Search keyword
    search_count: int = 5  # Number of search results
    fetch_limit: int = 3  # Number of URLs to fetch (taking first N from search results)
    search_engine: str = "bing"

    print(f"--- Step 1: Using '{search_engine}' to search for '{search_query}' (requesting {search_count} results) ---")

    try:
        # --- 2. Execute search ---
        search_request = ScrapeRequest(term=search_query, count=search_count)

        engine_kwargs = {}
        scraper = get_scraper(search_engine, **engine_kwargs)
        search_results: List[SearchResult] = await scraper.scrape(search_request)

        if not search_results:
            print("No search results found.")
            return

        # Ensure results don't exceed requested count
        search_results = search_results[:search_count]
        print(f"Successfully retrieved {len(search_results)} search results.")

        # --- 3. Extract URLs to fetch ---
        urls_to_fetch = [result.link for result in search_results if result.link][:fetch_limit]

        if not urls_to_fetch:
            print("Failed to extract any valid URLs from search results for fetching.")
            return

        print(f"\n--- Step 2: Preparing to fetch the first {len(urls_to_fetch)} result links ---")
        for i, url in enumerate(urls_to_fetch):
            print(f"  [{i+1}] {url}")

        # --- 4. Execute fetching ---
        print(f"\n--- Step 3: Starting to fetch content from {len(urls_to_fetch)} links ---")
        fetch_options = FetchOptions(
            timeout=30000,
            waitUntil="networkidle",  # Suitable for handling Baidu link redirects
            waitForNavigation=True,  # Ensure capturing redirects
            extractContent=True,  # Extract main content
            disableMedia=True,
        )
        fetcher = Fetcher()
        fetch_results: List[FetchResult] = await fetcher.fetch(urls_to_fetch, fetch_options)

        # --- 5. Print fetch results ---
        print("\n--- Step 4: Fetch Results ---")
        for result in fetch_results:
            print("-" * 40)
            print(f"Original URL: {result.url}")
            if result.success:
                print(f"Final URL: {result.link}")
                content_preview = (
                    result.content[:300] + "..." if len(result.content) > 300 else result.content
                )
                print(f"Content preview:\n{content_preview}")
            else:
                print(f"Fetch failed: {result.error}")
        print("-" * 40)

    except ValueError as e:
        print(f"\nError: Unsupported search engine '{search_engine}' or parameter error. {e}")
    except (BlockedException, ConfigException) as e:
        print(f"\nSearch or fetch configuration error: {e}")
    except Exception as e:
        print(f"\nUnknown error occurred during execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
