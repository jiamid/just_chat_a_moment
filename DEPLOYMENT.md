# 单域名部署配置说明

## 部署架构

所有服务现在都通过前端的nginx进行统一代理，实现单域名访问：

- `http://jiamid.com/` - 前端主页（通过外部nginx处理SSL）
- `http://jiamid.com/api` - 后端API接口
- `http://jiamid.com/ws` - WebSocket连接

**注意**：frontend容器只提供HTTP服务，SSL/HTTPS由外部的nginx（负载均衡器或反向代理）处理。

## 主要修改

### 1. Nginx配置 (`frontend/nginx.conf`)
- 移除了SSL配置，只保留HTTP服务
- 设置server_name为localhost（接受来自外部nginx的转发）
- 保留了API和WebSocket代理配置
- 保留了安全头设置

### 2. Docker Compose (`docker-compose.yml`)
- 移除了后端服务的端口暴露（8000端口不再对外暴露）
- 前端服务只暴露80端口
- 移除了SSL证书挂载
- 更新了构建参数，使用相对路径

### 3. 前端配置 (`frontend/src/config.js`)
- 修改为使用相对路径
- 自动检测协议（HTTP/HTTPS）
- 支持开发环境和生产环境的灵活配置

### 4. 前端Dockerfile
- 移除了SSL证书目录支持
- 只暴露80端口

## 部署步骤

### 1. 启动服务
```bash
# 构建并启动所有服务
docker-compose up -d --build
```

### 2. 配置外部nginx（推荐）
在外部nginx中配置SSL和反向代理：

```nginx
upstream frontend {
    server localhost:80;
}

server {
    listen 443 ssl http2;
    server_name jiamid.com www.jiamid.com;
    
    # SSL配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name jiamid.com www.jiamid.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. 验证部署
- 访问 `https://jiamid.com` 应该看到前端页面
- API请求会自动代理到 `https://jiamid.com/api`
- WebSocket连接会自动使用 `wss://jiamid.com/ws`

## 注意事项

1. **外部nginx**：需要配置外部的nginx来处理SSL和域名转发
2. **端口映射**：确保外部nginx能够访问到frontend容器的80端口
3. **域名解析**：确保域名 `jiamid.com` 解析到外部nginx服务器
4. **防火墙**：确保外部nginx的80和443端口对外开放

## 开发环境

如果需要本地开发，可以设置环境变量：
```bash
export VUE_APP_WS_HOST=localhost
export VUE_APP_WS_PORT=8000
export VUE_APP_WS_PROTOCOL=ws
export VUE_APP_API_BASE_URL=http://localhost:8000
```

这样前端会直接连接到后端，而不是通过nginx代理。