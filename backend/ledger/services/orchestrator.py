"""Orchestrator — Agentic LLM Logic"""

import json
from datetime import date

from ledger.services.llm_client import chat_completion
from ledger.services.transaction import TransactionService

# ── 도구 정의 ──

CREATE_TRANSACTION_TOOL = {
    "name": "create_transaction",
    "description": "가계부에 거래 내역을 저장합니다. 확실할 때만 호출하세요.",
    "parameters": {
        "type": "object",
        "properties": {
            "occurred_date": {
                "type": "string",
                "description": "YYYY-MM-DD. 없으면 오늘.",
            },
            "type": {"type": "string", "enum": ["expense", "income"]},
            "amount": {"type": "integer"},
            "category": {"type": "string"},
            "subcategory": {"type": "string"},
            "merchant": {"type": "string"},
            "memo": {"type": "string"},
        },
        "required": ["occurred_date", "type", "amount", "category", "subcategory"],
    },
}

SEARCH_TRANSACTIONS_TOOL = {
    "name": "search_transactions",
    "description": "거래 내역을 검색하여 ID를 찾습니다. 삭제하거나 수정하기 전에 반드시 먼저 검색하세요.",
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "가맹점, 카테고리, 메모 등 검색어",
            },
            "start_date": {"type": "string", "description": "YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "YYYY-MM-DD"},
            "min_amount": {"type": "integer"},
            "max_amount": {"type": "integer"},
        },
    },
}

DELETE_TRANSACTIONS_TOOL = {
    "name": "delete_transactions",
    "description": "ID 목록을 받아 거래를 영구 삭제합니다. search_transactions로 찾은 ID를 사용하세요.",
    "parameters": {
        "type": "object",
        "properties": {
            "tx_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "삭제할 거래의 tx_id 목록",
            },
        },
        "required": ["tx_ids"],
    },
}

TOOLS = [CREATE_TRANSACTION_TOOL, SEARCH_TRANSACTIONS_TOOL, DELETE_TRANSACTIONS_TOOL]


def _system_prompt() -> str:
    today = date.today().isoformat()
    return f"""당신은 유능한 가계부 AI 에이전트입니다.
오늘 날짜: {today}

**원칙**:
1. 사용자의 요청을 **검색(Search) → 판단 → 실행(Create/Delete)** 순서로 처리하세요.
2. **삭제 요청 시**: 무조건 `search_transactions`로 내역을 먼저 확인하고, **검색 결과가 있으면 즉시 `delete_transactions`로 ID를 넘겨 삭제하세요.** (다시 검색하지 마세요)
3. "오늘 내역 삭제해줘" -> 오늘 날짜로 `search` -> 검색된 **모든** ID로 `delete`.
4. "23000원 삭제" -> 금액으로 `search` -> 해당되는 것 `delete`.
5. 검색 결과가 없으면 사용자에게 없다고 알리세요.
6. **생성(Create)**: 명확하면 바로 생성하세요.

**중요**: 도구를 사용할 때는 반드시 Function Calling 형식을 사용하세요. 텍스트로 함수 이름을 쓰지 마세요.
"""


def _parse_text_tool_call(content: str) -> tuple[str, dict] | None:
    """텍스트에서 'tool_name(key=value)' 패턴 추출 (Fallback)."""
    import re
    import ast

    # 예: delete_transactions(tx_ids=['uuid1', 'uuid2'])
    # 함수 호출 패턴 찾기
    match = re.search(r"(\w+)\((.*)\)", content, re.DOTALL)
    if match:
        name = match.group(1)
        args_str = match.group(2)

        # ast.parse를 사용하여 안전하게 파싱
        try:
            # 가짜 함수 호출 코드로 만들어서 파싱
            tree = ast.parse(f"{name}({args_str})")
            call = tree.body[0].value

            args = {}
            if isinstance(call, ast.Call):
                for kw in call.keywords:
                    # keyword arguments (k=v)
                    try:
                        val = ast.literal_eval(kw.value)
                        # 만약 val이 문자열인데 리스트 형태라면 2차 파싱
                        if (
                            isinstance(val, str)
                            and val.strip().startswith("[")
                            and val.strip().endswith("]")
                        ):
                            try:
                                val = ast.literal_eval(val)
                            except:
                                # ast로 안 되면 단순 콤마 분리 (예: "[id1, id2]")
                                inner = val.strip()[1:-1]
                                val = [
                                    x.strip().strip("'\"")
                                    for x in inner.split(",")
                                    if x.strip()
                                ]
                        args[kw.arg] = val
                    except:
                        # kw.value 자체가 복잡한 Node(예: List of Names)여서 literal_eval 실패시
                        # List node라면 수동으로 추출 시도
                        if isinstance(kw.value, ast.List):
                            vals = []
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant):
                                    vals.append(elt.value)
                                elif isinstance(
                                    elt, ast.Name
                                ):  # 따옴표 없는 변수명 처리
                                    vals.append(elt.id)
                                elif isinstance(elt, ast.Str):  # Python < 3.8
                                    vals.append(elt.s)
                            args[kw.arg] = vals
                        # else:
                        #     pass  # 복잡한 표현식은 무시
        except:
            return None

        # 파라미터 매핑 보정 (Hallucination 대응)
        if name == "search_transactions":
            if "date" in args:
                d = args.pop("date")
                args["start_date"] = d
                args["end_date"] = d

        if name in ["create_transaction", "search_transactions", "delete_transactions"]:
            return name, args

    return None


