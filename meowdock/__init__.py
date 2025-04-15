import meowdock.library.vendor_hacks
from meowdock import config
from meowdock.cmd.search import deepsearch

__all__ = ["deepsearch", "cli"]


# CLI entry point
def cli():
    import typer
    from meowdock.main import app

    app()
