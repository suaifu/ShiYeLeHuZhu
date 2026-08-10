"""
重启 · 失业互助平台 - 数据模型 (Pydantic)
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


# ─── 枚举 ───
class JobStatus(str, Enum):
    APPLIED = "投递"
    WRITTEN = "笔试"
    INTERVIEW = "面试"
    OFFER = "Offer"
    REJECTED = "拒绝"
    ABANDONED = "已放弃"


class TxnType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"


class MoodLevel(int, Enum):
    VERY_LOW = 1
    LOW = 2
    OK = 3
    GOOD = 4
    HOPEFUL = 5


# ─── 用户 ───
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=64)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    nickname: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── 求职记录 ───
class JobApplicationCreate(BaseModel):
    company: str = Field(max_length=128)
    position: str = Field(max_length=128)
    salary: str = Field(default="", max_length=64)
    status: JobStatus = JobStatus.APPLIED
    apply_date: Optional[date] = None
    follow_date: Optional[date] = None
    feedback: str = Field(default="", max_length=2000)


class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[str] = None
    status: Optional[JobStatus] = None
    apply_date: Optional[date] = None
    follow_date: Optional[date] = None
    feedback: Optional[str] = None


class JobApplicationOut(BaseModel):
    id: int
    company: str
    position: str
    salary: str
    status: str
    apply_date: Optional[date]
    follow_date: Optional[date]
    feedback: str
    created_at: datetime


# ─── 失业日记 ───
class DiaryCreate(BaseModel):
    entry_date: date
    mood: MoodLevel
    achievement: str = Field(default="", max_length=500)


class DiaryOut(BaseModel):
    id: int
    entry_date: date
    mood: int
    achievement: str
    created_at: datetime


# ─── 收支记录 ───
class TransactionCreate(BaseModel):
    txn_type: TxnType
    amount: float = Field(gt=0)
    category: str = Field(max_length=32)
    txn_date: date
    note: str = Field(default="", max_length=256)


class TransactionOut(BaseModel):
    id: int
    txn_type: str
    amount: float
    category: str
    txn_date: date
    note: str
    created_at: datetime


# ─── 技能计划 ───
class SkillPlanCreate(BaseModel):
    name: str = Field(max_length=128)
    skill_type: str = Field(default="其他", max_length=32)
    current_progress: int = Field(default=0, ge=0)
    target_total: int = Field(default=0, ge=0)
    daily_goal: str = Field(default="", max_length=64)


class SkillPlanUpdate(BaseModel):
    name: Optional[str] = None
    skill_type: Optional[str] = None
    current_progress: Optional[int] = Field(default=None, ge=0)
    target_total: Optional[int] = Field(default=None, ge=0)
    daily_goal: Optional[str] = None


class SkillPlanOut(BaseModel):
    id: int
    name: str
    skill_type: str
    current_progress: int
    target_total: int
    daily_goal: str
    created_at: datetime


class SkillCheckinOut(BaseModel):
    skill_id: int
    checkin_date: date


# ─── 用户设置 ───
class UserSettingsUpdate(BaseModel):
    unemployment_start: Optional[date] = None
    monthly_budget: Optional[float] = None
    savings: Optional[float] = None


class UserSettingsOut(BaseModel):
    unemployment_start: Optional[date]
    monthly_budget: float
    savings: float


# ─── 订阅 ───
class SubscribeRequest(BaseModel):
    email: EmailStr


# ─── 通用响应 ───
class StandardResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    success: bool = True
    total: int
    page: int
    page_size: int
    data: List[dict]
