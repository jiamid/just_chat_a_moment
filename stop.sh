#!/bin/bash

# Just Chat A Moment - Docker 停止脚本

echo "🛑 停止 Just Chat A Moment 服务..."

# 停止并删除容器
docker-compose down

echo "✅ 服务已停止"
echo ""
echo "📋 其他命令:"
echo "  完全清理: docker-compose down -v"
echo "  删除镜像: docker-compose down --rmi all"
echo "  查看状态: docker-compose ps"
