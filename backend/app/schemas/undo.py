"""POST /undo 요청 스키마 (Step 6-3)"""
from pydantic import BaseModel, Field


class UndoRequest(BaseModel):
    """POST /undo 요청"""

    undo_token: str = Field(..., description="POST /transactions 응답의 undo_token")
