#!/bin/bash

echo "========================================"
echo "  Creative Master - Starting..."
echo "========================================"
echo ""

echo "[1/2] Starting Backend (Port 8002)..."
gnome-terminal -- bash -c "cd '$(pwd)' && python -m uvicorn backend.main:app --port 8002 --reload; exec bash" &

sleep 2

echo "[2/2] Starting Frontend (Port 3001)..."
gnome-terminal -- bash -c "cd '$(pwd)/frontend' && npm run dev -- --port 3001; exec bash" &

echo ""
echo "========================================"
echo "  Services Started!"
echo "  Backend:  http://127.0.0.1:8002"
echo "  Frontend: http://localhost:3001"
echo "========================================"
echo ""
echo "Opening browser..."
sleep 3
xdg-open http://localhost:3001 2>/dev/null || echo "Please open http://localhost:3001 in your browser"
