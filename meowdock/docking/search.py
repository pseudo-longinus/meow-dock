import asyncio
from typing import List, Union, Optional, Dict, Any

from .docking_factory import Docking, DockingFactory
from ..cmd.search.scrapers.scraper_factory import get_scraper
from ..cmd.search.scrapers import ScrapeRequest, SearchResult
from ..cmd.fetch import Fetcher, FetchOptions, FetchResult


class SearchDocking(Docking):
    def __init__(self, engine: str):
        super().__init__()
        self.engine = engine

    def run(self, prompt: str, count: int = 5, *args, **kwargs) -> str:
        """
        执行搜索并获取结果

        Args:
            prompt: 搜索查询
            count: 搜索结果数量
            *args: 额外参数
            **kwargs: 额外关键字参数

        Returns:
            str: 搜索结果的markdown格式字符串
        """
        # 将异步调用转换为同步
        return asyncio.run(self._async_run(prompt, self.engine, count, *args, **kwargs))

    async def _async_run(
        self, prompt: str, engine: Union[str, List[str]], count: int, *args, **kwargs
    ) -> str:
        """异步执行搜索并获取结果"""
        # 处理单个或多个搜索引擎
        engines = [engine] if isinstance(engine, str) else engine

        # 搜集各引擎的搜索结果
        all_results = []
        for eng in engines:
            results = await self._search_engine(eng, prompt, count, **kwargs)
            all_results.extend(results)

        # 提取URL列表
        urls = [result.link for result in all_results if result.link]

        # 如果没有获得任何URL，返回错误信息
        if not urls:
            return "No search results found"

        # 获取URL内容
        content_dict = await self._fetch_urls(urls)

        # 格式化为markdown
        return self._format_as_markdown(all_results, content_dict)

    async def _search_engine(
        self, engine: str, query: str, count: int, **kwargs
    ) -> List[SearchResult]:
        """使用指定搜索引擎执行搜索"""
        try:
            scraper = get_scraper(engine, **kwargs)
            request = ScrapeRequest(
                term=query,
                count=count,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k in ['domain', 'sleep', 'proxy', 'language', 'geo', 'filters']
                },
            )
            return await scraper.scrape(request)
        except Exception as e:
            print(f"Search engine {engine} error: {str(e)}")
            return []

    async def _fetch_urls(self, urls: List[str]) -> Dict[str, str]:
        """获取URL内容"""
        fetcher = Fetcher()
        options = FetchOptions(
            timeout=30000,
            extractContent=True,
            disableMedia=True,
            returnHtml=False,
        )

        results = await fetcher.fetch(urls, options)

        # 构建URL到内容的映射
        url_to_content = {}
        for i, result in enumerate(results):
            if result.success and result.content:
                url_to_content[urls[i]] = result.content

        return url_to_content

    def _format_as_markdown(
        self, search_results: List[SearchResult], content_dict: Dict[str, str]
    ) -> str:
        """将搜索结果格式化为markdown字符串"""
        if not search_results:
            return "No search results found"

        markdown_lines = []

        for rank, result in enumerate(search_results, 1):
            # 添加分隔线（第一个结果除外）
            if rank > 1:
                markdown_lines.append("---")

            # 添加排名
            markdown_lines.append(f"- **rank: {rank}**")

            # 使用markdown链接格式
            url = result.link
            title = result.title
            markdown_lines.append(f"  **url:** [{title}]({url})")

            # 优先使用获取的内容，否则使用搜索摘要
            content = content_dict.get(url, result.snippet or "")
            if content:
                markdown_lines.append(f"  **content:**\n  {content}")
            else:
                markdown_lines.append(f"  **content:** _(No content)_")

            # 添加额外的空行
            markdown_lines.append("")

        return "\n\n".join(markdown_lines)


@DockingFactory.register("baidu")
class BaiduDocking(SearchDocking):
    def __init__(self):
        super().__init__("baidu")


@DockingFactory.register("bing")
class BingDocking(SearchDocking):
    def __init__(self):
        super().__init__("bing")
