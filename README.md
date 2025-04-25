# Meow Dock 🐈🚢

<!-- 可选：在此处添加 Logo -->
<!-- 可选：在此处添加徽章，例如： -->
<!-- ![Build Status](URL_TO_BUILD_STATUS_IMAGE) -->
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**为99%个人用户提供无需GPU卡，无需额外token花费，低延迟的Agent工具调用层。**

## 解决的问题

`Meow Dock` 通过本地化方案，模拟人类操作网站与软件，将常见的与电脑交互的意图（如AI问答、网络搜索等）封装成易于调用的模块化组件（MCP或函数），从而为 AI Agent 或工作流提供稳定的模块化操作层。

我们专注于提供一个适用于 **低算力、低延迟、高隐私、高稳定的自动化需求场景** 的解决方案。

## 目标用户

本项目主要服务于 **专注 Agent或工作流 开发的个人开发者与企业**，帮助你们快速为 Agent 集成强大，稳定的外部工具能力。

## 特性 ✨

*   **网站：** 将常用网站，每个网站对应一个类的子类的实例，网站的一个操作意图封装为一个方法，一一对应。
*   **低GPU要求，低延迟：** 常用网站操作使用本地化方式进行，无需消耗Token。
*   **无额外费用：** 将AI网站也封装成类，用户已有账户情况下，可调用相应方法获得推理能力，无需再花费API费用。
*   **高隐私：** 关键数据可本地化存储，不需要在第三方云端进行，适用于高隐私流程自动化场景。

## 安装 🛠️

**从源码安装**

1.  **克隆仓库：**
    ```bash
    git clone https://github.com/pseudo-longinus/meow-dock.git     # 打开一个命令行（windows cmd或者powershell），使用命令克隆代码
    cd meow-dock  # 进入文件夹
    ```

2.  **创建虚拟环境，需要 Python>=3.11 :**
    ```bash
    python -m venv .venv        # 创建一个虚拟环境
    .venv\Scripts\activate      # 如果是Windows环境，使用这个命令激活
    #source .venv/bin/activate  # 如果是Linux/macOS环境，使用这个命令激活
    ```

3.  **安装依赖和项目：**
    ```bash
    pip install -e . -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
    ```


## 使用方法1 🚀
我是工程师，我想创建自己的工作流：

```python
from meowdock import deepsearch
import sys


def main():
    # 如果是第一次使用，需要先登录腾讯元宝
    # login(urls=["https://yuanbao.tencent.com/chat/"])
    # 获取命令行参数作为搜索关键词，如果没有则使用默认值
    query = sys.argv[1] if len(sys.argv) > 1 else "黄金为什么涨"

    print(f"正在执行搜索: '{query}'...")
    print("这可能需要一些时间，因为我们需要抓取每个网页的完整内容...\n")

    # 使用默认参数搜索
    result = deepsearch(query)
    print(result)

    print("\n搜索完成！以上结果包含了完整的网页正文内容，而不仅是搜索摘要。")
    print("这使得结果更加丰富和信息量更大。")


if __name__ == "__main__":
    main()
```

## 使用方法2 🚀

通过命令行使用（安装后）：

目前支持通过命令行进行网页搜索：

```bash
# 使用搜索引擎搜索并返回结构化数据
meowdock search "[你的搜索关键词]" --count [结果数量] --engine [搜索引擎名称]
# 使用多引擎深度搜索，抓取完整的网页内容并使用AI处理结果
meowdock deepsearch "[你的问题]" --engines [搜索引擎名称] --count [web搜索的数量] --executor [AI应用名称]
# 直接使用AI执行提示词
meowdock execute "[你的提示词]" [AI应用名称]
```

**示例：**

```bash
# 使用 Bing 搜索 15 条关于"大型语言模型"的结果
meowdock search "大型语言模型" --count 15 --engine bing

# 使用多引擎深度搜索，自动抓取网页内容并使用元宝处理结果
meowdock deepsearch "大语言模型的应用" --engines baidu,bing --count 15 --executor yuanbao

# 使用腾讯元宝让AI讲一个冷笑话
meowdock execute "给我讲一个冷笑话" yuanbao
```

## 项目结构 🏗️

```.
├── meowdock/           # 核心库代码
│   ├── __init__.py
│   ├── main.py         # 命令行入口
│   ├── agent/          # 组合命令相关模块
│   ├── cmd/            # 存放各个命令的具体实现
│   │   ├── search/     # 搜索命令相关模块
│   │   ├── fetch/      # 网页获取模块
│   │   ├── execute/    # 执行命令模块
│   │   └── login/      # 登录模块
│   ├── config.py       # 配置管理
│   ├── library/        # 通用库或辅助函数
|   └── resource/       # 资源文件 （xpath配置等）
├── setup.py            # 项目安装配置
├── LICENSE             # Apache 2.0 许可证
└── README.md           # 就是你正在看的这个文件
```

## 资源文件更新说明 🗂️

如果你需要获取最新的资源文件（如搜索引擎适配、xpath配置等），请按照以下步骤操作：

```bash
git pull origin main
```

这样可以确保你本地的资源文件和代码保持最新。


## 贡献指南 🤝

(待补充 - 欢迎贡献！请先查阅 CONTRIBUTING.md 文件或提交 Issue 讨论你想做的改进。)

## 许可证 📄

本项目采用 [Apache License 2.0](LICENSE) 授权。



