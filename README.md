# GitHub Repository Assistant

A FastAPI and Angular application for analyzing GitHub repositories through a real MCP server, grounded AI chat, static code analysis, commits, pull requests, and repository exploration.

## Architecture

- Angular 21 frontend
- FastAPI backend
- Independent official MCP SDK/FastMCP server
- Streamable HTTP MCP transport (stdio locally supported)
- SQLite and SQLAlchemy 2
- GitHub REST API
- OpenAI-compatible chat integration
- JWT authentication and encrypted GitHub OAuth tokens

## Windows setup

### 1. Backend

```powershell
cd d:\Arulraj\POC\interview_training\fastapi_angular_github
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
cd backend
uvicorn app.main:app --reload --port 8000
```

Generate an encryption key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Place the result in `ENCRYPTION_KEY` in `backend/.env`.

### 2. MCP server

Use a second terminal:

```powershell
cd d:\Arulraj\POC\interview_training\fastapi_angular_github
.\.venv\Scripts\Activate.ps1
cd backend
$env:MCP_TRANSPORT="stdio"
python -m mcp_server.server
```

For Streamable HTTP:

```powershell
$env:MCP_TRANSPORT="streamable-http"
python -m mcp_server.server
```

The default server endpoint is `http://localhost:8001/mcp`.

### 3. Angular frontend

```powershell
cd d:\Arulraj\POC\interview_training\fastapi_angular_github\frontend
npm install
npm start
```

Open `http://localhost:4200`.

## GitHub OAuth setup

1. Open GitHub **Settings → Developer settings → OAuth Apps → New OAuth App**.
2. Set the callback to `http://localhost:8000/api/v1/github/callback`.
3. Put the client ID and secret in `backend/.env`.
4. Register a local application, then sign in and choose **Connect GitHub**.

The OAuth request currently uses read-oriented repository and profile scopes. Pull request and issue operations are read-only. Repository/issue modifications are intentionally not exposed.

## API documentation

FastAPI provides Swagger at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

## Tests

```powershell
cd backend
pytest -q
cd ..\frontend
npm test -- --watch=false
```

## MCP client configuration

Configure compatible MCP clients with:

- Remote server URL: `http://localhost:8001/mcp`
- Local transport: `stdio`
- Command: `python`
- Arguments: `-m mcp_server.server`
- Working directory: backend directory

Every repository tool requires a GitHub access token argument supplied by FastAPI. The FastAPI execute endpoint is allowlisted and rejects write operations.

## Security notes

- GitHub tokens are encrypted at rest.
- Repository content is considered untrusted input.
- System instructions prohibit repository content from overriding security policy.
- Repository code is parsed or analyzed statically; it is never executed.
- FastAPI verifies repository ownership for all operations.
- Use a real secret and encryption key outside development.
