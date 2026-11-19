from typing import Any


class MCPClientError(RuntimeError):
    pass


class MCPClientService:
    def __init__(self, server_url: str):
        self.server_url = server_url

    async def list_tools(self) -> list[dict[str, Any]]:
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
            async with streamable_http_client(self.server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return [tool.model_dump() for tool in result.tools]
        except Exception as exc:
            raise MCPClientError(f"Unable to connect to MCP server: {exc}") from exc

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        allowed = {
            "list_repositories", "get_repository_details", "get_repository_branches",
            "get_repository_languages", "get_repository_readme", "get_repository_tree",
            "get_repository_contributors", "get_file_content", "list_files", "search_code",
            "find_todo_comments", "analyze_python_code", "find_unused_imports",
            "analyze_code_complexity", "get_commits", "get_commit_details",
            "compare_commits", "compare_branches", "list_pull_requests",
            "get_pull_request_details", "get_pull_request_files", "analyze_pull_request",
            "list_issues",
        }
        if name not in allowed:
            raise MCPClientError("Tool is not on the authorized allowlist")
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
            async with streamable_http_client(self.server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(name, arguments)
                    if result.isError:
                        raise MCPClientError("MCP tool execution failed")
                    if result.structuredContent:
                        structured = result.structuredContent
                        if isinstance(structured, dict) and "result" in structured:
                            return structured["result"]
                        return structured
                    if result.content:
                        return [{"type": item.type, "text": getattr(item, "text", None)} for item in result.content]
                    return {"ok": True}
        except MCPClientError:
            raise
        except Exception as exc:
            raise MCPClientError(f"Unable to execute MCP tool: {exc}") from exc
