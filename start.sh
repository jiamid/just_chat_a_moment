#!/bin/bash

# Just Chat A Moment - Docker 快速启动脚本

set -e

echo "🚀 启动 Just Chat A Moment..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp docker.env .env
    echo "⚠️  请编辑 .env 文件中的 SECRET_KEY 等配置"
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data

# 构建并启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "🌐 前端访问地址: http://localhost"
    echo "🔧 后端API地址: http://localhost:8000"
    echo "💊 健康检查: http://localhost:8000/api/health"
    echo ""
    echo "📋 常用命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo ""
else
    echo "❌ 服务启动失败，请查看日志:"
    docker-compose logs
    exit 1
fi
