"""커스텀 예외 — DRF Exception Handler가 일관된 JSON 응답으로 변환"""

from rest_framework.exceptions import APIException


class LLMBadRequestError(APIException):
    """LLM API 400 Bad Request"""

    status_code = 502
    default_detail = "LLM 요청 형식 오류예요. .env에서 모델명과 API 키를 확인해 주세요."
    default_code = "llm_bad_request"


class LLMQuotaExceededError(APIException):
    """LLM API 429 Rate Limit"""

    status_code = 429
    default_detail = "무료 할당량을 초과했어요. 1분 뒤에 다시 시도해 주세요."
    default_code = "llm_quota_exceeded"


class LLMAuthError(APIException):
    """LLM API 403 Authentication"""

    status_code = 502
    default_detail = "API 키를 확인해 주세요. (Gemini: aistudio.google.com, Groq: console.groq.com, Grok: x.ai)"
    default_code = "llm_auth_error"


class UndoTokenExpiredError(APIException):
    """Undo 토큰 만료 또는 유효하지 않음"""

    status_code = 400
    default_detail = (
        "undo_token이 만료됐거나 잘못됐습니다. 5분 이내에 다시 시도해주세요."
    )
    default_code = "undo_token_expired"


class TransactionNotFoundError(APIException):
    """거래 내역을 찾을 수 없음"""

    status_code = 404
    default_detail = "해당 트랜잭션을 찾을 수 없습니다."
    default_code = "transaction_not_found"
