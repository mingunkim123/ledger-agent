# 변경 보고서: 앱에서 로컬/클라우드 모델 선택

**일자**: 2025-02-04  
**요약**: 채팅 요청 시 **로컬 모델(Ollama)**과 **클라우드 모델(서버 기본값)** 중 사용자가 선택할 수 있도록 백엔드·Flutter 앱을 수정함.

---

## 1. 변경된 파일

| 파일 | 변경 유형 |
|------|-----------|
| `backend/app/schemas/chat.py` | 필드 추가 |
| `backend/app/llm_client.py` | 인자 추가 |
| `backend/app/services/orchestrator.py` | 인자 추가 |
| `backend/app/routers/chat.py` | 인자 전달 |
| `flutter_app/lib/api/chat_api.dart` | 파라미터 추가 |
| `flutter_app/lib/screens/chat_screen.dart` | UI 추가 |

---

## 2. 백엔드 변경

### 2.1 `backend/app/schemas/chat.py`

- **추가**: `llm_provider: str | None = None`
  - 설명: `ollama`(로컬) | `groq` | `gemini` | `grok`. 없으면 서버 기본값(.env) 사용.

### 2.2 `backend/app/llm_client.py`

- **`chat_completion`**  
  - 인자 추가: `provider_override: str | None = None`  
  - 동작: `provider_override`가 있으면 해당 프로바이더 사용, 없으면 `settings.llm_provider` 사용.

### 2.3 `backend/app/services/orchestrator.py`

- **`extract_transaction`**  
  - 인자 추가: `provider_override: str | None = None`  
  - `chat_completion(..., provider_override=provider_override)` 로 전달.

### 2.4 `backend/app/routers/chat.py`

- **POST /chat**  
  - `extract_transaction(..., provider_override=body.llm_provider)` 로 요청 body의 `llm_provider` 전달.

---

## 3. Flutter 앱 변경

### 3.1 `flutter_app/lib/api/chat_api.dart`

- **`sendMessage`**  
  - 인자 추가: `String? llmProvider`  
  - body에 `llm_provider`가 있으면 JSON에 포함해 전송.

### 3.2 `flutter_app/lib/screens/chat_screen.dart`

- **상태**: `_useLocalModel` (bool, 기본 false)  
  - `true` → 로컬(Ollama), `false` → 클라우드(서버 기본값).
- **UI**: 입력 영역 위에 **SegmentedButton** 추가  
  - "클라우드" / "로컬 (Ollama)" 선택.
- **전송 시**: `llmProvider: _useLocalModel ? 'ollama' : null` 로 API 호출.

---

## 4. 사용 방법

- **앱**: 채팅 화면 상단에서 "클라우드" 또는 "로컬 (Ollama)" 선택 후 메시지 전송.
- **클라우드**: `llm_provider`를 보내지 않음 → 서버 `.env`의 `LLM_PROVIDER`(예: groq) 사용.
- **로컬**: `llm_provider: "ollama"` 전송 → 해당 요청만 Ollama 사용.

---

## 5. 참고

- 서버 기본 클라우드 프로바이더는 `.env`의 `LLM_PROVIDER`로 설정 (groq / gemini / grok).
- 앱에서는 "로컬" vs "클라우드" 두 가지만 선택 가능. 클라우드 세부(groq/gemini/grok)는 서버 기본값에 따름.
