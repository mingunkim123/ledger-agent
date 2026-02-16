"""POST /chat — 자연어 → LLM 추출 → 저장 (Thin View)"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ledger.serializers import ChatRequestSerializer


class ChatView(APIView):
    """POST /chat — 자연어 입력 → 거래 생성 또는 질문 응답"""

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = str(request.user.id)  # ← JWT 토큰에서 추출
        message = data["message"]
        idem_key = data.get("idem_key")
        llm_provider = data.get("llm_provider")

        # ── 1) Agent Logic ──
        try:
            result = self._run_agent(user_id, message, llm_provider)
        except Exception as e:
            # 에러 로깅은 생략하고 502 리턴 (실무에선 로깅 필수)
            return Response(
                {"detail": f"Agent 오류: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ── 2) Response 구성 ──
        # Agent가 최종적으로 생성한 거래 중 첫 번째 것의 undo_token만 반환 (UI 제약)
        # 여러 개 생성되어도 일단 하나만 취소 가능하게 하거나, UI 스펙에 따라 다름.
        # 여기서는 가장 마지막 생성된 건의 토큰을 반환.

        created_txs = result.get("created_txs", [])
        tx_id = None
        undo_token = None

        if created_txs:
            last_tx = created_txs[-1]
            tx_id = last_tx["tx_id"]
            undo_token = last_tx["undo_token"]

        return Response(
            {
                "reply": result["reply"],
                "tx_id": tx_id,
                "undo_token": undo_token,
                "needs_clarification": False,  # Agent가 알아서 질문함
            }
        )

    # ── Private ──

    def _run_agent(self, user_id, message, llm_provider):
        from ledger.services.orchestrator import run_agent_loop

        return run_agent_loop(user_id, message, provider_override=llm_provider)
