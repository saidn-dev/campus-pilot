@echo off
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul
echo Open http://localhost:8000
.venv\Scripts\python -m uvicorn server.main:app --port 8000
