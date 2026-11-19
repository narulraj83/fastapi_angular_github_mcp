backend:
	cd backend && uvicorn app.main:app --reload --port 8000

mcp:
	cd backend && python -m mcp_server.server

frontend:
	cd frontend && npm start

test:
	cd backend && pytest -q
