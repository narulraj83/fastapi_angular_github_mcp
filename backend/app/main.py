from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import engine
from app.database import Base
from app.models import *  # noqa: F401,F403
from app.core.exceptions import AppError
from app.routers.auth_router import router as auth_router
from app.routers.github_router import router as github_router
from app.routers.repository_router import router as repository_router
from app.routers.chat_router import router as chat_router
from app.routers.analysis_router import router as analysis_router
from app.routers.commit_router import router as commit_router
from app.routers.pull_request_router import router as pull_request_router
from app.routers.mcp_router import router as mcp_router

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(auth_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1")
app.include_router(repository_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(commit_router, prefix="/api/v1")
app.include_router(pull_request_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}
