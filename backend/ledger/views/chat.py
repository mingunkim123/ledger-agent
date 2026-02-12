"""POST /chat — 자연어 → LLM 추출 → 저장 (Thin View)"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ledger.exceptions import LLMBadRequestError, LLMQuotaExceededError, LLMAuthError
from ledger.serializers import ChatRequestSerializer
from ledger.services.orchestrator import extract_transaction_sync
from ledger.services.simple_parser import parse_simple_expense
from ledger.services.transaction import TransactionService


class ChatView(APIView):
    """POST /chat — 자연어 입력 → 거래 생성 또는 질문 응답"""

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = data["user_id"]
        message = data["message"]
        idem_key = data.get("idem_key")
        llm_provider = data.get("llm_provider")

        # ── 1) LLM 추출 ──
        result = self._extract_with_fallback(user_id, message, llm_provider)
        if isinstance(result, Response):
            return result  # 에러 응답

        # ── 2) 질문(clarify) 응답 ──
        if result["action"] == "clarify":
            return Response(
                {
                    "reply": result["reply"],
                    "tx_id": None,
                    "undo_token": None,
                    "needs_clarification": True,
                }
            )

        # ── 3) 거래 생성 ──
        args = result["args"]
        args.setdefault("source_text", message)

        try:
            tx_result = TransactionService.create_transaction(
                user_id=args.get("user_id") or user_id,
                args=args,
                idem_key=idem_key,
            )
        except ValueError as e:
            return Response(
                {
                    "reply": f"입력 형식을 확인해주세요. ({e})",
                    "tx_id": None,
                    "undo_token": None,
                    "needs_clarification": True,
                }
            )

        if tx_result.get("cached"):
            return Response(
                {
                    "reply": "이미 기록된 내역이에요.",
                    "tx_id": tx_result["tx_id"],
                    "undo_token": None,
                    "needs_clarification": False,
                }
            )

        # 한 줄 확인 응답
        tx = tx_result
        type_label = "지출" if tx["type"] == "expense" else "수입"
        reply = (
            f"{tx['occurred_date']} {tx['category']}/{tx['subcategory']} "
            f"{type_label} {tx['amount']:,}원 기록했어요."
        )

        return Response(
            {
                "reply": reply,
                "tx_id": tx["tx_id"],
                "undo_token": tx["undo_token"],
                "needs_clarification": False,
            }
        )

    # ── Private ──

    def _extract_with_fallback(self, user_id, message, llm_provider):
        """LLM 추출 시도, 실패 시 에러 응답 또는 simple_parser 폴백."""
        try:
            return extract_transaction_sync(
                user_id,
                message,
                provider_override=llm_provider,
            )
        except (LLMBadRequestError, LLMAuthError, LLMQuotaExceededError):
            raise  # DRF Exception Handler가 처리
        except Exception as e:
            err_str = str(e).lower()
            code = getattr(e, "code", None) or getattr(e, "status_code", None)

            if code == 400 or "400" in str(e) or "bad request" in err_str:
                raise LLMBadRequestError()
            if (
                code == 429
                or "429" in str(e)
                or "rate" in err_str
                or "quota" in err_str
            ):
                fallback = parse_simple_expense(message)
                if fallback:
                    fallback["user_id"] = user_id
                    fallback["source_text"] = message
                    return {"action": "create", "args": fallback}
                raise LLMQuotaExceededError()
            if (
                code == 403
                or "403" in str(e)
                or "permission" in err_str
                or "auth" in err_str
            ):
                raise LLMAuthError()

            msg = getattr(e, "message", None) or str(e)
            return Response(
                {"detail": f"LLM 오류: {msg}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
