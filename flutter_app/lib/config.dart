/// API 서버 주소 (백엔드 uvicorn)
///
/// - 에뮬레이터: http://10.0.2.2:8001 (호스트 PC = 10.0.2.2)
/// - 실제 기기: PC와 같은 Wi-Fi에서 PC IP 확인 후 예) http://192.168.0.5:8001
///   (터미널에서 `ip addr` 또는 `hostname -I` 로 확인)
const String kApiBaseUrl = 'http://172.24.112.37:8001';
