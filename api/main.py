"""
重启 · 失业互助平台 - FastAPI 主入口

启动: cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000
生产: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import APP_NAME, APP_VERSION, CORS_ORIGINS, DEBUG
from database import init_pool, close_pool
from routes_auth import router as auth_router
from routes_jobs import router as jobs_router
from routes_data import (
    diary_router, finance_router, skill_router,
    settings_router, subscribe_router, feedback_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化连接池，关闭时释放"""
    init_pool()
    logger.info(f"{APP_NAME} v{APP_VERSION} started")
    yield
    close_pool()
    logger.info(f"{APP_NAME} stopped")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="失业人群互助平台 - 后端 API",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else "/docs",
    redoc_url="/redoc" if DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(diary_router)
app.include_router(finance_router)
app.include_router(skill_router)
app.include_router(settings_router)
app.include_router(subscribe_router)
app.include_router(feedback_router)


@app.get("/api/health")
def health():
    """健康检查"""
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


from fastapi.responses import FileResponse
from pathlib import Path

@app.get("/")
def root():
    """本地测试：直接返回前端页面"""
    html_path = Path(__file__).parent.parent / "restart.html"
    if html_path.exists():
        return FileResponse(html_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"message": "重启 API", "docs": "/docs"}
