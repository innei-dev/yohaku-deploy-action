#!/bin/bash

# Docker 部署回滚脚本
# 使用方式:
#   bash rollback.sh                  # 列出本地镜像存档并交互式选择回滚
#   bash rollback.sh sha-abc1234      # 直接回滚到指定标签 (从本地存档加载)
#   bash rollback.sh latest           # 重新加载 latest 并重启

set -e

IMAGE_DIR="$HOME/yohaku/images"

# 如果提供了标签参数，直接使用
if [ -n "$1" ]; then
  TAG="$1"
else
  echo "本地可用 Yohaku 镜像存档:"
  ls -1t "$IMAGE_DIR"/yohaku-*.tar.gz 2>/dev/null || {
    echo "  (无本地存档)"
    exit 1
  }

  echo ""
  read -r -p "输入要回滚到的标签 (例如 sha-abc1234，留空取消): " TAG

  if [ -z "$TAG" ]; then
    echo "取消回滚"
    exit 0
  fi
fi

ARCHIVE="$IMAGE_DIR/yohaku-$TAG.tar.gz"

if [ ! -f "$ARCHIVE" ]; then
  echo "错误: 未找到镜像存档 $ARCHIVE"
  echo "可用存档:"
  ls -1 "$IMAGE_DIR"/yohaku-*.tar.gz 2>/dev/null | sed 's/.*yohaku-/  /; s/\.tar\.gz//'
  exit 1
fi

echo "加载镜像 $TAG ..."
docker load < "$ARCHIVE"

echo "停止并移除旧容器..."
docker stop yohaku 2>/dev/null || true
docker rm yohaku 2>/dev/null || true

echo "启动新容器..."
docker run -d \
  --name yohaku \
  --restart always \
  -p 2323:2323 \
  -v "$HOME/yohaku/.env:/app/.env" \
  yohaku:latest \
  sh -c "set -a; . /app/.env 2>/dev/null || true; set +a; echo 'Mix Space Web [Yohaku] Image.' && node apps/web/server.js"

echo "回滚完成，当前运行: yohaku:$TAG"
docker ps --filter name=yohaku --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
