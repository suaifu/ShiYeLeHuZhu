"""
重启 · 失业互助平台 - 配置文件
"""

import os
from pathlib import Path

# ─── 数据库配置 ───
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fushuaiguo@localhost:5432/restart_db"
)

DB_POOL_MIN = 2
DB_POOL_MAX = 10

# ─── JWT 配置 ───
JWT_SECRET = os.getenv("JWT_SECRET", "restart-secret-change-in-production-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72

# ─── CORS 配置 ───
CORS_ORIGINS = [
    "http://localhost:*",
    "http://127.0.0.1:*",
    "https://guoshuaifu.cn",
    "https://*.guoshuaifu.cn",
]

# ─── 应用配置 ───
APP_NAME = "重启 API"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
