import typer
from typing import List

# Import functions from fetch module
from meowdock.cmd.fetch.main import fetch as fetch_single
from meowdock.cmd.fetch.main import fetch_urls

# Import functionality from search module
from meowdock.cmd.search.main import query
from meowdock.agent.deepsearch import deepsearch as deepsearch_func

from meowdock.cmd.execute.main import execute
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


# Add deepsearch command
@app.command(name="deepsearch")
def deepsearch(
    query: str = typer.Argument(..., help="搜索关键词"),
    engines: List[str] = typer.Option(["baidu", "bing"], help="搜索引擎列表"),
    count: int = typer.Option(10, help="返回结果数量"),
    executor: str = typer.Option("yuanbao", help="结果处理执行器，默认为'yuanbao'"),
):
    """多引擎深度搜索，自动抓取网页内容并使用AI处理结果"""
    result = deepsearch_func(query=query, engines=engines, count=count, executor=executor)
    print(result)


if __name__ == "__main__":
    app()
