"""
重启 · 失业互助平台 - 数据库连接池
使用 psycopg2.pool 管理连接，避免每次请求创建新连接
"""

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from config import DATABASE_URL, DB_POOL_MIN, DB_POOL_MAX
import logging

logger = logging.getLogger(__name__)

# 解析 DATABASE_URL
# postgresql://user:password@host:port/dbname
import urllib.parse
url = urllib.parse.urlparse(DATABASE_URL)

_pool: ThreadedConnectionPool = None


def init_pool():
    """初始化连接池，应用启动时调用一次"""
    global _pool
    if _pool is not None:
        return
    _pool = ThreadedConnectionPool(
        DB_POOL_MIN,
        DB_POOL_MAX,
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password,
    )
    logger.info(f"DB pool initialized: {url.hostname}:{url.port}/{url.path[1:]}")


def close_pool():
    """关闭连接池，应用关闭时调用"""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        logger.info("DB pool closed")


@contextmanager
def get_conn():
    """获取数据库连接（上下文管理器，自动归还）"""
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)


@contextmanager
def get_cursor(commit: bool = False):
    """
    获取游标，自动归还连接
    commit=True 时自动提交事务
    """
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
