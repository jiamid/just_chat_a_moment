# 前端配置说明

## WebSocket连接配置

现在WebSocket连接地址已经改为可配置的，支持通过环境变量进行配置。

### 配置文件

配置文件位置：`src/config.js`

### 环境变量配置

可以通过以下环境变量来配置连接地址：

- `VUE_APP_WS_HOST`: WebSocket服务器地址（默认：127.0.0.1）
- `VUE_APP_WS_PORT`: WebSocket服务器端口（默认：8000）
- `VUE_APP_WS_PROTOCOL`: WebSocket协议（默认：ws）
- `VUE_APP_API_BASE_URL`: API基础URL（默认：http://127.0.0.1:8000）

### 使用方法

#### 1. 开发环境配置

创建 `.env.development` 文件：

```bash
# 开发环境配置
VUE_APP_WS_HOST=127.0.0.1
VUE_APP_WS_PORT=8000
VUE_APP_WS_PROTOCOL=ws
VUE_APP_API_BASE_URL=http://127.0.0.1:8000
```

#### 2. 生产环境配置

创建 `.env.production` 文件：

```bash
# 生产环境配置
VUE_APP_WS_HOST=your-domain.com
VUE_APP_WS_PORT=8000
VUE_APP_WS_PROTOCOL=wss
VUE_APP_API_BASE_URL=https://your-domain.com:8000
```

#### 3. 本地配置

创建 `.env.local` 文件（此文件会被git忽略）：

```bash
# 本地自定义配置
VUE_APP_WS_HOST=192.168.1.100
VUE_APP_WS_PORT=8000
VUE_APP_WS_PROTOCOL=ws
VUE_APP_API_BASE_URL=http://192.168.1.100:8000
```

### 配置优先级

环境变量配置的优先级：
1. `.env.local`（最高优先级，本地配置）
2. `.env.[mode].local`（如：`.env.production.local`）
3. `.env.[mode]`（如：`.env.production`）
4. `.env`（最低优先级，默认配置）

### 代码中的使用

在代码中，可以通过以下方式使用配置：

```javascript
import config from '@/config'

// 获取WebSocket URL
const wsUrl = config.getWsUrl(roomId, token)

// 获取API URL
const apiUrl = config.getApiUrl('/api/me')
```

### 注意事项

1. 环境变量必须以 `VUE_APP_` 开头才能在客户端代码中使用
2. 修改环境变量后需要重启开发服务器
3. 生产环境建议使用 `wss` 协议（WebSocket Secure）
4. 确保后端服务器支持配置的协议和端口
