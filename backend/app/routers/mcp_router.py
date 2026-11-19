from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.mcp_client_service import MCPClientError, MCPClientService

router = APIRouter(prefix="/mcp", tags=["MCP Management"])


class ExecuteRequest(BaseModel):
    tool_name: str = Field(max_length=150)
    arguments: dict = Field(default_factory=dict)


@router.get("/status")
async def status(current_user: User = Depends(get_current_user)):
    try:
        tools = await MCPClientService(get_settings().mcp_server_url).list_tools()
        return {"connected": True, "tool_count": len(tools)}
    except MCPClientError:
        return {"connected": False, "tool_count": 0}


@router.get("/tools")
async def tools(current_user: User = Depends(get_current_user)):
    try:
        return await MCPClientService(get_settings().mcp_server_url).list_tools()
    except MCPClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/tools/execute")
async def execute(payload: ExecuteRequest, current_user: User = Depends(get_current_user)):
    try:
        return await MCPClientService(get_settings().mcp_server_url).execute_tool(payload.tool_name, payload.arguments)
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
