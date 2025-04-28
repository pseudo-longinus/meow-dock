"""
Browser Utilities Module

Provides common functions for browser detection, initialization, and user agent management
"""

import os
import logging
import random
from typing import List, Dict, Optional, Any
import json


def init_logger():
    """Initialize logging system"""
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s: %(message)s',
        level=logging.INFO,
    )


def check_browser_executable(path: str) -> bool:
    """Check if browser executable exists and is executable"""
    if os.path.exists(path):
        logging.info(f"Browser found: {path}")
        # Check execution permission on Unix systems
        if os.name == 'posix':
            return os.access(path, os.X_OK)
        return True
    return False


_chrome_path: Optional[str] = None


def find_chromium() -> str:
    global _chrome_path
    if not _chrome_path:
        _chrome_path = _find_chromium()
    return _chrome_path


def _find_chromium() -> str:
    """Find system installed Chromium or Chrome browser path"""
    # Mac paths
    mac_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # Prioritize Chrome
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ]
    # Linux paths
    linux_paths = [
        '/usr/bin/google-chrome',  # Prioritize Chrome
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
    ]
    # Windows paths
    windows_paths = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Prioritize Chrome
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files\\Chromium\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Chromium\\Application\\chrome.exe',
    ]

    # Check environment variable
    chrome_path = os.environ.get('CHROME_PATH')
    if chrome_path:
        logging.info(f"Browser path obtained from CHROME_PATH environment variable: {chrome_path}")
        if check_browser_executable(chrome_path):
            return chrome_path
        else:
            logging.warning(
                f"Browser specified in CHROME_PATH does not exist or is not executable: {chrome_path}"
            )

    # Choose path list based on operating system
    if os.name == 'posix':  # Unix-like systems (Mac and Linux)
        if os.uname().sysname == 'Darwin':  # Mac
            paths = mac_paths
            system_name = "macOS"
        else:  # Linux
            paths = linux_paths
            system_name = "Linux"
    else:  # Windows
        paths = windows_paths
        system_name = "Windows"

    logging.debug(f"Searching for browser on {system_name} system...")

    # Check all possible paths
    for path in paths:
        logging.debug(f"Checking path: {path}")
        if check_browser_executable(path):
            logging.info(f"Will use browser: {path}")
            return path

    # If browser not found, provide detailed error information
    error_msg = f"""
Chrome or Chromium browser not found on {system_name} system.

Checked the following paths:
{chr(10).join(' - ' + path for path in paths)}

Please ensure one of the following browsers is installed:
1. Google Chrome
2. Chromium

Or set the CHROME_PATH environment variable to specify browser path:
export CHROME_PATH=/path/to/your/chrome  # macOS/Linux
set CHROME_PATH=C:\\path\\to\\your\\chrome.exe  # Windows
"""
    logging.error(error_msg)
    raise RuntimeError(error_msg)


def get_user_agents() -> List[str]:
    """Get list of common user agent strings"""
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    ]


def get_random_user_agent() -> str:
    """Get a random user agent string"""
    return random.choice(get_user_agents())


def get_default_headers() -> Dict[str, str]:
    """Get default request headers"""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


_cookies : Optional[List[Dict[str, Any]]] = None
def get_cookies() -> List[Dict[str, Any]]:
    global _cookies
    if _cookies is None:
        COOKIES_PATH = os.getenv('COOKIES_JSON_PATH', "cookies.json")
        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH, "r+", encoding="utf-8") as f:
                s = f.read()
                if len(s) > 2:
                    _cookies = json.loads(s)
        else:
            _cookies = []
    return _cookies
