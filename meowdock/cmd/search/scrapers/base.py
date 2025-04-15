from abc import ABCMeta, abstractmethod
from random import choice
from typing import Dict, List, Optional
from aiohttp import ClientSession, ClientError
from meowdock.cmd.search.const import _USER_AGENTS


class BlockedException(Exception):
    pass


class ConfigException(Exception):
    pass


class ScrapeRequest:
    def __init__(
        self,
        term: str,
        count: int,
        domain: Optional[str] = None,
        sleep: int = 0,
        proxy: Optional[str] = None,
        language: Optional[str] = None,
        geo: Optional[str] = None,
        filters: Dict = {},
    ):
        self.term = term
        self.count = count
        self.domain = domain
        self.sleep = sleep
        self.proxy = proxy
        self.language = language
        self.geo = geo
        self.filters = filters


class SearchResult:
    def __init__(
        self,
        rank: int,
        link: int,
        title: str,
        snippet: str,
    ):
        self.rank = rank
        self.link = link
        self.title = title
        self.snippet = snippet

    def __repr__(self):
        return "<SearchResult: Rank:{}, URL: {}>".format(self.rank, self.link)


class ScrapeResponse:
    def __init__(self, html: str, status: int, json: Optional[Dict] = None):
        self.html = html
        self.json = json
        self.status = status

    def __repr__(self):
        return "<ScrapeResponse: html:{}, status:{}>".format(
            self.html[:10],
            self.status,
        )


class SearchScraper(metaclass=ABCMeta):
    @staticmethod
    def user_agent() -> Dict[str, str]:
        return {
            "User-Agent": choice(_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def _scrape_one(
        self, url: str, headers: Dict[str, str], proxy: Optional[str]
    ) -> ScrapeResponse:
        async with ClientSession() as client:
            try:
                async with client.get(url, headers=headers, proxy=proxy, timeout=60) as response:
                    html = await response.text()
                    return ScrapeResponse(html, response.status)
            except ClientError as err:
                raise err

    @abstractmethod
    def _check_exceptions(self, res: ScrapeResponse) -> None:
        pass

    @abstractmethod
    def _paginate(self, term: str, domain: str, language: str, count: int) -> List[str]:
        pass

    @abstractmethod
    async def scrape(self, request: ScrapeRequest) -> List[SearchResult]:
        pass
