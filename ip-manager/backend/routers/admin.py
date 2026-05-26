"""管理路由 — 用户管理 + 操作日志"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import require_admin, hash_password
from models import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── 用户管理 ────────────────────────────────────────────


@router.get("/users")
def list_users(user: dict = Depends(require_admin)):
    with get_db() as db:
        rows = db.execute(
            "SELECT id, username, display_name, is_admin, created_at FROM users ORDER BY id"
        ).fetchall()
    return [
        {
            "id": r["id"],
            "username": r["username"],
            "displayName": r["display_name"],
            "isAdmin": bool(r["is_admin"]),
            "createdAt": r["created_at"],
        }
        for r in rows
    ]


class ResetPasswordRequest(BaseModel):
    userId: int
    newPassword: str


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, user: dict = Depends(require_admin)):
    if len(req.newPassword) < 4:
        raise HTTPException(400, "密码至少 4 个字符")
    with get_db() as db:
        db.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (hash_password(req.newPassword), req.userId),
        )
        db.commit()
    return {"message": "密码已重置"}


class DeleteUserRequest(BaseModel):
    userId: int


@router.post("/delete-user")
def delete_user(req: DeleteUserRequest, user: dict = Depends(require_admin)):
    with get_db() as db:
        target = db.execute("SELECT username FROM users WHERE id=?", (req.userId,)).fetchone()
        if target is None:
            raise HTTPException(404, "用户不存在")
        if target["username"] == user["username"]:
            raise HTTPException(400, "不能删除自己")
        db.execute("DELETE FROM users WHERE id=?", (req.userId,))
        db.commit()
    return {"message": "用户已删除"}


# ── 操作日志 ────────────────────────────────────────────


@router.get("/logs")
def list_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    username: str = Query(""),
    action: str = Query(""),
    user: dict = Depends(require_admin),
):
    with get_db() as db:
        conditions = []
        params = []
        if username:
            conditions.append("username LIKE ?")
            params.append(f"%{username}%")
        if action:
            conditions.append("action = ?")
            params.append(action)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        count = db.execute(f"SELECT COUNT(*) as c FROM audit_logs {where}", params).fetchone()["c"]
        rows = db.execute(
            f"SELECT * FROM audit_logs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [pageSize, (page - 1) * pageSize],
        ).fetchall()

    return {
        "total": count,
        "page": page,
        "pageSize": pageSize,
        "items": [
            {
                "id": r["id"],
                "timestamp": r["timestamp"],
                "username": r["username"],
                "action": r["action"],
                "sheetName": r["sheet_name"],
                "rowIndex": r["row_index"],
                "ipAddress": r["ip_address"],
                "detail": r["detail"],
            }
            for r in rows
        ],
    }
