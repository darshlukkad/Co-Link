"""
CoLink Common Authentication Module

Shared authentication utilities for all CoLink services.
Handles JWT verification, Keycloak integration, and user context.
"""

from .jwt_handler import (
    JWTHandler,
    get_jwt_handler,
    init_jwt_handler,
    verify_token,
    decode_token,
)
from .dependencies import (
    get_current_user,
    get_current_user_optional,
    require_role,
    require_admin,
    get_user_id,
)
from .models import UserContext, TokenData

__all__ = [
    "JWTHandler",
    "get_jwt_handler",
    "init_jwt_handler",
    "verify_token",
    "decode_token",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_admin",
    "get_user_id",
    "UserContext",
    "TokenData",
]
