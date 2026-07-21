#!/bin/bash
# CRM 安全部署脚本：先备份，再部署
# 用法: ./safe-deploy.sh [frontend|backend|all，默认 all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$SCRIPT_DIR/.."
TARGET="${1:-all}"

green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }

echo "=== CRM 安全部署 ==="

# 1. 自动备份
green "1/3 备份现有数据..."
"$SCRIPT_DIR/backup.sh"

# 2. 构建镜像
green "2/3 构建 Docker 镜像 ($TARGET)..."
cd "$DEPLOY_DIR"
if [ "$TARGET" = "all" ] || [ "$TARGET" = "backend" ]; then
    docker compose build backend
fi
if [ "$TARGET" = "all" ] || [ "$TARGET" = "frontend" ]; then
    docker compose build frontend
fi

# 3. 重新创建容器
green "3/3 重启容器..."
if [ "$TARGET" = "all" ]; then
    docker compose up -d
elif [ "$TARGET" = "backend" ]; then
    docker compose up -d backend
elif [ "$TARGET" = "frontend" ]; then
    docker compose up -d frontend
fi

green "=== 部署完成 ==="
