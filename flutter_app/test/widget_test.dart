import 'package:flutter_test/flutter_test.dart';
import 'package:expense_tracker_app/main.dart';

void main() {
  testWidgets('앱이 정상적으로 실행되는지 확인', (WidgetTester tester) async {
    await tester.pumpWidget(const ExpenseTrackerApp());

    // 홈 탭이 보이는지 확인
    expect(find.text('홈'), findsOneWidget);
    expect(find.text('내역'), findsOneWidget);
    expect(find.text('추가'), findsOneWidget);
  });
}
