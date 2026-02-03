/// POST /chat API (Step 9)
import 'dart:convert';

import 'package:http/http.dart' as http;

class ChatApi {
  ChatApi({this.baseUrl = 'http://localhost:8000'});
  final String baseUrl;

  Future<ChatResponse> sendMessage({
    required String userId,
    required String message,
    String? idemKey,
  }) async {
    final uri = Uri.parse('$baseUrl/chat');
    final body = jsonEncode({
      'user_id': userId,
      'message': message,
      if (idemKey != null) 'idem_key': idemKey,
    });
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: body,
    );
    if (response.statusCode != 200) {
      throw Exception('${response.statusCode}: ${response.body}');
    }
    final map = jsonDecode(response.body) as Map<String, dynamic>;
    return ChatResponse(
      reply: map['reply'] as String? ?? '',
      txId: map['tx_id'] as String?,
      undoToken: map['undo_token'] as String?,
      needsClarification: map['needs_clarification'] as bool? ?? false,
    );
  }
}

class ChatResponse {
  ChatResponse({
    required this.reply,
    this.txId,
    this.undoToken,
    required this.needsClarification,
  });
  final String reply;
  final String? txId;
  final String? undoToken;
  final bool needsClarification;
}
