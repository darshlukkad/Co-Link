"""
Authentication data models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """JWT token claims"""

    sub: str  # Subject (user ID from Keycloak)
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email_verified: bool = False
    realm_roles: List[str] = Field(default_factory=list)
    resource_access: dict = Field(default_factory=dict)
    azp: Optional[str] = None  # Authorized party (client_id)
    scope: Optional[str] = None
    exp: Optional[int] = None  # Expiration timestamp
    iat: Optional[int] = None  # Issued at timestamp
    jti: Optional[str] = None  # JWT ID


class UserContext(BaseModel):
    """User context extracted from JWT"""

    user_id: str  # Keycloak user ID (sub claim)
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    is_admin: bool = False
    email_verified: bool = False
    token_jti: Optional[str] = None

    @classmethod
    def from_token_data(cls, token_data: TokenData) -> "UserContext":
        """Create UserContext from TokenData"""
        roles = token_data.realm_roles or []

        return cls(
            user_id=token_data.sub,
            username=token_data.preferred_username or token_data.email or "unknown",
            email=token_data.email,
            display_name=token_data.name or token_data.preferred_username,
            roles=roles,
            is_admin="admin" in roles,
            email_verified=token_data.email_verified,
            token_jti=token_data.jti,
        )

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if user has all of the specified roles"""
        return all(role in self.roles for role in roles)


class KeycloakPublicKey(BaseModel):
    """Keycloak public key for JWT verification"""

    kid: str  # Key ID
    kty: str  # Key type (RSA)
    alg: str  # Algorithm (RS256)
    use: str  # Usage (sig)
    n: str  # Modulus
    e: str  # Exponent
