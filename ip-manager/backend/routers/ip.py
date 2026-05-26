"""IP 查询与操作路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import require_user
from excel_handler import (
    get_sheet_list,
    get_sheet_records,
    get_cached_sheets,
    occupy_ip_cache,
    release_ip_cache,
    schedule_sync,
    check_reload,
)
from config import READONLY_SHEETS
from models import get_db

router = APIRouter(prefix="/api/ip", tags=["ip"])


class OccupyRequest(BaseModel):
    sheet: str
    excelRow: int
    ip: str
    useUser: str = ""
    department: str = ""
    useDevice: str = ""
    model: str = ""
    macAddress: str = ""
    location: str = ""
    remark: str = ""


class ReleaseRequest(BaseModel):
    sheet: str
    excelRow: int
    ip: str


# ── 查询 ────────────────────────────────────────────────


@router.get("/sheets")
def list_sheets():
    """获取所有网段（Sheet）概览。"""
    return get_sheet_list()


@router.get("/stats")
def get_stats():
    """整体统计。"""
    sheets = get_sheet_list()
    total = sum(s["total"] for s in sheets)
    used = sum(s["used"] for s in sheets)
    free = sum(s["free"] for s in sheets)
    return {
        "total": total,
        "used": used,
        "free": free,
        "usageRate": round(used / total * 100, 1) if total > 0 else 0,
        "sheetCount": len(sheets),
    }


@router.get("/list")
def list_ips(
    sheet: str = Query(..., description="Sheet 名称"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=1000),
    search: str = Query("", description="搜索关键词"),
    status: str = Query("all", description="all / free / used"),
):
    """分页查询 IP 列表。"""
    all_records = get_sheet_records(sheet)
    if not all_records:
        return {"total": 0, "page": page, "pageSize": pageSize, "items": []}

    # 筛选
    filtered = all_records
    if status == "free":
        filtered = [r for r in filtered if r["free"]]
    elif status == "used":
        filtered = [r for r in filtered if not r["free"]]

    if search:
        kw = search.lower()
        filtered = [
            r for r in filtered
            if kw in r["ip"].lower()
            or kw in r.get("department", "").lower()
            or kw in r.get("useUser", "").lower()
            or kw in r.get("useDevice", "").lower()
            or kw in r.get("location", "").lower()
        ]

    # 分页
    total = len(filtered)
    start = (page - 1) * pageSize
    end = start + pageSize
    items = filtered[start:end]

    return {
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "items": items,
    }


@router.get("/detail")
def get_ip_detail(
    sheet: str = Query(...),
    excelRow: int = Query(...),
):
    """获取单条 IP 详情。"""
    records = get_sheet_records(sheet)
    for r in records:
        if r["excel_row"] == excelRow:
            return r
    raise HTTPException(404, "未找到该 IP 记录")


@router.post("/reload")
def reload_excel(user: dict = Depends(require_user)):
    """手动从 Excel 刷新数据。"""
    from excel_handler import load_all_sheets
    load_all_sheets()
    sheets = get_sheet_list()
    total = sum(s["total"] for s in sheets)
    return {"message": "已刷新", "sheets": len(sheets), "total": total}


# ── 操作 ────────────────────────────────────────────────


def _log_action(db, username: str, action: str, sheet: str, row: int, ip: str, detail: str = ""):
    db.execute(
        "INSERT INTO audit_logs (username, action, sheet_name, row_index, ip_address, detail) VALUES (?,?,?,?,?,?)",
        (username, action, sheet, row, ip, detail),
    )
    db.commit()


@router.post("/occupy")
def occupy(req: OccupyRequest, user: dict = Depends(require_user)):
    """占用 IP（立即更新缓存，后台队列同步 Excel）。"""
    if req.sheet in READONLY_SHEETS:
        raise HTTPException(400, f"该网段 ({req.sheet}) 为只读，不支持占用操作")

    if not req.useUser:
        raise HTTPException(400, "请输入使用人")
    if not req.useDevice:
        raise HTTPException(400, "请选择使用设备")

    try:
        success = occupy_ip_cache(
            sheet_name=req.sheet,
            excel_row=req.excelRow,
            use_user=req.useUser,
            department=req.department,
            use_device=req.useDevice,
            model=req.model,
            mac_address=req.macAddress,
            location=req.location,
            remark=req.remark,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    if not success:
        raise HTTPException(409, "该 IP 已被占用，请刷新页面")

    schedule_sync(req.sheet, req.excelRow)

    with get_db() as db:
        _log_action(db, user["username"], "occupy", req.sheet, req.excelRow, req.ip,
                    f"使用人:{req.useUser} 设备:{req.useDevice} 部门:{req.department}")

    return {"message": "占用成功", "ip": req.ip}


@router.post("/release")
def release(req: ReleaseRequest, user: dict = Depends(require_user)):
    """释放 IP。"""
    if req.sheet in READONLY_SHEETS:
        raise HTTPException(400, f"该网段 ({req.sheet}) 为只读，不支持释放操作")

    try:
        success = release_ip_cache(sheet_name=req.sheet, excel_row=req.excelRow)
    except ValueError as e:
        raise HTTPException(404, str(e))

    if not success:
        raise HTTPException(400, "该 IP 已经是空闲状态")

    schedule_sync(req.sheet, req.excelRow)

    with get_db() as db:
        _log_action(db, user["username"], "release", req.sheet, req.excelRow, req.ip, "")

    return {"message": "释放成功", "ip": req.ip}


@router.put("/update")
def update_ip(req: OccupyRequest, user: dict = Depends(require_user)):
    """修改 IP 占用信息（仅管理员）。"""
    if not user["is_admin"]:
        raise HTTPException(403, "需要管理员权限")

    if req.sheet in READONLY_SHEETS:
        raise HTTPException(400, f"该网段 ({req.sheet}) 为只读")

    try:
        release_ip_cache(sheet_name=req.sheet, excel_row=req.excelRow)
        success = occupy_ip_cache(
            sheet_name=req.sheet,
            excel_row=req.excelRow,
            use_user=req.useUser,
            department=req.department,
            use_device=req.useDevice,
            model=req.model,
            mac_address=req.macAddress,
            location=req.location,
            remark=req.remark,
        )
    except ValueError as e:
        raise HTTPException(500, str(e))

    schedule_sync(req.sheet, req.excelRow)

    with get_db() as db:
        _log_action(db, user["username"], "update", req.sheet, req.excelRow, req.ip,
                    f"使用人:{req.useUser} 设备:{req.useDevice} 部门:{req.department}")

    return {"message": "修改成功", "ip": req.ip}
