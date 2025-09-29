import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'auth_service.dart';
import 'services/websocket_service.dart';
import 'services/music_service.dart';
import 'models/chat_message.dart';
// import 'api_service.dart';

class ChatPage extends StatefulWidget {
  final int? roomId;
  
  const ChatPage({super.key, this.roomId});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> with TickerProviderStateMixin {
  // 基础状态
  final TextEditingController _messageController = TextEditingController();
  final TextEditingController _jumpRoomController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final WebSocketService _webSocketService = WebSocketService();
  final MusicService _musicService = MusicService();
  
  // 数据状态
  List<ChatMessage> _messages = [];
  String _username = '';
  int? _currentRoomId;
  bool _isConnected = false;
  int _currentRoomCount = 0;
  String _systemMessage = '';
  Map<String, dynamic> _musicConfig = {};
  List<int> _recentRooms = [];
  
  // UI状态
  bool _showMobileNavbar = false;
  bool _showMusicMenu = false;
  bool _isMobile = false;
  bool _isKeyboardOpen = false;
  double _initialViewportHeight = 0;
  
  // 音乐状态
  bool _isPlaying = false;
  String? _currentMusicId;
  bool _isMuted = false;
  bool _isUserMuted = false;
  
  // 动画控制器
  late AnimationController _systemMessageController;
  late AnimationController _musicMenuController;
  
  @override
  void initState() {
    super.initState();
    _currentRoomId = widget.roomId;
    _initializeAnimations();
    _checkMobileDevice();
    _loadUserInfo();
    _loadRecentRooms();
    if (_currentRoomId != null) {
      _loadMusicConfig();
      _connectWebSocket();
    }
  }

  void _initializeAnimations() {
    _systemMessageController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _musicMenuController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
  }

  void _checkMobileDevice() {
    final mediaQuery = MediaQuery.of(context);
    _isMobile = mediaQuery.size.width <= 768;
    _initialViewportHeight = mediaQuery.size.height;
    
    // 监听键盘变化
    mediaQuery.viewInsets.bottom > 0 ? _isKeyboardOpen = true : _isKeyboardOpen = false;
  }

  Future<void> _loadUserInfo() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _username = prefs.getString('username') ?? 'Unknown';
      setState(() {});
    } catch (e) {
      print('Failed to load user info: $e');
    }
  }

  Future<void> _loadRecentRooms() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('recentRooms');
      if (saved != null) {
        _recentRooms = List<int>.from(jsonDecode(saved));
      } else {
        _recentRooms = [1, 2, 3, 4, 5];
      }
      setState(() {});
    } catch (e) {
      print('Failed to load recent rooms: $e');
      _recentRooms = [1, 2, 3, 4, 5];
    }
  }

  Future<void> _saveRecentRooms() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('recentRooms', jsonEncode(_recentRooms));
    } catch (e) {
      print('Failed to save recent rooms: $e');
    }
  }

  Future<void> _loadMusicConfig() async {
    if (_currentRoomId == null) return;
    try {
      _musicConfig = await _musicService.getMusicConfig(_currentRoomId!);
      setState(() {});
    } catch (e) {
      print('Failed to load music config: $e');
    }
  }

  Future<void> _connectWebSocket() async {
    if (_currentRoomId == null) return;
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      if (token == null) return;
      
      await _webSocketService.connect(_currentRoomId!, token);
      
      // 监听连接状态
      _webSocketService.connectionStream.listen((isConnected) {
        if (mounted) {
          setState(() {
            _isConnected = isConnected;
          });
        }
      });
      
      // 监听消息
      _webSocketService.messageStream.listen((message) {
        if (mounted) {
          _handleMessage(message);
        }
      });
    } catch (e) {
      print('Failed to connect WebSocket: $e');
    }
  }

  void _handleMessage(ChatMessage message) {
    setState(() {
      switch (message.type) {
        case MessageType.roomCount:
          _updateRoomCount(message.content);
          break;
        case MessageType.system:
          _showSystemMessage(message.content);
          break;
        case MessageType.music:
          _handleMusicMessage(message);
          break;
        case MessageType.userText:
        default:
          _addMessage(message);
          break;
      }
    });
  }

  void _updateRoomCount(String content) {
    final regex = RegExp(r'当前房间人数: (\d+)');
    final match = regex.firstMatch(content);
    if (match != null) {
      _currentRoomCount = int.parse(match.group(1)!);
    }
  }

  void _showSystemMessage(String content) {
    _systemMessage = content;
    _systemMessageController.forward();
    
    Timer(const Duration(seconds: 3), () {
      if (mounted) {
        _systemMessageController.reverse();
        setState(() {
          _systemMessage = '';
        });
      }
    });
  }

  void _handleMusicMessage(ChatMessage message) {
    final musicInfo = _musicConfig[message.content];
    final displayContent = musicInfo != null 
        ? '🎵 ${musicInfo['name']}' 
        : '🎵 音乐: ${message.content}';
    
    final musicMessage = message.copyWith(
      content: displayContent,
      musicId: message.content,
      musicUrl: musicInfo?['url'],
    );
    
    _addMessage(musicMessage);
    
    if (musicInfo != null) {
      _playMusicWithDelay(message.content, message.timestamp);
    }
  }

  void _addMessage(ChatMessage message) {
    // 检查是否需要隐藏用户名（与上一条消息是同一用户）
    bool showHeader = true;
    if (_messages.isNotEmpty) {
      final lastMessage = _messages.last;
      if (lastMessage.user == message.user && lastMessage.isOwn == message.isOwn) {
        showHeader = false;
      }
    }
    
    final newMessage = message.copyWith(showHeader: showHeader);
    _messages.add(newMessage);
    
    // 滚动到底部
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 100),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _playMusicWithDelay(String musicId, int targetTimestamp) {
    final musicInfo = _musicConfig[musicId];
    if (musicInfo == null || musicInfo['url'] == null) return;
    
    final currentTime = DateTime.now().millisecondsSinceEpoch;
    final delay = targetTimestamp - currentTime;
    
    if (delay <= 0) {
      _playMusic(musicInfo['url'], musicId);
    } else {
      Timer(Duration(milliseconds: delay), () {
        _playMusic(musicInfo['url'], musicId);
      });
    }
  }

  void _playMusic(String musicUrl, String musicId) {
    _musicService.playMusic(musicUrl, musicId).then((_) {
      if (mounted) {
        setState(() {
          _isPlaying = true;
          _currentMusicId = musicId;
          _isMuted = false;
          _isUserMuted = false;
        });
      }
    }).catchError((e) {
      print('Failed to play music: $e');
      if (_isMobile) {
        // 移动端播放失败时自动静音
        setState(() {
          _isMuted = true;
          _isUserMuted = false;
        });
      }
    });
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty || !_isConnected) return;
    
    final message = ChatMessage(
      user: _username,
      roomId: _currentRoomId!,
      content: text,
      timestamp: DateTime.now().millisecondsSinceEpoch,
      type: MessageType.userText,
      isOwn: true,
    );
    
    _webSocketService.sendMessage(message);
    _messageController.clear();
  }

  void _sendMusic(String musicId) {
    if (!_isConnected) return;
    
    final message = ChatMessage(
      user: _username,
      roomId: _currentRoomId!,
      content: musicId,
      timestamp: DateTime.now().millisecondsSinceEpoch,
      type: MessageType.music,
      isOwn: true,
    );
    
    _webSocketService.sendMessage(message);
    _showMusicMenu = false;
    setState(() {});
  }

  void _switchRoom(int roomId) {
    if (roomId == _currentRoomId) return;
    
    setState(() {
      _currentRoomId = roomId;
      _messages.clear();
      _currentRoomCount = 0;
      _showMobileNavbar = false;
    });
    
    _addToRecentRooms(roomId);
    _webSocketService.disconnect();
    _loadMusicConfig();
    _connectWebSocket();
  }

  void _addToRecentRooms(int roomId) {
    _recentRooms.remove(roomId);
    _recentRooms.insert(0, roomId);
    _recentRooms = _recentRooms.take(5).toList();
    _saveRecentRooms();
  }

  void _jumpToRoom() {
    final roomId = int.tryParse(_jumpRoomController.text);
    if (roomId != null && roomId > 0) {
      _jumpRoomController.clear();
      _switchRoom(roomId);
    }
  }

  void _toggleMusicMenu() {
    setState(() {
      _showMusicMenu = !_showMusicMenu;
    });
    if (_showMusicMenu) {
      _musicMenuController.forward();
    } else {
      _musicMenuController.reverse();
    }
  }

  void _toggleMute() {
    if (_isPlaying) {
      _musicService.toggleMute().then((_) {
        if (mounted) {
          setState(() {
            _isMuted = !_isMuted;
            _isUserMuted = _isMuted;
          });
        }
      });
    }
  }

  Future<void> _logout() async {
    await AuthService().logout();
    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed('/login');
  }

  @override
  void dispose() {
    _messageController.dispose();
    _jumpRoomController.dispose();
    _scrollController.dispose();
    _webSocketService.dispose();
    _musicService.dispose();
    _systemMessageController.dispose();
    _musicMenuController.dispose();
    super.dispose();
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
        child: Row(
          children: [
            // 左侧导航栏
            _buildLeftSidebar(),
            // 右侧聊天区域
            Expanded(child: _buildRightChat()),
          ],
        ),
      ),
    );
  }

  Widget _buildLeftSidebar() {
    return Container(
      width: 250,
      decoration: BoxDecoration(
        color: const Color(0x0FFFFFFF), // rgba(255, 255, 255, 0.06)
        border: const Border(
          right: BorderSide(
            color: Color(0x1FFFFFFF), // rgba(255, 255, 255, 0.12)
            width: 1,
          ),
        ),
      ),
      child: Column(
        children: [
          // Logo 区域
          _buildLogoSection(),
          // 房间列表区域
          Expanded(child: _buildRoomsSection()),
          // 用户信息区域
          _buildUserSection(),
        ],
      ),
    );
  }

  Widget _buildLogoSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Color(0x1FFFFFFF),
            width: 1,
          ),
        ),
      ),
      child: const Text(
        'Just Chat A Moment',
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
    );
  }

  Widget _buildRoomsSection() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '最近房间',
            style: TextStyle(
              fontSize: 16,
              color: Color(0xFFCDD0E5),
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          // 房间列表
          Expanded(
            child: ListView.builder(
              itemCount: _recentRooms.length,
              itemBuilder: (context, index) {
                final roomId = _recentRooms[index];
                final isActive = roomId == _currentRoomId;
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: () => _switchRoom(roomId),
                      borderRadius: BorderRadius.circular(10),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: isActive
                              ? const Color(0xB36366F1) // 渐变背景
                              : const Color(0x0FFFFFFF),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: const Color(0x1FFFFFFF),
                            width: 1,
                          ),
                        ),
                        child: Center(
                          child: Text(
                            '房间 $roomId',
                            style: TextStyle(
                              fontWeight: FontWeight.w500,
                              color: isActive ? Colors.white : const Color(0xFFE6E6F0),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 24),
          // 房间跳转
          const Text(
            '跳转房间',
            style: TextStyle(
              fontSize: 14,
              color: Color(0xFFBDC3C7),
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0x0FFFFFFF),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: const Color(0x1FFFFFFF),
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _jumpRoomController,
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                    style: const TextStyle(
                      color: Color(0xFFE6E6F0),
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                    decoration: const InputDecoration(
                      hintText: '房间号',
                      hintStyle: TextStyle(
                        color: Color(0x8CE6E6F0),
                        fontWeight: FontWeight.w500,
                      ),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.zero,
                    ),
                    onSubmitted: (_) => _jumpToRoom(),
                  ),
                ),
                const SizedBox(width: 8),
                Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: _jumpToRoom,
                    borderRadius: BorderRadius.circular(6),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      child: const Text(
                        'GO',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(
            color: Color(0x1FFFFFFF),
            width: 1,
          ),
        ),
      ),
      child: Column(
        children: [
          // 用户信息
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _username,
                      style: const TextStyle(
                        fontWeight: FontWeight.w500,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    // 连接状态
                    Row(
                      children: [
                        if (_isConnected) ...[
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: Color(0xFF22C55E),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            '已连接',
                            style: TextStyle(
                              color: Color(0xFF86EFAC),
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ] else ...[
                          Material(
                            color: Colors.transparent,
                            child: InkWell(
                              onTap: () => _connectWebSocket(),
                              borderRadius: BorderRadius.circular(6),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [Color(0xFFF97316), Color(0xFFEF4444)],
                                  ),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: const Text(
                                  '重连',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // 退出按钮
          SizedBox(
            width: double.infinity,
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: _logout,
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [
                        Color(0xFF6366F1),
                        Color(0xFF8B5CF6),
                        Color(0xFFEC4899),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    '退出登录',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRightChat() {
    return Column(
      children: [
        // 顶部：房间信息
        _buildChatHeader(),
        // 系统消息提示条
        if (_systemMessage.isNotEmpty) _buildSystemNotification(),
        // 移动端静音提示
        if (_isMobile && _currentMusicId != null && _isMuted && !_isUserMuted)
          _buildMobileMuteNotification(),
        // 中间：消息区域
        Expanded(child: _buildChatMain()),
        // 底部：输入区域
        if (_currentRoomId != null) _buildInputContainer(),
      ],
    );
  }

  Widget _buildChatHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: const BoxDecoration(
        color: Color(0x0FFFFFFF),
        border: Border(
          bottom: BorderSide(
            color: Color(0x1FFFFFFF),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          // 移动端菜单按钮
          if (_isMobile)
            Container(
              margin: const EdgeInsets.only(right: 16),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () {
                    setState(() {
                      _showMobileNavbar = !_showMobileNavbar;
                    });
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [
                          Color(0xFF6366F1),
                          Color(0xFF8B5CF6),
                          Color(0xFFEC4899),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.menu,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                ),
              ),
            ),
          // 房间标题
          Expanded(
            child: Text(
              _currentRoomId != null
                  ? '房间 $_currentRoomId${_currentRoomCount > 0 ? ' [$_currentRoomCount]' : ''}'
                  : '选择房间开始聊天',
              style: const TextStyle(
                color: Color(0xFFE6E6F0),
                fontSize: 24,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          // 音乐控制按钮
          if (_currentRoomId != null && _currentMusicId != null)
            Container(
              margin: const EdgeInsets.only(left: 16),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _toggleMute,
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [
                          Color(0xFF6366F1),
                          Color(0xFF8B5CF6),
                          Color(0xFFEC4899),
                        ],
                      ),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      _isMuted ? Icons.volume_off : Icons.music_note,
                      color: Colors.white,
                      size: 16,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSystemNotification() {
    return Container(
      height: 30,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Color(0xE66366F1),
            Color(0xE68B5CF6),
            Color(0xE6EC4899),
          ],
        ),
      ),
      child: Center(
        child: Text(
          _systemMessage,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _buildMobileMuteNotification() {
    return Container(
      height: 40,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Color(0xE6F59E0B),
            Color(0xE6FBBF24),
          ],
        ),
      ),
      child: const Center(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('🔇', style: TextStyle(fontSize: 16)),
            SizedBox(width: 8),
            Text(
              '移动端自动静音播放，点击音乐按钮可开启声音',
              style: TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatMain() {
    if (_currentRoomId == null) {
      return _buildNoRoomMessage();
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: ListView.builder(
        controller: _scrollController,
        itemCount: _messages.length,
        itemBuilder: (context, index) {
          final message = _messages[index];
          return _buildMessageItem(message);
        },
      ),
    );
  }

  Widget _buildNoRoomMessage() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '欢迎使用 Just Chat A Moment',
            style: TextStyle(
              color: Color(0xFFE6E6F0),
              fontSize: 24,
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: 16),
          Text(
            '请从左侧选择一个房间开始聊天，或者输入自定义房间号',
            style: TextStyle(
              color: Color(0xFFCDD0E5),
              fontSize: 16,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildMessageItem(ChatMessage message) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: message.isOwn 
            ? MainAxisAlignment.end 
            : MainAxisAlignment.start,
        children: [
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.7,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              gradient: message.isOwn
                  ? const LinearGradient(
                      colors: [
                        Color(0xE66366F1),
                        Color(0xE68B5CF6),
                        Color(0xE6EC4899),
                      ],
                    )
                  : null,
              color: message.isOwn 
                  ? null 
                  : const Color(0x0FFFFFFF),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(18),
                topRight: const Radius.circular(18),
                bottomLeft: message.isOwn 
                    ? const Radius.circular(18)
                    : const Radius.circular(4),
                bottomRight: message.isOwn 
                    ? const Radius.circular(4)
                    : const Radius.circular(18),
              ),
              border: message.isOwn 
                  ? null 
                  : Border.all(
                      color: const Color(0x1FFFFFFF),
                      width: 1,
                    ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (message.showHeader)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text(
                      message.user,
                      style: TextStyle(
                        fontSize: 12,
                        color: message.isOwn 
                            ? Colors.white.withValues(alpha: 0.8)
                            : const Color(0xFFE6E6F0).withValues(alpha: 0.6),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                Text(
                  message.content,
                  style: TextStyle(
                    color: message.isOwn 
                        ? Colors.white 
                        : const Color(0xFFE6E6F0),
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputContainer() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Color(0x0FFFFFFF),
        border: Border(
          top: BorderSide(
            color: Color(0x1FFFFFFF),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          // 音乐按钮
          _buildMusicButton(),
          const SizedBox(width: 16),
          // 输入框
          Expanded(
            child: TextField(
              controller: _messageController,
              enabled: _isConnected,
              style: const TextStyle(
                color: Color(0xFFE6E6F0),
                fontSize: 16,
              ),
              decoration: InputDecoration(
                hintText: '输入消息...',
                hintStyle: const TextStyle(
                  color: Color(0x8CE6E6F0),
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(
                    color: Color(0x1FFFFFFF),
                    width: 1,
                  ),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(
                    color: Color(0x1FFFFFFF),
                    width: 1,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
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
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 16),
          // 发送按钮
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: _isConnected && _messageController.text.trim().isNotEmpty
                  ? _sendMessage
                  : null,
              borderRadius: BorderRadius.circular(14),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  gradient: _isConnected && _messageController.text.trim().isNotEmpty
                      ? const LinearGradient(
                          colors: [
                            Color(0xFF6366F1),
                            Color(0xFF8B5CF6),
                            Color(0xFFEC4899),
                          ],
                        )
                      : null,
                  color: _isConnected && _messageController.text.trim().isNotEmpty
                      ? null
                      : Colors.grey.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Text(
                  '发送',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMusicButton() {
    return Stack(
      children: [
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: _isConnected ? _toggleMusicMenu : null,
            borderRadius: BorderRadius.circular(12),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                gradient: _isConnected
                    ? const LinearGradient(
                        colors: [
                          Color(0xFF6366F1),
                          Color(0xFF8B5CF6),
                          Color(0xFFEC4899),
                        ],
                      )
                    : null,
                color: _isConnected ? null : Colors.grey.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.music_note,
                color: Colors.white,
                size: 20,
              ),
            ),
          ),
        ),
        // 音乐选择菜单
        if (_showMusicMenu) _buildMusicMenu(),
      ],
    );
  }

  Widget _buildMusicMenu() {
    return Positioned(
      bottom: 100,
      left: 0,
      child: Container(
        width: 200,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.95),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withValues(alpha: 0.2),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.3),
              blurRadius: 32,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 菜单标题
            Container(
              padding: const EdgeInsets.all(12),
              decoration: const BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: Color(0x33FFFFFF),
                    width: 1,
                  ),
                ),
              ),
              child: const Row(
                children: [
                  Text(
                    '选择音乐',
                    style: TextStyle(
                      color: Color(0xFF1F2937),
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            // 音乐列表
            Container(
              constraints: const BoxConstraints(maxHeight: 200),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _musicConfig.length,
                itemBuilder: (context, index) {
                  final musicId = _musicConfig.keys.elementAt(index);
                  final musicInfo = _musicConfig[musicId];
                  return Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: () => _sendMusic(musicId),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: const BoxDecoration(
                          border: Border(
                            bottom: BorderSide(
                              color: Color(0x1AFFFFFF),
                              width: 1,
                            ),
                          ),
                        ),
                        child: Text(
                          '🎵 ${musicInfo['name'] ?? musicId}',
                          style: const TextStyle(
                            color: Color(0xFF374151),
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}