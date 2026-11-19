from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import decrypt_secret
from app.database import get_db
from app.models.github_account import GitHubAccount
from app.models.repository import Repository
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import CreateChatSession, ChatMessageRequest
from app.services.ai_service import AIService
from app.services.mcp_client_service import MCPClientService

router = APIRouter(prefix="/chat", tags=["AI Chat"])


def owned_session(db: Session, session_id: int, user_id: int) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.post("/sessions", status_code=201)
def create_session(payload: CreateChatSession, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repository = db.get(Repository, payload.repository_id)
    if repository is None or repository.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")
    session = ChatSession(user_id=current_user.id, repository_id=repository.id, session_title=payload.session_title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions")
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc()).all()


@router.get("/sessions/{session_id}")
def get_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, session_id, current_user.id)
    return {"id": session.id, "session_title": session.session_title, "repository_id": session.repository_id, "messages": session.messages}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: int, payload: ChatMessageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, session_id, current_user.id)
    repository = db.get(Repository, session.repository_id)
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == current_user.id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")

    user_message = ChatMessage(session_id=session.id, role="user", message=payload.question, created_at=datetime.now(timezone.utc))
    db.add(user_message)

    token = decrypt_secret(account.access_token_encrypted)
    mcp = MCPClientService(get_settings().mcp_server_url)
    context: dict = {"repository": repository.full_name, "files": []}
    try:
        details = await mcp.execute_tool("get_repository_details", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name})
        context["repository_details"] = details
        readme = await mcp.execute_tool("get_repository_readme", {"access_token": token, "owner": repository.owner, "repo": repository.repository_name})
        context["readme"] = (readme.get("content", "") if isinstance(readme, dict) else "")[:20_000]
    except Exception:
        context["retrieval_warning"] = "Repository metadata could not be retrieved through MCP"

    history = [{"role": x.role, "content": x.message} for x in session.messages[-8:]]
    result = await AIService().answer(payload.question, context, history)

    assistant_message = ChatMessage(session_id=session.id, role="assistant", message=result["answer"], response_metadata={k: v for k, v in result.items() if k != "answer"}, created_at=datetime.now(timezone.utc))
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, session_id, current_user.id)
    db.delete(session)
    db.commit()
