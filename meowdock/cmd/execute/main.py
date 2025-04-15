import typer
from typing_extensions import Annotated
from meowdock.cmd.execute.executors.base import ExecutorWrapper
from meowdock.cmd.execute.executors.executors_factory import get_executor
import asyncio

app = typer.Typer(help="获取网页内容")


@app.command()
def execute(
    prompt: Annotated[str, typer.Argument(help="提示词")],
    mode: Annotated[str, typer.Argument(help="执行器的类型")],
    headless: Annotated[bool, typer.Option(help="是否启用无头模式")] = False,
    debug: Annotated[bool, typer.Option(help="是否启用调试模式")] = False
):
    
    executor = get_executor(mode, debug=debug, headless=headless)
    print(asyncio.run(executor.execute(prompt=prompt)))
