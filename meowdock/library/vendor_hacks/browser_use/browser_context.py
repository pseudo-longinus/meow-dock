from browser_use.browser.context import BrowserContext, logger
from browser_use.dom.views import DOMElementNode
from browser_use.browser.views import BrowserError
from browser_use.utils import time_execution_async
from functools import wraps
from typing import Iterable
import asyncio


class SafeList:
    '''A list with a lock. Lock all operations that modify list elements.
    '''

    def __init__(self, iterable: Iterable = None):
        self._list = list(iterable) if iterable else []
        self._lock = asyncio.Lock()

    @property
    def lock(self):
        return self._lock

    async def append(self, item):
        async with self._lock:
            self._list.append(item)

    async def extend(self, iterable):
        async with self._lock:
            self._list.extend(iterable)

    async def pop(self, index=-1):
        async with self._lock:
            return self._list.pop(index)

    async def remove(self, item):
        async with self._lock:
            self._list.remove(item)

    async def clear(self):
        async with self._lock:
            self._list.clear()

    def count(self, item):
        return self._list.count(item)

    def index(self, item):
        return self._list.index(item)

    async def insert(self, index, item):
        async with self._lock:
            self._list.insert(index, item)

    async def __aiter__(self):
        for item in self._list:
            yield item

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, index):
        return self._list[index]


old_init = BrowserContext.__init__
old_create_context = BrowserContext._create_context
old_input_text = BrowserContext._create_context


@wraps(old_init)
def new_init(self, *args, **kw):
    old_init(self, *args, **kw)
    self._event_streams = SafeList()


@wraps(old_create_context)
async def new_create_context(self, *args, **kw):
    context = await old_create_context(self, *args, **kw)

    # Register event stream listener for all pages in this context
    async def _listen_stream(response) -> None:
        content_type = response.headers.get('content-type', '').lower()
        if content_type.startswith("text/event-stream"):
            await self._event_streams.append(response)

    context.on('page', lambda page: page.on('response', _listen_stream))
    return context


@time_execution_async('--input_text_element_node')
async def new_input_text(self, element_node: DOMElementNode, text: str):
    """
    Input text into an element with proper error handling and state management.
    Handles different types of input fields and ensures proper element state before input.
    """
    try:
        # Highlight before typing
        # if element_node.highlight_index is not None:
        # 	await self._update_state(focus_element=element_node.highlight_index)

        element_handle = await self.get_locate_element(element_node)

        if element_handle is None:
            raise BrowserError(f'Element: {repr(element_node)} not found')

        # Ensure element is ready for input
        try:
            await element_handle.wait_for_element_state('stable', timeout=1000)
            is_hidden = await element_handle.is_hidden()
            if not is_hidden:
                await element_handle.scroll_into_view_if_needed(timeout=1000)
        except Exception:
            pass

        # Get element properties to determine input method
        tag_handle = await element_handle.get_property('tagName')
        tag_name = (await tag_handle.json_value()).lower()
        is_contenteditable = await element_handle.get_property('isContentEditable')
        readonly_handle = await element_handle.get_property('readOnly')
        disabled_handle = await element_handle.get_property('disabled')

        readonly = await readonly_handle.json_value() if readonly_handle else False
        disabled = await disabled_handle.json_value() if disabled_handle else False

        await element_handle.fill(text)

    except Exception as e:
        logger.debug(f'❌  Failed to input text into element: {repr(element_node)}. Error: {str(e)}')
        raise BrowserError(f'Failed to input text into index {element_node.highlight_index}')

BrowserContext.__init__ = new_init
BrowserContext._create_context = new_create_context
BrowserContext._input_text_element_node = new_input_text
