import typer
import asyncio
import os
import json
from typing import List, Optional
from typing_extensions import Annotated

from .scrapers.scraper_factory import get_scraper
from .scrapers import ScrapeRequest, SearchResult

# Import possible exceptions for error handling
from .scrapers import BlockedException, ConfigException

app = typer.Typer(help="Search Engine Query")


@app.command()
def query(
    title: Annotated[str, typer.Argument(help="Search keyword")],
    count: Annotated[int, typer.Option(help="Total number of results to get")] = 10,
    engine: Annotated[str, typer.Option(help="Search engine to use (e.g., baidu, bing)")] = "baidu",
    output: Annotated[Optional[str], typer.Option(help="Output file path (JSON)")] = None,
    # Search engine specific parameters (add more as needed)
    max_pages: Annotated[
        Optional[int], typer.Option(help="[Baidu] Maximum number of pages to search")
    ] = None,
    max_results_per_page: Annotated[
        Optional[int], typer.Option(help="[Bing] Maximum results per page")
    ] = None,
    # Common scraping parameters
    proxy: Annotated[
        Optional[str], typer.Option(help="Proxy server address (e.g., http://user:pass@host:port)")
    ] = None,
    sleep: Annotated[int, typer.Option(help="Sleep seconds between requests")] = 0,
    domain: Annotated[Optional[str], typer.Option(help="Specific domain to search")] = None,
    language: Annotated[Optional[str], typer.Option(help="Search language code")] = None,
    geo: Annotated[Optional[str], typer.Option(help="Geographic location code")] = None,
    # filters: Optional[dict] = None, # Filters not supported via command line, too complex
):
    """Search for results on specified search engine based on keyword"""
    try:
        request = ScrapeRequest(
            term=title,
            count=count,
            proxy=proxy,
            sleep=sleep,
            domain=domain,
            language=language,
            geo=geo,
            filters={},  # Complex filters not supported via command line
        )

        # Prepare engine-specific initialization parameters
        engine_kwargs = {}
        if engine == 'baidu' and max_pages is not None:
            engine_kwargs['max_pages'] = max_pages
        elif engine == 'bing' and max_results_per_page is not None:
            engine_kwargs['max_results_per_page'] = max_results_per_page
        # More elif statements can be added for other engines

        # Get and execute search
        scraper = get_scraper(engine, **engine_kwargs)
        results = asyncio.run(scraper.scrape(request))

        # Process and display/save results
        if not results:
            if not output:
                typer.echo(f"No search results found for '{title}'", err=True)
            return

        results_data = [
            {
                "rank": result.rank,
                "title": result.title,
                "link": result.link,
                "snippet": result.snippet,
            }
            for result in results
        ]

        # Ensure results don't exceed requested count (although scrapers might handle this internally)
        results_data = results_data[:count]

        if output:
            output_dir = os.path.dirname(output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
            typer.echo(f"Search results saved to: {output}")
        else:
            # Print JSON to stdout
            print(json.dumps(results_data, ensure_ascii=False, indent=2))

    except ValueError as e:
        # Engine not supported
        typer.echo(f"Error: {str(e)}", err=True)
    except (BlockedException, ConfigException) as e:
        typer.echo(f"Search configuration or execution error: {str(e)}", err=True)
    except Exception as e:
        typer.echo(f"Unhandled error occurred during search: {str(e)}", err=True)


# Add other search-related commands here if needed

# Remove main entry point, as this app will be added to the root main.py
# if __name__ == "__main__":
#     app()
