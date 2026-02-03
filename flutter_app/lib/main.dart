/// 가계부 에이전트 - Flutter 앱 (Step 9)
import 'package:flutter/material.dart';

import 'screens/chat_screen.dart';

void main() {
  runApp(const ExpenseTrackerApp());
}

class ExpenseTrackerApp extends StatelessWidget {
  const ExpenseTrackerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '가계부 에이전트',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const ChatScreen(
        userId: 'user1',
        baseUrl: 'http://localhost:8000',
      ),
    );
  }
}
