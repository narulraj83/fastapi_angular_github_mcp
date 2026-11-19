from typing import Any
from urllib.parse import urlencode
import httpx

from app.config import get_settings


class GitHubService:
    def __init__(self, access_token: str | None = None):
        self.settings = get_settings()
        self.access_token = access_token

    def authorization_url(self, state: str) -> str:
        params = urlencode({"client_id": self.settings.github_client_id, "redirect_uri": self.settings.github_callback_url, "scope": "read:user repo", "state": state})
        return f"https://github.com/login/oauth/authorize?{params}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post("https://github.com/login/oauth/access_token", headers={"Accept": "application/json"}, data={"client_id": self.settings.github_client_id, "client_secret": self.settings.github_client_secret, "code": code, "redirect_uri": self.settings.github_callback_url})
            response.raise_for_status()
            return response.json()

    async def get_profile(self) -> dict[str, Any]:
        if not self.access_token:
            raise RuntimeError("GitHub account is not connected")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.github.com/user", headers={"Authorization": f"Bearer {self.access_token}", "Accept": "application/vnd.github+json"})
            response.raise_for_status()
            return response.json()

    async def list_repositories(self, page: int = 1, per_page: int = 30) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.github.com/user/repos", headers={"Authorization": f"Bearer {self.access_token}", "Accept": "application/vnd.github+json"}, params={"page": page, "per_page": min(per_page, 100), "sort": "updated"})
            response.raise_for_status()
            return response.json()

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers={"Authorization": f"Bearer {self.access_token}", "Accept": "application/vnd.github+json"})
            response.raise_for_status()
            return response.json()
