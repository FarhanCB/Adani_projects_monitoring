import ipaddress
import socket
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_password_hash(password: str) -> str:
    """Hash password securely using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """FastAPI dependency to extract and validate authenticated user."""
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


def get_current_admin(current_user=Depends(get_current_user)):
    """All authenticated users have full administrative and configuration access."""
    return current_user


def validate_url_safe(url: str) -> bool:
    """SSRF protection: validate URL scheme and block cloud metadata / dangerous addresses,
    while permitting corporate intranet domains and IPs.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block cloud metadata addresses
        blocked_hostnames = {
            "169.254.169.254",
            "metadata.google.internal",
            "metadata.internal",
            "100.100.100.200",  # Alibaba
            "169.254.170.2",    # AWS task metadata
        }
        if hostname.lower() in blocked_hostnames:
            return False

        # If IP directly given, verify not link-local
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_link_local or ip.is_multicast:
                return False
        except ValueError:
            pass  # It's a hostname (e.g. example.com, adani.internal, localhost)

        return True
    except Exception:
        return False
