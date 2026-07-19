#!/bin/bash
# CRM 数据恢复脚本
# 用法: ./restore.sh [备份目录名]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_ROOT="${2:-$SCRIPT_DIR/../backups}"
DATA_DIR="$SCRIPT_DIR/../data"

red() { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }

# 列出可用备份
if [ -z "${1:-}" ]; then
    echo "=== 可用备份 ==="
    if [ -d "$BACKUP_ROOT" ]; then
        ls -1dt "$BACKUP_ROOT"/20* 2>/dev/null | while read dir; do
            name=$(basename "$dir")
            db_size=$(du -h "$dir/crm.db" 2>/dev/null | cut -f1 || echo "无")
            echo "  $name  (数据库: $db_size)"
        done
    fi
    echo ""
    echo "用法: $0 <备份目录名>"
    echo "示例: $0 20260719_120000"
    exit 1
fi

BACKUP_DIR="$BACKUP_ROOT/$1"

if [ ! -d "$BACKUP_DIR" ]; then
    red "错误: 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

echo "=== 从 $1 恢复数据 ==="
echo "数据目录: $DATA_DIR"

# 1. 先做一次安全备份（以防恢复错）
mkdir -p "$BACKUP_ROOT"
SAFE_BAK="$DATA_DIR/crm.db.before_restore_$(date +%Y%m%d_%H%M%S)"
if [ -f "$DATA_DIR/crm.db" ]; then
    cp "$DATA_DIR/crm.db" "$SAFE_BAK"
    green "✓ 当前数据库已备份到: $(basename "$SAFE_BAK")"
fi

# 2. 恢复数据库
if [ -f "$BACKUP_DIR/crm.db" ]; then
    cp "$BACKUP_DIR/crm.db" "$DATA_DIR/crm.db"
    green "✓ 数据库已恢复"
else
    red "错误: 备份中无数据库文件"
fi

# 3. 恢复上传文件
if [ -f "$BACKUP_DIR/uploads.tar.gz" ]; then
    rm -rf "$DATA_DIR/uploads"
    tar -xzf "$BACKUP_DIR/uploads.tar.gz" -C "$DATA_DIR"
    green "✓ 上传文件已恢复"
fi

red "===================================="
red " 重要：请手动重启后端容器使其生效"
red " docker compose restart backend"
red "===================================="
