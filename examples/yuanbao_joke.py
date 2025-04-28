"""
Example: Using YuanbaoDocking to interact with AI

This example demonstrates using YuanbaoDocking to request a joke
from the Yuanbao AI service.
"""

from meowdock.docking.docking_factory import DockingFactory
from meowdock.cmd.login.main import login
import sys


def main():
    # When the login is invalid, you need to use login.py to log in.
    login(urls=["https://yuanbao.tencent.com/chat/"])

    # Get command line argument as prompt, use default if not provided
    prompt = sys.argv[1] if len(sys.argv) > 1 else "给我讲一个冷笑话"

    print(f"Executing with Yuanbao using prompt: '{prompt}'...")
    print("Please wait a moment, we are getting the AI response...\n")

    # 使用DockingFactory获取yuanbao的docking实例
    factory = DockingFactory()
    yuanbao_docking = factory.get_docking("yuanbao")

    if not yuanbao_docking:
        print("Error: Yuanbao docking not found!")
        return

    # 使用docking的run方法执行prompt
    result = yuanbao_docking.run(prompt)

    # Print the result
    print(result)

    print("\nExecution completed!")


if __name__ == "__main__":
    main()
