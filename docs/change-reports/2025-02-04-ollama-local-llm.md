# 변경 보고서: Ollama 로컬 LLM 지원 (RTX 3060)

**일자**: 2025-02-04  
**요약**: API 대신 로컬 GPU(Ollama)로 LLM 호출할 수 있도록 `ollama` 프로바이더 추가.

---

## 1. 변경된 파일 목록

| 파일 | 변경 유형 |
|------|-----------|
| `backend/app/config.py` | 설정 추가 |
| `backend/app/llm_client.py` | 로직 추가 |
| `backend/.env.example` | 문서/예시 추가 |

---

## 2. 파일별 변경 내용

### 2.1 `backend/app/config.py`

**추가된 설정**

- `ollama_base_url: str = "http://localhost:11434/v1"` — Ollama 서버 주소
- `ollama_model: str = "llama3.2"` — 사용할 로컬 모델 이름

**수정된 주석**

- `# LLM - gemini(...)` → `# LLM - ollama(로컬 GPU) | gemini | groq | grok`
- Ollama 관련 한 줄 설명 추가

```python
# LLM - ollama(로컬 GPU) | gemini | groq | grok
llm_provider: str = "groq"
# Ollama: 로컬 GPU 사용, API 키 불필요 (https://ollama.com)
ollama_base_url: str = "http://localhost:11434/v1"
ollama_model: str = "llama3.2"
# ... 기존 gemini, groq, grok 설정 유지
```

---

### 2.2 `backend/app/llm_client.py`

**1) `_chat_openai_style` 함수**

- docstring: "Groq / Grok" → "Ollama / Groq / Grok(OpenAI 호환) 공통"
- API 키 검사: `ollama`일 때는 키 없어도 통과하도록 분기 추가
- `api_key`가 빈 문자열일 때 `"ollama"` 더미 사용

```python
# Ollama는 로컬이라 API 키 불필요 (빈 값이면 더미 사용)
if provider != "ollama" and not api_key:
    raise ValueError(...)
kwargs = {"api_key": api_key or "ollama"}
```

**2) `chat_completion` 함수**

- docstring에 `ollama` 명시
- 기본 provider 폴백: `"gemini"` → `"groq"` (기존과 동일하게 유지)
- `provider == "ollama"` 분기 추가: `_chat_openai_style("ollama", "", ollama_model, ollama_base_url, ...)` 호출
- 에러 메시지: `"gemini | groq | grok"` → `"ollama | gemini | groq | grok"`

```python
provider = (settings.llm_provider or "groq").strip().lower()
if provider == "ollama":
    return await _chat_openai_style(
        "ollama",
        "",
        settings.ollama_model,
        settings.ollama_base_url,
        messages,
        tools,
    )
# ... gemini, groq, grok 기존 분기 유지
raise ValueError(f"... ollama | gemini | groq | grok")
```

---

### 2.3 `backend/.env.example`

**추가된 내용**

- LLM 주석에 `ollama(로컬 GPU)` 포함
- Ollama 사용 방법 주석 블록 추가:
  - Ollama 설치 및 `ollama run llama3.2` 안내
  - `LLM_PROVIDER=ollama` 변경 안내
  - `OLLAMA_BASE_URL`, `OLLAMA_MODEL` 예시 (주석 처리)

```env
# LLM: ollama(로컬 GPU) | gemini | groq | grok
LLM_PROVIDER=groq

# Ollama - 로컬 RTX 3060 등 GPU 사용, API 키 불필요 (https://ollama.com)
# 1) Ollama 설치 후 터미널에서: ollama run llama3.2 (또는 phi3, mistral 등)
# 2) 아래 설정 후 LLM_PROVIDER=ollama 로 변경
# OLLAMA_BASE_URL=http://localhost:11434/v1
# OLLAMA_MODEL=llama3.2
```

---

## 3. 동작 요약

- `.env`에서 `LLM_PROVIDER=ollama`로 설정하면 `chat_completion()`이 `OLLAMA_BASE_URL`(기본 `http://localhost:11434/v1`)로 OpenAI 호환 API를 호출합니다.
- API 키는 사용하지 않으며, 로컬 Ollama 서버만 떠 있으면 됩니다.
- 기존 Gemini/Groq/Grok 사용 방식은 그대로 유지됩니다.

---

## 4. 사용자 측 조치

1. Ollama 설치 (https://ollama.com)
2. 터미널에서 `ollama run llama3.2` (또는 원하는 모델) 실행
3. `backend/.env`에 `LLM_PROVIDER=ollama`, 필요 시 `OLLAMA_BASE_URL`, `OLLAMA_MODEL` 설정
4. 백엔드 재시작
