from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_hours: Optional[int] = None) -> str:
    """Create a JWT token with an expiry time.

    Args:
        data: Payload to encode (e.g. {"sub": "admin", "role": "admin"})
        expires_hours: Override default expiry. Defaults to JWT_EXPIRE_HOURS.

    Returns:
        Encoded JWT string.
    """
    hours = expires_hours if expires_hours is not None else JWT_EXPIRE_HOURS
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=hours)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token.

    Returns:
        Payload dict if valid, None if expired or invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
