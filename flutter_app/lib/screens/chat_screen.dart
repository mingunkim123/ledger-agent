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
  /// true = 로컬(Ollama), false = 클라우드(서버 기본값)
  var _useLocalModel = false;

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
      final res = await api.sendMessage(
        userId: widget.userId,
        message: text,
        llmProvider: _useLocalModel ? 'ollama' : null,
      );
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
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('지출 추가'),
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
            color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.5),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '말하듯이 적어보세요. 예: 오늘 점심 치킨 23,000원',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Text(
                      '모델: ',
                      style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    SegmentedButton<bool>(
                      segments: const [
                        ButtonSegment(value: false, label: Text('클라우드'), icon: Icon(Icons.cloud_rounded)),
                        ButtonSegment(value: true, label: Text('로컬 (Ollama)'), icon: Icon(Icons.computer_rounded)),
                      ],
                      selected: {_useLocalModel},
                      onSelectionChanged: (Set<bool> selected) {
                        setState(() => _useLocalModel = selected.first);
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
              itemCount: _messages.length,
              itemBuilder: (context, i) {
                final m = _messages[i];
                return Align(
                  alignment: m.isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: m.isUser
                          ? theme.colorScheme.primaryContainer
                          : theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: theme.shadowColor.withOpacity(0.06),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
                    child: Text(
                      m.text,
                      style: theme.textTheme.bodyLarge,
                    ),
                  ),
                );
              },
            ),
          ),
          if (_loading)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2, color: theme.colorScheme.primary),
              ),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: '지출 내용 입력',
                      filled: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(
                  onPressed: _loading ? null : _send,
                  icon: const Icon(Icons.send_rounded, size: 20),
                  label: const Text('전송'),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                  ),
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
