/// GET /transactions, GET /summary API
import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

/// API 요청 타임아웃 (연결 안 될 때 무한 로딩 방지)
const Duration _kTimeout = Duration(seconds: 12);

class TransactionsApi {
  TransactionsApi({required this.baseUrl});
  final String baseUrl;

  Future<List<Transaction>> getTransactions({
    required String userId,
    String? from,
    String? to,
    String? category,
  }) async {
    final q = <String>['user_id=$userId'];
    if (from != null) q.add('from=$from');
    if (to != null) q.add('to=$to');
    if (category != null) q.add('category=${Uri.encodeComponent(category)}');
    final uri = Uri.parse('$baseUrl/transactions?${q.join('&')}');
    final response = await http.get(uri).timeout(_kTimeout, onTimeout: () {
      throw TimeoutException('서버에 연결할 수 없습니다. 주소($baseUrl)와 백엔드 실행 여부를 확인해 주세요.');
    });
    if (response.statusCode != 200) {
      throw Exception('${response.statusCode}: ${response.body}');
    }
    final map = jsonDecode(response.body) as Map<String, dynamic>;
    final list = map['transactions'] as List<dynamic>? ?? [];
    return list.map((e) => Transaction.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Summary> getSummary({required String userId, required String month}) async {
    final uri = Uri.parse('$baseUrl/summary?month=$month&user_id=${Uri.encodeComponent(userId)}');
    final response = await http.get(uri).timeout(_kTimeout, onTimeout: () {
      throw TimeoutException('서버에 연결할 수 없습니다. 주소($baseUrl)와 백엔드 실행 여부를 확인해 주세요.');
    });
    if (response.statusCode != 200) {
      throw Exception('${response.statusCode}: ${response.body}');
    }
    final map = jsonDecode(response.body) as Map<String, dynamic>;
    return Summary.fromJson(map);
  }
}

class Transaction {
  Transaction({
    required this.txId,
    required this.userId,
    required this.occurredDate,
    required this.type,
    required this.amount,
    required this.currency,
    required this.category,
    this.merchant,
    this.memo,
    this.sourceText,
    this.createdAt,
  });
  final String txId;
  final String userId;
  final String occurredDate;
  final String type;
  final int amount;
  final String currency;
  final String category;
  final String? merchant;
  final String? memo;
  final String? sourceText;
  final String? createdAt;

  static Transaction fromJson(Map<String, dynamic> json) {
    return Transaction(
      txId: json['tx_id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      occurredDate: json['occurred_date'] as String? ?? '',
      type: json['type'] as String? ?? 'expense',
      amount: (json['amount'] is int) ? json['amount'] as int : int.tryParse(json['amount'].toString()) ?? 0,
      currency: json['currency'] as String? ?? 'KRW',
      category: json['category'] as String? ?? '',
      merchant: json['merchant'] as String?,
      memo: json['memo'] as String?,
      sourceText: json['source_text'] as String?,
      createdAt: json['created_at'] as String?,
    );
  }
}

class Summary {
  Summary({
    required this.month,
    required this.total,
    required this.byCategory,
  });
  final String month;
  final int total;
  final Map<String, int> byCategory;

  static Summary fromJson(Map<String, dynamic> json) {
    final byCat = json['by_category'] as Map<String, dynamic>? ?? {};
    final map = <String, int>{};
    for (final e in byCat.entries) {
      map[e.key as String] = (e.value is int) ? e.value as int : int.tryParse(e.value.toString()) ?? 0;
    }
    return Summary(
      month: json['month'] as String? ?? '',
      total: (json['total'] is int) ? json['total'] as int : int.tryParse(json['total'].toString()) ?? 0,
      byCategory: map,
    );
  }
}
