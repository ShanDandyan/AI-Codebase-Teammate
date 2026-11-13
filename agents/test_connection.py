import asyncio
import os
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER_PATH = r"C:\Users\shaan\Desktop\AI Codebase Teamate\mcp_server\server.py"


async def main():
    print("--- CONNECTING TO MCP SERVER OVER STDIO ---")

    client = MultiServerMCPClient(
        {
            "codebase": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [SERVER_PATH],
            }
        }
    )

    tools = await client.get_tools()

    print(f"\nSuccessfully connected! Found {len(tools)} tool(s):\n")
    for tool in tools:
        print(f" - Tool Name : {tool.name}")
        print(f"   Description: {tool.description}\n")


if __name__ == "__main__":
    if not os.path.exists(SERVER_PATH):
        raise FileNotFoundError(
            f"Could not find mcp_server/server.py at path: {SERVER_PATH}"
        )

    asyncio.run(main())