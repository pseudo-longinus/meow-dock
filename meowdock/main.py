import typer
from typing import List

# Import functions from fetch module
from meowdock.cmd.fetch.main import fetch as fetch_single
from meowdock.cmd.fetch.main import fetch_urls

# Import functionality from search module
from meowdock.cmd.search.main import query
from meowdock.agent.deepsearch import deepsearch as deepsearch_func

from meowdock.cmd.execute.main import execute, ask_yuanbao
from meowdock.cmd.login.main import login

app = typer.Typer()


# Add smart fetch command
@app.command(name="fetch")
def smart_fetch(
    urls: List[str] = typer.Argument(..., help="One or more URLs to fetch"),
):
    """Fetch web content, automatically choose single or batch mode based on URL count"""
    # Call original function with default parameters
    if len(urls) == 1:
        # Single URL case
        url = urls[0]
        fetch_single(url=url)
    else:
        # Multiple URLs case, directly use new function
        fetch_urls(urls=urls)


# Add search command (directly as main command rather than subcommand group)
app.command(name="search")(query)
app.command(name="execute")(execute)
app.command(name="login")(login)
app.command(name="ask-yuanbao")(ask_yuanbao)


# Add deepsearch command
@app.command(name="deepsearch")
def deepsearch(
    query: str = typer.Argument(..., help="Search query"),
    engines: str = typer.Option(
        "baidu,bing", help="Comma-separated list of search engines, e.g. baidu,bing"
    ),
    count: int = typer.Option(10, help="Number of results to return"),
    executor: str = typer.Option("yuanbao", help="Result processor executor, default is 'yuanbao'"),
):
    """Multi-engine deep search, automatically fetches web content and processes results using AI"""
    # Convert comma-separated engine string to list
    engine_list = [e.strip() for e in engines.split(",") if e.strip()]

    result = deepsearch_func(query=query, engines=engine_list, count=count, executor=executor)
    print(result)


if __name__ == "__main__":
    app()
