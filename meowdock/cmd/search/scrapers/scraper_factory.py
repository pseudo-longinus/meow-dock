from typing import Dict, Type
from warnings import warn
from meowdock.cmd.search.scrapers.base import SearchScraper

# Register available search engines
_SCRAPERS: Dict[str, Type[SearchScraper]] = {}


def register(name):
    def deco(cls: Type[SearchScraper]):
        if not issubclass(cls, SearchScraper):
            warn(
                f'WARNING: {cls.__name__} is not a subclass of ExecutorWrapper.')
        if name in _SCRAPERS.keys():
            warn(f'WARNING: {name} ExecutorWrapper has been rewritten.')
        _SCRAPERS[name] = cls
        return cls
    return deco


def get_scraper(engine: str, **kwargs) -> SearchScraper:
    """
    Factory method that returns a search engine instance based on the engine name

    Args:
        engine: Search engine name, e.g. 'bing'
        **kwargs: Parameters passed to the search engine constructor

    Returns:
        SearchScraper: Search engine instance

    Raises:
        ValueError: If the specified engine is not supported
    """
    engine = engine.lower().strip()

    if engine not in _SCRAPERS:
        supported = ", ".join(_SCRAPERS.keys())
        raise ValueError(f"Unsupported search engine: {engine}. Supported engines: {supported}")

    return _SCRAPERS[engine](**kwargs)
