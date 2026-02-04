# 변경 보고서: 로컬 모델 품질 개선 (날짜 주입 + system/user 분리)

**일자**: 2025-02-04  
**요약**: 로컬 LLM이 오늘 날짜를 모르고 저장을 잘 못하던 문제를 줄이기 위해, 시스템 프롬프트에 **오늘 날짜를 명시**하고 **system / user 메시지를 분리**했습니다.

---

## 1. 변경된 파일

| 파일 | 변경 유형 |
|------|-----------|
| `backend/app/services/orchestrator.py` | 수정 |

---

## 2. 변경 내용

### 2.1 문제

- 로컬 모델(Ollama 등)은 **현재 날짜를 알 수 없음** → "날짜 없으면 오늘"이라고만 하면 잘못된 날짜를 넣거나 생략함.
- 시스템 지시와 사용자 입력이 **한 덩어리 user 메시지**로 전달되어, 작은 모델이 역할을 구분하기 어려움.

### 2.2 조치

**1) 오늘 날짜 주입**

- `datetime.date.today().isoformat()`으로 `YYYY-MM-DD`를 구해, 시스템 프롬프트에 **"오늘 날짜: YYYY-MM-DD"**를 명시.
- "날짜 없으면 반드시 이 날짜 사용"이라고 규칙을 구체화.

**2) system / user 분리**

- **이전**: `[{"role": "user", "content": SYSTEM_PROMPT + "\n\n사용자 입력: " + message}]`
- **이후**:  
  - `{"role": "system", "content": _system_prompt_with_date()}`  
  - `{"role": "user", "content": message.strip() or "입력 없음"}`  
- LLM이 지시(system)와 사용자 입력(user)을 구분해 처리하기 쉬워짐.

**3) 코드 변경 요약**

- `SYSTEM_PROMPT` 상수 → `_system_prompt_with_date()` 함수로 변경 (매 요청마다 오늘 날짜 반영).
- `extract_transaction`에서 `messages`를 system + user 두 메시지로 구성.

---

## 3. 기대 효과

- **날짜**: 서버가 알려주는 오늘 날짜를 그대로 쓰도록 유도 → 잘못된/빈 날짜 감소.
- **저장 품질**: system으로 역할이 분리되어, 도구 호출(create_transaction) 조건을 더 잘 따를 가능성 증가.

---

## 4. 추가 권장 (품질이 여전히 부족할 때)

- **Groq 사용**: `.env`에서 `LLM_PROVIDER=groq`로 바꾸고 `GROQ_API_KEY` 설정 시, 70B급 모델로 더 안정적인 추출 가능 (무료 한도 내).
- **로컬 모델 교체**: Ollama에서 더 큰/양자화 모델 시험 (예: `mistral`, `llama3.2:3b` 대신 7B 등, RTX 3060 12GB 한도 내).
