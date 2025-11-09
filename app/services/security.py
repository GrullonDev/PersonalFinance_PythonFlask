from __future__ import annotations

from passlib.context import CryptContext


_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a PBKDF2-SHA256 hash for the provided password."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against its encoded hash."""
    return _pwd_context.verify(password, password_hash)
