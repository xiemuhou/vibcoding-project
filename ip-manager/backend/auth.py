"""JWT 认证模块"""

import datetime
from typing import Optional

import jwt
import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_token(username: str, is_admin: bool) -> str:
    payload = {
        "sub": username,
        "is_admin": is_admin,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的登录凭证")


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """从 JWT 解析当前用户（可选认证，未登录返回 None）。"""
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    return {"username": payload["sub"], "is_admin": payload["is_admin"]}


def require_user(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """要求登录，否则返回 401。"""
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def require_admin(user: dict = Depends(require_user)) -> dict:
    """要求管理员权限。"""
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
