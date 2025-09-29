class ChatMessage {
  final String user;
  final int roomId;
  final String content;
  final int timestamp;
  final MessageType type;
  final bool isOwn;
  final bool showHeader;
  final String? musicId;
  final String? musicUrl;

  ChatMessage({
    required this.user,
    required this.roomId,
    required this.content,
    required this.timestamp,
    required this.type,
    required this.isOwn,
    this.showHeader = true,
    this.musicId,
    this.musicUrl,
  });

  factory ChatMessage.fromProtobuf(dynamic protoMessage, String currentUser) {
    return ChatMessage(
      user: protoMessage.user,
      roomId: protoMessage.roomId,
      content: protoMessage.content,
      timestamp: protoMessage.timestamp,
      type: MessageType.fromValue(protoMessage.type.value),
      isOwn: protoMessage.user == currentUser,
    );
  }

  ChatMessage copyWith({
    String? user,
    int? roomId,
    String? content,
    int? timestamp,
    MessageType? type,
    bool? isOwn,
    bool? showHeader,
    String? musicId,
    String? musicUrl,
  }) {
    return ChatMessage(
      user: user ?? this.user,
      roomId: roomId ?? this.roomId,
      content: content ?? this.content,
      timestamp: timestamp ?? this.timestamp,
      type: type ?? this.type,
      isOwn: isOwn ?? this.isOwn,
      showHeader: showHeader ?? this.showHeader,
      musicId: musicId ?? this.musicId,
      musicUrl: musicUrl ?? this.musicUrl,
    );
  }
}

enum MessageType {
  unknown(0),
  system(1),
  userText(2),
  queryCount(3),
  roomCount(4),
  music(5);

  const MessageType(this.value);
  final int value;

  static MessageType fromValue(int value) {
    return MessageType.values.firstWhere(
      (e) => e.value == value,
      orElse: () => MessageType.unknown,
    );
  }
}
