import base64
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.services.github_api import GitHubAPI
from mcp_server.services.code_analyzer import CodeAnalyzer

mcp = FastMCP("github-repository-assistant", host="0.0.0.0", port=8001)


def api(access_token: str | None = None) -> GitHubAPI:
    token = access_token or os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("A GitHub access token is required")
    return GitHubAPI(token)


@mcp.tool()
async def list_repositories(access_token: str, page: int = 1, per_page: int = 30) -> list[dict[str, Any]]:
    """List repositories accessible to the authenticated GitHub user."""
    return await api(access_token).list_repositories(page, min(per_page, 100))


@mcp.tool()
async def get_repository_details(access_token: str, owner: str, repo: str) -> dict[str, Any]:
    """Get repository metadata."""
    return await api(access_token).get_repository(owner, repo)


@mcp.tool()
async def get_repository_branches(access_token: str, owner: str, repo: str) -> list[dict[str, Any]]:
    return await api(access_token).get_branches(owner, repo)


@mcp.tool()
async def get_repository_languages(access_token: str, owner: str, repo: str) -> dict[str, int]:
    return await api(access_token).get_languages(owner, repo)


@mcp.tool()
async def get_repository_readme(access_token: str, owner: str, repo: str, ref: str | None = None) -> dict[str, Any]:
    item = await api(access_token).get_readme(owner, repo, ref)
    content = base64.b64decode(item.get("content", "") if item.get("encoding") == "base64" else "").decode("utf-8", "replace")
    return {"path": item.get("path"), "sha": item.get("sha"), "content": content[:100_000]}


@mcp.tool()
async def get_repository_tree(access_token: str, owner: str, repo: str, ref: str = "HEAD", recursive: bool = True) -> dict[str, Any]:
    return await api(access_token).get_tree(owner, repo, ref, recursive)


@mcp.tool()
async def get_repository_contributors(access_token: str, owner: str, repo: str) -> list[dict[str, Any]]:
    return await api(access_token).get_contributors(owner, repo)


@mcp.tool()
async def get_file_content(access_token: str, owner: str, repo: str, path: str, ref: str | None = None) -> dict[str, Any]:
    """Read a text file and return bounded content with metadata."""
    item = await api(access_token).get_contents(owner, repo, path, ref)
    if not isinstance(item, dict) or item.get("type") != "file":
        raise ValueError("The requested path is not a file")
    encoded = item.get("content", "")
    content = base64.b64decode(encoded).decode("utf-8", "replace") if item.get("encoding") == "base64" else ""
    lines = content.splitlines()
    return {"path": path, "sha": item.get("sha"), "size": item.get("size", len(content.encode())), "line_count": len(lines), "content": content[:200_000]}


@mcp.tool()
async def list_files(access_token: str, owner: str, repo: str, path: str = "", ref: str | None = None) -> list[dict[str, Any]]:
    item = await api(access_token).get_contents(owner, repo, path, ref)
    if not isinstance(item, list):
        item = [item]
    return [{"name": x.get("name"), "path": x.get("path"), "type": x.get("type"), "size": x.get("size")} for x in item]


@mcp.tool()
async def search_code(access_token: str, owner: str, repo: str, query: str) -> dict[str, Any]:
    """Search GitHub code and return structured matches."""
    data = await api(access_token).get("/search/code", {"q": f"{query} repo:{owner}/{repo}"})
    return {"total_count": data.get("total_count", 0), "matches": [{"path": x.get("path"), "html_url": x.get("html_url")} for x in data.get("items", [])[:30]]}


@mcp.tool()
async def find_todo_comments(access_token: str, owner: str, repo: str, ref: str = "HEAD") -> list[dict[str, Any]]:
    tree = await api(access_token).get_tree(owner, repo, ref, True)
    findings: list[dict[str, Any]] = []
    git = api(access_token)
    for entry in tree.get("tree", [])[:500]:
        if entry.get("type") != "blob" or entry.get("size", 0) > 200_000:
            continue
        path = entry.get("path", "")
        if not path or not path.lower().endswith((".py", ".js", ".ts", ".java", ".cs", ".html", ".css", ".md", ".sql")):
            continue
        try:
            item = await git.get_contents(owner, repo, path, ref)
            content = base64.b64decode(item.get("content", "")).decode("utf-8", "replace") if isinstance(item, dict) else ""
            findings.extend(CodeAnalyzer.find_todos(content, path))
        except RuntimeError:
            continue
    return findings[:500]


@mcp.tool()
async def analyze_python_code(access_token: str, owner: str, repo: str, path: str, ref: str | None = None) -> dict[str, Any]:
    item = await api(access_token).get_contents(owner, repo, path, ref)
    content = base64.b64decode(item.get("content", "")).decode("utf-8", "replace") if isinstance(item, dict) else ""
    return CodeAnalyzer.analyze_python(content, path)


@mcp.tool()
async def find_unused_imports(access_token: str, owner: str, repo: str, path: str, ref: str | None = None) -> dict[str, Any]:
    result = await analyze_python_code(access_token, owner, repo, path, ref)
    findings = [x for x in result.get("verified_static_findings", []) if x.get("category") == "unused_import"]
    return {"verified_static_findings": findings, "ai_suggestions": []}


@mcp.tool()
async def analyze_code_complexity(access_token: str, owner: str, repo: str, path: str, ref: str | None = None) -> dict[str, Any]:
    result = await analyze_python_code(access_token, owner, repo, path, ref)
    return {"functions": result.get("functions", [])}


@mcp.tool()
async def get_commits(access_token: str, owner: str, repo: str, sha: str | None = None, per_page: int = 30) -> list[dict[str, Any]]:
    return await api(access_token).get_commits(owner, repo, sha, min(per_page, 100))


