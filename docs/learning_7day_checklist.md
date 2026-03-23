# 7일 이해도 부스팅 루틴 (하루 45분)

목표:
- 바이브코딩 속도를 유지하면서도, 코드 흐름을 스스로 설명 가능한 수준으로 올린다.
- 7일 후 `transactions` 생성/조회/예외 흐름을 코드 없이 말로 재현한다.

적용 범위:
- `backend/config/settings.py`
- `backend/config/urls.py`
- `backend/ledger/urls.py`
- `backend/ledger/views/transactions.py`
- `backend/ledger/serializers.py`
- `backend/ledger/services/transaction_command.py`
- `backend/ledger/services/transaction_query.py`
- `backend/core/exceptions.py`
- `backend/ledger/exceptions.py`
- `backend/tests/`

## 공통 규칙 (매일 동일)

- 시간 고정: `45분`만 한다.
- 순서 고정: `읽기 15분 -> 추적 15분 -> 작성/테스트 10분 -> 회고 5분`.
- 매일 결과물 2개를 남긴다.
1. `6줄 요약`  
2. `테스트 1개 또는 테스트 개선 1개`

`6줄 요약` 템플릿:
1. 입력은 어디서 들어오는가
2. 어떤 검증을 거치는가
3. 어떤 정규화/비즈니스 규칙이 적용되는가
4. 어디에 저장/조회되는가
5. 부수효과(캐시, 감사로그, 토큰)는 무엇인가
6. 실패 시 어떤 예외/응답으로 끝나는가

## Day 1: 요청 흐름 지도 만들기

집중 파일:
- `backend/config/urls.py`
- `backend/ledger/urls.py`
- `backend/ledger/views/transactions.py`

체크리스트:
- [ ] `POST /api/v1/transactions/`의 호출 경로를 파일/함수 단위로 적기
- [ ] `GET /api/v1/transactions/`의 호출 경로도 별도로 적기
- [ ] 인증/스로틀이 어디서 적용되는지 확인하기 (`permission_classes`, `throttle_scope`)
- [ ] 직접 6줄 요약 작성

산출물:
- `docs/change-reports/day1-flow-map.md` 파일 생성

## Day 2: Serializer와 입력 계약 이해

집중 파일:
- `backend/ledger/serializers.py`
- `backend/ledger/views/transactions.py`

체크리스트:
- [ ] `CreateTransactionSerializer`의 필수/선택 필드 분리 표 작성
- [ ] `TransactionListQuerySerializer`의 `from`, `to` 매핑 방식 설명
- [ ] 잘못된 입력 3개를 상상하고 예상 에러 응답 형태 적기
- [ ] 6줄 요약 작성

실습:
- [ ] `backend/tests/test_serializers.py`에 케이스 1개 추가

## Day 3: 생성 Command의 원자성 이해

집중 파일:
- `backend/ledger/services/transaction_command.py`
- `backend/ledger/services/idempotency.py`
- `backend/ledger/services/undo.py`
- `backend/ledger/services/audit.py`

체크리스트:
- [ ] `create_transaction()` 단계(멱등성 -> 정규화 -> 검증 -> DB -> 감사로그 -> undo)를 순서도로 작성
- [ ] `transaction.atomic()`이 필요한 이유를 본인 말로 3줄 정리
- [ ] `idem_key`가 있을 때/없을 때 반환값 차이 정리
- [ ] 6줄 요약 작성

실습:
- [ ] `backend/tests/test_services.py` 또는 `backend/tests/test_api_ledger.py`에 멱등성 관련 케이스 1개 추가

## Day 4: 조회/요약 Query 흐름 이해

집중 파일:
- `backend/ledger/services/transaction_query.py`
- `backend/ledger/views/summary.py`
- `backend/ledger/views/transactions.py`

체크리스트:
- [ ] 리스트 조회 필터(`from_date`, `to_date`, `category`) 동작 정리
- [ ] 요약 로직(`month` vs `from_date/to_date`) 분기 정리
- [ ] `by_category`, `total` 계산 과정을 SQL 관점으로 설명해보기
- [ ] 6줄 요약 작성

실습:
- [ ] `backend/tests/test_api_ledger.py`에 summary 경계값 테스트 1개 추가

## Day 5: 예외 체계 완전 이해

집중 파일:
- `backend/core/exceptions.py`
- `backend/ledger/exceptions.py`
- `backend/config/settings.py` (`EXCEPTION_HANDLER`)
- `backend/ledger/views/transactions.py`

체크리스트:
- [ ] `ApplicationError`와 DRF `APIException` 관계 정리
- [ ] `custom_exception_handler()`가 응답을 어떻게 표준화하는지 정리
- [ ] `TransactionValueError`가 발생하는 실제 코드 경로 추적
- [ ] 6줄 요약 작성

실습:
- [ ] 예외 응답 포맷을 검증하는 API 테스트 1개 추가

## Day 6: 인증/권한/스로틀 이해

집중 파일:
- `backend/config/settings.py`
- `backend/accounts/urls.py`
- `backend/accounts/views.py`
- `backend/ledger/permissions.py`
- `backend/tests/test_auth_permission.py`

체크리스트:
- [ ] JWT 인증이 적용되는 지점 정리 (`DEFAULT_AUTHENTICATION_CLASSES`)
- [ ] `IsOwner`가 지금 구조에서 실제로 보장하는 범위 설명
- [ ] 스로틀 레이트(`anon`, `user`, `transactions.create`) 정리
- [ ] 6줄 요약 작성

실습:
- [ ] 인증 실패/권한 분리 테스트 1개 보강

## Day 7: 통합 설명 + 미니 리팩터링

집중 파일:
- Day 1~6에서 다룬 파일 전체

체크리스트:
- [ ] `POST /api/v1/transactions/` 전체를 2분 내 구두 설명 (코드 미참조)
- [ ] 실패 시나리오 5개와 최종 응답 코드를 표로 정리
- [ ] 기술부채 3개를 선정하고 우선순위 매기기
- [ ] 6줄 요약 작성

실습:
- [ ] 가장 작은 리팩터링 1개 수행 (예: 중복 코드 정리, 변수명 개선, 테스트 이름 개선)
- [ ] 전체 테스트 실행: `cd backend && ./run_tests.sh -q`

## 매일 끝날 때 기록 포맷 (복붙용)

```md
## Day N 결과
- 오늘 본 파일:
- 이해한 흐름(6줄):
1.
2.
3.
4.
5.
6.
- 추가/수정한 테스트:
- 막힌 지점:
- 내일 확인할 질문 1개:
```

## AI 사용 규칙 (이해도 유지용)

- 코드 생성 요청 전에 먼저 아래 2개를 물어본다.
1. `이 코드의 실패 경로 3개`
2. `이 코드가 깨질 경계값 3개`

- 생성된 코드는 바로 붙이지 말고 다음 순서로 사용한다.
1. 내가 먼저 5줄로 구현 의도를 쓴다.
2. AI 코드와 diff를 비교한다.
3. 테스트를 먼저 추가하고 코드 반영한다.

- 하루에 최소 1번은 코드 없이 설명한다.
- 설명이 막히면 그 구간만 다시 읽고, 다시 2분 설명한다.
