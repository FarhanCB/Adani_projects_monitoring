from app.core.security import (
    create_access_token,
    get_password_hash,
    validate_url_safe,
    verify_password,
)
from jose import jwt
from app.core.config import settings


def test_password_hashing():
    pw = "SuperSecret@123"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation():
    token = create_access_token({"sub": "admin@adani.com", "role": "ADMIN"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "admin@adani.com"
    assert payload["role"] == "ADMIN"


def test_ssrf_url_validation():
    # Valid company / web urls
    assert validate_url_safe("https://adani.com") is True
    assert validate_url_safe("http://internal.adani.local:8080/health") is True
    assert validate_url_safe("https://httpbin.org/status/200") is True

    # Blocked dangerous schemes and cloud metadata
    assert validate_url_safe("ftp://example.com") is False
    assert validate_url_safe("file:///etc/passwd") is False
    assert validate_url_safe("http://169.254.169.254/latest/meta-data/") is False
    assert validate_url_safe("http://metadata.google.internal/computeMetadata/v1/") is False
