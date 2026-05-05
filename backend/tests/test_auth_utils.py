import pytest
import time
from datetime import datetime


class TestHashPassword:
    """Tests for password hashing."""

    def test_hash_is_string(self):
        from services.auth import hash_password
        result = hash_password("secret123")
        assert isinstance(result, str)

    def test_hash_is_not_plaintext(self):
        from services.auth import hash_password
        result = hash_password("secret123")
        assert result != "secret123"

    def test_hash_is_bcrypt_format(self):
        from services.auth import hash_password
        result = hash_password("secret123")
        assert result.startswith("$2b$")

    def test_different_passwords_different_hashes(self):
        from services.auth import hash_password
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_same_password_different_hashes(self):
        """Bcrypt generates unique salts — same password = different hash."""
        from services.auth import hash_password
        h1 = hash_password("same_pass")
        h2 = hash_password("same_pass")
        assert h1 != h2


class TestVerifyPassword:
    """Tests for password verification."""

    def test_correct_password_verifies(self):
        from services.auth import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_wrong_password_fails(self):
        from services.auth import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password(self):
        from services.auth import hash_password, verify_password
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_password_with_special_chars(self):
        from services.auth import hash_password, verify_password
        pw = "p@$$w0rd!#%^&*()"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_password_with_unicode(self):
        from services.auth import hash_password, verify_password
        pw = "møter_æøå_密码"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True


class TestCreateToken:
    """Tests for JWT token creation."""

    def test_token_is_string(self):
        from services.auth import create_token
        token = create_token({"sub": "admin", "role": "admin"})
        assert isinstance(token, str)

    def test_token_has_three_parts(self):
        """JWT format: header.payload.signature"""
        from services.auth import create_token
        token = create_token({"sub": "admin", "role": "admin"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_custom_expiry(self):
        from services.auth import create_token, decode_token
        token = create_token({"sub": "test"}, expires_hours=1)
        payload = decode_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_token_contains_payload(self):
        from services.auth import create_token, decode_token
        token = create_token({"sub": "admin", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"


class TestDecodeToken:
    """Tests for JWT token decoding."""

    def test_valid_token_decodes(self):
        from services.auth import create_token, decode_token
        token = create_token({"sub": "admin", "role": "admin"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "admin"

    def test_expired_token_returns_none(self):
        from services.auth import create_token, decode_token
        token = create_token({"sub": "test"}, expires_hours=0)
        # Small sleep to ensure token is expired
        time.sleep(1)
        payload = decode_token(token)
        # Token with 0 hours expiry — may or may not be expired yet
        # Use negative hours to force expiry
        # Actually, let's create with -1 hours (already expired)
        from jose import jwt as jose_jwt
        from datetime import timedelta
        from config import JWT_SECRET, JWT_ALGORITHM
        data = {"sub": "test", "exp": datetime.utcnow() - timedelta(hours=1)}
        expired_token = jose_jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)
        assert decode_token(expired_token) is None

    def test_invalid_token_returns_none(self):
        from services.auth import decode_token
        assert decode_token("invalid.token.string") is None

    def test_tampered_token_returns_none(self):
        from services.auth import create_token, decode_token
        token = create_token({"sub": "admin", "role": "admin"})
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_empty_token_returns_none(self):
        from services.auth import decode_token
        assert decode_token("") is None

    def test_token_with_extra_data(self):
        from services.auth import create_token, decode_token
        data = {"sub": "admin", "role": "admin", "department": "HR"}
        token = create_token(data)
        payload = decode_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"
        assert payload["department"] == "HR"
