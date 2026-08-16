"""
重启 · 失业互助平台 - 失业日记 + 收支记账 + 技能充电 + 设置 路由
合并到一个文件，避免文件过多
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import date as date_type
from database import get_cursor
from auth import get_current_user
from models import (
    UserOut, DiaryCreate, DiaryOut,
    TransactionCreate, TransactionOut,
    SkillPlanCreate, SkillPlanUpdate, SkillPlanOut,
    UserSettingsUpdate, UserSettingsOut,
    SubscribeRequest, FeedbackRequest, StandardResponse,)

# ═══════════════════════════════════════
# 失业日记
# ═══════════════════════════════════════
diary_router = APIRouter(prefix="/api/diary", tags=["失业日记"])


@diary_router.get("", response_model=list[DiaryOut])
def list_diary(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: UserOut = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, entry_date, mood, achievement, created_at
               FROM diary_entries WHERE user_id = %s
               ORDER BY entry_date DESC LIMIT %s OFFSET %s""",
            (user.id, page_size, offset),
        )
        rows = cur.fetchall()
    return [DiaryOut(id=r[0], entry_date=r[1], mood=r[2], achievement=r[3], created_at=r[4]) for r in rows]


@diary_router.post("", response_model=DiaryOut, status_code=201)
def create_diary(body: DiaryCreate, user: UserOut = Depends(get_current_user)):
    """新增/更新日记（同一天会覆盖）"""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO diary_entries (user_id, entry_date, mood, achievement)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (user_id, entry_date) DO UPDATE
               SET mood = EXCLUDED.mood, achievement = EXCLUDED.achievement
               RETURNING id, entry_date, mood, achievement, created_at""",
            (user.id, body.entry_date, body.mood.value, body.achievement),
        )
        r = cur.fetchone()
    return DiaryOut(id=r[0], entry_date=r[1], mood=r[2], achievement=r[3], created_at=r[4])


@diary_router.delete("/{diary_id}", status_code=204)
def delete_diary(diary_id: int, user: UserOut = Depends(get_current_user)):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM diary_entries WHERE id = %s AND user_id = %s",
            (diary_id, user.id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "日记不存在")


# ═══════════════════════════════════════
# 收支记账
# ═══════════════════════════════════════
finance_router = APIRouter(prefix="/api/finance", tags=["收支记账"])


@finance_router.get("", response_model=list[TransactionOut])
def list_transactions(
    txn_type: Optional[str] = Query(None),
    month: Optional[str] = Query(None, description="YYYY-MM"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: UserOut = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    query = "SELECT id, txn_type, amount, category, txn_date, note, created_at FROM transactions WHERE user_id = %s"
    params = [user.id]
    if txn_type:
        query += " AND txn_type = %s"
        params.append(txn_type)
    if month:
        query += " AND to_char(txn_date, 'YYYY-MM') = %s"
        params.append(month)
    query += " ORDER BY txn_date DESC, created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return [TransactionOut(
        id=r[0], txn_type=r[1], amount=float(r[2]), category=r[3],
        txn_date=r[4], note=r[5], created_at=r[6]
    ) for r in rows]


@finance_router.get("/summary")
def finance_summary(user: UserOut = Depends(get_current_user)):
    """月度收支汇总"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT
                COALESCE(SUM(CASE WHEN txn_type='expense' THEN amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN txn_type='income' THEN amount ELSE 0 END), 0)
               FROM transactions
               WHERE user_id = %s AND to_char(txn_date, 'YYYY-MM') = to_char(NOW(), 'YYYY-MM')""",
            (user.id,),
        )
        expense, income = cur.fetchone()
        # 按分类汇总
        cur.execute(
            """SELECT category, SUM(amount) FROM transactions
               WHERE user_id = %s AND txn_type = 'expense'
               AND to_char(txn_date, 'YYYY-MM') = to_char(NOW(), 'YYYY-MM')
               GROUP BY category ORDER BY SUM(amount) DESC""",
            (user.id,),
        )
        cats = {r[0]: float(r[1]) for r in cur.fetchall()}
    return {
        "month_expense": float(expense),
        "month_income": float(income),
        "categories": cats,
    }


@finance_router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(body: TransactionCreate, user: UserOut = Depends(get_current_user)):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO transactions (user_id, txn_type, amount, category, txn_date, note)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id, txn_type, amount, category, txn_date, note, created_at""",
            (user.id, body.txn_type.value, body.amount, body.category, body.txn_date, body.note),
        )
        r = cur.fetchone()
    return TransactionOut(
        id=r[0], txn_type=r[1], amount=float(r[2]), category=r[3],
        txn_date=r[4], note=r[5], created_at=r[6]
    )


