import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:fixnum/fixnum.dart' as $fixnum;
import '../models/chat_message.dart' as models;
import '../proto/chat.pb.dart' as proto;

class WebSocketService {
  WebSocketChannel? _channel;
  StreamController<models.ChatMessage> _messageController = StreamController<models.ChatMessage>.broadcast();
  StreamController<bool> _connectionController = StreamController<bool>.broadcast();

  Stream<models.ChatMessage> get messageStream => _messageController.stream;
  Stream<bool> get connectionStream => _connectionController.stream;

  bool get isConnected => _channel != null;

  Future<void> connect(int roomId, String token) async {
    try {
      // 构建 WebSocket URL，参考前端配置
      final baseUrl = String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'https://im.jiamid.com',
      ).replaceAll('http://', 'ws://').replaceAll('https://', 'wss://');

      final wsUrl = '$baseUrl/ws/$roomId?token=$token';

      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _channel!.stream.listen(
            (data) {
          try {
            Uint8List bytes;
            if (data is List<int>) {
              bytes = Uint8List.fromList(data);
            } else if (data is String) {
              bytes = Uint8List.fromList(utf8.encode(data));
            } else {
              return;
            }

            final chatMessage = proto.ChatMessage.fromBuffer(bytes);
            final message = models.ChatMessage.fromProtobuf(chatMessage, '');
            _messageController.add(message);
          } catch (e) {
            print('Failed to decode message: $e');
          }
        },
        onError: (error) {
          print('WebSocket error: $error');
          _connectionController.add(false);
        },
        onDone: () {
          print('WebSocket disconnected');
          _connectionController.add(false);
        },
      );

      _connectionController.add(true);
      print('WebSocket connected');
    } catch (e) {
      print('Failed to connect WebSocket: $e');
      _connectionController.add(false);
    }
  }

  void sendMessage(models.ChatMessage message) {
    if (_channel == null) return;

    try {
      final protoMessage = proto.ChatMessage()
        ..user = message.user
        ..roomId = message.roomId
        ..content = message.content
        ..timestamp = $fixnum.Int64(message.timestamp)
        ..type = proto.MessageType.values[message.type.value];

      _channel!.sink.add(protoMessage.writeToBuffer());
    } catch (e) {
      print('Failed to send message: $e');
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
    _connectionController.add(false);
  }

  void dispose() {
    disconnect();
    _messageController.close();
    _connectionController.close();
  }
}
