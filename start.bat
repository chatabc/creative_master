@echo off
chcp 65001 >nul
echo ========================================
echo   Creative Master - Starting...
echo ========================================
echo.

echo [1/2] Starting Backend (Port 8002)...
start "Creative Master - Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --port 8002 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend (Port 3001)...
start "Creative Master - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --port 3001"

echo.
echo ========================================
echo   Services Started!
echo   Backend:  http://127.0.0.1:8002
echo   Frontend: http://localhost:3001
echo ========================================
echo.
echo Press any key to open browser...
pause >nul
start http://localhost:3001
