import 'package:flutter/material.dart';
import 'auth_service.dart';
import 'login_page.dart';
import 'chat_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'JustChatAMoment',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      routes: {
        '/login': (BuildContext context) => const LoginPage(),
        '/chat': (BuildContext context) => const ChatPage(),
      },
      home: const _Launcher(),
    );
  }
}

class _Launcher extends StatefulWidget {
  const _Launcher({super.key});

  @override
  State<_Launcher> createState() => _LauncherState();
}

class _LauncherState extends State<_Launcher> {
  bool _loading = true;
  bool _loggedIn = false;

  @override
  void initState() {
    super.initState();
    _checkLogin();
  }

  Future<void> _checkLogin() async {
    final bool hasLogin = await AuthService().isLoggedIn();
    if (!mounted) return;
    setState(() {
      _loggedIn = hasLogin;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    return _loggedIn ? const ChatPage() : const LoginPage();
  }
}
