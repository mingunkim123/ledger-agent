/// 홈 대시보드 - 기간별 총 지출, 카테고리별, 최근 내역
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import 'package:provider/provider.dart';

import '../api/transactions_api.dart';
import '../config.dart';
import '../services/auth_service.dart';
import '../widgets/category_style.dart';
import 'daily_calendar_screen.dart';
import 'transaction_list_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    this.baseUrl = kApiBaseUrl,
  });
  final String baseUrl;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Summary? _summary;
  List<Transaction> _recent = [];

  // ── 기간 모드 ──
  // true: 월(month) 기준,  false: 커스텀 기간(from~to)
  bool _isMonthMode = true;
  String _month = '';
  DateTimeRange? _customRange;

  var _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _month = DateFormat('yyyy-MM').format(DateTime.now());
    _load();
  }

  // ── 현재 기간의 from / to 날짜 계산 ──
  String get _fromDate {
    if (!_isMonthMode && _customRange != null) {
      return DateFormat('yyyy-MM-dd').format(_customRange!.start);
    }
    return '$_month-01';
  }

  String get _toDate {
    if (!_isMonthMode && _customRange != null) {
      return DateFormat('yyyy-MM-dd').format(_customRange!.end);
    }
    final now = DateTime.now();
    final isCurrentMonth = _month == DateFormat('yyyy-MM').format(now);
    final endDay = isCurrentMonth
        ? now.day
        : DateTime(int.parse(_month.substring(0, 4)),
                int.parse(_month.substring(5, 7)) + 1, 0)
            .day;
    return '$_month-${endDay.toString().padLeft(2, '0')}';
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = TransactionsApi(baseUrl: widget.baseUrl);

      final token = context.read<AuthService>().token;
      if (token == null) return;

      // ── 요약 조회 ──
      final Summary summary;
      if (_isMonthMode) {
        summary = await api.getSummary(token: token, month: _month);
      } else {
        summary = await api.getSummary(
          token: token,
          fromDate: _fromDate,
          toDate: _toDate,
        );
      }

      // ── 거래 내역 조회 ──
      final list = await api.getTransactions(
        token: token,
        from: _fromDate,
        to: _toDate,
      );
      final expenseList = list.where((tx) => tx.type == 'expense').toList();

      setState(() {
        _summary = summary;
        _recent = expenseList.take(10).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  // ── 월 이동 ──
  void _changeMonth(int delta) {
    final year = int.parse(_month.substring(0, 4));
    final m = int.parse(_month.substring(5, 7));
    final d = DateTime(year, m + delta, 1);
    setState(() {
      _month = DateFormat('yyyy-MM').format(d);
      _isMonthMode = true;
      _customRange = null;
    });
    _load();
  }

  // ── 커스텀 기간 선택 ──
  Future<void> _pickDateRange() async {
    final now = DateTime.now();
    final initial = _customRange ??
        DateTimeRange(
          start: DateTime(now.year, now.month, 1),
          end: now,
        );
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(now.year + 1, 12, 31),
      initialDateRange: initial,
      locale: const Locale('ko', 'KR'),
      helpText: '기간 선택',
      saveText: '적용',
      cancelText: '취소',
    );
    if (picked != null) {
      setState(() {
        _customRange = picked;
        _isMonthMode = false;
      });
      _load();
    }
  }

  // ── 월 모드로 복귀 ──
  void _resetToMonth() {
    setState(() {
      _isMonthMode = true;
      _customRange = null;
      _month = DateFormat('yyyy-MM').format(DateTime.now());
    });
    _load();
  }

  static final _currencyFormat = NumberFormat('#,###', 'ko_KR');
  static final _dateDisplayFmt = DateFormat('M월 d일');

  String get _periodLabel {
    if (!_isMonthMode && _customRange != null) {
      return '${_dateDisplayFmt.format(_customRange!.start)} ~ ${_dateDisplayFmt.format(_customRange!.end)}';
    }
    return _month.length >= 7
        ? '${_month.substring(0, 4)}년 ${_month.substring(5)}월'
        : _month;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (_loading && _summary == null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('가계부'),
          centerTitle: true,
          elevation: 0,
          scrolledUnderElevation: 2,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      appBar: AppBar(
        title: const Text('가계부'),
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
        backgroundColor: theme.colorScheme.surface,
        foregroundColor: theme.colorScheme.onSurface,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: '로그아웃',
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('로그아웃'),
                  content: const Text('정말 로그아웃 하시겠습니까?'),
                  actions: [
                    TextButton(
                      child: const Text('취소'),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                    TextButton(
                      child: const Text('로그아웃'),
                      onPressed: () {
                        Navigator.pop(ctx);
                        context.read<AuthService>().logout();
                      },
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: CustomScrollView(
          slivers: [
            if (_error != null)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Card(
                    color: theme.colorScheme.errorContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(_error!,
                              style: TextStyle(
                                  color: theme.colorScheme.onErrorContainer)),
                          const SizedBox(height: 12),
                          Text(
                            'PC와 같은 Wi‑Fi인지, lib/config.dart 주소가 PC IP인지 확인하세요.',
                            style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onErrorContainer
                                    .withOpacity(0.9)),
                          ),
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
                ),
              ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: _buildPeriodCard(theme),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('날짜별 지출',
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w600)),
                    TextButton(
                      onPressed: _openDailyCalendar,
                      child: const Text('달력 보기'),
                    ),
                  ],
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                child: _buildDailyCalendarEntry(theme),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Text('카테고리별',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                child: _buildCategoryList(theme),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('최근 내역',
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w600)),
                    TextButton(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) =>
                              TransactionListScreen(baseUrl: widget.baseUrl),
                        ),
                      ),
                      child: const Text('전체보기'),
                    ),
                  ],
                ),
              ),
            ),
            if (_recent.isEmpty)
              const SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(child: Text('최근 지출 내역이 없습니다.')),
                ),
              )
            else
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, i) {
                    final tx = _recent[i];
                    final style = categoryStyle(tx.category);
                    return Card(
                      margin: const EdgeInsets.symmetric(
                          horizontal: 20, vertical: 4),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: style.color.withOpacity(0.2),
                          child: Icon(style.icon, color: style.color, size: 22),
                        ),
                        title: Text(tx.merchant ?? tx.category,
                            maxLines: 1, overflow: TextOverflow.ellipsis),
                        subtitle: Text(
                          '${tx.occurredDate} · ${tx.category}/${tx.subcategory}',
                          style: theme.textTheme.bodySmall,
                        ),
                        trailing: Text(
                          '${_currencyFormat.format(tx.amount)}원',
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                      ),
                    );
                  },
                  childCount: _recent.length,
                ),
              ),
            const SliverToBoxAdapter(child: SizedBox(height: 24)),
          ],
        ),
      ),
    );
  }

  /// ── 기간 표시 카드 (월 / 커스텀) ──
  Widget _buildPeriodCard(ThemeData theme) {
    final total = _summary?.total ?? 0;
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            theme.colorScheme.primaryContainer,
            theme.colorScheme.primaryContainer.withOpacity(0.8),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: theme.colorScheme.shadow.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 기간 라벨 + 이동/선택 버튼 ──
          Row(
            children: [
              // 월 모드일 때 좌우 이동
              if (_isMonthMode) ...[
                InkWell(
                  onTap: () => _changeMonth(-1),
                  borderRadius: BorderRadius.circular(20),
                  child: Padding(
                    padding: const EdgeInsets.all(4),
                    child: Icon(Icons.chevron_left,
                        size: 22, color: theme.colorScheme.onPrimaryContainer),
                  ),
                ),
              ],
              Expanded(
                child: Text(
                  _periodLabel,
                  style: theme.textTheme.titleMedium?.copyWith(
                    color:
                        theme.colorScheme.onPrimaryContainer.withOpacity(0.9),
                  ),
                  textAlign: _isMonthMode ? TextAlign.center : TextAlign.left,
                ),
              ),
              if (_isMonthMode) ...[
                InkWell(
                  onTap: () => _changeMonth(1),
                  borderRadius: BorderRadius.circular(20),
                  child: Padding(
                    padding: const EdgeInsets.all(4),
                    child: Icon(Icons.chevron_right,
                        size: 22, color: theme.colorScheme.onPrimaryContainer),
                  ),
                ),
              ],
              const SizedBox(width: 4),
              // 기간 선택 버튼
              InkWell(
                onTap: _pickDateRange,
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color:
                        theme.colorScheme.onPrimaryContainer.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.date_range,
                          size: 16,
                          color: theme.colorScheme.onPrimaryContainer),
                      const SizedBox(width: 4),
                      Text(
                        '기간 선택',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onPrimaryContainer,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          // 커스텀 모드일 때 "이번 달로 돌아가기" 버튼
          if (!_isMonthMode) ...[
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerRight,
              child: InkWell(
                onTap: _resetToMonth,
                borderRadius: BorderRadius.circular(12),
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  child: Text(
                    '이번 달로 돌아가기',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color:
                          theme.colorScheme.onPrimaryContainer.withOpacity(0.7),
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            '${_currencyFormat.format(total)}원',
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(height: 4),
          Text(_isMonthMode ? '이번 달 지출' : '선택 기간 지출',
              style: theme.textTheme.bodySmall?.copyWith(
                  color:
                      theme.colorScheme.onPrimaryContainer.withOpacity(0.8))),
        ],
      ),
    );
  }

  Widget _buildCategoryList(ThemeData theme) {
    final byCat = _summary?.byCategory ?? {};
    if (byCat.isEmpty) {
      return Card(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: const Padding(
          padding: EdgeInsets.all(24),
          child: Center(child: Text('이 기간 카테고리별 지출이 없습니다.')),
        ),
      );
    }
    final total = _summary!.total;
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          children: byCat.entries.map((e) {
            final style = categoryStyle(e.key);
            final pct = total > 0 ? (e.value / total) : 0.0;
            return ListTile(
              leading: CircleAvatar(
                radius: 20,
                backgroundColor: style.color.withOpacity(0.2),
                child: Icon(style.icon, color: style.color, size: 20),
              ),
              title: Text(e.key),
              subtitle: total > 0
                  ? LinearProgressIndicator(
                      value: pct,
                      backgroundColor:
                          theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(4))
                  : null,
              trailing: Text('${_currencyFormat.format(e.value)}원',
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600)),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildDailyCalendarEntry(ThemeData theme) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        onTap: _openDailyCalendar,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          radius: 20,
          backgroundColor: theme.colorScheme.secondaryContainer,
          child: Icon(Icons.calendar_month,
              size: 20, color: theme.colorScheme.onSecondaryContainer),
        ),
        title: Text('달력에서 날짜 선택',
            style: theme.textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.w600)),
        subtitle: Text(
          '특정 날짜를 누르면 카테고리 분석이 보이고, 등록 안 된 날짜는 0원으로 표시됩니다.',
          style: theme.textTheme.bodySmall,
        ),
        trailing: Icon(Icons.chevron_right, color: theme.colorScheme.outline),
      ),
    );
  }

  void _openDailyCalendar() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DailyCalendarScreen(
          baseUrl: widget.baseUrl,
          initialMonth: _month,
        ),
      ),
    );
  }
}
