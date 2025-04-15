from browser_use import Controller, ActionResult
from browser_use.browser.context import BrowserContext
import json
from functools import wraps
from browser_use.controller.service import logger
from pydantic import BaseModel
from typing import Optional


old_init = Controller.__init__

class ClickElementByTextAction(BaseModel):
    text: str
    element_type: Optional[str]
    nth: int = 0

class WaitForElementAction(BaseModel):
	selector: str
	timeout: Optional[int] = 10000  # Timeout in milliseconds

@wraps(old_init)
def new_init(self, *args, **kw):
    old_init(self, *args, **kw)
    # Content Actions
    @self.registry.action(
        'Extract page content to retrieve specific information from the page, e.g. all company names, a specific description, all information about, links with companies in structured format or simply links',
    )
    async def extract_content(
        goal: str, should_strip_link_urls: bool, browser: BrowserContext,
    ):
        page = await browser.get_current_page()
        import markdownify

        strip = []
        if should_strip_link_urls:
            strip = ['a', 'img']

        content = markdownify.markdownify(await page.content(), strip=strip)

        # manually append iframe text into the content so it's readable by the LLM (includes cross-origin iframes)
        for iframe in page.frames:
            if iframe.url != page.url and not iframe.url.startswith('data:'):
                content += f'\n\nIFRAME {iframe.url}:\n'
                content += markdownify.markdownify(await iframe.content())
        out = {
            'data': content,
            'code': 0,
        }
        print(json.dumps(out, ensure_ascii=False))
        return ActionResult(extracted_content=content, include_in_memory=True)

    @self.registry.action('Click element with text', param_model=ClickElementByTextAction)
    async def click_element_by_text(params: ClickElementByTextAction, browser: BrowserContext):
        try:
            element_node = await browser.get_locate_element_by_text(
                text=params.text, nth=params.nth, element_type=params.element_type
            )

            if element_node:
                try:
                    is_hidden = await element_node.is_hidden()
                    if not is_hidden:
                        await element_node.scroll_into_view_if_needed()
                    await element_node.click(timeout=1500, force=True)
                except Exception:
                    try:
                        # Handle with js evaluate if fails to click using playwright
                        await element_node.evaluate('el => el.click()')
                    except Exception as e:
                        logger.warning(f"Element not clickable with text '{params.text}' - {e}")
                        return ActionResult(error=str(e))
                msg = f'🖱️  Clicked on element with text "{params.text}"'
                return ActionResult(extracted_content=msg, include_in_memory=True)
            else:
                return ActionResult(error=f"No element found for text '{params.text}'")
        except Exception as e:
            logger.warning(f"Element not clickable with text '{params.text}' - {e}")
            return ActionResult(error=str(e))

    @self.registry.action('Wait for element to be visible', param_model=WaitForElementAction)
    async def wait_for_element(params: WaitForElementAction, browser: BrowserContext):
        """Waits for the element specified by the CSS selector to become visible within the given timeout."""
        try:
            await browser.wait_for_element(params.selector, params.timeout)
            msg = f'👀  Element with selector "{params.selector}" became visible within {params.timeout}ms.'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            err_msg = f'❌  Failed to wait for element "{params.selector}" within {params.timeout}ms: {str(e)}'
            logger.error(err_msg)
            raise Exception(err_msg)

Controller.__init__ = new_init
