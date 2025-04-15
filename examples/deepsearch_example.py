from meowdock import deepsearch
from meowdock.cmd.login.main import login
import sys
import os


def is_first_run() -> bool:
    first_run_path = f'./.cache/meowdock/deepsearch/firstrun'
    if os.path.exists(first_run_path):
        return False
    else:
        os.makedirs(os.path.dirname(first_run_path), exist_ok=True)
        with open(first_run_path, 'a+'):
            ...
        return True


def main():
    # First login to Tencent Yuanbao before using
    if is_first_run():
        login(urls=["https://yuanbao.tencent.com/chat/"])
    # Get command line argument as search keyword, use default if not provided
    query = sys.argv[1] if len(sys.argv) > 1 else "Why is gold rising"

    print(f"Executing search: '{query}'...")
    print("This may take some time, as we need to fetch the full content of each webpage...\n")

    # Search using default parameters
    result = deepsearch(query)
    print(result)

    print(
        "\nSearch completed! The results above contain full webpage content, not just search snippets."
    )
    print("This makes the results more comprehensive and informative.")


if __name__ == "__main__":
    main()
