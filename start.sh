#!/bin/bash

echo "========================================"
echo "  Creative Master - Starting..."
echo "========================================"
echo ""

echo "[1/2] Starting Backend (Port 8002)..."
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && python -m uvicorn backend.main:app --port 8002 --reload"'

sleep 2

echo "[2/2] Starting Frontend (Port 3001)..."
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'/frontend\" && npm run dev -- --port 3001"'

echo ""
echo "========================================"
echo "  Services Started!"
echo "  Backend:  http://127.0.0.1:8002"
echo "  Frontend: http://localhost:3001"
echo "========================================"
echo ""
echo "Opening browser..."
sleep 3
open http://localhost:3001
