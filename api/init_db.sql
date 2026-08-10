-- ═══════════════════════════════════════════════════════
-- 重启 · 失业互助平台 - 数据库初始化脚本
-- PostgreSQL 14+ | UTF-8
-- ═══════════════════════════════════════════════════════

-- 创建数据库（如不存在）
-- CREATE DATABASE restart_db WITH ENCODING 'UTF8';

-- 连接: \c restart_db

-- ─── 用户表 ───
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    nickname        VARCHAR(64) NOT NULL DEFAULT '',
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 索引：邮箱查询加速
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE is_active = TRUE;

-- ─── 求职记录表 ───
CREATE TABLE IF NOT EXISTS job_applications (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company         VARCHAR(128) NOT NULL,
    position        VARCHAR(128) NOT NULL,
    salary          VARCHAR(64) DEFAULT '',
    status          VARCHAR(16) DEFAULT '投递' CHECK (status IN ('投递','笔试','面试','Offer','拒绝','已放弃')),
    apply_date      DATE,
    follow_date     DATE,
    feedback        TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON job_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON job_applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_apply_date ON job_applications(user_id, apply_date DESC);

-- ─── 失业日记表 ───
CREATE TABLE IF NOT EXISTS diary_entries (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entry_date      DATE NOT NULL,
    mood            SMALLINT CHECK (mood BETWEEN 1 AND 5),
    achievement     VARCHAR(500) DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, entry_date)
);

CREATE INDEX IF NOT EXISTS idx_diary_user_date ON diary_entries(user_id, entry_date DESC);

-- ─── 收支记录表 ───
CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    txn_type        VARCHAR(8) NOT NULL CHECK (txn_type IN ('expense','income')),
    amount          NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    category        VARCHAR(32) NOT NULL,
    txn_date        DATE NOT NULL,
    note            VARCHAR(256) DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, txn_date DESC);
CREATE INDEX IF NOT EXISTS idx_txn_user_type ON transactions(user_id, txn_type);

-- ─── 技能计划表 ───
CREATE TABLE IF NOT EXISTS skill_plans (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(128) NOT NULL,
    skill_type      VARCHAR(32) DEFAULT '其他',
    current_progress INTEGER DEFAULT 0,
    target_total    INTEGER DEFAULT 0,
    daily_goal      VARCHAR(64) DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skills_user_id ON skill_plans(user_id);

-- ─── 技能打卡记录表 ───
CREATE TABLE IF NOT EXISTS skill_checkins (
    id              SERIAL PRIMARY KEY,
    skill_id        INTEGER NOT NULL REFERENCES skill_plans(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_date    DATE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(skill_id, checkin_date)
);

CREATE INDEX IF NOT EXISTS idx_checkin_skill_date ON skill_checkins(skill_id, checkin_date DESC);
CREATE INDEX IF NOT EXISTS idx_checkin_user_date ON skill_checkins(user_id, checkin_date DESC);

-- ─── 用户设置表 ───
CREATE TABLE IF NOT EXISTS user_settings (
    user_id             INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    unemployment_start  DATE DEFAULT NULL,
    monthly_budget      NUMERIC(10,2) DEFAULT 5000,
    savings             NUMERIC(12,2) DEFAULT 50000,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 订阅者表（邮件订阅） ───
CREATE TABLE IF NOT EXISTS subscribers (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 自动更新 updated_at 触发器 ───
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated     BEFORE UPDATE ON users             FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_jobs_updated      BEFORE UPDATE ON job_applications  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_skills_updated    BEFORE UPDATE ON skill_plans       FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_settings_updated  BEFORE UPDATE ON user_settings     FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════
-- 完成
-- ═══════════════════════════════════════════════════════
