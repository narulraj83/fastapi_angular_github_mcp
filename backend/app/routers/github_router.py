from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from jose import JWTError
from sqlalchemy.orm import Session
import secrets

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token, decrypt_secret, encrypt_secret, decode_token, hash_password
from app.database import get_db
from app.models.github_account import GitHubAccount
from app.models.user import User
from app.models.repository import Repository
from app.services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["GitHub"])
settings = get_settings()


@router.get("/signin")
def signin():
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env.")
    state = create_access_token("github-signin")
    return {"authorization_url": GitHubService().authorization_url(state)}


@router.get("/connect")
def connect(current_user: User = Depends(get_current_user)):
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env.")
    state = create_access_token(str(current_user.id))
    return {"authorization_url": GitHubService().authorization_url(state)}


@router.get("/callback")
async def callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    try:
        payload = decode_token(state, "access")
        subject = payload["sub"]
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    data = await GitHubService().exchange_code(code)
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail=data.get("error_description", "GitHub OAuth failed"))

    github = GitHubService(token)
    profile = await github.get_profile()

    if subject == "github-signin":
        account = db.query(GitHubAccount).filter(GitHubAccount.github_user_id == str(profile["id"])).first()

        if account is None:
            email = profile.get("email") or f"{profile['login']}@users.noreply.github.com"
            user = db.query(User).filter(User.email == email).first()

            if user is None:
                base_username = str(profile["login"])
                username = base_username
                suffix = 1
                while db.query(User).filter(User.username == username).first() is not None:
                    username = f"{base_username}-{suffix}"
                    suffix += 1
                user = User(
                    username=username,
                    email=email,
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    is_active=True,
                )
                db.add(user)
                db.flush()

            account = GitHubAccount(user_id=user.id)
            db.add(account)

        account.github_username = profile["login"]
        account.github_user_id = str(profile["id"])
        account.access_token_encrypted = encrypt_secret(token)
        db.commit()
        db.refresh(account)

        access_token = create_access_token(str(account.user_id))
        refresh_token = create_refresh_token(str(account.user_id))
        fragment = f"access_token={access_token}&refresh_token={refresh_token}"
        response = RedirectResponse(url=f"{settings.frontend_url}/auth/callback#{fragment}")

        await sync_repositories(db, account.user_id, token)

        return response

    try:
        user_id = int(subject)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
    if account is None:
        account = GitHubAccount(user_id=user_id)
        db.add(account)
    account.github_username = profile["login"]
    account.github_user_id = str(profile["id"])
    account.access_token_encrypted = encrypt_secret(token)
    db.commit()

    await sync_repositories(db, user_id, token)

    return RedirectResponse(url=f"{settings.frontend_url}/dashboard?github=connected")


@router.delete("/disconnect")
def disconnect(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == current_user.id).first()
    if account:
        db.delete(account)
        db.commit()
    return {"ok": True}


@router.get("/profile")
async def profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == current_user.id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    return await GitHubService(decrypt_secret(account.access_token_encrypted)).get_profile()


@router.get("/repositories")
async def repositories(page: int = Query(1, ge=1), per_page: int = Query(30, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == current_user.id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    return await GitHubService(decrypt_secret(account.access_token_encrypted)).list_repositories(page, per_page)


@router.get("/connect/status")
def connect_status(current_user: User = Depends(get_current_user)):
    configured = bool(settings.github_client_id and settings.github_client_secret)
    return {"configured": configured, "message": "GitHub OAuth is configured" if configured else "Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to backend/.env"}


@router.post("/sync")
async def sync(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == current_user.id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="GitHub account is not connected")
    token = decrypt_secret(account.access_token_encrypted)
    count = await sync_repositories(db, current_user.id, token)
    return {"synced": count}


async def sync_repositories(db: Session, user_id: int, access_token: str) -> int:
    """Sync GitHub repositories into the application's local repository records."""

    repositories = await GitHubService(access_token).list_repositories(per_page=100)
    synced = 0

    for data in repositories:
        if not data.get("full_name"):
            continue

        repository = db.query(Repository).filter(
            (Repository.user_id == user_id)
            & (
                (Repository.github_repo_id == str(data["id"]))
                | (Repository.full_name == data["full_name"])
            )
        ).first()

        if repository is None:
            repository = Repository(user_id=user_id)
            db.add(repository)

        repository.github_repo_id = str(data["id"])
        repository.owner = data["owner"]["login"]
        repository.repository_name = data["name"]
        repository.full_name = data["full_name"]
        repository.description = data.get("description")
        repository.default_branch = data.get("default_branch") or "main"
        repository.visibility = data.get("visibility") or "public"
        repository.html_url = data["html_url"]
        synced += 1

    db.commit()
    return synced
