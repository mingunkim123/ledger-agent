"""Orchestrator — Tool 스키마 + LLM 추출 로직 (동기 전용)"""

from datetime import date

from ledger.services.llm_client import chat_completion

# create_transaction 도구 스키마 (Gemini function declaration)
CREATE_TRANSACTION_TOOL = {
    "name": "create_transaction",
    "description": "가계부에 거래 내역을 저장합니다. 사용자가 지출/수입을 입력하면 날짜, 금액, 항목, 카테고리, 세부 카테고리, 지출/수입 유형을 추출하여 호출합니다. 확실할 때만 호출하고, 애매하면 호출하지 말고 질문 1개만 하세요.",
    "parameters": {
        "type": "object",
        "properties": {
            "occurred_date": {
                "type": "string",
                "description": "거래 발생일. YYYY-MM-DD 형식. 없으면 오늘.",
            },
            "type": {
                "type": "string",
                "enum": ["expense", "income"],
                "description": "지출(expense) 또는 수입(income). 구매/결제/먹음→expense, 입금/월급/환급→income.",
            },
            "amount": {
                "type": "integer",
                "description": "금액 (원). 23000, 2.3만→23000.",
            },
            "category": {
                "type": "string",
                "description": "상위 카테고리. 식비/교통/쇼핑/문화/의료/교육/통신/기타 중 하나.",
            },
            "subcategory": {
                "type": "string",
                "description": "세부 카테고리. 예: 카페, 식사, 택시, 생필품, 영화, 약국, 학원, 통신요금. 애매하면 기타.",
            },
            "merchant": {
                "type": "string",
                "description": "가맹점/항목 (선택). 예: BHC, 스타벅스.",
            },
            "memo": {
                "type": "string",
                "description": "메모 (선택).",
            },
        },
        "required": ["occurred_date", "type", "amount", "category", "subcategory"],
    },
}


def _system_prompt_with_date() -> str:
    """오늘 날짜를 포함한 시스템 프롬프트."""
    today = date.today().isoformat()
    return f"""당신은 가계부 기록 도우미입니다.
사용자가 한 줄로 지출/수입을 입력하면, create_transaction 도구를 호출하여 저장합니다.

**오늘 날짜: {today}** (날짜를 안 말하면 반드시 이 날짜 사용)

규칙:
1. 날짜 없으면 반드시 {today} 사용
2. 금액: "2.3만"→23000, "23,000원"→23000
3. 지출/수입: 구매/결제/먹음→expense, 입금/월급/환급→income
4. 카테고리와 세부 카테고리는 사용자가 명시하지 않아도 문맥으로 반드시 추론
5. 애매하면 도구 호출 금지. 질문 1개만 하세요.
6. 확실할 때만 create_transaction 호출
"""


def extract_transaction_sync(
    user_id: str,
    message: str,
    provider_override: str | None = None,
) -> dict:
    """
    자연어 메시지에서 거래 정보 추출 (동기).

    LLM 클라이언트가 이제 동기 전용이므로, 불안정한 asyncio 래퍼가 불필요합니다.
    """
    messages = [
        {"role": "system", "content": _system_prompt_with_date()},
        {"role": "user", "content": message.strip() or "입력 없음"},
    ]
    result = chat_completion(
        messages,
        tools=[CREATE_TRANSACTION_TOOL],
        provider_override=provider_override,
    )

    if result.get("function_call"):
        fc = result["function_call"]
        if fc["name"] == "create_transaction":
            args = fc.get("args", {})
            args["user_id"] = user_id
            args["source_text"] = message
            return {"action": "create", "args": args}

    reply = result.get("content") or "다시 한 번 입력해주세요."
    return {"action": "clarify", "reply": reply}
