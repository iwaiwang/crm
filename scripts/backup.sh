#!/bin/bash
# CRM 数据备份脚本
# 用法: ./backup.sh [备份目录路径，默认 ../backups]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_ROOT="${1:-$SCRIPT_DIR/../backups}"
DATA_DIR="$SCRIPT_DIR/../data"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
KEEP_COUNT="${2:-7}"

# 颜色输出
green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }

# 检查数据目录是否存在
if [ ! -d "$DATA_DIR" ]; then
    echo "错误: 数据目录不存在: $DATA_DIR"
    exit 1
fi

echo "=== CRM 数据备份 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "备份目录: $BACKUP_DIR"

mkdir -p "$BACKUP_DIR"

# 1. 备份数据库（带压缩）
if [ -f "$DATA_DIR/crm.db" ]; then
    cp "$DATA_DIR/crm.db" "$BACKUP_DIR/crm.db"
    sqlite3 "$DATA_DIR/crm.db" ".backup '$BACKUP_DIR/crm.db'"
    green "✓ 数据库备份完成 ($(du -h "$BACKUP_DIR/crm.db" | cut -f1))"
else
    echo "⚠ 未找到数据库文件 crm.db"
fi

# 2. 备份上传文件（用 tar 打包压缩）
if [ -d "$DATA_DIR/uploads" ]; then
    tar -czf "$BACKUP_DIR/uploads.tar.gz" -C "$DATA_DIR" uploads
    green "✓ 上传文件备份完成 ($(du -h "$BACKUP_DIR/uploads.tar.gz" | cut -f1))"
else
    echo "⚠ 未找到上传文件目录 uploads"
fi

# 3. 清理旧备份（只保留最近 N 天）
if [ -d "$BACKUP_ROOT" ]; then
    DELETED=$(find "$BACKUP_ROOT" -maxdepth 1 -type d -name "20*" -mtime +$KEEP_COUNT 2>/dev/null | wc -l | tr -d ' ')
    find "$BACKUP_ROOT" -maxdepth 1 -type d -name "20*" -mtime +$KEEP_COUNT -exec rm -rf {} \; 2>/dev/null || true
    if [ "$DELETED" -gt 0 ]; then
        yellow "✓ 清理了 $DELETED 个旧备份（保留最近 ${KEEP_COUNT} 天）"
    fi
fi

green "=== 备份完成: $TIMESTAMP ==="
