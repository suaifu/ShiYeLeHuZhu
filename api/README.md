# 重启 · 失业互助平台 API

## 快速启动

```bash
# 1. 安装依赖（首次）
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary python-jose bcrypt python-multipart "pydantic[email]"

# 2. 初始化数据库
psql -d postgres -c "CREATE DATABASE restart_db WITH ENCODING 'UTF8';"
psql -d restart_db -f init_db.sql

# 3. 启动服务
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. 查看 API 文档
# 浏览器打开 http://localhost:8000/docs
```

## API 接口一览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | /api/auth/register | 注册 | 否 |
| POST | /api/auth/login | 登录 | 否 |
| GET | /api/auth/me | 获取当前用户 | 是 |
| GET | /api/jobs | 求职列表 | 是 |
| POST | /api/jobs | 新增求职 | 是 |
| PUT | /api/jobs/{id} | 编辑求职 | 是 |
| DELETE | /api/jobs/{id} | 删除求职 | 是 |
| GET | /api/jobs/stats | 求职统计 | 是 |
| GET | /api/diary | 日记列表 | 是 |
| POST | /api/diary | 新增/更新日记 | 是 |
| DELETE | /api/diary/{id} | 删除日记 | 是 |
| GET | /api/finance | 收支列表 | 是 |
| POST | /api/finance | 新增收支 | 是 |
| DELETE | /api/finance/{id} | 删除收支 | 是 |
| GET | /api/finance/summary | 月度汇总 | 是 |
| GET | /api/skills | 技能列表(含打卡) | 是 |
| POST | /api/skills | 新增技能 | 是 |
| PUT | /api/skills/{id} | 编辑技能 | 是 |
| DELETE | /api/skills/{id} | 删除技能 | 是 |
| POST | /api/skills/{id}/checkin | 打卡/取消 | 是 |
| GET | /api/settings | 获取设置 | 是 |
| PUT | /api/settings | 更新设置 | 是 |
| POST | /api/subscribe | 邮箱订阅 | 否 |
| GET | /api/health | 健康检查 | 否 |

## 数据库配置

默认连接：`postgresql://fushuaiguo@localhost:5432/restart_db`

通过环境变量覆盖：`DATABASE_URL=postgresql://user:pass@host:port/db`

## 技术栈

- FastAPI 0.141 + Uvicorn
- PostgreSQL 14 + psycopg2
- JWT (python-jose) + bcrypt 密码哈希
- 连接池：ThreadedConnectionPool (2-10 连接)

## 文件结构

```
api/
├── main.py           # FastAPI 主入口
├── config.py         # 配置（DB/CORS/JWT）
├── database.py       # 连接池管理
├── models.py         # Pydantic 数据模型
├── auth.py           # JWT + 密码哈希
├── routes_auth.py    # 认证路由
├── routes_jobs.py    # 求职追踪路由
├── routes_data.py    # 日记+收支+技能+设置+订阅路由
├── init_db.sql       # 建表脚本
└── test_api.sh       # API 测试脚本
```
