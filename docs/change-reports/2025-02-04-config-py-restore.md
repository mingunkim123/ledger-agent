# 변경 보고서: config.py 복원/정리

**일자**: 2025-02-04  
**요약**: `backend/app/config.py`를 새로 작성하여 환경 설정을 한 곳에서 관리하도록 복원·정리함.

---

## 1. 변경된 파일

| 파일 | 변경 유형 |
|------|-----------|
| `backend/app/config.py` | 신규 작성(복원) |

---

## 2. config.py 내용

- **역할**: `.env` 및 환경변수 로드, `Settings` 단일 인스턴스 제공.
- **구성**:
  - `pydantic_settings.BaseSettings` 사용, `backend/.env` 경로 고정.
  - 앱 공통: `app_name`, `debug`
  - DB: `database_url`
  - JWT: `jwt_secret`, `jwt_algorithm`
  - Redis: `redis_url`, `undo_ttl_seconds`
  - LLM: `llm_provider`, Ollama/Gemini/Groq/Grok 관련 필드
- **LLM 관련 필드**: `llm_provider`, `ollama_base_url`, `ollama_model`, `gemini_*`, `groq_*`, `grok_*` 모두 포함하여 `llm_client.py` 및 기타 모듈에서 그대로 사용 가능.

---

## 3. 변경 포인트 요약

- 기존 Step 주석(Step 3-3, Step 4, Step 6 등) 제거 후 역할만 주석으로 명시.
- 설정을 DB / JWT / Redis / LLM 블록으로 나누어 가독성 정리.
- Ollama 설정 유지: `ollama_base_url`, `ollama_model` 기본값 동일.
- `model_config`로 `env_file` 경로·인코딩 지정 유지.

---

## 4. 사용처 (변경 없음)

- `app.main` — `settings` 참조
- `app.database` — `settings.database_url`, `settings.debug`
- `app.redis_client` — `settings.redis_url`
- `app.llm_client` — `settings.llm_provider`, `settings.ollama_*`, `settings.gemini_*`, `settings.groq_*`, `settings.grok_*`
- `app.services.undo` — `settings.undo_ttl_seconds`

위 모듈들은 수정 없이 기존처럼 `from app.config import settings`로 사용 가능.
