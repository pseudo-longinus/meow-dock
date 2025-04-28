# Meow Dock 🐈🚢
<p align="center">
  <img src="logo.png" alt="Project Logo" width="700"/>
</p>

[中文版](README.md) | English

<!-- Optional: Add Logo here -->
<!-- Optional: Add badges, e.g.: -->
<!-- ![Build Status](URL_TO_BUILD_STATUS_IMAGE) -->
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**A tool for 99% of personal edge devices, providing stable, low-latency, high-reliability operations without requiring a GPU or extra API compute purchases.**

## Problem Solved

Our goal is to encapsulate common operations on personal edge devices (e.g., searching the web and then asking an AI) into stable, low-latency, GPU-free modular components (MCPs or functions), bridging the last mile between AI and device operations.

## Target Users

This project mainly serves **individual developers and enterprises working on Agents, workflow automation, or other edge device operation scenarios**.

## Features ✨

*   **Functionality:** Operate websites/software with a single Python command. Currently supports: Baidu Search and Yuanbao Q&A
*   **Characteristics:**
*    (1). All supported website/software operations are performed on CPU, with no need for GPU or third-party LLM APIs, resulting in faster response times
*    (2). No need for users to purchase extra API compute resources, making it cost-effective
*    (3). Compared to pure cloud solutions, local operation offers better privacy


## Installation 🛠️

**Install from Source**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pseudo-longinus/meow-dock.git     # Open a command line (Windows cmd or PowerShell) and use the command to clone the code
    cd meow-dock  # Enter the folder
    ```

2.  **Create a virtual environment, requires Python>=3.12:**
    ```bash
    python -m venv .venv        # Create a virtual environment
    .venv\Scripts\activate      # If you're on Windows, use this command to activate
    #source .venv/bin/activate  # If you're on Linux/macOS, use this command to activate
    ```

3.  **Install dependencies and the project:**
    ```bash
    pip install -e . -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
    ```


## Example 1: Ask Yuanbao for a Joke and Get the Result 🚀

```python
from meowdock.docking.docking_factory import DockingFactory
from meowdock.cmd.login.main import login
import sys


def main():
    # If this is your first time, you need to log in to Tencent Yuanbao
    login(urls=["https://yuanbao.tencent.com/chat/"])

    prompt = "Tell me a cold joke"
    print(f"Executing with Yuanbao using prompt: '{prompt}'...")
    # Use DockingFactory to get the yuanbao docking instance
    factory = DockingFactory()
    yuanbao_docking = factory.get_docking("yuanbao")
    # Use the docking's run method to execute the prompt
    result = yuanbao_docking.run(prompt)
    print(result)

if __name__ == "__main__":
    main()

```

# Example 2: Search and Summarize
```python
from meowdock.docking.docking_factory import DockingFactory
from meowdock.cmd.login.main import login


def main():
    # When login is invalid, you need to use login.py to log in.
    # login(urls=["https://yuanbao.tencent.com/chat/"])
    # Define parameters
    search_query = "Why is gold rising"
    search_engine = "bing"

    try:
        # Initialize factory and get docking instances
        factory = DockingFactory()
        # Get search docking instance
        search_docking = factory.get_docking(search_engine)
        print(f"Searching for '{search_query}' using {search_engine}...")
        search_results = search_docking.run(search_query)
        if not search_results:
            print("No search results found.")
            return
        print("search_results:", search_results)
        yuanbao_docking = factory.get_docking("yuanbao")
        # Process search results with Yuanbao
        print("Processing search results with AI...")
        combined_prompt = f"Please summarize the key points about {search_query} based on these search results:\n\n{search_results}"
        analysis_result = yuanbao_docking.run(combined_prompt)

        # Display the analysis
        print("\nAnalysis result:")
        print("-" * 40)
        print(analysis_result)
        print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    main()
```

## Project Structure 🏗️

```
.
├── meowdock/           # Core library code
│   ├── __init__.py
│   ├── main.py         # Command line entry
│   ├── agent/          # Combined command related modules
│   ├── cmd/            # Stores specific implementations of each command
│   │   ├── search/     # Search command related modules
│   │   ├── fetch/      # Webpage retrieval module
│   │   ├── execute/    # Execute command module
│   │   └── login/      # Login module
│   ├── config.py       # Configuration management
│   ├── library/        # Common libraries or helper functions
│   └── resources/      # Resource files (xpath configurations, etc.)
├── setup.py            # Project installation configuration
├── LICENSE             # Apache 2.0 license
└── README.md           # Documentation file
```

## FAQ 🗂️

1. Do I need to log in to the website?
Yes, you do. However, since the program uses its own browser, you need to run login.py to log in, not log in directly from your usual browser. We will develop a better login management module soon.

2. What websites are currently supported?
Currently, Yuanbao and Baidu Search are supported, and more will be added. You can submit the websites you want to be supported here:
English version
https://docs.qq.com/form/page/DWUZVU2hZbk5DSXVm

Chinese version
https://docs.qq.com/form/page/DWU9rZU5nTVFqT0JN


3. Why might it not work?
It may be because the target website/software interface or version has changed. You can try pulling the latest updates and try again:
```bash
git pull origin main
```

If you still encounter problems, please submit the log file log\executor\xxx.zip to the issue tracker or email guanzhao3000@gmail.com. We will analyze the failure and optimize the code.



## License 📄

This project is open source (community version) and licensed under the [Apache License 2.0](LICENSE).

## Third-party libraries:

This project uses the following third-party libraries, which are licensed under the MIT License:

- [Browser-Use](https://github.com/browser-use/browser-use) Browser Use: Enable AI to control your browser
  - License: MIT
  - Copyright: Müller, Magnus and Žunič, Gregor (2024)
  - Modifications: Modified for Adaptation for web docking
  - License: [LICENSE](https://opensource.org/licenses/MIT) 