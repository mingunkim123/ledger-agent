/// 내역 목록 - 월/카테고리 필터
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api/transactions_api.dart';
import '../config.dart';
import '../widgets/category_style.dart';

class TransactionListScreen extends StatefulWidget {
  const TransactionListScreen({
    super.key,
    this.userId = 'user1',
    this.baseUrl = kApiBaseUrl,
  });
  final String userId;
  final String baseUrl;

  @override
  State<TransactionListScreen> createState() => _TransactionListScreenState();
}

class _TransactionListScreenState extends State<TransactionListScreen> {
  List<Transaction> _list = [];
  String _month = '';
  String? _category;
  var _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _month = DateFormat('yyyy-MM').format(DateTime.now());
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = TransactionsApi(baseUrl: widget.baseUrl);
      final year = int.parse(_month.substring(0, 4));
      final m = int.parse(_month.substring(5, 7));
      final lastDay = DateTime(year, m + 1, 0).day;
      final from = '$_month-01';
      final to = '$_month-${lastDay.toString().padLeft(2, '0')}';
      final list = await api.getTransactions(
        userId: widget.userId,
        from: from,
        to: to,
        category: _category,
      );
      setState(() {
        _list = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  static final _currencyFormat = NumberFormat('#,###', 'ko_KR');

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('지출 내역'),
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () => _showFilter(context),
          ),
        ],
      ),
      body: _loading && _list.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: _error != null
                  ? ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Card(
                          color: theme.colorScheme.errorContainer,
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(_error!, style: TextStyle(color: theme.colorScheme.onErrorContainer)),
                                const SizedBox(height: 12),
                                FilledButton.icon(
                                  onPressed: _load,
                                  icon: const Icon(Icons.refresh, size: 18),
                                  label: const Text('다시 시도'),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    )
                  : _list.isEmpty
                      ? ListView(
                          children: [
                            const SizedBox(height: 48),
                            Center(
                              child: Column(
                                children: [
                                  Icon(Icons.receipt_long, size: 64, color: theme.colorScheme.outline),
                                  const SizedBox(height: 16),
                                  Text('이 기간 지출 내역이 없습니다.', style: theme.textTheme.bodyLarge?.copyWith(color: theme.colorScheme.outline)),
                                ],
                              ),
                            ),
                          ],
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                          itemCount: _list.length,
                          itemBuilder: (context, i) {
                            final tx = _list[i];
                            final style = categoryStyle(tx.category);
                            return Card(
                              margin: const EdgeInsets.only(bottom: 8),
                              elevation: 0,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: style.color.withOpacity(0.2),
                                  child: Icon(style.icon, color: style.color, size: 22),
                                ),
                                title: Text(tx.merchant ?? tx.category, maxLines: 1, overflow: TextOverflow.ellipsis),
                                subtitle: Text(
                                  '${tx.occurredDate} · ${tx.category}',
                                  style: theme.textTheme.bodySmall,
                                ),
                                trailing: Text(
                                  '- ${_currencyFormat.format(tx.amount)}원',
                                  style: theme.textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w600,
                                    color: theme.colorScheme.error,
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
            ),
    );
  }

  Future<void> _showFilter(BuildContext context) async {
    final theme = Theme.of(context);
    final months = <String>[];
    final now = DateTime.now();
    for (var i = 0; i < 12; i++) {
      final d = DateTime(now.year, now.month - i, 1);
      months.add(DateFormat('yyyy-MM').format(d));
    }
    final categories = ['식비', '교통', '쇼핑', '문화', '의료', '교육', '통신', '기타'];
    await showModalBottomSheet(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModal) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('기간', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: months.map((m) {
                      final selected = _month == m;
                      return FilterChip(
                        label: Text(m),
                        selected: selected,
                        onSelected: (_) {
                          setState(() => _month = m);
                          setModal(() {});
                          _load();
                          Navigator.pop(ctx);
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  Text('카테고리', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilterChip(
                        label: const Text('전체'),
                        selected: _category == null,
                        onSelected: (_) {
                          setState(() => _category = null);
                          setModal(() {});
                          _load();
                          Navigator.pop(ctx);
                        },
                      ),
                      ...categories.map((c) {
                        final selected = _category == c;
                        return FilterChip(
                          label: Text(c),
                          selected: selected,
                          onSelected: (_) {
                            setState(() => _category = c);
                            setModal(() {});
                            _load();
                            Navigator.pop(ctx);
                          },
                        );
                      }),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
