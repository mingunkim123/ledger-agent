import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthService extends ChangeNotifier {
  // 백엔드 URL (에뮬레이터: 10.0.2.2, 실기기: PC IP)
  // 현재 설정된 URL을 사용해야 함. main.dart 등에서 주입받거나 상수로 관리 필요.
  // 여기서는 임시로 하드코딩하거나 생성자에서 받도록 함.
  final String baseUrl;
  final _storage = const FlutterSecureStorage();

  String? _token;
  String? get token => _token;
  bool get isAuthenticated => _token != null;

  AuthService({required this.baseUrl});

  Future<void> loadToken() async {
    _token = await _storage.read(key: 'jwt_token');
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/accounts/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access'];
        await _storage.write(key: 'jwt_token', value: _token);
        // Refresh token도 저장하면 좋지만, 일단 Access Token만 처리
        if (data['refresh'] != null) {
          await _storage.write(key: 'refresh_token', value: data['refresh']);
        }
        notifyListeners();
        return true;
      } else {
        return false;
      }
    } catch (e) {
      debugPrint('Login error: $e');
      return false;
    }
  }

  Future<String?> register(
      String username, String password, String email) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/accounts/register/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
          'password2': password,
          'email': email,
        }),
      );

      if (response.statusCode == 201) {
        return null; // Success
      }
      final body = utf8.decode(response.bodyBytes);
      debugPrint('Register failed: ${response.statusCode} $body');
      try {
        final data = jsonDecode(body);
        if (data is Map<String, dynamic>) {
          // 첫 번째 에러 메시지 추출
          final firstKey = data.keys.first;
          final firstVal = data[firstKey];
          if (firstVal is List && firstVal.isNotEmpty)
            return '$firstKey: ${firstVal[0]}';
          return '$firstKey: $firstVal';
        }
      } catch (_) {}
      return '회원가입 실패 (${response.statusCode})';
    } catch (e) {
      debugPrint('Register error: $e');
      return '네트워크 오류가 발생했습니다.';
    }
  }

  Future<void> logout() async {
    _token = null;
    await _storage.deleteAll();
    notifyListeners();
  }
}
