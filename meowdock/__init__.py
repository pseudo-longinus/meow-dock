import meowdock.library.vendor_hacks
from meowdock import config
from meowdock.main import deepsearch
import meowdock.docking

__all__ = ["deepsearch", "cli", "docking"]


# CLI entry point
def cli():
    import typer
    from meowdock.main import app

    app()
