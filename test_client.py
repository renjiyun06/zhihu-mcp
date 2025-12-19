"""Test client for Zhihu MCP server"""

import asyncio
from fastmcp import Client


async def main():
    # Connect to the running server via HTTP
    async with Client("http://localhost:8001/sse") as client:
        # List available tools
        print("Listing tools...")
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}\n")

        # Call publish_article tool
        print("Calling publish_article tool...")
        result = await client.call_tool(
            "publish_article",
            {
                "title": "测试文章标题 - DOM方式",
                "content": "这是一篇测试文章的内容。\n\n使用evaluate_script和DOM选择器方式实现。\n\n验证是否能正确填写标题和内容,并成功发布。"
            }
        )
        print(f"Result: {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
