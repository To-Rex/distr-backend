import secrets
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_password_hash(plain_password) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_expiration_date(duration_seconds: int = 86400 * 30) -> datetime:
    return (datetime.now(tz=timezone.utc) + timedelta(seconds=duration_seconds)).replace(tzinfo=None)

def generate_access_token() -> str:
    return secrets.token_urlsafe(64)
