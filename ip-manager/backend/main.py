"""IP 地址管理系统 — FastAPI 主入口"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models import init_db, init_admin
from excel_handler import init_excel_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    init_db()
    init_admin()
    init_excel_handler()
    yield
    # 关闭


app = FastAPI(title="IP 地址管理系统", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.auth import router as auth_router
from routers.ip import router as ip_router
from routers.admin import router as admin_router

app.include_router(auth_router)
app.include_router(ip_router)
app.include_router(admin_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 静态文件 + SPA fallback
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=static_dir), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """SPA fallback — 所有非 /api 路径返回 index.html。"""
    from fastapi.responses import FileResponse
    index = static_dir / "index.html"
    if not index.exists():
        return {"message": "Frontend not found"}
    return FileResponse(index)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
