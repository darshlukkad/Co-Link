"""
FastAPI Dependencies for Authentication

Provides reusable dependencies for protecting API endpoints.
"""

import logging
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose.exceptions import ExpiredSignatureError, JWTError

from .jwt_handler import get_jwt_handler
from .models import UserContext, TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserContext:
    """
    Dependency to get current authenticated user

    Validates JWT token and returns user context.
    Returns 401 if token is missing or invalid.

    Usage:
        @app.get("/protected")
        async def protected_route(user: UserContext = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        handler = get_jwt_handler()
        token_data = await handler.verify_token(token)
        user = UserContext.from_token_data(token_data)
        return user

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.exception(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserContext]:
    """
    Dependency to get current user (optional)

    Returns UserContext if valid token provided, None otherwise.
    Does not raise 401 if token is missing.

    Usage:
        @app.get("/public-or-private")
        async def route(user: Optional[UserContext] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.username}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None

    try:
        handler = get_jwt_handler()
        token_data = await handler.verify_token(credentials.credentials)
        user = UserContext.from_token_data(token_data)
        return user
    except (JWTError, ExpiredSignatureError) as e:
        logger.warning(f"Optional auth failed: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during optional authentication: {e}")
        return None


def require_role(required_role: str):
    """
    Dependency factory to require a specific role

    Usage:
        @app.post("/admin/action")
        async def admin_action(user: UserContext = Depends(require_role("admin"))):
            return {"action": "performed"}
    """

    async def role_checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user

    return role_checker


def require_any_role(required_roles: List[str]):
    """
    Dependency factory to require any of the specified roles

    Usage:
        @app.post("/moderation")
        async def moderate(user: UserContext = Depends(require_any_role(["admin", "moderator"]))):
            return {"action": "moderated"}
    """

    async def role_checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_any_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {required_roles} required",
            )
        return user

    return role_checker


def require_all_roles(required_roles: List[str]):
    """
    Dependency factory to require all of the specified roles

    Usage:
        @app.post("/super-admin")
        async def super_action(user: UserContext = Depends(require_all_roles(["admin", "super"]))):
            return {"action": "super performed"}
    """

    async def role_checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_all_roles(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All roles {required_roles} required",
            )
        return user

    return role_checker


# Convenience dependency for admin-only routes
require_admin = require_role("admin")


async def get_user_id(user: UserContext = Depends(get_current_user)) -> str:
    """
    Dependency to get current user ID only

    Usage:
        @app.get("/my-data")
        async def get_data(user_id: str = Depends(get_user_id)):
            return {"user_id": user_id}
    """
    return user.user_id


async def get_token_data(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenData:
    """
    Dependency to get raw token data (all JWT claims)

    Usage:
        @app.get("/token-info")
        async def token_info(token_data: TokenData = Depends(get_token_data)):
            return token_data
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        handler = get_jwt_handler()
        token_data = await handler.verify_token(credentials.credentials)
        return token_data

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
