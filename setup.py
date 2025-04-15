from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="meowdock",
    version="0.1.1",
    author="MeowDock Team",
    author_email="guanzhao3000@gmail.com",
    description="Web content retrieval, search, and interaction toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pseudo-longinus/meow-dock",
    packages=find_namespace_packages(include=["meowdock", "meowdock.*"]),
    include_package_data=True,
    package_data={
        'meowdock': ['cmd/**/*', 'resources/**/*'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "typer>=0.9.0",
        "aiohttp>=3.8.4",
        "beautifulsoup4>=4.12.2",
        "python-dotenv>=1.0.0",
        "asyncio>=3.4.3",
        "httpx>=0.27.2",
        "requests>=2.32.3",
        "posthog>=3.7.0",
        "playwright>=1.51.0",
        "typing-extensions>=4.12.2",
        "html2text>=2020.1.16",
        "readability-lxml>=0.8.1",
        "lxml>=5.3.2",
        "lxml_html_clean>=0.4.1",
        "browser-use==0.1.41",
        "numpy>=2.1.0",
        "pywin32>=307",
    ],
    entry_points={
        "console_scripts": [
            "meowdock=meowdock:cli",
        ],
    },
)
