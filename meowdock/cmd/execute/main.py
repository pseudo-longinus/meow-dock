import typer
from typing_extensions import Annotated
from meowdock.cmd.execute.executors.base import ExecutorWrapper
from meowdock.cmd.execute.executors.executors_factory import get_executor
import asyncio
import os


app = typer.Typer(help="获取网页内容")


@app.command()
def execute(
    prompt: Annotated[str, typer.Argument(help="提示词")],
    mode: Annotated[str, typer.Argument(help="执行器的类型")],
    headless: Annotated[bool, typer.Option(help="是否启用无头模式")] = True,
    debug: Annotated[bool, typer.Option(help="是否启用调试模式")] = False
):
    executor = get_executor(mode, debug=debug, headless=headless)
    try:
        print(asyncio.run(executor.execute(prompt=prompt)))
    except:
        raise



@app.command(name='ask-yuanbao')
def ask_yuanbao(
    prompt: Annotated[str, typer.Argument(help="提示词")],
    headless: Annotated[bool, typer.Option(help="是否启用无头模式")] = True,
    debug: Annotated[bool, typer.Option(help="是否启用调试模式")] = False
):
    mode = 'yuanbao'
    execute(prompt=prompt, mode=mode, headless=headless, debug=debug)
