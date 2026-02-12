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
    this.fixedDate,
  });
  final String userId;
  final String baseUrl;
  final String? fixedDate;

  @override
  State<TransactionListScreen> createState() => _TransactionListScreenState();
}

class _TransactionListScreenState extends State<TransactionListScreen> {
  List<Transaction> _list = [];
  Map<String, int> _byCategory = {};
  int _expenseTotal = 0;
  String _month = '';
  String? _category;
  var _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _month = widget.fixedDate != null && widget.fixedDate!.length >= 7
        ? widget.fixedDate!.substring(0, 7)
        : DateFormat('yyyy-MM').format(DateTime.now());
    _load();
  }

  bool get _isFixedDateMode =>
      widget.fixedDate != null && widget.fixedDate!.isNotEmpty;

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = TransactionsApi(baseUrl: widget.baseUrl);
      String from;
      String to;
      if (_isFixedDateMode) {
        from = widget.fixedDate!;
        to = widget.fixedDate!;
      } else {
        final year = int.parse(_month.substring(0, 4));
        final m = int.parse(_month.substring(5, 7));
        final lastDay = DateTime(year, m + 1, 0).day;
        from = '$_month-01';
        to = '$_month-${lastDay.toString().padLeft(2, '0')}';
      }
      final list = await api.getTransactions(
        userId: widget.userId,
        from: from,
        to: to,
        category: _isFixedDateMode ? null : _category,
      );
      final expenseList = list.where((tx) => tx.type == 'expense').toList();
      final byCategory = <String, int>{};
      var total = 0;
      for (final tx in expenseList) {
        total += tx.amount;
        byCategory.update(tx.category, (prev) => prev + tx.amount,
            ifAbsent: () => tx.amount);
      }
      setState(() {
        _list = expenseList;
        _byCategory = byCategory;
        _expenseTotal = total;
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
    final title = _isFixedDateMode
        ? '${_formatDateLabel(widget.fixedDate!)} 지출'
        : '지출 내역';
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
        actions: _isFixedDateMode
            ? null
            : [
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
                                Text(_error!,
                                    style: TextStyle(
                                        color: theme
                                            .colorScheme.onErrorContainer)),
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
                                  Icon(Icons.receipt_long,
                                      size: 64,
                                      color: theme.colorScheme.outline),
                                  const SizedBox(height: 16),
                                  Text('이 기간 지출 내역이 없습니다.',
                                      style: theme.textTheme.bodyLarge
                                          ?.copyWith(
                                              color:
                                                  theme.colorScheme.outline)),
                                ],
                              ),
                            ),
                          ],
                        )
                      : ListView(
                          padding: const EdgeInsets.symmetric(
                              vertical: 8, horizontal: 16),
                          children: [
                            if (_isFixedDateMode)
                              _buildCategorySummaryCard(theme),
                            ..._list.map((tx) {
                              final style = categoryStyle(tx.category);
                              return Card(
                                margin: const EdgeInsets.only(bottom: 8),
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12)),
                                child: ListTile(
                                  leading: CircleAvatar(
                                    backgroundColor:
                                        style.color.withOpacity(0.2),
                                    child: Icon(style.icon,
                                        color: style.color, size: 22),
                                  ),
                                  title: Text(tx.merchant ?? tx.subcategory,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis),
                                  subtitle: Text(
                                    _isFixedDateMode
                                        ? '${tx.category} · ${tx.subcategory}'
                                        : '${tx.occurredDate} · ${tx.category}/${tx.subcategory}',
                                    style: theme.textTheme.bodySmall,
                                  ),
                                  trailing: Text(
                                    '- ${_currencyFormat.format(tx.amount)}원',
                                    style:
                                        theme.textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.w600,
                                      color: theme.colorScheme.error,
                                    ),
                                  ),
                                ),
                              );
                            }),
                          ],
                        ),
            ),
    );
  }

  Widget _buildCategorySummaryCard(ThemeData theme) {
    if (_byCategory.isEmpty) {
      return const SizedBox.shrink();
    }
    final entries = _byCategory.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          children: [
            ListTile(
              title: Text(
                '카테고리별 합계',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              trailing: Text(
                '${_currencyFormat.format(_expenseTotal)}원',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            ...entries.map((entry) {
              final style = categoryStyle(entry.key);
              final progress =
                  _expenseTotal > 0 ? entry.value / _expenseTotal : 0.0;
              return ListTile(
                leading: CircleAvatar(
                  radius: 20,
                  backgroundColor: style.color.withOpacity(0.2),
                  child: Icon(style.icon, color: style.color, size: 20),
                ),
                title: Text(entry.key),
                subtitle: _expenseTotal > 0
                    ? LinearProgressIndicator(
                        value: progress,
                        backgroundColor:
                            theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(4),
                      )
                    : null,
                trailing: Text(
                  '${_currencyFormat.format(entry.value)}원',
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  String _formatDateLabel(String ymd) {
    final dt = DateTime.tryParse(ymd);
    if (dt == null) return ymd;
    const weekdays = ['월', '화', '수', '목', '금', '토', '일'];
    return '${dt.month}월 ${dt.day}일 (${weekdays[dt.weekday - 1]})';
  }

  Future<void> _showFilter(BuildContext context) async {
    final theme = Theme.of(context);
    final months = <String>[];
    final now = DateTime.now();
    for (var i = 0; i < 12; i++) {
      final d = DateTime(now.year, now.month - i, 1);
      months.add(DateFormat('yyyy-MM').format(d));
    }
    final categories = [
      '식비',
      '카페',
      '교통',
      '쇼핑',
      '생활',
      '문화',
      '여행',
      '의료',
      '교육',
      '통신',
      '구독',
      '기타',
    ];
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
                  Text('기간',
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w600)),
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
                  Text('카테고리',
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w600)),
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
