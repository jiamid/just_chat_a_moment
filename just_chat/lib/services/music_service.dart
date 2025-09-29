import 'package:dio/dio.dart';
import 'package:audioplayers/audioplayers.dart';
// import '../models/chat_message.dart';

class MusicService {
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isPlaying = false;
  String? _currentMusicId;
  bool _isMuted = false;

  bool get isPlaying => _isPlaying;
  String? get currentMusicId => _currentMusicId;
  bool get isMuted => _isMuted;

  Future<Map<String, dynamic>> getMusicConfig(int roomId) async {
    try {
      final baseUrl = String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000/api',
      );
      
      final dio = Dio();
      final response = await dio.get(
        '$baseUrl/music/config/$roomId',
        options: Options(
          headers: {'Content-Type': 'application/json'},
        ),
      );

      if (response.statusCode == 200) {
        final json = response.data;
        if (json['code'] == 0) {
          return Map<String, dynamic>.from(json['data'] ?? {});
        }
      }
      return {};
    } catch (e) {
      print('Failed to get music config: $e');
      return {};
    }
  }

  Future<void> playMusic(String musicUrl, String musicId, {int? delayMs}) async {
    try {
      if (delayMs != null && delayMs > 0) {
        await Future.delayed(Duration(milliseconds: delayMs));
      }

      await _audioPlayer.play(UrlSource(musicUrl));
      _isPlaying = true;
      _currentMusicId = musicId;
      _isMuted = false;
      
      print('Playing music: $musicId');
    } catch (e) {
      print('Failed to play music: $e');
      _isPlaying = false;
      _currentMusicId = null;
    }
  }

  Future<void> stopMusic() async {
    try {
      await _audioPlayer.stop();
      _isPlaying = false;
      _currentMusicId = null;
      _isMuted = false;
    } catch (e) {
      print('Failed to stop music: $e');
    }
  }

  Future<void> toggleMute() async {
    try {
      _isMuted = !_isMuted;
      await _audioPlayer.setVolume(_isMuted ? 0.0 : 1.0);
    } catch (e) {
      print('Failed to toggle mute: $e');
    }
  }

  void dispose() {
    _audioPlayer.dispose();
  }
}
