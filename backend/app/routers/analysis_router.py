from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import decrypt_secret
from app.database import get_db
from app.models.analysis_report import AnalysisReport
from app.models.github_account import GitHubAccount
from app.models.repository import Repository
from app.models.user import User
from app.services.mcp_client_service import MCPClientService

router = APIRouter(prefix="/analysis", tags=["Code Analysis"])


class FileAnalysisRequest(BaseModel):
    repository_id: int
    path: str


class RepositoryAnalysisRequest(BaseModel):
    repository_id: int


def context(db: Session, user_id: int, repository_id: int):
    repository = db.get(Repository, repository_id)
    if repository is None or repository.user_id != user_id:
        raise HTTPException(status_code=404, detail="Repository not found")
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    return repository, decrypt_secret(account.access_token_encrypted)


@router.post("/file")
async def analyze_file(payload: FileAnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, payload.repository_id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    result = await mcp.execute_tool("analyze_python_code", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "path": payload.path})
    report = AnalysisReport(user_id=current_user.id, repository_id=repository.id, analysis_type="file", report_title=f"Analysis of {payload.path}", report_content=str(result), severity="warning" if result.get("verified_static_findings") else "info", status="completed")
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "result": result}


@router.post("/repository")
async def analyze_repository(payload: RepositoryAnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, payload.repository_id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    tree = await mcp.execute_tool("get_repository_tree", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "ref": repository.default_branch, "recursive": True})
    report = AnalysisReport(user_id=current_user.id, repository_id=repository.id, analysis_type="repository", report_title="Repository structure analysis", report_content=str(tree), severity="info", status="completed")
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "tree": tree}


@router.post("/security")
async def security(payload: RepositoryAnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, payload.repository_id)
    mcp = MCPClientService(get_settings().mcp_server_url)
    result = await mcp.execute_tool("find_todo_comments", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name, "ref": repository.default_branch})
    report = AnalysisReport(user_id=current_user.id, repository_id=repository.id, analysis_type="security", report_title="Security review", report_content=str(result), severity="warning", status="completed")
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "verified_static_findings": [], "todo_markers": result, "ai_suggestions": ["Run Semgrep or Bandit in CI before production deployment."]}


@router.post("/code-quality")
async def code_quality(payload: RepositoryAnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository, token = context(db, current_user.id, payload.repository_id)
    return await analyze_repository(payload, current_user, db)


@router.get("/reports")
def reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(AnalysisReport).filter(AnalysisReport.user_id == current_user.id).order_by(AnalysisReport.created_at.desc()).all()


@router.get("/reports/{report_id}")
def report(report_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(AnalysisReport, report_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    return item
