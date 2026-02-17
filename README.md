# Expense Tracker Agent

Django/DRF 백엔드와 Flutter 앱으로 구성된 가계부 시스템입니다.  
자연어 입력(`chat`)과 폼 입력(`transactions`)을 모두 지원하며, 실무에서 필요한 인증/멱등성/Undo/감사로그를 포함합니다.

## 핵심 기능

- JWT 기반 인증 (`register`, `login`, `refresh`)
- 거래 생성/조회/요약 API
- 자연어 입력 기반 거래 처리 (`/api/v1/chat/`)
- 멱등성 키(`idem_key`)로 중복 저장 방지
- Redis TTL 기반 Undo 토큰 지원
- 감사로그(`audit_logs`) 저장
- OpenAPI 스키마 및 Swagger/ReDoc 제공
- API 버저닝 (`/api/v1`, `/api/v2`)

## 기술 스택

- Backend: Django, Django REST Framework, SimpleJWT
- DB: PostgreSQL
- Cache: Redis
- LLM: Ollama / Gemini / Groq / Grok (선택)
- Frontend: Flutter
- Test: pytest, pytest-django

## 저장소 구조

```text
.
├── backend/          # Django API 서버
├── flutter_app/      # Flutter 클라이언트
├── docs/             # 다이어그램/문서 자산
├── schema.sql        # DB 스키마 참고
└── README.md
```

## 빠른 시작 (Backend)

### 1) 사전 준비

- Python 3.10+
- PostgreSQL
- Redis

### 2) 설치

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3) 환경변수 설정 (`backend/.env`)

필수/주요 항목:

| 변수 | 설명 | 예시 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | `postgresql://myuser:password@localhost:5432/expense_db` |
| `REDIS_URL` | Redis 연결 문자열 | `redis://localhost:6379/0` |
| `LLM_PROVIDER` | `ollama` \| `gemini` \| `groq` \| `grok` | `groq` |
| `GROQ_API_KEY` | `LLM_PROVIDER=groq`일 때 필요 | `...` |

선택 항목:

- `SECRET_KEY` (운영 환경에서는 반드시 설정)
- `DEBUG` (`True/False`, 기본값 `False`)
- `UNDO_TTL_SECONDS` (기본값 `300`)
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- `GEMINI_API_KEY`, `GEMINI_MODEL`
- `GROQ_MODEL`
- `GROK_API_KEY`, `GROK_MODEL`

참고: `DATABASE_URL`은 `postgresql+asyncpg://...` 형식도 내부에서 자동 변환해 사용합니다.

### 4) 마이그레이션 및 실행

```bash
cd backend
source venv/bin/activate
python manage.py migrate
./run.sh
```

기본 실행 주소: `http://localhost:8001`

### 5) 헬스체크

```bash
curl http://localhost:8001/health/
curl http://localhost:8001/health/db/
```

## API 개요

### 공개 엔드포인트 (인증 불필요)

- `GET /`
- `GET /health/`
- `GET /health/db/`
- `GET /api/schema/`
- `GET /api/schema/swagger-ui/`
- `GET /api/schema/redoc/`
- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/login/`
- `POST /api/v1/accounts/token/refresh/`

### 인증 필요 엔드포인트 (Bearer JWT)

- `POST /api/v1/chat/`
- `GET, POST /api/v1/transactions/`
- `POST /api/v1/undo/`
- `GET /api/v1/summary/`

버저닝:

- `v2`는 현재 `v1`과 동일 라우팅으로 동작 (`/api/v2/...`)

## API 사용 예시

### 1) 회원가입

```bash
curl -X POST http://localhost:8001/api/v1/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo12345!",
    "password2": "demo12345!"
  }'
```

### 2) 로그인 (access 토큰 발급)

```bash
curl -X POST http://localhost:8001/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo12345!"
  }'
```

### 3) 거래 생성

```bash
curl -X POST http://localhost:8001/api/v1/transactions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "occurred_date": "2026-02-13",
    "type": "expense",
    "amount": "12000",
    "category": "식비",
    "idem_key": "demo-001"
  }'
```

### 4) 자연어 거래 입력

```bash
curl -X POST http://localhost:8001/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "message": "오늘 점심 12000원 썼어",
    "llm_provider": "groq"
  }'
```

### 5) 월별 요약

```bash
curl "http://localhost:8001/api/v1/summary/?month=2026-02" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 테스트

```bash
cd backend
./run_tests.sh -v
```

주요 포인트:

- 테스트 설정은 `config.test_settings`(SQLite in-memory) 사용
- 인증/권한, API 버저닝, 스키마 엔드포인트, 서비스 계층 테스트 포함

## Flutter 앱 실행

```bash
cd flutter_app
flutter pub get
flutter run
```

실행 전 `flutter_app/lib/config.dart`의 `kApiBaseUrl`을 환경에 맞게 수정하세요.

- 로컬 PC에서 앱 실행: `http://localhost:8001/api/v1`
- Android 에뮬레이터: `http://10.0.2.2:8001/api/v1`
- 실기기: `http://<PC_IP>:8001/api/v1`

## 운영 체크리스트

- `DEBUG=False`
- 안전한 `SECRET_KEY` 설정
- `ALLOWED_HOSTS` 제한
- PostgreSQL/Redis 가용성 모니터링
- LLM API 키를 환경변수/시크릿 매니저로 관리

## 참고 문서

- `docs/folder_structure.png`
- `docs/data_flow.png`
- `docs/file_responsibilities.png`
