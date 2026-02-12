"""POST /chat 요청 스키마 (Step 8-3)"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /chat 요청"""

    user_id: str = Field(..., description="사용자 ID")
    message: str = Field(..., description="한 줄 입력 (자연어)")
    session_id: str | None = Field(None, description="세션 ID (선택)")
    idem_key: str | None = Field(None, description="중복 방지용 (선택)")
    llm_provider: str | None = Field(
        None,
        description="LLM 선택: ollama(로컬) | groq | gemini | grok. 없으면 서버 기본값(.env)",
    )