@mcp.tool()
async def get_commit_details(access_token: str, owner: str, repo: str, sha: str) -> dict[str, Any]:
    return await api(access_token).get_commit(owner, repo, sha)


@mcp.tool()
async def compare_commits(access_token: str, owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
    return await api(access_token).compare(owner, repo, base, head)


@mcp.tool()
async def compare_branches(access_token: str, owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
    return await api(access_token).compare(owner, repo, base, head)


@mcp.tool()
async def list_pull_requests(access_token: str, owner: str, repo: str, state: str = "open", per_page: int = 30) -> list[dict[str, Any]]:
    return await api(access_token).pull_requests(owner, repo, state, min(per_page, 100))


@mcp.tool()
async def get_pull_request_details(access_token: str, owner: str, repo: str, number: int) -> dict[str, Any]:
    return await api(access_token).pull_request(owner, repo, number)


@mcp.tool()
async def get_pull_request_files(access_token: str, owner: str, repo: str, number: int) -> list[dict[str, Any]]:
    return await api(access_token).pull_request_files(owner, repo, number)


@mcp.tool()
async def analyze_pull_request(access_token: str, owner: str, repo: str, number: int) -> dict[str, Any]:
    details = await api(access_token).pull_request(owner, repo, number)
    files = await api(access_token).pull_request_files(owner, repo, number)
    return {"title": details.get("title"), "body": details.get("body")[:20_000] if details.get("body") else None, "changed_files": [f.get("filename") for f in files], "patches": [{"filename": f.get("filename"), "patch": (f.get("patch") or "")[:20_000]} for f in files[:30]]}


@mcp.tool()
async def list_issues(access_token: str, owner: str, repo: str, state: str = "open", per_page: int = 30) -> list[dict[str, Any]]:
    return await api(access_token).issues(owner, repo, state, min(per_page, 100))


@mcp.tool()
async def get_issue_details(access_token: str, owner: str, repo: str, number: int) -> dict[str, Any]:
    """Get one issue while excluding pull requests."""
    data = await api(access_token).get(f"/repos/{owner}/{repo}/issues/{number}")
    if "pull_request" in data:
        raise ValueError("The requested number is a pull request, not an issue")
    return data


@mcp.tool()
async def search_issues(access_token: str, owner: str, repo: str, query: str) -> dict[str, Any]:
    """Search issues and pull requests in a repository."""
    data = await api(access_token).get("/search/issues", {"q": f"{query} repo:{owner}/{repo}"})
    return {"total_count": data.get("total_count", 0), "items": data.get("items", [])[:100]}


@mcp.tool()
async def summarize_issues(access_token: str, owner: str, repo: str, state: str = "open", limit: int = 30) -> dict[str, Any]:
    """Return a structured summary input for GitHub issues."""
    issues = await api(access_token).issues(owner, repo, state, min(limit, 100))
    real_issues = [x for x in issues if "pull_request" not in x]
    return {"count": len(real_issues), "issues": [{"number": x.get("number"), "title": x.get("title"), "state": x.get("state"), "labels": [label.get("name") for label in x.get("labels", [])], "body": (x.get("body") or "")[:5000]} for x in real_issues]}


@mcp.tool()
async def analyze_django_project(access_token: str, owner: str, repo: str, ref: str = "HEAD") -> dict[str, Any]:
    """Identify Django structure from static repository files."""
    tree = await api(access_token).get_tree(owner, repo, ref, True)
    paths = [entry.get("path", "") for entry in tree.get("tree", []) if entry.get("type") == "blob"]
    django = {"settings": [x for x in paths if x.endswith("settings.py")], "models": [x for x in paths if x.endswith("models.py")], "views": [x for x in paths if x.endswith("views.py")], "serializers": [x for x in paths if x.endswith("serializers.py")], "urls": [x for x in paths if x.endswith("urls.py")], "templates": [x for x in paths if "templates/" in x], "detected": any(x.endswith("manage.py") for x in paths)}
    django["detected"] = django["detected"] or bool(django["settings"])
    return django


@mcp.tool()
async def analyze_fastapi_project(access_token: str, owner: str, repo: str, ref: str = "HEAD") -> dict[str, Any]:
    """Identify FastAPI route and application files by static tree analysis."""
    tree = await api(access_token).get_tree(owner, repo, ref, True)
    paths = [entry.get("path", "") for entry in tree.get("tree", []) if entry.get("type") == "blob"]
    return {"routers": [x for x in paths if "router" in x.lower() and x.endswith(".py")], "main_files": [x for x in paths if x.endswith("main.py") or x.endswith("app.py")], "schemas": [x for x in paths if "schema" in x.lower() and x.endswith(".py")], "detected": any("fastapi" in x.lower() for x in paths)}


@mcp.resource("github://repository/{owner}/{repo}")
async def repository_resource(owner: str, repo: str) -> str:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        return '{"error":"GITHUB_TOKEN is required"}'
    import json
    data = await api(token).get_repository(owner, repo)
    return json.dumps(data)


@mcp.prompt()
def explain_repository(owner: str, repo: str) -> str:
    return f"Analyze the repository {owner}/{repo} using repository files and metadata. Separate verified findings from suggestions and cite file paths and line numbers."


@mcp.prompt()
def review_pull_request(owner: str, repo: str, number: int) -> str:
    return f"Review pull request #{number} in {owner}/{repo}. Identify bugs and security concerns, cite changed files and lines, and do not propose publishing comments."


@mcp.prompt()
def generate_unit_tests(language: str, symbol: str) -> str:
    return f"Generate review-only unit tests for the {language} symbol '{symbol}'. Use existing project conventions and do not claim tests passed."


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
