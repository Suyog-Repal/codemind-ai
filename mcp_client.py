from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from config import get_settings


class RemoteMCPClient:
    """Async client for the optional GitHub MCP streamable HTTP service."""

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None

    async def __aenter__(self) -> "RemoteMCPClient":
        if not self.api_key:
            raise RuntimeError(
                "GITHUB_MCP_TOKEN is not configured; GitHub MCP is disabled."
            )

        stack = AsyncExitStack()
        await stack.__aenter__()
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            http_client = create_mcp_http_client(headers=headers)
            await stack.enter_async_context(http_client)
            read_stream, write_stream = await stack.enter_async_context(
                streamable_http_client(self.server_url, http_client=http_client)
            )
            self.session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
        except Exception:
            await stack.__aexit__(None, None, None)
            raise

        self._exit_stack = stack
        return self

    async def __aexit__(self, *exc_info):
        if self._exit_stack is not None:
            await self._exit_stack.__aexit__(*exc_info)
        self._exit_stack = None
        self.session = None

    async def connect(self) -> "RemoteMCPClient":
        if self._exit_stack is None:
            await self.__aenter__()
        return self

    async def disconnect(self) -> None:
        if self._exit_stack is not None:
            await self.__aexit__(None, None, None)

    async def list_tools(self) -> list[dict]:
        if self.session is None:
            raise RuntimeError("GitHub MCP client is not connected.")
        result = await self.session.list_tools()
        return [{"name": t.name, "description": t.description} for t in result.tools]

    async def call_tool(self, tool_name: str, params: dict) -> dict:
        if self.session is None:
            raise RuntimeError("GitHub MCP client is not connected.")
        try:
            result = await self.session.call_tool(tool_name, params)
            return {"status": "success", "data": result.content}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}


def get_github_mcp_client() -> RemoteMCPClient:
    settings = get_settings()
    return RemoteMCPClient(settings.github_mcp_url, settings.github_mcp_token)
