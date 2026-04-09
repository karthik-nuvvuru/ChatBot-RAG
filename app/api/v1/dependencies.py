"""API dependencies for authentication and common operations."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import validate_token
from app.core.rate_limiter import check_rate_limit

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate JWT token and return current user.

    Args:
        token: JWT token from Authorization header

    Returns:
        User dict with 'sub' (user_id) and other claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return validate_token(token)


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    """Optional user extraction - returns None if no valid token.

    Args:
        token: Optional JWT token

    Returns:
        User dict or None
    """
    if not token:
        return None

    try:
        return validate_token(token)
    except HTTPException:
        return None


async def require_active_user(
    user: dict = Depends(get_current_user)
) -> dict:
    """Require an active (non-expired) user.

    Args:
        user: User from get_current_user

    Returns:
        User dict

    Raises:
        HTTPException: If user is expired or invalid
    """
    return user


def require_role(required_role: str):
    """Dependency factory for role-based access control.

    Args:
        required_role: Role that the user must have

    Returns:
        Dependency function
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        roles = user.get("roles", [])
        if required_role not in roles and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user

    return role_checker


async def rate_limit_dependency(user: dict = Depends(get_current_user)) -> None:
    """Check rate limit for user.

    Args:
        user: Current user

    Raises:
        HTTPException: If rate limit exceeded
    """
    await check_rate_limit(user["sub"])