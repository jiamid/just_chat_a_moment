# Just Chat A Moment
## 聊一会儿

一个基于 FastAPI + Vue 的实时聊天应用，支持用户注册登录、房间聊天，使用 WebSocket + Protobuf 进行实时通信。

## 功能特性

### 后端功能（FastAPI）
- ✅ 用户邮箱注册，自定义用户名和头像
- ✅ JWT 身份认证
- ✅ 房间管理（输入房间号即可加入，自动创建）
- ✅ WebSocket 实时通信，仅房间内广播
- ✅ Protobuf 二进制消息协议
- ✅ SQLite 数据库存储用户信息
- ✅ 异步架构，高性能

### 前端功能（Vue 3）
- ✅ 用户注册/登录界面
- ✅ JWT Token 管理
- ✅ 房间加入与 WebSocket 连接
- ✅ 实时消息收发
- ✅ Protobuf 消息编解码
- ✅ 响应式聊天界面
- ✅ 连接状态显示

## 快速开始

### 环境要求
- Python 3.8+ (本地开发)
- Node.js 16+ (本地开发)
- npm 或 yarn (本地开发)
- Docker & Docker Compose (容器化部署)

## 🐳 Docker 部署（推荐）

使用 Docker Compose 可以一键部署整个应用，无需手动配置环境。

### 1. 快速启动

```bash
# 克隆项目
git clone <your-repo-url>
cd just_chat_a_moment


# 编辑配置文件（重要：修改SECRET_KEY）
nano .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```
