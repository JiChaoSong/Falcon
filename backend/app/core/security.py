import secrets
from datetime import timedelta, datetime
from typing import Any, Optional, Dict

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings
from app.utils.time_utils import utc_from_timestamp, utc_now

import logging
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:

    return pwd_context.hash(password)


class TokenPayload(BaseModel):
    """令牌载荷"""
    id: int = None  # 用户ID
    username: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None  # 令牌唯一标识



def verify_access_token(token: str) -> Optional[TokenPayload]:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # # 验证令牌类型
        # if payload.get("type") != "access":
        #     return None

        # 验证过期时间
        exp = payload.get("exp")
        if exp and utc_now() > utc_from_timestamp(exp):
            return None

        return TokenPayload(**payload)

    except JWTError:
        return None

def create_access_token(data:Dict[str,Any], expires_delta:Optional[timedelta] = None) -> str:

    to_encode = data.copy()

    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update(
        {
            "exp": expire,
            "iat": utc_now(),
            "jti": secrets.token_urlsafe(32),  # 令牌唯一标识
            "type": "access"
        })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def refresh_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建刷新令牌

    Args:
        data: 令牌数据
        expires_delta: 过期时间

    Returns:
        JWT刷新令牌
    """
    to_encode = data.copy()

    # 刷新令牌过期时间更长
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({
        "exp": expire,
        "iat": utc_now(),
        "jti": secrets.token_urlsafe(32),  # 令牌唯一标识
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt
