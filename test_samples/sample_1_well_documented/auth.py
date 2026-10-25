"""Authentication module — fully documented with Google-style docstrings."""

import hashlib
import secrets
from datetime import datetime, timedelta


class AuthenticationError(Exception):
    """Raised when an authentication attempt fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT or session token has expired."""
    pass


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a plaintext password using SHA-256 with a random salt.

    Args:
        password: The plaintext password to hash.
        salt: Optional salt string; generated if not provided.

    Returns:
        A tuple of (hashed_password, salt).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Args:
        password: The plaintext password to verify.
        hashed: The stored hash to compare against.
        salt: The salt used during hashing.

    Returns:
        True if the password matches, False otherwise.
    """
    computed, _ = hash_password(password, salt)
    return secrets.compare_digest(computed, hashed)


def generate_token(user_id: str, expires_in: int = 3600) -> dict:
    """Generate a simple bearer token for a user session.

    Args:
        user_id: Unique identifier of the authenticated user.
        expires_in: Token lifetime in seconds (default 3600).

    Returns:
        A dictionary with ``token``, ``user_id``, and ``expires_at`` keys.
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    return {
        "token": token,
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
    }


def validate_email(email: str) -> bool:
    """Perform a basic structural validation on an email address.

    Args:
        email: The email address string to validate.

    Returns:
        True if the email has a valid structure, False otherwise.
    """
    if not email or "@" not in email:
        return False
    local, domain = email.rsplit("@", 1)
    return len(local) > 0 and "." in domain and len(domain) > 2
