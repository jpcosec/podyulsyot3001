import asyncio
import json
from langchain_mcp_adapters.tools import load_mcp_tools

async def main():
    mcp_url = "http://127.0.0.1:9000/mcp"
    print(f"Connecting to {mcp_url}...")
    try:
        tools = await load_mcp_tools(mcp_url)
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"  Description: {tool.description}")
            print(f"  Args: {tool.args_schema.schema() if hasattr(tool, 'args_schema') else 'No schema'}")
            print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
