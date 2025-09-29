import 'package:flutter/material.dart';
// import 'package:flutter/services.dart';
import 'dart:async';
// import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import 'auth_service.dart';
import 'api_service.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> with TickerProviderStateMixin {
  // 基础状态
  bool _isLogin = true;
  bool _isLoading = false;
  String? _error;
  int _countdown = 0;
  Timer? _timer;
  
  // 表单控制器
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _codeController = TextEditingController();
  
  // 表单数据
  String _sign = '';
  int _expiresAt = 0;
  
  // 动画控制器
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _checkAutoLogin();
  }

  void _initializeAnimations() {
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
    _animationController.forward();
  }

  Future<void> _checkAutoLogin() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      if (token == null) return;

      // 验证 token 是否有效
      try {
        await ApiService.getMe();
        // token 有效，直接跳转到聊天页面
        if (mounted) {
          Navigator.of(context).pushReplacementNamed('/chat');
        }
      } catch (e) {
        // token 无效，清除
        await prefs.remove('token');
        print('token 无效，已清除');
      }
    } catch (e) {
      print('自动登录检查失败: $e');
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _codeController.dispose();
    _animationController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (_isLogin) {
        await _login();
      } else {
        await _register();
      }
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _login() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      throw Exception('请输入邮箱和密码');
    }

    final token = await ApiService.login(username: email, password: password);
    await AuthService().saveToken(token);

    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed('/chat');
  }

  Future<void> _register() async {
    final email = _emailController.text.trim();
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();
    final code = _codeController.text.trim();

    if (email.isEmpty || username.isEmpty || password.isEmpty || code.isEmpty) {
      throw Exception('请填写所有必填字段');
    }

    // 调用注册接口
    final response = await ApiService.register({
      'email': email,
      'username': username,
      'password': password,
      'code': code,
      'sign': _sign,
      'expires_at': _expiresAt,
    });

    // 注册成功，切换到登录模式
    setState(() {
      _isLogin = true;
      _usernameController.clear();
      _codeController.clear();
      _error = null;
    });
    // 可以显示成功提示
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('注册成功，请登录')),
    );
  }

  Future<void> _getCode() async {
    final email = _emailController.text.trim();
    if (email.isEmpty) {
      setState(() {
        _error = '请先输入邮箱';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await ApiService.getSmsCode({'email': email});
      
      _expiresAt = response['data']['expires_at'];
      _sign = response['data']['sign'];
      _error = null;
      
      // 开始倒计时 120s
      _countdown = 120;
      _timer?.cancel();
      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (_countdown > 0) {
          setState(() {
            _countdown--;
          });
        } else {
          timer.cancel();
        }
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1020),
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(-0.9, -0.9),
            radius: 1.2,
            colors: [
              Color(0x2E6366F1), // rgba(99, 102, 241, 0.18)
              Color(0x006366F1),
            ],
            stops: [0.0, 0.6],
          ),
        ),
        child: Center(
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: _buildLoginBox(),
          ),
        ),
      ),
    );
  }

  Widget _buildLoginBox() {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(maxWidth: 420),
      margin: const EdgeInsets.symmetric(horizontal: 24),
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: const Color(0x0FFFFFFF), // rgba(255, 255, 255, 0.06)
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0x1FFFFFFF), // rgba(255, 255, 255, 0.12)
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 60,
            offset: const Offset(0, 20),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 标题
          _buildTitle(),
          const SizedBox(height: 32),
          // 表单标签
          _buildFormTabs(),
          const SizedBox(height: 24),
          // 表单
          _buildForm(),
        ],
      ),
    );
  }

  Widget _buildTitle() {
    return ShaderMask(
      shaderCallback: (bounds) => const LinearGradient(
        colors: [Color(0xFFE5E7FF), Color(0xFFC7D2FE), Color(0xFFFBCFE8)],
      ).createShader(bounds),
      child: const Text(
        'Just Chat A Moment',
        style: TextStyle(
          fontSize: 28,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
    );
  }

  Widget _buildFormTabs() {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: const Color(0x1FFFFFFF),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildTabButton('登录', _isLogin, () {
              setState(() {
                _isLogin = true;
                _error = null;
              });
            }),
          ),
          Expanded(
            child: _buildTabButton('注册', !_isLogin, () {
              setState(() {
                _isLogin = false;
                _error = null;
              });
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildTabButton(String text, bool isActive, VoidCallback onTap) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            gradient: isActive
                ? const LinearGradient(
                    colors: [
                      Color(0xFF6366F1),
                      Color(0xFF8B5CF6),
                      Color(0xFFEC4899),
                    ],
                  )
                : null,
            color: isActive ? null : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            boxShadow: isActive
                ? [
                    BoxShadow(
                      color: const Color(0xFF6366F1).withValues(alpha: 0.35),
                      blurRadius: 24,
                      offset: const Offset(0, 8),
                    ),
                  ]
                : null,
          ),
          child: Text(
            text,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: isActive ? Colors.white : const Color(0xFFCDD0E5),
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildForm() {
    return Column(
      children: [
        // 邮箱输入框
        _buildFormField(
          controller: _emailController,
          label: '邮箱',
          hintText: '请输入邮箱',
          keyboardType: TextInputType.emailAddress,
          prefixIcon: Icons.email_outlined,
        ),
        const SizedBox(height: 16),
        
        // 用户名输入框（仅注册时显示）
        if (!_isLogin) ...[
          _buildFormField(
            controller: _usernameController,
            label: '用户名',
            hintText: '请输入用户名',
            keyboardType: TextInputType.text,
            prefixIcon: Icons.person_outline,
          ),
          const SizedBox(height: 16),
        ],
        
        // 密码输入框
        _buildFormField(
          controller: _passwordController,
          label: '密码',
          hintText: '请输入密码',
          obscureText: true,
          prefixIcon: Icons.lock_outline,
        ),
        const SizedBox(height: 16),
        
        // 验证码输入框（仅注册时显示）
        if (!_isLogin) ...[
          _buildCodeField(),
          const SizedBox(height: 16),
        ],
        
        // 提交按钮
        _buildSubmitButton(),
        
        // 错误信息
        if (_error != null) ...[
          const SizedBox(height: 16),
          _buildErrorMessage(),
        ],
      ],
    );
  }

  Widget _buildFormField({
    required TextEditingController controller,
    required String label,
    required String hintText,
    TextInputType? keyboardType,
    bool obscureText = false,
    IconData? prefixIcon,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFFCDD0E5),
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          obscureText: obscureText,
          style: const TextStyle(
            color: Color(0xFFE6E6F0),
            fontSize: 16,
          ),
          decoration: InputDecoration(
            hintText: hintText,
            hintStyle: const TextStyle(
              color: Color(0x8CE6E6F0),
            ),
            prefixIcon: prefixIcon != null
                ? Icon(
                    prefixIcon,
                    color: const Color(0xFFCDD0E5),
                    size: 20,
                  )
                : null,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(
                color: Color(0x1FFFFFFF),
                width: 1,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(
                color: Color(0x1FFFFFFF),
                width: 1,
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(
                color: Color(0xFF6366F1),
                width: 2,
              ),
            ),
            filled: true,
            fillColor: const Color(0x0FFFFFFF),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 12,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCodeField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '验证码',
          style: TextStyle(
            color: Color(0xFFCDD0E5),
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _codeController,
                keyboardType: TextInputType.number,
                style: const TextStyle(
                  color: Color(0xFFE6E6F0),
                  fontSize: 16,
                ),
                decoration: InputDecoration(
                  hintText: '请输入邮箱验证码',
                  hintStyle: const TextStyle(
                    color: Color(0x8CE6E6F0),
                  ),
                  prefixIcon: const Icon(
                    Icons.verified_user_outlined,
                    color: Color(0xFFCDD0E5),
                    size: 20,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(
                      color: Color(0x1FFFFFFF),
                      width: 1,
                    ),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(
                      color: Color(0x1FFFFFFF),
                      width: 1,
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(
                      color: Color(0xFF6366F1),
                      width: 2,
                    ),
                  ),
                  filled: true,
                  fillColor: const Color(0x0FFFFFFF),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: (_countdown > 0 || _isLoading || _emailController.text.trim().isEmpty)
                    ? null
                    : _getCode,
                borderRadius: BorderRadius.circular(10),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: const Color(0x1FFFFFFF),
                      width: 1,
                    ),
                    borderRadius: BorderRadius.circular(10),
                    color: (_countdown > 0 || _isLoading || _emailController.text.trim().isEmpty)
                        ? Colors.grey.withValues(alpha: 0.3)
                        : Colors.transparent,
                  ),
                  child: Text(
                    _countdown > 0 ? '${_countdown}s' : '获取验证码',
                    style: TextStyle(
                      color: (_countdown > 0 || _isLoading || _emailController.text.trim().isEmpty)
                          ? const Color(0xFFCDD0E5).withValues(alpha: 0.6)
                          : const Color(0xFFCDD0E5),
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSubmitButton() {
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _isLoading ? null : _handleSubmit,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              gradient: _isLoading
                  ? null
                  : const LinearGradient(
                      colors: [
                        Color(0xFF6366F1),
                        Color(0xFF8B5CF6),
                        Color(0xFFEC4899),
                      ],
                    ),
              color: _isLoading ? Colors.grey.withValues(alpha: 0.3) : null,
              borderRadius: BorderRadius.circular(12),
              boxShadow: _isLoading
                  ? null
                  : [
                      BoxShadow(
                        color: const Color(0xFF6366F1).withValues(alpha: 0.35),
                        blurRadius: 24,
                        offset: const Offset(0, 10),
                      ),
                      BoxShadow(
                        color: const Color(0xFFEC4899).withValues(alpha: 0.25),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ],
            ),
            child: _isLoading
                ? const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      ),
                      SizedBox(width: 12),
                      Text(
                        '处理中...',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  )
                : Text(
                    _isLogin ? '登录' : '注册',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildErrorMessage() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0x26EF4444), // rgba(239, 68, 68, 0.15)
        border: Border.all(
          color: const Color(0x59EF4444), // rgba(239, 68, 68, 0.35)
          width: 1,
        ),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        _error!,
        textAlign: TextAlign.center,
        style: const TextStyle(
          color: Color(0xFFFECACA),
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
