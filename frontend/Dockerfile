# syntax=docker/dockerfile:1

# 构建阶段
FROM node:18-alpine as build-stage

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装所有依赖（包括devDependencies，构建需要vue-cli-service）
# 使用缓存挂载来加速后续构建
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# 复制源代码
COPY . .

# 声明构建参数
ARG VUE_APP_WS_HOST
ARG VUE_APP_WS_PORT
ARG VUE_APP_WS_PROTOCOL
ARG VUE_APP_API_BASE_URL

# 设置环境变量（Vue CLI在构建时会读取这些变量）
ENV VUE_APP_WS_HOST=$VUE_APP_WS_HOST
ENV VUE_APP_WS_PORT=$VUE_APP_WS_PORT
ENV VUE_APP_WS_PROTOCOL=$VUE_APP_WS_PROTOCOL
ENV VUE_APP_API_BASE_URL=$VUE_APP_API_BASE_URL

# 构建应用
RUN NODE_OPTIONS="--max_old_space_size=4096" npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建的文件到nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 创建nginx运行目录并设置权限
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    mkdir -p /run && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /run

# 切换到nginx用户
USER nginx

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
