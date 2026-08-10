#!/bin/bash
# ═══════════════════════════════════════════
# 重启 · 失业互助平台 - 一键部署脚本
# 在服务器上执行：bash deploy.sh
# ═══════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════"
echo "  重启 · 失业互助平台 - 部署脚本"
echo "═══════════════════════════════════════════"

# 1. 检查 .env
if [ ! -f .env ]; then
    echo "[1/6] 创建 .env 配置文件..."
    cp .env.example .env
    echo "  ⚠️  请编辑 .env 修改密码和密钥后重新运行！"
    echo "  命令: nano .env"
    exit 1
fi

echo "[1/6] .env 配置文件 ✓"

# 2. 检查 Docker
echo "[2/6] 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "  安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi
echo "  Docker ✓"

# 3. 检查 Docker Compose
echo "[3/6] 检查 Docker Compose..."
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo "  安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    COMPOSE="docker-compose"
fi
echo "  $COMPOSE ✓"

# 4. 构建镜像
echo "[4/6] 构建 Docker 镜像..."
$COMPOSE build
echo "  构建完成 ✓"

# 5. 启动服务
echo "[5/6] 启动服务..."
$COMPOSE up -d
echo "  服务已启动 ✓"

# 6. 等待健康检查
echo "[6/6] 健康检查..."
sleep 5
for i in {1..10}; do
    if curl -s http://localhost/api/health | grep -q "ok"; then
        echo "  API 健康 ✓"
        break
    fi
    echo "  等待 API 启动... ($i/10)"
    sleep 3
done

echo ""
echo "═══════════════════════════════════════════"
echo "  部署完成！"
echo "═══════════════════════════════════════════"
echo ""
echo "  前端页面: http://$(hostname -I | awk '{print $1}')/"
echo "  API 文档: http://$(hostname -I | awk '{print $1}')/docs"
echo "  健康检查: http://$(hostname -I | awk '{print $1}')/api/health"
echo ""
echo "  常用命令:"
echo "    查看日志:   $COMPOSE logs -f"
echo "    重启服务:   $COMPOSE restart"
echo "    停止服务:   $COMPOSE down"
echo "    更新代码:   git pull && $COMPOSE up -d --build"
echo ""
echo "═══════════════════════════════════════════"
