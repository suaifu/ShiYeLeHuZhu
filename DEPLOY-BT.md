# 宝塔面板部署方案

## 前提条件

- 服务器已安装宝塔面板
- 宝塔软件商店已安装：Nginx + PostgreSQL（或 MySQL）
- Python 项目需要 Python 3.10+

---

## 第 1 步：拉取项目代码

宝塔面板 -> 终端：

```bash
cd /www/wwwroot
git clone https://github.com/suaifu/ShiYeLeHuZhu.git
cd ShiYeLeHuZhu

# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
```

---

## 第 2 步：初始化数据库

### 方式 A：宝塔面板可视化操作

1. 宝塔面板 -> 数据库 -> PostgreSQL -> 添加数据库
   - 数据库名：`restart_db`
   - 用户名：`restart`
   - 密码：自己设一个强密码
   - 访问权限：本地服务器

2. 导入表结构：
   - 点击数据库后面的「导入」按钮
   - 上传 `/www/wwwroot/ShiYeLeHuZhu/api/init_db.sql`
   - 执行导入

### 方式 B：终端命令

```bash
# 如果用宝塔自带的 PostgreSQL
su - postgres
psql -c "CREATE USER restart WITH PASSWORD '你的密码';"
psql -c "CREATE DATABASE restart_db OWNER restart;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE restart_db TO restart;"
psql -d restart_db -f /www/wwwroot/ShiYeLeHuZhu/api/init_db.sql
exit
```

---

## 第 3 步：修改配置文件

```bash
nano /www/wwwroot/ShiYeLeHuZhu/api/config.py
```

修改 `DATABASE_URL`：

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://restart:你的密码@127.0.0.1:5432/restart_db"
)
```

同时修改 `JWT_SECRET` 为一个随机字符串：

```python
JWT_SECRET = os.getenv("JWT_SECRET", "这里换成一串随机32位以上的字符")
```

---

## 第 4 步：宝塔创建网站（托管前端）

1. 宝塔面板 -> 网站 -> 添加站点
   - 域名：填你的域名（或服务器IP）
   - 根目录：`/www/wwwroot/ShiYeLeHuZhu/web`
   - PHP版本：纯静态
   - 数据库：不创建

2. 创建静态目录并复制前端文件：

```bash
mkdir -p /www/wwwroot/ShiYeLeHuZhu/web
cp /www/wwwroot/ShiYeLeHuZhu/restart.html /www/wwwroot/ShiYeLeHuZhu/web/index.html
```

---

## 第 5 步：配置 Nginx 反向代理

宝塔面板 -> 网站 -> 你的站点 -> 设置 -> 配置文件

在 `server { }` 块内，找到 `location / { }` 部分，替换为以下内容：

```nginx
    # 静态页面
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    # API 文档（调试用，上线后可删）
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
```

保存后，宝塔会自动重载 Nginx。

---

## 第 6 步：用宝塔 Python 项目管理器运行 API

### 方式 A：宝塔 Python 项目管理器（推荐）

1. 宝塔软件商店 -> 搜索「Python 项目管理器」-> 安装

2. 打开 Python 项目管理器 -> 添加项目
   - 项目名称：`restart-api`
   - 路径：`/www/wwwroot/ShiYeLeHuZhu`
   - Python 版本：选 3.10+ 的版本
   - 框架：FastAPI
   - 启动方式：uvicorn
   - 启动文件/模块：`api.main:app`
   - 端口：`8000`
   - 启动参数：`--host 127.0.0.1 --port 8000 --workers 4`
   - 环境变量：
     ```
     PYTHONPATH=/www/wwwroot/ShiYeLeHuZhu/api
     ```

3. 点击「启动」

### 方式 B：手动 systemd（宝塔没有 Python 管理器时）

宝塔终端执行：

```bash
cat > /etc/systemd/system/restart-api.service << 'EOF'
[Unit]
Description=Restart API (FastAPI)
After=network.target postgresql.service

[Service]
Type=simple
User=www
WorkingDirectory=/www/wwwroot/ShiYeLeHuZhu/api
Environment=PYTHONPATH=/www/wwwroot/ShiYeLeHuZhu/api
ExecStart=/www/wwwroot/ShiYeLeHuZhu/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable restart-api
systemctl start restart-api
```

---

## 第 7 步：配置 SSL（可选但推荐）

1. 宝塔面板 -> 网站 -> 你的站点 -> SSL
2. 选择「Let's Encrypt」-> 申请证书（免费）
3. 勾选「强制 HTTPS」
4. 宝塔会自动配置 Nginx 的 443 端口和证书续期

---

## 第 8 步：验证

宝塔终端执行：

```bash
# 检查 API 是否运行
curl http://127.0.0.1:8000/api/health
# 应返回: {"status":"ok","service":"重启 API","version":"1.0.0"}

# 检查 Nginx 代理
curl http://127.0.0.1/api/health
# 应返回同样的内容

# 浏览器访问
# http://你的域名/          -> 前端页面
# http://你的域名/api/health -> 健康检查
# http://你的域名/docs       -> API 文档
```

---

## 防火墙配置

宝塔面板 -> 安全：

| 端口 | 协议 | 说明 |
|------|------|------|
| 80 | TCP | HTTP（必须放行） |
| 443 | TCP | HTTPS（开了SSL才需要） |
| 8000 | - | **不要放行**（仅本机访问，通过Nginx代理） |
| 5432 | - | **不要放行**（仅本机访问） |

---

## 常用运维操作

### 查看日志

```bash
# API 日志（宝塔 Python 管理器）
# 直接在宝塔 Python 项目管理器界面查看

# API 日志（systemd 方式）
journalctl -u restart-api -f

# Nginx 日志
# 宝塔面板 -> 网站 -> 你的站点 -> 日志
```

### 更新代码

```bash
cd /www/wwwroot/ShiYeLeHuZhu
git pull
cp restart.html /www/wwwroot/ShiYeLeHuZhu/web/index.html

# 如果有新依赖
source venv/bin/activate
pip install -r api/requirements.txt

# 重启 API
# 宝塔 Python 管理器：界面点击「重启」
# 或终端：
systemctl restart restart-api
```

### 数据库备份

```bash
# 手动备份
pg_dump -U restart restart_db > /www/backup/restart_db_$(date +%Y%m%d).sql

# 宝塔定时任务（宝塔面板 -> 计划任务 -> 添加）
# 任务类型：Shell 脚本
# 执行周期：每天凌晨 3 点
# 脚本内容：
pg_dump -U restart restart_db > /www/backup/restart_db_$(date +\%Y\%m\%d).sql
find /www/backup/restart_db_*.sql -mtime +30 -delete
```

---

## 故障排查

| 问题 | 排查方法 |
|------|---------|
| 页面打开白屏 | 检查 `/web/index.html` 是否存在 |
| API 502 Bad Gateway | `systemctl status restart-api` 看是否在运行 |
| API 500 内部错误 | `journalctl -u restart-api` 看报错日志 |
| 数据库连接失败 | 检查 `config.py` 里的连接串和密码 |
| 注册/登录报错 | 确认 `init_db.sql` 已导入，表已创建 |
| CORS 报错 | `config.py` 的 `CORS_ORIGINS` 加上你的域名 |
| Nginx 代理不生效 | 检查站点配置文件是否保存成功，`nginx -t` 测试 |
