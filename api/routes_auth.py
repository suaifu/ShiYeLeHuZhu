"""
重启 · 失业互助平台 - 认证路由
POST /api/auth/register  注册
POST /api/auth/login     登录
GET  /api/auth/me        获取当前用户
"""

from fastapi import APIRouter, Depends, HTTPException, status
from database import get_cursor
from auth import hash_password, verify_password, create_token, get_current_user
from models import UserRegister, UserLogin, Token, UserOut

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=Token, status_code=201)
def register(body: UserRegister):
    """用户注册"""
    with get_cursor(commit=True) as cur:
        # 检查邮箱是否已注册
        cur.execute("SELECT id FROM users WHERE email = %s", (body.email,))
        if cur.fetchone():
            raise HTTPException(400, "该邮箱已注册")
        # 创建用户
        cur.execute(
            "INSERT INTO users (email, nickname, password_hash) VALUES (%s, %s, %s) RETURNING id, created_at",
            (body.email, body.nickname or body.email.split("@")[0], hash_password(body.password)),
        )
        row = cur.fetchone()
        user_id, created_at = row[0], row[1]
        # 初始化设置
        cur.execute(
            "INSERT INTO user_settings (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (user_id,),
        )
    token = create_token(user_id, body.email)
    return Token(
        access_token=token,
        user=UserOut(id=user_id, email=body.email, nickname=body.nickname or body.email.split("@")[0], created_at=created_at),
    )


@router.post("/login", response_model=Token)
def login(body: UserLogin):
    """用户登录"""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, nickname, password_hash, created_at FROM users WHERE email = %s AND is_active = TRUE",
            (body.email,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(401, "邮箱或密码错误")
    user_id, email, nickname, pwd_hash, created_at = row
    if not verify_password(body.password, pwd_hash):
        raise HTTPException(401, "邮箱或密码错误")
    token = create_token(user_id, email)
    return Token(
        access_token=token,
        user=UserOut(id=user_id, email=email, nickname=nickname, created_at=created_at),
    )


@router.get("/me", response_model=UserOut)
def me(user: UserOut = Depends(get_current_user)):
    """获取当前用户信息"""
    return user
