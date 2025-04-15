from meowdock.cmd.execute.executors.executors_factory import get_executor
from meowdock.cmd.login.main import login
import asyncio
import sys


def main():
    # First login to Tencent Yuanbao
    login(urls=["https://yuanbao.tencent.com/chat/"])

    # Get command line argument as prompt, use default if not provided
    prompt = sys.argv[1] if len(sys.argv) > 1 else "给我讲一个冷笑话"

    print(f"Executing with Yuanbao using prompt: '{prompt}'...")
    print("Please wait a moment, we are getting the AI response...\n")

    # Get yuanbao executor
    executor = get_executor("yuanbao")

    # Execute the prompt
    result = asyncio.run(executor.execute(prompt=prompt))

    # Print the result
    print(result)

    print("\nExecution completed!")


if __name__ == "__main__":
    main()
