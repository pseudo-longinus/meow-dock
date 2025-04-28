"""
Example: Using Docking classes for Search and Execute functionality

This example demonstrates using docking interfaces for search and AI processing:
1. Search for information using a search engine docking
2. Process the results with YuanbaoDocking
"""

from meowdock.docking.docking_factory import DockingFactory
from meowdock.cmd.login.main import login


def main():
    # When the login is invalid, you need to use login.py to log in.
    # login(urls=["https://yuanbao.tencent.com/chat/"])
    # Define parameters
    search_query = "黄金为什么涨"
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
        # Process search results with yuanbao
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
