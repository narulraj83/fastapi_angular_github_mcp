from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import decrypt_secret
from app.database import get_db
from app.models.github_account import GitHubAccount
from app.models.repository import Repository
from app.models.user import User
from app.services.github_service import GitHubService
from app.services.mcp_client_service import MCPClientService

router = APIRouter(prefix="/repositories", tags=["Repositories"])


class ConnectRepository(BaseModel):
    owner: str
    repo: str


def _account(db: Session, user_id: int) -> GitHubAccount:
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    return account


def _owned(db: Session, repository_id: int, user_id: int) -> Repository:
    repository = db.get(Repository, repository_id)
    if repository is None or repository.user_id != user_id:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


@router.post("/connect", status_code=201)
async def connect(payload: ConnectRepository, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = _account(db, current_user.id)
    token = decrypt_secret(account.access_token_encrypted)
    data = await GitHubService(token).get_repository(payload.owner, payload.repo)
    repository = db.query(Repository).filter(Repository.full_name == data["full_name"], Repository.user_id == current_user.id).first()
    if repository is None:
        repository = Repository(user_id=current_user.id)
        db.add(repository)
    repository.github_repo_id = str(data["id"])
    repository.owner = data["owner"]["login"]
    repository.repository_name = data["name"]
    repository.full_name = data["full_name"]
    repository.description = data.get("description")
    repository.default_branch = data["default_branch"]
    repository.visibility = data["visibility"]
    repository.html_url = data["html_url"]
    db.commit()
    db.refresh(repository)
    return repository


@router.get("")
def list_repositories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Repository).filter(Repository.user_id == current_user.id).order_by(Repository.updated_at.desc()).all()


@router.get("/{repository_id}")
def details(repository_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned(db, repository_id, current_user.id)


@router.get("/{repository_id}/tree")
async def tree(repository_id: int, ref: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository = _owned(db, repository_id, current_user.id)
    account = _account(db, current_user.id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    return await mcp.execute_tool("get_repository_tree", {"access_token": decrypt_secret(account.access_token_encrypted), "owner": repository.owner, "repo": repository.repository_name, "ref": ref or repository.default_branch, "recursive": True})


@router.get("/{repository_id}/readme")
async def readme(repository_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository = _owned(db, repository_id, current_user.id)
    account = _account(db, current_user.id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    return await mcp.execute_tool("get_repository_readme", {"access_token": decrypt_secret(account.access_token_encrypted), "owner": repository.owner, "repo": repository.repository_name})


@router.get("/{repository_id}/branches")
async def branches(repository_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository = _owned(db, repository_id, current_user.id)
    account = _account(db, current_user.id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    return await mcp.execute_tool("get_repository_branches", {"access_token": decrypt_secret(account.access_token_encrypted), "owner": repository.owner, "repo": repository.repository_name})


@router.get("/{repository_id}/files")
async def files(repository_id: int, path: str = "", ref: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository = _owned(db, repository_id, current_user.id)
    account = _account(db, current_user.id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    return await mcp.execute_tool("list_files", {"access_token": decrypt_secret(account.access_token_encrypted), "owner": repository.owner, "repo": repository.repository_name, "path": path, "ref": ref or repository.default_branch})


@router.get("/{repository_id}/files/content")
async def file_content(repository_id: int, path: str = Query(...), ref: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository = _owned(db, repository_id, current_user.id)
    account = _account(db, current_user.id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    return await mcp.execute_tool("get_file_content", {"access_token": decrypt_secret(account.access_token_encrypted), "owner": repository.owner, "repo": repository.repository_name, "path": path, "ref": ref or repository.default_branch})
