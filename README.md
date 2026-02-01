# 가계부 에이전트 (Expense Tracker Agent)

> **핵심 원칙**: LLM은 "추출/판단"만, 서버는 "정규화/검증/저장"의 최종 책인자

---

## 1. 프로젝트 목표

### 사용자 경험
- **한 줄 입력** → 날짜/금액/항목/카테고리/지출·수입 자동 추출 → DB 즉시 반영 → 한 줄 확인 응답
- 애매하면 **딱 1개 질문**만으로 확인 후 기록

### 시스템 목표
| 목표 | 설명 |
|------|------|
| 정확성 | 날짜/금액/지출·수입 실수 최소화 |
| 중복 방지 | 네트워크 재시도에도 1건만 저장 (idempotency) |
| 되돌리기 | 자동 저장 후 "Undo" 지원 |
| 감사로그 | 저장/수정/삭제 기록 유지 |

---

## 2. 구현 단계 (Step-by-Step)

| 단계 | 내용 | 산출물 |
|------|------|--------|
| **Step 1** | 프로젝트 구조 & README | ✅ 이 문서 |
| **Step 2** | DB 스키마 (MVP 테이블) | ✅ `schema.sql` |
| **Step 3-1** | FastAPI 최소 골격 (requirements + main.py) | ✅ `backend/` |
| **Step 3-2** | 라우터 구조 (4개 엔드포인트 플레이스홀더) | ✅ `routers/` |
| **Step 3-3** | Config + Auth 플레이스홀더 | ✅ `config.py`, `auth.py` |
| **Step 4** | Idempotency 레이어 | `idempotency_keys` 구현 |
| **Step 5** | 트랜잭션 CRUD + 정규화 규칙 | `transactions` API |
| **Step 6** | Undo + Redis TTL | `POST /undo` |
| **Step 7** | 감사로그 | `audit_logs` 기록 |
| **Step 8** | LLM Orchestrator + Tool 호출 | `/chat` 엔드포인트 |
| **Step 9** | Flutter 앱 기본 UI | 채팅 입력 + 응답 표시 |

---

## 3. 아키텍처 개요

```
[Flutter App] → [REST API] → [Auth] → [Orchestrator] → [LLM]
                                    ↓
                              [Normalizer] → [Idempotency] → [Tool Executor]
                                    ↓                              ↓
                              [PostgreSQL] ←───────────────────────┘
                              [Redis - Undo TTL]
```

---

## 4. MVP API 엔드포인트

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/chat` | 자연어 입력 → 추출 → 저장 → 응답 |
| POST | `/transactions` | 명시적 폼 입력 |
| POST | `/undo` | 마지막 저장 취소 |
| GET | `/summary?month=YYYY-MM` | 월별 요약 |
| GET | `/transactions` | 리스트 조회 |

---

## 5. 설계 규칙 (서버 최종 책임)

- **날짜**: 연도 없으면 "가장 최근 해당 날짜" (오늘 2026-02-01 → "1/31" = 2026-01-31)
- **금액**: "2.3만", "23,000원" → KRW 정수
- **지출/수입**: "구매/결제" → expense, "입금/월급" → income, 애매하면 질문 1개
- **카테고리**: 초기 고정 세트 → 이후 사용자 규칙(merchant→category) 학습

---

*다음 단계: Step 4 - Idempotency 레이어*