def run_agent_loop(
    user_id: str, message: str, provider_override: str | None = None
) -> dict:
    """
    Multi-turn Agent Loop.
    Returns: { "reply": str, "tx_ids": list, "undo_tokens": list }
    """
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": message},
    ]

    # 실행 결과 추적
    created_txs = []  # {tx_id, undo_token}
    deleted_count = 0

    MAX_TURNS = 5
    for _ in range(MAX_TURNS):
        response = chat_completion(
            messages, tools=TOOLS, provider_override=provider_override
        )

        fc = response.get("function_call")
        content = response.get("content")

        # 0) Fallback: 텍스트에 함수 호출이 포함된 경우 파싱
        if not fc and content:
            parsed = _parse_text_tool_call(content)
            if parsed:
                fc = {"name": parsed[0], "args": parsed[1]}
                # 텍스트는 무시하고 도구 호출로 처리
                content = None

        # 1) 도구 호출 확인
        if fc:
            tool_name = fc["name"]
            args = fc.get("args", {})

            # 도구 실행
            tool_result = _execute_tool(user_id, tool_name, args, created_txs)

            # 결과 메시지에 추가
            messages.append(
                {"role": "assistant", "content": f"{tool_name}({args})"}
            )  # FC 대신 텍스트로 기록 (로컬 모델 친화적)
            messages.append(
                {
                    "role": "user",  # function role 대신 user role 사용 (로컬 모델 호환성)
                    "content": f"Tool Result ({tool_name}): {json.dumps(tool_result, ensure_ascii=False)}\n\n이제 위 결과의 tx_id들을 사용하여 delete_transactions를 호출하세요.",
                }
            )
            # 삭제 카운트 (결과 분석)
            if tool_name == "delete_transactions" and tool_result.get("success"):
                # "2건의 내역을 삭제했습니다" -> 2 추출하거나, 그냥 성공 여부만
                import re

                m = re.search(r"(\d+)건", tool_result["message"])
                if m:
                    deleted_count += int(m.group(1))

            continue  # 루프 계속 (LLM이 결과 보고 다음 행동 결정)

        # 2) 최종 응답 (텍스트)
        if content:
            return {
                "reply": content,
                "created_txs": created_txs,
                "deleted_count": deleted_count,
            }

        # 내용도 없고 도구도 없으면 종료
        break

    return {
        "reply": "처리 중 문제가 발생했습니다.",
        "created_txs": [],
        "deleted_count": 0,
    }


def _execute_tool(user_id: str, name: str, args: dict, created_txs_acc: list) -> dict:
    """실제 서비스 호출"""
    if name == "create_transaction":
        # TransactionService.create_transaction 호출
        # args에 user_id 주입 필요? 서비스 메서드는 user_id 별도 인자
        try:
            res = TransactionService.create_transaction(user_id, args)
            created_txs_acc.append(
                {"tx_id": res["tx_id"], "undo_token": res["undo_token"]}
            )
            return {"status": "success", "result": res}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif name == "search_transactions":
        # 인자 매핑
        return TransactionService.search_transactions(
            user_id=user_id,
            keyword=args.get("keyword"),
            start_date=args.get("start_date"),
            end_date=args.get("end_date"),
            min_amount=args.get("min_amount"),
            max_amount=args.get("max_amount"),
        )

    elif name == "delete_transactions":
        tx_ids = args.get("tx_ids", [])

        # Robustness: tx_ids가 문자열인 경우 리스트로 변환 시도
        if isinstance(tx_ids, str):
            import ast

            try:
                # 1차 시도: JSON/Python 리스트 파싱
                tx_ids = ast.literal_eval(tx_ids)
            except:
                # 2차 시도: 대괄호 제거 후 콤마 분리
                inner = tx_ids.strip()
                if inner.startswith("[") and inner.endswith("]"):
                    inner = inner[1:-1]
                tx_ids = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]

        return TransactionService.delete_transactions_by_ids(user_id, tx_ids)

    return {"status": "error", "message": "Unknown tool"}
