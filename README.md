# ShiYeLeHuZhu · 失业乐互助

> 暂停，不是终点，是重新出发的起点。

失业人群互助平台 -- 信息门户 + 个人管理工具台 + FastAPI 后端，帮助失业者走过这段不确定的路。

## 项目结构

```
├── restart.html          # 前端页面（信息门户 + 工具台 + 登录注册）
├── api/                  # FastAPI 后端
│   ├── main.py           # 应用入口
│   ├── config.py         # 配置（DB/CORS/JWT）
│   ├── database.py       # 连接池
│   ├── models.py         # 数据模型
│   ├── auth.py           # JWT + bcrypt 认证
│   ├── routes_auth.py    # 认证路由
│   ├── routes_jobs.py    # 求职追踪路由
│   ├── routes_data.py    # 日记/收支/技能/设置路由
│   ├── init_db.sql       # 建表脚本
│   ├── Dockerfile        # API 容器镜像
│   └── requirements.txt  # Python 依赖
├── docker-compose.yml    # 三容器编排（PG + API + Nginx）
├── nginx/nginx.conf      # 反向代理配置
├── deploy.sh             # 一键部署脚本
└── .env.example          # 环境变量模板
```

## 功能

### 信息门户（公开访问）
- 失业困境分析、就业市场数据透视、行业趋势
- 资源工具箱（失业保险/社保/培训/法律维权详解）
- 技能测评（5题问卷 + SVG雷达图）
- 心理关怀（24小时热线 + 自救指南）
- 真实转型故事、30天行动清单、财务计算器、FAQ

### 个人管理工具台（需登录）
- **求职追踪**：投递记录 CRUD + 状态筛选 + 统计
- **失业日记**：每日心情打卡 + 小成就 + 失业天数倒计时
- **收支记账**：月度收支汇总 + 存款支撑月数 + 分类记录
- **技能充电**：学习计划 + 每日打卡 + 连续天数 + 14天热力图

### 后端 API
- FastAPI + PostgreSQL 14
- JWT 认证 + bcrypt 密码哈希
- 23 个 REST API 接口
- ThreadedConnectionPool 连接池
- API 文档自动生成（/docs）

## 快速部署

```bash
# 1. 克隆仓库
git clone https://github.com/suaifu/ShiYeLeHuZhu.git
cd ShiYeLeHuZhu

# 2. 配置环境变量
cp .env.example .env
nano .env  # 修改数据库密码和JWT密钥

# 3. 一键部署
bash deploy.sh
```

部署后访问 `http://服务器IP/` 即可。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | 纯 HTML/CSS/JS（单文件，零外部依赖，SVG 图标系统） |
| 后端 | FastAPI 0.141 + Uvicorn |
| 数据库 | PostgreSQL 14 |
| 部署 | Docker Compose（Nginx + FastAPI + PostgreSQL） |
| 认证 | JWT (python-jose) + bcrypt |

## 数据来源

- 国家统计局 (stats.gov.cn)
- 人社部 (mohrss.gov.cn)
- 教育部 (moe.gov.cn)
- 国家社保平台 (si.12333.gov.cn)
- 智联招聘/BOSS直聘（行业趋势估算）

## License

MIT
