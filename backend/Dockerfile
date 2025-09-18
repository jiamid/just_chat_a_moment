# 使用Python 3.12官方镜像
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
# 复制后端依赖列表并安装
COPY requirements.txt .
RUN pip install -U pip
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制后端代码
COPY . .

# 暴露应用端口（默认为 9099，参考 AppConfig.app_port）
EXPOSE 8000
# 启动 FastAPI 应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]