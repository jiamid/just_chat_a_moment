#!/bin/bash

# Docker配置测试脚本

echo "🧪 测试 Docker 配置..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请启动 Docker"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 验证配置文件
echo "📋 验证配置文件..."

if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml 不存在"
    exit 1
fi

if [ ! -f "backend/Dockerfile" ]; then
    echo "❌ backend/Dockerfile 不存在"
    exit 1
fi

if [ ! -f "frontend/Dockerfile" ]; then
    echo "❌ frontend/Dockerfile 不存在"
    exit 1
fi

if [ ! -f "frontend/nginx.conf" ]; then
    echo "❌ frontend/nginx.conf 不存在"
    exit 1
fi

echo "✅ 配置文件验证通过"

# 测试构建（不启动服务）
echo "🔨 测试镜像构建..."

echo "构建后端镜像..."
if docker-compose build backend; then
    echo "✅ 后端镜像构建成功"
else
    echo "❌ 后端镜像构建失败"
    exit 1
fi

echo "构建前端镜像..."
if docker-compose build frontend; then
    echo "✅ 前端镜像构建成功"
else
    echo "❌ 前端镜像构建失败"
    exit 1
fi

echo ""
echo "🎉 所有测试通过！Docker 配置正确"
echo ""
echo "下一步："
echo "  1. 运行 ./start.sh 启动服务"
echo "  2. 访问 http://localhost 使用应用"
echo "  3. 运行 ./stop.sh 停止服务"