@finance_router.delete("/{txn_id}", status_code=204)
def delete_transaction(txn_id: int, user: UserOut = Depends(get_current_user)):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (txn_id, user.id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "记录不存在")


# ═══════════════════════════════════════
# 技能充电
# ═══════════════════════════════════════
skill_router = APIRouter(prefix="/api/skills", tags=["技能充电"])


@skill_router.get("", response_model=list[dict])
def list_skills(user: UserOut = Depends(get_current_user)):
    """获取技能计划列表（含打卡记录和连续天数）"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, name, skill_type, current_progress, target_total, daily_goal, created_at
               FROM skill_plans WHERE user_id = %s ORDER BY created_at""",
            (user.id,),
        )
        plans = cur.fetchall()
        # 批量获取所有打卡记录
        cur.execute(
            """SELECT skill_id, checkin_date FROM skill_checkins
               WHERE user_id = %s ORDER BY checkin_date DESC""",
            (user.id,),
        )
        all_checkins = cur.fetchall()
    # 按技能分组打卡记录
    checkin_map = {}
    for skill_id, checkin_date in all_checkins:
        checkin_map.setdefault(skill_id, []).append(checkin_date.isoformat())
    # 计算连续天数
    from collections import defaultdict
    result = []
    today = date_type.today().isoformat()
    for p in plans:
        checkins = checkin_map.get(p[0], [])
        # streak
        streak = 0
        checkin_set = set(checkins)
        d = today
        if d not in checkin_set:
            # 检查昨天
            from datetime import timedelta
            d = (date_type.today() - timedelta(days=1)).isoformat()
        while d in checkin_set:
            streak += 1
            from datetime import timedelta
            d = (date_type.fromisoformat(d) - timedelta(days=1)).isoformat()
        result.append({
            "id": p[0], "name": p[1], "skill_type": p[2],
            "current_progress": p[3], "target_total": p[4],
            "daily_goal": p[5], "created_at": p[6].isoformat(),
            "checkins": checkins, "streak": streak,
        })
    return result


