# syntax=docker/dockerfile:1

# 使用Python 3.12官方镜像
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 设置工作目录
WORKDIR /app

# 创建非特权用户
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# 安装系统依赖（bcrypt需要编译工具）
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装Python依赖
# 使用缓存挂载来加速后续构建
RUN pip install -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录并设置权限
RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app

# 切换到非特权用户
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
