"""
Resource control utility module

Provides browser resource loading control related functions.
"""

from typing import List, Set, Optional


# Default resource types to block
DEFAULT_BLOCK_RESOURCES = {
    "image",
    "stylesheet",
    "media",
    "script",
    "xhr",
    "font",
    "eventsource",
    "websocket",
}


async def abort_resource(route, block_resources: Optional[Set[str]] = None):
    """
    Block unnecessary resources from loading.

    Args:
        route: Playwright route object
        block_resources: Set of resource types to block, if None uses default settings

    Usage:
        # Use in Playwright
        await context.route("**/*", abort_resource)
    """
    if block_resources is None:
        block_resources = DEFAULT_BLOCK_RESOURCES

    if route.request.resource_type in block_resources:
        await route.abort()
    else:
        await route.continue_()


def get_minimal_resources() -> Set[str]:
    """
    Get minimal resource blocking set (only block media and fonts).

    Returns:
        Set of resource types to block
    """
    return {"image", "media", "font"}


def get_moderate_resources() -> Set[str]:
    """
    Get moderate resource blocking set (block media, fonts, and stylesheets).

    Returns:
        Set of resource types to block
    """
    return {"image", "media", "font", "stylesheet"}


def get_strict_resources() -> Set[str]:
    """
    Get strict resource blocking set (block all except HTML and documents).

    Returns:
        Set of resource types to block
    """
    return DEFAULT_BLOCK_RESOURCES