@skill_router.post("", response_model=SkillPlanOut, status_code=201)
def create_skill(body: SkillPlanCreate, user: UserOut = Depends(get_current_user)):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO skill_plans (user_id, name, skill_type, current_progress, target_total, daily_goal)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id, name, skill_type, current_progress, target_total, daily_goal, created_at""",
            (user.id, body.name, body.skill_type, body.current_progress, body.target_total, body.daily_goal),
        )
        r = cur.fetchone()
    return SkillPlanOut(id=r[0], name=r[1], skill_type=r[2], current_progress=r[3],
                        target_total=r[4], daily_goal=r[5], created_at=r[6])


@skill_router.put("/{skill_id}", response_model=SkillPlanOut)
def update_skill(skill_id: int, body: SkillPlanUpdate, user: UserOut = Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(400, "没有需要更新的字段")
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    params = list(updates.values()) + [skill_id, user.id]
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"""UPDATE skill_plans SET {set_clause}
                WHERE id = %s AND user_id = %s
                RETURNING id, name, skill_type, current_progress, target_total, daily_goal, created_at""",
            params,
        )
        r = cur.fetchone()
    if r is None:
        raise HTTPException(404, "计划不存在")
    return SkillPlanOut(id=r[0], name=r[1], skill_type=r[2], current_progress=r[3],
                        target_total=r[4], daily_goal=r[5], created_at=r[6])


@skill_router.post("/{skill_id}/checkin", status_code=201)
def checkin_skill(skill_id: int, user: UserOut = Depends(get_current_user)):
    """今日打卡（重复点击取消）"""
    today = date_type.today()
    with get_cursor(commit=True) as cur:
        # 验证归属
        cur.execute("SELECT id, target_total, current_progress FROM skill_plans WHERE id = %s AND user_id = %s", (skill_id, user.id))
        plan = cur.fetchone()
        if plan is None:
            raise HTTPException(404, "计划不存在")
        # 检查是否已打卡
        cur.execute("SELECT id FROM skill_checkins WHERE skill_id = %s AND checkin_date = %s", (skill_id, today))
        existing = cur.fetchone()
        if existing:
            # 取消打卡
            cur.execute("DELETE FROM skill_checkins WHERE id = %s", (existing[0],))
            if plan[1] > 0:
                cur.execute("UPDATE skill_plans SET current_progress = GREATEST(0, current_progress - 1) WHERE id = %s", (skill_id,))
            return {"checked_in": False, "message": "已取消打卡"}
        else:
            # 打卡
            cur.execute(
                "INSERT INTO skill_checkins (skill_id, user_id, checkin_date) VALUES (%s, %s, %s)",
                (skill_id, user.id, today),
            )
            if plan[1] > 0 and plan[2] < plan[1]:
                cur.execute("UPDATE skill_plans SET current_progress = current_progress + 1 WHERE id = %s", (skill_id,))
            return {"checked_in": True, "message": "打卡成功"}


@skill_router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: int, user: UserOut = Depends(get_current_user)):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM skill_plans WHERE id = %s AND user_id = %s", (skill_id, user.id))
        if cur.rowcount == 0:
            raise HTTPException(404, "计划不存在")


# ═══════════════════════════════════════
# 用户设置
# ═══════════════════════════════════════
settings_router = APIRouter(prefix="/api/settings", tags=["用户设置"])


@settings_router.get("", response_model=UserSettingsOut)
def get_settings(user: UserOut = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            """SELECT unemployment_start, monthly_budget, savings FROM user_settings WHERE user_id = %s""",
            (user.id,),
        )
        r = cur.fetchone()
        if r is None:
            return UserSettingsOut(unemployment_start=None, monthly_budget=5000, savings=50000)
    return UserSettingsOut(unemployment_start=r[0], monthly_budget=float(r[1]), savings=float(r[2]))


@settings_router.put("")
def update_settings(body: UserSettingsUpdate, user: UserOut = Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        return {"message": "无更新"}
    columns = list(updates.keys())
    values = list(updates.values())
    col_list = ", ".join(columns)
    val_placeholders = ", ".join(["%s"] * len(columns))
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns)
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"""INSERT INTO user_settings (user_id, {col_list})
                VALUES (%s, {val_placeholders})
                ON CONFLICT (user_id) DO UPDATE SET {set_clause}""",
            [user.id] + values,
        )
    return {"message": "设置已更新"}


# ═══════════════════════════════════════
# 订阅
# ═══════════════════════════════════════
subscribe_router = APIRouter(prefix="/api/subscribe", tags=["订阅"])


@subscribe_router.post("", response_model=StandardResponse)
def subscribe(body: SubscribeRequest):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO subscribers (email) VALUES (%s)
               ON CONFLICT (email) DO UPDATE SET is_active = TRUE
               RETURNING id""",
            (body.email,),
        )
        _ = cur.fetchone()
    return StandardResponse(success=True, message="订阅成功！每周一将为你发送就业简报。")


# ═══════════════════════════════════════
# 反馈
# ═══════════════════════════════════════
feedback_router = APIRouter(prefix="/api/feedback", tags=["反馈"])


@feedback_router.post("", response_model=StandardResponse, status_code=201)
def submit_feedback(body: FeedbackRequest):
    """匿名反馈（无需登录）"""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO feedback (mood, message) VALUES (%s, %s) RETURNING id",
            (body.mood, body.message or ""),
        )
        _ = cur.fetchone()
    return StandardResponse(success=True, message="感谢你的反馈！")
