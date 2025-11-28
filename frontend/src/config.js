// 应用配置文件
const config = {
  // WebSocket连接配置
  ws: {
    // 使用相对路径，通过nginx代理
    host: process.env.VUE_APP_WS_HOST || '',
    port: process.env.VUE_APP_WS_PORT || '',
    protocol: process.env.VUE_APP_WS_PROTOCOL || 'ws'
  },

  // API配置
  api: {
    baseURL: process.env.VUE_APP_API_BASE_URL || ''
  }
}

// 获取完整的WebSocket URL
config.getWsUrl = function (roomId, token) {
  const { protocol, host, port } = this.ws

  // 如果配置了host和port，使用绝对URL
  if (host && port) {
    return `${protocol}://${host}:${port}/room/ws/${roomId}?token=${token}`
  }

  // 否则使用相对路径，通过nginx代理
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${wsProtocol}//${window.location.host}/room/ws/${roomId}?token=${token}`
}

// 获取API基础URL
config.getApiUrl = function (path = '') {
  const baseURL = this.api.baseURL

  // 如果配置了baseURL，使用绝对URL
  if (baseURL) {
    return `${baseURL}${path}`
  }

  // 否则使用相对路径，通过nginx代理
  return `/api${path}`
}

export default config
