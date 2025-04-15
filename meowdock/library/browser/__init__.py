"""
Browser-related utility library

Provides browser detection, resource control, and content extraction functions.
"""

from .browser_utils import (
    find_chromium,
    check_browser_executable,
    init_logger,
    get_user_agents,
    get_random_user_agent,
    get_default_headers,
    get_cookies,
)
from .content_utils import extract_main_content, extract_chinese_content
from .resource_utils import (
    abort_resource,
    get_minimal_resources,
    get_moderate_resources,
    get_strict_resources,
)

__all__ = [
    "find_chromium",
    "check_browser_executable",
    "init_logger",
    "get_user_agents",
    "get_random_user_agent",
    "get_default_headers",
    "get_cookies",
    "extract_main_content",
    "extract_chinese_content",
    "abort_resource",
    "get_minimal_resources",
    "get_moderate_resources",
    "get_strict_resources",
]
