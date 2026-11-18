"""Passwords, tokens and one-time codes."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.clock import utc_now
from app.core.config import get_settings
from app.core.constants import JWT_ALGORITHM, REFRESH_TOKEN_BYTES

_hasher = PasswordHash.recommended()  # Argon2id

# Used when the email is unknown, so a failed login takes the same time either way.
_DUMMY_HASH = _hasher.hash("timing-equaliser")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    return _hasher.verify(password, password_hash or _DUMMY_HASH)


# --- Access tokens (JWT, short-lived) -------------------------------------------------------------


class TokenError(Exception):
    """Access token is missing, malformed or signed with another key."""


class TokenExpiredError(TokenError):
    """Access token was valid but has expired: the app should use its refresh token."""


@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    session_id: int


def _secret() -> str:
    secret = get_settings().jwt_secret.get_secret_value()
    if not secret:
        raise RuntimeError("JWT_SECRET is not configured")
    return secret


def create_access_token(user_id: int, session_id: int) -> tuple[str, datetime]:
    issued = utc_now()
    expires = issued + timedelta(minutes=get_settings().access_token_ttl_minutes)
    payload = {"sub": str(user_id), "sid": session_id, "typ": "access", "iat": issued, "exp": expires}
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM), expires


def decode_access_token(token: str) -> AccessClaims:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM], options={"require": ["exp", "sub", "sid"]})
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError from exc
    if payload.get("typ") != "access":
        raise TokenError
    return AccessClaims(user_id=int(payload["sub"]), session_id=int(payload["sid"]))


# --- Refresh tokens and one-time codes (random, stored only as hashes) ----------------------------


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """SHA-256 is right here: refresh tokens are long random values, not guessable passwords."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_numeric_code(length: int) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))
