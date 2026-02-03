# 가계부 에이전트 - Flutter 앱 (Step 9)

## 사전 준비

1. Flutter SDK 설치
2. 백엔드 서버 실행: `cd backend && uvicorn app.main:app --reload --port 8000`

## 실행

```bash
cd flutter_app
flutter pub get
# android/ios 폴더가 없으면: flutter create . --project-name expense_tracker_app
flutter run
```

- **웹**: `flutter run -d chrome`
- **Android 에뮬레이터**: `localhost` 대신 `http://10.0.2.2:8000` 사용 (main.dart 또는 ChatScreen baseUrl 수정)

## 기능

- 한 줄 입력창 + 전송 버튼
- 사용자 메시지 / 봇 응답 표시
- POST /chat 호출 → reply 표시
