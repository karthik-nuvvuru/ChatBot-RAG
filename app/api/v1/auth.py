"""Authentication API router."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    user_id: str
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """Create an access token for a user.

    This is a simplified auth endpoint for development/testing.
    In production, this would validate credentials against a user store.
    """
    if not request.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    token = create_access_token(
        data={
            "sub": request.user_id,
            "email": request.email,
            "roles": ["user"]
        }
    )

    return TokenResponse(access_token=token)