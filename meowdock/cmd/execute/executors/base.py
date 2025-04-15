from abc import ABC, abstractmethod
from meowdock.cmd.execute.executors.core import Executor
from browser_use import Browser, BrowserConfig, BrowserContextConfig, Controller
from browser_use.browser.context import BrowserContext
from contextlib import asynccontextmanager
import os
import json
from typing import Optional
from meowdock.library.browser import find_chromium
import pathlib
from meowdock.library.browser.content_utils import extract_page_content
from meowdock.cmd.execute.controller_factory import get_controller
from meowdock.cmd.execute.executors.core import SimplifiedHistoryActionList, SimplifiedHistoryActionTreeNode
from typing_extensions import override


COOKIES_PATH = os.getenv('COOKIES_JSON_PATH', "cookies.json")
CHROME_PATH = find_chromium()
USER_DATA_DIR = pathlib.Path(os.getenv('CHROME_USER_DATA_PATH', "chrome_data/")).resolve()


class ExecutorWrapper(ABC):
    history_str = ''
    available_function: list[str] = []
    def __init__(self, headless=True, debug=False, *args, **kw):
        self._browser_config = BrowserConfig(
            headless=headless,
            browser_binary_path=CHROME_PATH,
            extra_browser_args=[f'--user-data-dir={USER_DATA_DIR}'],
        )
        self._browser_context_config = BrowserContextConfig(
            cookies_file=COOKIES_PATH,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            highlight_elements=debug,
        )
        self.debug = debug
        self._controller: Optional[Controller] = None

    @property
    def history(self):
        return self.history_str

    def _init_controller(self) -> None:
        self._controller = get_controller(self.available_function)

    @property
    def controller(self) -> Controller:
        if not self._controller:
            self._init_controller()
        return self._controller

    @asynccontextmanager
    async def get_executor(self, *args, **kw):
        try:
            b = Browser(self._browser_config)
            ctx = await b.new_context(self._browser_context_config)
            await ctx.navigate_to(r'https://yuanbao.tencent.com/chat/naQivTmsDa')
            yield Executor(
                browser_context=ctx,
                controller=self.controller,
                detailed_logging=self.debug,
                *args,
                **kw,
            )
        finally:
            if ctx:
                await ctx.close()
            await b.close()

    @abstractmethod
    async def execute(self, prompt: str) -> str:
        '''Execute the given prompt.

        Args:
            prompt (str): User inputing prompt

        Returns:
            str:

        Raises:
            ValueError: When browser is not ready.
            XPathError: When the xpath of the given element doesn't exist in the current page.
        '''
        pass

    async def _extract_content(self, executor: Executor, browser_context: BrowserContext) -> str:
        return await extract_page_content(await browser_context.get_current_page())


class ListExecutor(ExecutorWrapper):
    history_str_path = './meowdock/resources/yuanbao_history.json'
    available_function = ['wait_message']

    @override
    @property
    def history(self):
        return open(self.history_str_path, 'r', encoding='utf-8').read()

    @override
    async def execute(self, prompt: str) -> str:
        async with self.get_executor() as executor:
            # First escape the prompt for JSON compatibility, and remove the enclosing double quotes
            escaped_prompt = json.dumps(prompt)[1:-1]
            d = json.loads(self.history.replace("给我讲一个冷笑话", escaped_prompt))
            ActionModelRuntime = executor.controller.registry.create_action_model()
            history = SimplifiedHistoryActionList[ActionModelRuntime](**d)
            await executor.rerun_list_history(history)
            return await self._extract_content(
                executor=executor, browser_context=executor.browser_context
            )

class TreeExecutor(ExecutorWrapper):
    history_str_path = './meowdock/resources/yuanbao_history2.json'
    available_function = ['wait_message']

    @override
    @property
    def history(self):
        return open(self.history_str_path, 'r', encoding='utf-8').read()

    @override
    async def execute(self, prompt: str) -> str:
        async with self.get_executor() as executor:
            # First escape the prompt for JSON compatibility, and remove the enclosing double quotes
            escaped_prompt = json.dumps(prompt)[1:-1]
            d = json.loads(self.history.replace("给我讲一个冷笑话", escaped_prompt))
            ActionModelRuntime = executor.controller.registry.create_action_model()
            history = SimplifiedHistoryActionTreeNode[ActionModelRuntime](**d)
            await executor.rerun_tree_history(history)
            return await self._extract_content(
                executor=executor, browser_context=executor.browser_context
            )
