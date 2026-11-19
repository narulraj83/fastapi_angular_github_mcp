import asyncio
from typing import Any
import httpx


class GitHubAPI:
    def __init__(self, token: str, api_url: str = "https://api.github.com"):
        self.token = token
        self.api_url = api_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-repository-assistant",
        }

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(f"{self.api_url}{path}", headers=self._headers(), params=params)
            if response.status_code >= 400:
                raise RuntimeError(f"GitHub API error {response.status_code}: {response.text[:300]}")
            return response.json()

    async def list_repositories(self, page: int = 1, per_page: int = 30) -> list[dict[str, Any]]:
        return await self.get("/user/repos", {"page": page, "per_page": per_page, "sort": "updated", "affiliation": "owner,collaborator,organization_member"})

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return await self.get(f"/repos/{owner}/{repo}")

    async def get_branches(self, owner: str, repo: str) -> list[dict[str, Any]]:
        return await self.get(f"/repos/{owner}/{repo}/branches", {"per_page": 100})

    async def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return await self.get(f"/repos/{owner}/{repo}/languages")

    async def get_readme(self, owner: str, repo: str, ref: str | None = None) -> dict[str, Any]:
        params = {"ref": ref} if ref else None
        return await self.get(f"/repos/{owner}/{repo}/readme", params)

    async def get_tree(self, owner: str, repo: str, ref: str, recursive: bool = True) -> dict[str, Any]:
        return await self.get(f"/repos/{owner}/{repo}/git/trees/{ref}", {"recursive": "1"} if recursive else None)

    async def get_commits(self, owner: str, repo: str, sha: str | None = None, per_page: int = 30) -> list[dict[str, Any]]:
        params = {"per_page": per_page}
        if sha:
            params["sha"] = sha
        return await self.get(f"/repos/{owner}/{repo}/commits", params)

    async def get_commit(self, owner: str, repo: str, sha: str) -> dict[str, Any]:
        return await self.get(f"/repos/{owner}/{repo}/commits/{sha}")

    async def compare(self, owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
        return await self.get(f"/repos/{owner}/{repo}/compare/{base}...{head}")

    async def pull_requests(self, owner: str, repo: str, state: str = "open", per_page: int = 30) -> list[dict[str, Any]]:
        return await self.get(f"/repos/{owner}/{repo}/pulls", {"state": state, "per_page": per_page})

    async def pull_request(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        return await self.get(f"/repos/{owner}/{repo}/pulls/{number}")

    async def pull_request_files(self, owner: str, repo: str, number: int) -> list[dict[str, Any]]:
        return await self.get(f"/repos/{owner}/{repo}/pulls/{number}/files", {"per_page": 100})

    async def issues(self, owner: str, repo: str, state: str = "open", per_page: int = 30) -> list[dict[str, Any]]:
        return await self.get(f"/repos/{owner}/{repo}/issues", {"state": state, "per_page": per_page})

    async def get_contributors(self, owner: str, repo: str) -> list[dict[str, Any]]:
        return await self.get(f"/repos/{owner}/{repo}/contributors", {"per_page": 100})

    async def get_contents(self, owner: str, repo: str, path: str = "", ref: str | None = None) -> Any:
        params = {"ref": ref} if ref else None
        return await self.get(f"/repos/{owner}/{repo}/contents/{path}", params)
