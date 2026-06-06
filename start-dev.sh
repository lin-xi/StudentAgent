#!/bin/bash
# 启动开发环境：后端 + 前端
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 启动后端 (FastAPI)..."
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID (http://localhost:8000)"

sleep 2

echo "🚀 启动前端 (Vite)..."
cd "$SCRIPT_DIR/frontend"
vite dev --host 0.0.0.0 &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID (http://localhost:5173)"

echo ""
echo "✅ 开发环境已启动！"
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo ""
#echo "按 Ctrl+C 停止所有服务"

#trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
#wait
