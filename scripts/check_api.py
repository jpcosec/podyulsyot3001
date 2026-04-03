import asyncio
import os
from src.core.api_client import LangGraphAPIClient

async def main():
    try:
        url = LangGraphAPIClient.ensure_server(port=8130)
        client = LangGraphAPIClient(url)
        assistants = await client.client.assistants.search()
        print("Registered assistants:")
        for a in assistants:
            print(f"- {a['assistant_id']} (graph: {a['graph_id']})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
