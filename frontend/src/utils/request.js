// !/usr/bin/env node
// -*- coding: utf-8 -*-
/**
@File    : request.js
@Date    : 2025/1/18
@Author  : JIAMID
@Contact : jiamid@qq.com
@Desc    : 统一的HTTP请求管理
*/

import axios from 'axios'
import config from '@/config'

// 创建axios实例
const request = axios.create({
  baseURL: config.getApiUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 统一添加认证信息
request.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一处理响应
request.interceptors.response.use(
  (response) => {
    // 如果响应成功，直接返回data字段
    if (response.data.code === 0) {
      return response.data
    } else {
      // 如果业务状态码不为0，抛出错误
      const error = new Error(response.data.message || '请求失败')
      error.code = response.data.code
      return Promise.reject(error)
    }
  },
  (error) => {
    console.error('响应拦截器错误:', error)

    // 处理401未授权
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      // 跳转到首页
      window.location.href = '/'
      return Promise.reject(new Error('登录已过期，请重新登录'))
    }

    // 处理其他HTTP错误
    const message = error.response?.data?.detail || error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(message))
  }
)

// API方法封装
export const api = {
  // 认证相关
  auth: {
    // 获取验证码
    getSmsCode: (data) => request.post('/auth/gen_sms', data),

    // 用户注册
    register: (data) => request.post('/auth/register', data),

    // 用户登录
    login: (data) => {
      // 登录使用FormData格式
      const formData = new FormData()
      formData.append('username', data.username)
      formData.append('password', data.password)

      return request.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
    }
  },

  // 用户相关
  user: {
    // 获取用户信息
    getMe: () => request.get('/me')
  },

  // 音乐相关
  music: {
    // 获取音乐配置
    getConfig: (roomId) => request.get(`/music/config/${roomId}`)
  },

  // 麦当劳 MCP / 优惠券相关
  mcd: {
    // 查询当前用户已保存的 MCP Token
    getToken: () => request.get('/mcd/token'),

    // 保存 / 更新 MCP Token
    saveToken: (data) => request.post('/mcd/token', data),

    // 与麦当劳 MCP AI 助手聊天
    chat: (data) => request.post('/mcd/chat', data)
  }
}

// 导出默认实例
export default request
