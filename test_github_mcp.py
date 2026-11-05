import asyncio
from mcp_client import get_github_mcp_client
from config import get_settings


async def main():
    client = get_github_mcp_client()
    await client.connect()

    tools = await client.list_tools()
    print(f"Connected. {len(tools)} tools available:\n")
    for t in tools:
        print(f"- {t['name']}: {t['description']}")

    await client.disconnect()


asyncio.run(main())