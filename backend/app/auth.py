"""Auth/JWT 플레이스홀더 (Step 3-3) - Step 4 이후 구현"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer(auto_error=False)


async def get_current_user_id():
    """
    JWT에서 user_id 추출.
    현재: 플레이스홀더. Step 4에서 구현 예정.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 필요 (Step 4에서 구현)",
    )
