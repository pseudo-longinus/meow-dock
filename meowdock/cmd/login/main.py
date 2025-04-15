from playwright.async_api import async_playwright
import json
import os
import sys
import asyncio
from meowdock.library.browser import find_chromium, get_cookies
import typer
from typing_extensions import Annotated
from typing import List, Optional


app = typer.Typer(help="Login and save cookies")


CHROME_PATH = find_chromium()
COOKIES_PATH = os.getenv('COOKIES_JSON_PATH', "cookies.json")
USER_DATA_DIR = os.getenv('CHROME_USER_DATA_PATH', 'chrome_data/')

tracked_pages = set()
cookies = get_cookies()


async def track_new_page(page):
    tracked_pages.add(page)
    page.on("close", on_page_close)


async def on_page_close(page):
    global cookies, COOKIES_PATH
    tracked_pages.discard(page)
    cookies = (await page.context.cookies())
    with open(COOKIES_PATH, 'w+', encoding='utf-8') as f:
        f.write(json.dumps(cookies, ensure_ascii=False))


async def alogin(urls=[]):
    global cookies
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(user_data_dir=USER_DATA_DIR, executable_path=CHROME_PATH, headless=False, args=['--disable-blink-features=AutomationControlled'])
        await context.add_cookies(cookies)
        if len(urls) > 0:
            for url in urls:
                page = await context.new_page()
                await page.goto(url)
        else:
            page = await context.new_page()

        for page in context.pages:
            tracked_pages.add(page)
            page.on('close', on_page_close)

        context.on("page", track_new_page)

        while tracked_pages:
            await asyncio.sleep(.2)

        print({'code': 0, 'data': 'success'})


@app.command()
def login(urls: Optional[List[str]] = typer.Option([], "--url", '-u', help="Initially opened urls")):
    asyncio.run(alogin(urls=urls))
