from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import decrypt_secret
from app.database import get_db
from app.models.github_account import GitHubAccount
from app.models.repository import Repository
from app.models.user import User
from app.services.mcp_client_service import MCPClientService

router = APIRouter(tags=["Pull Requests"])


def context(db: Session, user_id: int, repository_id: int):
    repository = db.get(Repository, repository_id)
    if repository is None or repository.user_id != user_id:
        raise HTTPException(status_code=404, detail="Repository not found")
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    return repository, decrypt_secret(account.access_token_encrypted)


@router.get("/repositories/{repository_id}/pull-requests")
async def list_pull_requests(repository_id: int, state: str = Query("open"), per_page: int = Query(30, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, repository_id)
    return await MCPClientService(get_settings().mcp_server_url).execute_tool("list_pull_requests", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "state": state, "per_page": per_page})


@router.get("/repositories/{repository_id}/pull-requests/{number}")
async def pull_request_details(repository_id: int, number: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, repository_id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    details = await mcp.execute_tool("get_pull_request_details", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "number": number})
    files = await mcp.execute_tool("get_pull_request_files", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "number": number})
    return {"details": details, "files": files}


@router.post("/repositories/{repository_id}/pull-requests/{number}/analyze")
async def analyze_pull_request(repository_id: int, number: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, repository_id)
    return await MCPClientService(get_settings().mcp_server_url).execute_tool("analyze_pull_request", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "number": number})
