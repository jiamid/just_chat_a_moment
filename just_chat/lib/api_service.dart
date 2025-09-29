import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // 可通过 --dart-define=API_BASE_URL=... 传入，例如 http://192.168.1.100:8000/api
  // Android 模拟器常用: http://10.0.2.2:8000/api
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://im.jiamid.com/api',
  );

  static final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
    sendTimeout: const Duration(seconds: 30),
    followRedirects: true,
    maxRedirects: 5,
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'JustChatFlutter/1.0.0',
    },
  ));

  static bool _initialized = false;

  static void _configureHttpClient() {
    if (!kIsWeb) {
      (_dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
        final client = HttpClient();
        
        // 完全禁用证书验证（仅用于调试）
        client.badCertificateCallback = (cert, host, port) {
          print('Certificate check for $host:$port - ALLOWING ALL');
          return true;
        };
        
        // 设置连接超时
        client.connectionTimeout = const Duration(seconds: 30);
        // 设置空闲超时
        client.idleTimeout = const Duration(seconds: 30);
        
        // 设置代理为直连
        client.findProxy = (uri) => 'DIRECT';
        
        return client;
      };
    }
  }

  static void _setupInterceptors() {
    if (_initialized) return;
    _initialized = true;

    // 请求拦截器 - 统一添加认证信息
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // 从SharedPreferences获取token
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // 处理401未授权
        if (error.response?.statusCode == 401) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.remove('token');
          // 可以在这里添加跳转到登录页的逻辑
        }
        handler.next(error);
      },
    ));

    // 响应拦截器 - 统一处理响应
    _dio.interceptors.add(InterceptorsWrapper(
      onResponse: (response, handler) {
        final data = response.data;
        if (data is Map<String, dynamic>) {
          final code = data['code'] ?? 500;
          if (code == 0) {
            // 如果业务状态码为0，直接返回data字段
            response.data = data;
          } else {
            // 如果业务状态码不为0，抛出错误
            final message = data['message'] ?? '请求失败';
            final error = DioException(
              requestOptions: response.requestOptions,
              response: response,
              message: message,
            );
            handler.reject(error);
            return;
          }
        }
        handler.next(response);
      },
    ));
  }

  static Future<void> _init() async {
    _configureHttpClient();
    _setupInterceptors();
  }

  // 认证相关
  static Future<Map<String, dynamic>> getSmsCode(Map<String, dynamic> data) async {
    await _init();
    try {
      final response = await _dio.post('/auth/gen_sms', data: data);
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // 用户注册
  static Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    await _init();
    try {
      final response = await _dio.post('/auth/register', data: data);
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // 用户登录
  static Future<String> login({required String username, required String password}) async {
    await _init();
    try {
      print('Attempting login to: $baseUrl/auth/login');
      print('Username: $username');
      print('Platform: ${kIsWeb ? 'Web' : 'Mobile'}');
      print('Base URL: $baseUrl');
      
      // 跳过连接测试，直接尝试登录
      
      final response = await _dio.post(
        '/auth/login',
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          contentType: 'application/x-www-form-urlencoded',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        ),
      );
      
      print('Login response status: ${response.statusCode}');
      print('Login response data: ${response.data}');

      final Map<String, dynamic> json = response.data as Map<String, dynamic>;
      final int code = (json['code'] ?? 500) as int;
      
      if (code != 0) {
        final String msg = (json['message'] ?? '登录失败') as String;
        throw Exception(msg);
      }
      
      final Map<String, dynamic> data = json['data'] as Map<String, dynamic>;
      final String token = (data['access_token'] ?? '') as String;
      
      if (token.isEmpty) {
        throw Exception('登录失败：未返回 token');
      }

      // 保存token到SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', token);
      
      return token;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // 获取用户信息
  static Future<Map<String, dynamic>> getMe() async {
    await _init();
    try {
      final response = await _dio.get('/me');
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // 获取音乐配置
  static Future<Map<String, dynamic>> getMusicConfig(String roomId) async {
    await _init();
    try {
      final response = await _dio.get('/music/config/$roomId');
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // 统一错误处理
  static Exception _handleError(DioException e) {
    print('DioException: ${e.type} - ${e.message}');
    print('Response: ${e.response?.data}');
    print('Status Code: ${e.response?.statusCode}');
    
    if (e.response != null) {
      final Map<String, dynamic>? json = e.response?.data as Map<String, dynamic>?;
      final String detail = json?['detail'] ?? json?['message'] ?? '请求失败';
      return Exception(detail);
    } else {
      String errorMsg = '网络连接失败';
      switch (e.type) {
        case DioExceptionType.connectionTimeout:
          errorMsg = '连接超时，请检查网络';
          break;
        case DioExceptionType.sendTimeout:
          errorMsg = '发送超时，请检查网络';
          break;
        case DioExceptionType.receiveTimeout:
          errorMsg = '接收超时，请检查网络';
          break;
        case DioExceptionType.badResponse:
          errorMsg = '服务器响应错误';
          break;
        case DioExceptionType.cancel:
          errorMsg = '请求被取消';
          break;
        case DioExceptionType.connectionError:
          errorMsg = '连接错误，请检查网络';
          break;
        case DioExceptionType.badCertificate:
          errorMsg = '证书验证失败';
          break;
        case DioExceptionType.unknown:
          errorMsg = '未知网络错误: ${e.message}';
          break;
      }
      return Exception(errorMsg);
    }
  }
}


