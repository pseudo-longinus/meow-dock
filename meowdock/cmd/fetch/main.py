import json
import asyncio
from typing import List, Optional
import typer
from typing_extensions import Annotated

from meowdock.cmd.fetch.fetcher import Fetcher, FetchOptions, FetchResult

app = typer.Typer(help="Fetch web page content")


@app.command()
def fetch(
    url: Annotated[str, typer.Argument(help="URL to fetch")],
    timeout: Annotated[int, typer.Option(help="Timeout in milliseconds")] = 30000,
    wait_until: Annotated[str, typer.Option(help="Wait condition for page load")] = "load",
    extract_content: Annotated[bool, typer.Option(help="Whether to extract main content")] = True,
    max_length: Annotated[
        Optional[int], typer.Option(help="Maximum length of returned content")
    ] = None,
    return_html: Annotated[
        bool, typer.Option(help="Whether to return HTML (otherwise text)")
    ] = False,
    wait_for_navigation: Annotated[
        bool, typer.Option(help="Whether to wait for additional navigation")
    ] = False,
    navigation_timeout: Annotated[int, typer.Option(help="Navigation timeout")] = 10000,
    disable_media: Annotated[bool, typer.Option(help="Whether to disable media resources")] = True,
    debug: Annotated[bool, typer.Option(help="Whether to enable debug mode")] = False,
    output: Annotated[Optional[str], typer.Option(help="Output file path")] = None,
):
    """Fetch content for a single URL"""
    if wait_until not in ["load", "domcontentloaded", "networkidle", "commit"]:
        typer.echo(
            f"Error: wait_until must be one of 'load', 'domcontentloaded', 'networkidle', 'commit'"
        )
        raise typer.Exit(1)

    options = FetchOptions(
        timeout=timeout,
        waitUntil=wait_until,  # type: ignore
        extractContent=extract_content,
        maxLength=max_length,
        returnHtml=return_html,
        waitForNavigation=wait_for_navigation,
        navigationTimeout=navigation_timeout,
        disableMedia=disable_media,
        debug=debug,
    )

    fetcher = Fetcher()
    result = fetcher.fetch_sync(url, options)

    if result.success:
        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result.__dict__, f, ensure_ascii=False, indent=2)
            typer.echo(f"Content saved to: {output}")
        else:
            # When no output file is specified, print results to stdout
            print(f"--- URL: {result.url} ---")
            if result.link and result.link != result.url:
                print(f"Redirected URL: {result.link}")
            print(f"Content:\n{result.content}")
            print("--- END --- \n")

    else:
        typer.echo(f"Failed to fetch content: {result.error}", err=True)
        raise typer.Exit(1)


# Add a new function that accepts URL array instead of a file
async def fetch_urls_async(
    urls: List[str], options: FetchOptions, concurrency: int = 5
) -> List[FetchResult]:
    """Use semaphore to limit concurrency"""
    fetcher = Fetcher()
    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_with_semaphore(url: str, index: int) -> FetchResult:
        async with semaphore:
            # Catch errors for individual URLs so batch processing can continue
            try:
                return await fetcher._fetch_url(url, options, index)
            except Exception as e:
                typer.echo(f"Internal error occurred while fetching {url}: {e}", err=True)
                # Return a FetchResult with the error
                return FetchResult(success=False, error=str(e), url=url, index=index)

    tasks = [fetch_with_semaphore(url, i) for i, url in enumerate(urls)]
    results = await asyncio.gather(*tasks)
    return results  # Returns a List[FetchResult]


@app.command()
def fetch_urls(
    urls: List[str],
    timeout: int = 30000,
    wait_until: str = "load",
    extract_content: bool = True,
    max_length: Optional[int] = None,
    return_html: bool = False,
    wait_for_navigation: bool = False,
    navigation_timeout: int = 10000,
    disable_media: bool = True,
    debug: bool = False,
    output: Optional[str] = None,
    concurrency: int = 5,
):
    """Batch fetch content for multiple URLs (directly from URL list)"""
    if wait_until not in ["load", "domcontentloaded", "networkidle", "commit"]:
        typer.echo(
            f"Error: wait_until must be one of 'load', 'domcontentloaded', 'networkidle', 'commit'",
            err=True,
        )
        raise typer.Exit(1)

    if not urls:
        typer.echo("URL list is empty", err=True)
        raise typer.Exit(1)

    options = FetchOptions(
        timeout=timeout,
        waitUntil=wait_until,  # type: ignore
        extractContent=extract_content,
        maxLength=max_length,
        returnHtml=return_html,
        waitForNavigation=wait_for_navigation,
        navigationTimeout=navigation_timeout,
        disableMedia=disable_media,
        debug=debug,
    )

    # Execute batch fetch
    typer.echo(f"Starting to fetch {len(urls)} URLs (concurrency: {concurrency})...")
    results_list = asyncio.run(
        fetch_urls_async(urls, options, concurrency)
    )  # This is a list of FetchResult

    # Calculate result statistics
    success_count = sum(1 for r in results_list if r.success)
    fail_count = len(results_list) - success_count

    # Output results
    if output:
        # Convert result list to dictionary list for JSON serialization
        results_dict = [r.__dict__ for r in results_list]
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        typer.echo(f"Results saved to: {output}")
    else:
        # When no output file is specified, print each successful result to stdout
        typer.echo("--- Fetch Results ---")
        for result in results_list:
            if result.success:
                print(f"--- URL: {result.url} ---")
                if result.link and result.link != result.url:
                    print(f"Redirected URL: {result.link}")
                # Limit preview length
                content_preview = (
                    result.content[:500] + "..." if len(result.content) > 500 else result.content
                )
                print(f"Content:\n{content_preview}")
                print("--- END --- \n")
            else:
                # Print failure information to stderr
                typer.echo(f"Fetch failed: {result.url} - {result.error}", err=True)

    # Print final statistics to stderr
    typer.echo(f"Fetch completed: {success_count} successful, {fail_count} failed", err=True)
    return results_list
