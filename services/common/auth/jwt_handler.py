"""
JWT Token Handler with Keycloak Integration

Handles JWT verification using Keycloak's public keys (JWKS).
Supports caching of public keys and automatic key rotation.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from jose import jwt, JWTError, jwk
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from .models import TokenData, KeycloakPublicKey

logger = logging.getLogger(__name__)


class JWTHandler:
    """
    Handles JWT verification with Keycloak

    Features:
    - Fetches and caches Keycloak public keys (JWKS)
    - Verifies JWT signatures using RS256
    - Validates token expiration and claims
    - Automatic key rotation support
    """

    def __init__(
        self,
        keycloak_url: str,
        realm: str,
        client_id: Optional[str] = None,
        cache_ttl: int = 3600,  # Cache keys for 1 hour
    ):
        self.keycloak_url = keycloak_url.rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.cache_ttl = cache_ttl

        # Cache for public keys
        self._keys_cache: Optional[Dict[str, Any]] = None
        self._keys_cache_time: Optional[datetime] = None

        # JWKS endpoint
        self.jwks_url = (
            f"{self.keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
        )
        self.issuer = f"{self.keycloak_url}/realms/{realm}"

    async def get_public_keys(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch Keycloak public keys (JWKS)

        Args:
            force_refresh: Force refresh even if cached

        Returns:
            Dictionary of public keys keyed by kid (key ID)
        """
        # Check cache
        if not force_refresh and self._keys_cache and self._keys_cache_time:
            age = datetime.utcnow() - self._keys_cache_time
            if age < timedelta(seconds=self.cache_ttl):
                logger.debug("Using cached public keys")
                return self._keys_cache

        # Fetch fresh keys
        logger.info(f"Fetching public keys from Keycloak: {self.jwks_url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()

            # Build key dictionary
            keys = {}
            for key_data in jwks.get("keys", []):
                kid = key_data.get("kid")
                if kid:
                    keys[kid] = key_data

            # Update cache
            self._keys_cache = keys
            self._keys_cache_time = datetime.utcnow()

            logger.info(f"Cached {len(keys)} public keys")
            return keys

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch public keys from Keycloak: {e}")
            # Return cached keys if available, even if expired
            if self._keys_cache:
                logger.warning("Using expired cached keys due to fetch failure")
                return self._keys_cache
            raise

    async def verify_token(
        self,
        token: str,
        verify_exp: bool = True,
        verify_aud: bool = False,
    ) -> TokenData:
        """
        Verify JWT token and extract claims

        Args:
            token: JWT token string
            verify_exp: Verify token expiration
            verify_aud: Verify audience claim

        Returns:
            TokenData with verified claims

        Raises:
            JWTError: If token is invalid
            ExpiredSignatureError: If token is expired
        """
        try:
            # Decode header to get kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise JWTError("Token missing 'kid' in header")

            # Get public key
            keys = await self.get_public_keys()
            key_data = keys.get(kid)

            if not key_data:
                # Try refreshing keys (maybe key rotation occurred)
                logger.info(f"Key {kid} not found in cache, refreshing...")
                keys = await self.get_public_keys(force_refresh=True)
                key_data = keys.get(kid)

                if not key_data:
                    raise JWTError(f"Public key not found for kid: {kid}")

            # Verify and decode token
            options = {
                "verify_signature": True,
                "verify_exp": verify_exp,
                "verify_aud": verify_aud,
                "verify_iss": True,
            }

            payload = jwt.decode(
                token,
                key_data,
                algorithms=["RS256"],
                issuer=self.issuer,
                options=options,
                audience=self.client_id if verify_aud and self.client_id else None,
            )

            # Extract token data
            token_data = TokenData(
                sub=payload.get("sub"),
                email=payload.get("email"),
                preferred_username=payload.get("preferred_username"),
                name=payload.get("name"),
                given_name=payload.get("given_name"),
                family_name=payload.get("family_name"),
                email_verified=payload.get("email_verified", False),
                realm_roles=payload.get("realm_access", {}).get("roles", []),
                resource_access=payload.get("resource_access", {}),
                azp=payload.get("azp"),
                scope=payload.get("scope"),
                exp=payload.get("exp"),
                iat=payload.get("iat"),
                jti=payload.get("jti"),
            )

            logger.debug(
                f"Token verified for user: {token_data.preferred_username} ({token_data.sub})"
            )
            return token_data

        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise

    async def decode_token_unverified(self, token: str) -> Dict[str, Any]:
        """
        Decode token without verification (use only for debugging)

        Args:
            token: JWT token string

        Returns:
            Token payload as dictionary
        """
        return jwt.get_unverified_claims(token)


# Singleton instance
_jwt_handler: Optional[JWTHandler] = None


def init_jwt_handler(
    keycloak_url: str,
    realm: str,
    client_id: Optional[str] = None,
) -> JWTHandler:
    """
    Initialize global JWT handler instance

    Args:
        keycloak_url: Keycloak base URL
        realm: Keycloak realm name
        client_id: Client ID for audience verification

    Returns:
        JWTHandler instance
    """
    global _jwt_handler
    _jwt_handler = JWTHandler(
        keycloak_url=keycloak_url,
        realm=realm,
        client_id=client_id,
    )
    return _jwt_handler


def get_jwt_handler() -> JWTHandler:
    """
    Get global JWT handler instance

    Returns:
        JWTHandler instance

    Raises:
        RuntimeError: If handler not initialized
    """
    if _jwt_handler is None:
        raise RuntimeError(
            "JWT handler not initialized. Call init_jwt_handler() first."
        )
    return _jwt_handler


# Convenience functions
async def verify_token(token: str) -> TokenData:
    """Verify token using global handler"""
    handler = get_jwt_handler()
    return await handler.verify_token(token)


async def decode_token(token: str) -> Dict[str, Any]:
    """Decode token without verification (debug only)"""
    handler = get_jwt_handler()
    return await handler.decode_token_unverified(token)
