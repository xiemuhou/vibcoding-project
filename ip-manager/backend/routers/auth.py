"""认证路由 — 注册、登录"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import hash_password, verify_password, create_token, require_user
from models import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    displayName: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(req: RegisterRequest):
    if len(req.username) < 2 or len(req.username) > 50:
        raise HTTPException(400, "用户名长度 2-50 个字符")
    if len(req.password) < 4:
        raise HTTPException(400, "密码至少 4 个字符")

    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE username=?", (req.username,)).fetchone()
        if existing:
            raise HTTPException(400, "用户名已存在")
        db.execute(
            "INSERT INTO users (username, password_hash, display_name) VALUES (?,?,?)",
            (req.username, hash_password(req.password), req.displayName or req.username),
        )
        db.commit()
    return {"message": "注册成功", "username": req.username}


@router.post("/login")
def login(req: LoginRequest):
    with get_db() as db:
        user = db.execute(
            "SELECT username, password_hash, is_admin FROM users WHERE username=?",
            (req.username,),
        ).fetchone()
        if user is None or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(401, "用户名或密码错误")

    token = create_token(user["username"], bool(user["is_admin"]))
    return {
        "token": token,
        "username": user["username"],
        "isAdmin": bool(user["is_admin"]),
    }


@router.get("/me")
def me(user: dict = Depends(require_user)):
    with get_db() as db:
        row = db.execute(
            "SELECT username, display_name, is_admin FROM users WHERE username=?",
            (user["username"],),
        ).fetchone()
    return {
        "username": row["username"],
        "displayName": row["display_name"],
        "isAdmin": bool(row["is_admin"]),
    }
