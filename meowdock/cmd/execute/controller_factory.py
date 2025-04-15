from pydantic import BaseModel
from browser_use.browser.context import BrowserContext
from browser_use import Controller, ActionResult
from typing import Optional, Any, Type, Callable
import time
import asyncio
import warnings


class Registry:
    def __init__(self):
        self._registry: dict[str, dict[str, Any]] = {}

    def action(self,
               description: str,
               param_model: Optional[Type[BaseModel]] = None,
               domains: Optional[list[str]] = None,
               page_filter: Optional[Callable[[Any], bool]] = None):
        def deco(func: Callable):
            self._registry[func.__name__] = {
                'description': description,
                'param_model': param_model,
                'domains': domains,
                'page_filter': page_filter,
                'function': func
            }
            return func
        return deco

    def get(self, key, default=None):
        return self._registry.get(key, default)


registry = Registry()


class WaitMessageAction(BaseModel):
    timeout: Optional[int] = 90


@registry.action('Wait for all message streams to complete', param_model=WaitMessageAction)
async def wait_message(params: WaitMessageAction, browser: BrowserContext):
    '''Actually wait for all event-streams to disconnect, or timeout'''
    await asyncio.sleep(5)
    streams = browser._event_streams
    t0 = time.time()
    async with streams.lock:
        tasks = list(map(lambda x: asyncio.create_task(
            asyncio.wait_for(x.body(), timeout=params.timeout)), streams))
        errs = await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0.1)
        streams._list.clear()
    t1 = time.time()
    msg = f'🕒  Waiting for all message-streams to finish, or timeout. Actual wait time: {t1-t0: .3f}s.'
    # print(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)


def get_controller(funcs: list[str] = []):
    controller = Controller()

    for func_name in funcs:
        kw = registry.get(func_name, None)
        if kw is None:
            if func_name not in controller.registry.registry.actions.keys():
                warnings.warn(f'Function `{func_name}` is not defined')
            continue
        controller.registry.action(
            **{k: v for k, v in kw.items() if k != 'function'}
        )(kw['function'])

    return controller
