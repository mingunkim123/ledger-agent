/// 홈 대시보드 - 이번 달 총 지출, 카테고리별, 최근 내역
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api/transactions_api.dart';
import '../config.dart';
import '../widgets/category_style.dart';
import 'transaction_list_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    this.userId = 'user1',
    this.baseUrl = kApiBaseUrl,
  });
  final String userId;
  final String baseUrl;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Summary? _summary;
  List<Transaction> _recent = [];
  String _month = '';
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
      final summary = await api.getSummary(userId: widget.userId, month: _month);
      final now = DateTime.now();
      final isCurrentMonth = _month == DateFormat('yyyy-MM').format(now);
      final endDay = isCurrentMonth ? now.day : DateTime(int.parse(_month.substring(0, 4)), int.parse(_month.substring(5, 7)) + 1, 0).day;
      final to = '$_month-${endDay.toString().padLeft(2, '0')}';
      final list = await api.getTransactions(userId: widget.userId, from: '$_month-01', to: to);
      setState(() {
        _summary = summary;
        _recent = list.take(10).toList();
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
                          Text(_error!, style: TextStyle(color: theme.colorScheme.onErrorContainer)),
                          const SizedBox(height: 12),
                          Text(
                            'PC와 같은 Wi‑Fi인지, lib/config.dart 주소가 PC IP인지 확인하세요.',
                            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onErrorContainer.withOpacity(0.9)),
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
                child: _buildMonthCard(theme),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Text('카테고리별', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
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
                    Text('최근 내역', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                    TextButton(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => TransactionListScreen(userId: widget.userId, baseUrl: widget.baseUrl),
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
                      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: style.color.withOpacity(0.2),
                          child: Icon(style.icon, color: style.color, size: 22),
                        ),
                        title: Text(tx.merchant ?? tx.category, maxLines: 1, overflow: TextOverflow.ellipsis),
                        subtitle: Text(tx.occurredDate, style: theme.textTheme.bodySmall),
                        trailing: Text(
                          '${_currencyFormat.format(tx.amount)}원',
                          style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
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

  Widget _buildMonthCard(ThemeData theme) {
    final total = _summary?.total ?? 0;
    final monthLabel = _month.length >= 7 ? '${_month.substring(0, 4)}년 ${_month.substring(5)}월' : _month;
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
          Text(monthLabel, style: theme.textTheme.titleMedium?.copyWith(color: theme.colorScheme.onPrimaryContainer.withOpacity(0.9))),
          const SizedBox(height: 8),
          Text(
            '${_currencyFormat.format(total)}원',
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(height: 4),
          Text('이번 달 지출', style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onPrimaryContainer.withOpacity(0.8))),
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
          child: Center(child: Text('이번 달 카테고리별 지출이 없습니다.')),
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
              subtitle: total > 0 ? LinearProgressIndicator(value: pct, backgroundColor: theme.colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(4)) : null,
              trailing: Text('${_currencyFormat.format(e.value)}원', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            );
          }).toList(),
        ),
      ),
    );
  }
}
