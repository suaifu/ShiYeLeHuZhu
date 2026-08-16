#!/bin/bash
# ShiYeLeHuZhu 本地测试一键启动
# 用法：bash run_local.sh

cd /Users/fushuaiguo/Documents/work/2026-08-02-00-12-34/api
export PYTHONPATH=/Users/fushuaiguo/Documents/work/2026-08-02-00-12-34/api

echo "═══════════════════════════════════════════"
echo "  ShiYeLeHuZhu 本地测试"
echo "═══════════════════════════════════════════"
echo ""

# 杀掉旧进程
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1

# 启动 API + 前端
/Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload &

echo ""
echo "  启动中..."
sleep 3

# 验证
echo ""
echo "  前端页面: http://127.0.0.1:8000/"
echo "  API 文档: http://127.0.0.1:8000/docs"
echo "  健康检查: http://127.0.0.1:8000/api/health"
echo ""
echo "  按 Ctrl+C 停止"
echo ""
echo "═══════════════════════════════════════════"
echo ""

# 自动打开浏览器
open http://127.0.0.1:8000/ 2>/dev/null

# 等待退出
wait
