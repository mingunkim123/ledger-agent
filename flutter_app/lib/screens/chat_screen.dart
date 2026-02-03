/// 채팅 화면 (Step 9) - 한 줄 입력 + 응답 표시
import 'package:flutter/material.dart';

import '../api/chat_api.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({
    super.key,
    this.userId = 'user1',
    this.baseUrl = 'http://localhost:8000',
  });
  final String userId;
  final String baseUrl;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  final _messages = <_MessageItem>[];
  var _loading = false;

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _loading) return;
    _controller.clear();
    setState(() {
      _messages.add(_MessageItem(isUser: true, text: text));
      _loading = true;
    });
    try {
      final api = ChatApi(baseUrl: widget.baseUrl);
      final res = await api.sendMessage(userId: widget.userId, message: text);
      setState(() {
        _messages.add(_MessageItem(
          isUser: false,
          text: res.reply,
          txId: res.txId,
          undoToken: res.undoToken,
        ));
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add(_MessageItem(isUser: false, text: '오류: $e'));
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('가계부 에이전트'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
              itemCount: _messages.length,
              itemBuilder: (context, i) {
                final m = _messages[i];
                return Align(
                  alignment: m.isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: m.isUser
                          ? Theme.of(context).colorScheme.primaryContainer
                          : Theme.of(context).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      m.text,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                  ),
                );
              },
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: '한 줄로 입력 (예: 오늘 치킨 23000원)',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: _loading ? null : _send,
                  child: const Text('전송'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageItem {
  _MessageItem({
    required this.isUser,
    required this.text,
    this.txId,
    this.undoToken,
  });
  final bool isUser;
  final String text;
  final String? txId;
  final String? undoToken;
}
