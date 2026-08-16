"""
重启 · 失业互助平台 - 认证模块
JWT 生成/验证 + 密码哈希
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_cursor
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from models import UserOut
import logging

logger = logging.getLogger(__name__)

# Bearer token 提取
security = HTTPBearer()


def hash_password(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.warning(f"密码验证异常: {e}")
        return False


def create_token(user_id: int, email: str) -> str:
    """生成 JWT token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        logger.warning(f"JWT 解码失败: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserOut:
    """
    依赖注入：从请求头提取 JWT，返回当前用户
    所有需要登录的接口都加 Depends(get_current_user)
    """
    payload = decode_token(credentials.credentials)
    if payload is None:
        logger.warning(f"认证失败: token 无效")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )
    user_id = int(payload.get("sub", 0))
    if user_id == 0:
        logger.warning("认证失败: token 缺少 sub")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
        )
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, nickname, created_at FROM users WHERE id = %s AND is_active = TRUE",
            (user_id,),
        )
        row = cur.fetchone()
    if row is None:
        logger.warning(f"认证失败: user_id={user_id} 不存在或已禁用")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    return UserOut(id=row[0], email=row[1], nickname=row[2], created_at=row[3])
