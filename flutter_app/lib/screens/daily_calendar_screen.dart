/// 날짜별 지출 달력 + 선택 날짜 분석
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api/transactions_api.dart';
import '../config.dart';
import '../widgets/category_style.dart';
import 'transaction_list_screen.dart';

class DailyCalendarScreen extends StatefulWidget {
  const DailyCalendarScreen({
    super.key,
    this.userId = 'user1',
    this.baseUrl = kApiBaseUrl,
    this.initialMonth,
  });
  final String userId;
  final String baseUrl;
  final String? initialMonth;

  @override
  State<DailyCalendarScreen> createState() => _DailyCalendarScreenState();
}

class _DailyCalendarScreenState extends State<DailyCalendarScreen> {
  late DateTime _displayMonth;
  late DateTime _selectedDate;
  List<Transaction> _monthExpenseTransactions = [];
  Map<String, int> _dailyTotals = {};
  var _loading = true;
  String? _error;

  static final _currencyFormat = NumberFormat('#,###', 'ko_KR');
  static const _weekdayLabels = ['월', '화', '수', '목', '금', '토', '일'];

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    final month =
        _parseMonth(widget.initialMonth) ?? DateTime(now.year, now.month, 1);
    _displayMonth = DateTime(month.year, month.month, 1);
    if (month.year == now.year && month.month == now.month) {
      _selectedDate = DateTime(month.year, month.month, now.day);
    } else {
      _selectedDate = DateTime(month.year, month.month, 1);
    }
    _loadMonth();
  }

  DateTime? _parseMonth(String? raw) {
    if (raw == null || raw.length < 7) return null;
    final parts = raw.split('-');
    if (parts.length != 2) return null;
    final year = int.tryParse(parts[0]);
    final month = int.tryParse(parts[1]);
    if (year == null || month == null || month < 1 || month > 12) return null;
    return DateTime(year, month, 1);
  }

  String _ymd(DateTime date) => DateFormat('yyyy-MM-dd').format(date);

  Future<void> _loadMonth() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = TransactionsApi(baseUrl: widget.baseUrl);
      final from = DateTime(_displayMonth.year, _displayMonth.month, 1);
      final to = DateTime(_displayMonth.year, _displayMonth.month + 1, 0);
      final list = await api.getTransactions(
        userId: widget.userId,
        from: _ymd(from),
        to: _ymd(to),
      );
      final expenseList = list.where((tx) => tx.type == 'expense').toList();
      final totals = <String, int>{};
      for (var day = 1; day <= to.day; day++) {
        final key =
            _ymd(DateTime(_displayMonth.year, _displayMonth.month, day));
        totals[key] = 0;
      }
      for (final tx in expenseList) {
        totals.update(tx.occurredDate, (prev) => prev + tx.amount,
            ifAbsent: () => tx.amount);
      }
      setState(() {
        _monthExpenseTransactions = expenseList;
        _dailyTotals = totals;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _moveMonth(int delta) {
    final nextMonth =
        DateTime(_displayMonth.year, _displayMonth.month + delta, 1);
    final maxDay = DateTime(nextMonth.year, nextMonth.month + 1, 0).day;
    final nextSelectedDay =
        _selectedDate.day <= maxDay ? _selectedDate.day : maxDay;
    setState(() {
      _displayMonth = nextMonth;
      _selectedDate =
          DateTime(nextMonth.year, nextMonth.month, nextSelectedDay);
    });
    _loadMonth();
  }

  List<Transaction> _selectedTransactions() {
    final key = _ymd(_selectedDate);
    return _monthExpenseTransactions
        .where((tx) => tx.occurredDate == key)
        .toList();
  }

  Map<String, int> _selectedByCategory() {
    final byCategory = <String, int>{};
    for (final tx in _selectedTransactions()) {
      byCategory.update(tx.category, (prev) => prev + tx.amount,
          ifAbsent: () => tx.amount);
    }
    return byCategory;
  }

  int _selectedTotal() {
    var total = 0;
    for (final tx in _selectedTransactions()) {
      total += tx.amount;
    }
    return total;
  }

  String _formatDateLabel(DateTime date) {
    final weekday = _weekdayLabels[date.weekday - 1];
    return '${date.month}월 ${date.day}일 ($weekday)';
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final monthLabel = DateFormat('yyyy년 M월').format(_displayMonth);
    return Scaffold(
      appBar: AppBar(
        title: const Text('날짜별 지출'),
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
      ),
      body: RefreshIndicator(
        onRefresh: _loadMonth,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: Row(
                  children: [
                    IconButton(
                      onPressed: () => _moveMonth(-1),
                      icon: const Icon(Icons.chevron_left),
                    ),
                    Expanded(
                      child: Center(
                        child: Text(
                          monthLabel,
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () => _moveMonth(1),
                      icon: const Icon(Icons.chevron_right),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            _buildCalendar(theme),
            const SizedBox(height: 12),
            _buildAnalysis(theme),
            const SizedBox(height: 12),
            _buildSelectedTransactions(theme),
            if (_loading)
              const Padding(
                padding: EdgeInsets.only(top: 12),
                child: Center(child: CircularProgressIndicator()),
              ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Card(
                  color: theme.colorScheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      _error!,
                      style:
                          TextStyle(color: theme.colorScheme.onErrorContainer),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildCalendar(ThemeData theme) {
    final firstDay = DateTime(_displayMonth.year, _displayMonth.month, 1);
    final lastDay = DateTime(_displayMonth.year, _displayMonth.month + 1, 0);
    final leading = firstDay.weekday - 1;
    final total = leading + lastDay.day;
    final trailing = (7 - total % 7) % 7;
    final cellCount = total + trailing;

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 8, 8, 12),
        child: Column(
          children: [
            Row(
              children: _weekdayLabels.map((label) {
                return Expanded(
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Text(
                        label,
                        style: theme.textTheme.labelMedium
                            ?.copyWith(color: theme.colorScheme.outline),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: cellCount,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 7,
                // 저해상도/큰 글꼴에서도 날짜 셀 내부 텍스트가 잘리지 않도록 높이를 조금 더 확보
                childAspectRatio: 0.78,
              ),
              itemBuilder: (context, i) {
                if (i < leading || i >= leading + lastDay.day) {
                  return const SizedBox.shrink();
                }
                final day = i - leading + 1;
                final date =
                    DateTime(_displayMonth.year, _displayMonth.month, day);
                final key = _ymd(date);
                final amount = _dailyTotals[key] ?? 0;
                final selected = _sameDay(date, _selectedDate);
                final isToday = _sameDay(date, DateTime.now());
                return InkWell(
                  borderRadius: BorderRadius.circular(10),
                  onTap: () => setState(() => _selectedDate = date),
                  child: Container(
                    margin: const EdgeInsets.all(2),
                    padding:
                        const EdgeInsets.symmetric(horizontal: 2, vertical: 4),
                    decoration: BoxDecoration(
                      color: selected
                          ? theme.colorScheme.primaryContainer
                          : Colors.transparent,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: selected
                            ? theme.colorScheme.primary
                            : (isToday
                                ? theme.colorScheme.primary.withOpacity(0.4)
                                : theme.colorScheme.outlineVariant
                                    .withOpacity(0.6)),
                      ),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.max,
                      children: [
                        Text(
                          '$day',
                          style: theme.textTheme.bodySmall?.copyWith(
                            fontSize: 11,
                            height: 1.0,
                            fontWeight: FontWeight.w600,
                            color: selected
                                ? theme.colorScheme.onPrimaryContainer
                                : null,
                          ),
                        ),
                        const Spacer(),
                        FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            '${_currencyFormat.format(amount)}원',
                            style: theme.textTheme.labelSmall?.copyWith(
                              fontSize: 10,
                              height: 1.0,
                              color: amount == 0
                                  ? theme.colorScheme.outline
                                  : (selected
                                      ? theme.colorScheme.onPrimaryContainer
                                      : theme.colorScheme.onSurface),
                              fontWeight: amount == 0
                                  ? FontWeight.w400
                                  : FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalysis(ThemeData theme) {
    final byCategory = _selectedByCategory();
    final total = _selectedTotal();
    final sorted = byCategory.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          children: [
            ListTile(
              leading: CircleAvatar(
                backgroundColor: theme.colorScheme.secondaryContainer,
                child: Icon(Icons.insights,
                    color: theme.colorScheme.onSecondaryContainer),
              ),
              title: Text(
                '${_formatDateLabel(_selectedDate)} 분석',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              trailing: Text(
                '${_currencyFormat.format(total)}원',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            if (sorted.isEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                child: Text(
                  '등록된 지출이 없어 0원입니다.',
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(color: theme.colorScheme.outline),
                ),
              )
            else
              ...sorted.map((entry) {
                final style = categoryStyle(entry.key);
                final progress = total > 0 ? entry.value / total : 0.0;
                return ListTile(
                  leading: CircleAvatar(
                    radius: 20,
                    backgroundColor: style.color.withOpacity(0.2),
                    child: Icon(style.icon, color: style.color, size: 20),
                  ),
                  title: Text(entry.key),
                  subtitle: total > 0
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

  Widget _buildSelectedTransactions(ThemeData theme) {
    final list = _selectedTransactions();
    if (list.isEmpty) {
      return Card(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: const Padding(
          padding: EdgeInsets.all(20),
          child: Center(child: Text('이 날짜의 지출 내역이 없습니다.')),
        ),
      );
    }
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          ListTile(
            title: Text(
              '지출 내역',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            trailing: TextButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => TransactionListScreen(
                    userId: widget.userId,
                    baseUrl: widget.baseUrl,
                    fixedDate: _ymd(_selectedDate),
                  ),
                ),
              ),
              child: const Text('전체 보기'),
            ),
          ),
          ...list.map((tx) {
            final style = categoryStyle(tx.category);
            return ListTile(
              leading: CircleAvatar(
                backgroundColor: style.color.withOpacity(0.2),
                child: Icon(style.icon, color: style.color, size: 20),
              ),
              title: Text(tx.merchant ?? tx.subcategory),
              subtitle: Text('${tx.category}/${tx.subcategory}'),
              trailing: Text(
                '- ${_currencyFormat.format(tx.amount)}원',
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: theme.colorScheme.error,
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
