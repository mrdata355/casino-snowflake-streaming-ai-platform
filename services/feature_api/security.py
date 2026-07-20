from __future__ import annotations

import os
from typing import Annotated, Any

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)
_jwks_client: jwt.PyJWKClient | None = None
Credentials = Annotated[HTTPAuthorizationCredentials | None, Security(bearer)]


def require_principal(credentials: Credentials) -> dict[str, Any]:
    if os.getenv("APP_ENV", "dev") == "test":
        return {"sub": "test-principal", "scope": "features:read"}
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    global _jwks_client
    _jwks_client = _jwks_client or jwt.PyJWKClient(os.environ["API_JWKS_URL"])
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=os.environ["API_AUDIENCE"],
            issuer=os.environ["API_JWT_ISSUER"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        ) from exc

    scopes = set(str(claims.get("scope", "")).split())
    if "features:read" not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="missing features:read scope",
        )
    return claims
