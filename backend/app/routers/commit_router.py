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

router = APIRouter(tags=["Commits"])


def repository_context(db: Session, user_id: int, repository_id: int):
    repository = db.get(Repository, repository_id)
    if repository is None or repository.user_id != user_id:
        raise HTTPException(status_code=404, detail="Repository not found")
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    return repository, decrypt_secret(account.access_token_encrypted)


@router.get("/repositories/{repository_id}/commits")
async def commits(repository_id: int, sha: str | None = None, per_page: int = Query(30, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = repository_context(db, current_user.id, repository_id)
    return await MCPClientService(get_settings().mcp_server_url).execute_tool("get_commits", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "sha": sha, "per_page": per_page})


@router.get("/repositories/{repository_id}/commits/{commit_sha}")
async def commit_details(repository_id: int, commit_sha: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = repository_context(db, current_user.id, repository_id)
    return await MCPClientService(get_settings().mcp_server_url).execute_tool("get_commit_details", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "sha": commit_sha})


@router.get("/repositories/{repository_id}/compare")
async def compare(repository_id: int, base: str = Query(...), head: str = Query(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = repository_context(db, current_user.id, repository_id)
    return await MCPClientService(get_settings().mcp_server_url).execute_tool("compare_branches", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "base": base, "head": head})
