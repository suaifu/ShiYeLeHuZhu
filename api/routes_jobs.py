"""
重启 · 失业互助平台 - 求职追踪路由
GET    /api/jobs          列表（支持状态筛选+分页）
POST   /api/jobs          新增
PUT    /api/jobs/{id}     编辑
DELETE /api/jobs/{id}     删除
GET    /api/jobs/stats    统计
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database import get_cursor
from auth import get_current_user
from models import UserOut, JobApplicationCreate, JobApplicationUpdate, JobApplicationOut
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["求职追踪"])


@router.get("", response_model=list[JobApplicationOut])
def list_jobs(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: UserOut = Depends(get_current_user),
):
    """获取求职列表（支持状态筛选+分页）"""
    offset = (page - 1) * page_size
    with get_cursor() as cur:
        if status:
            cur.execute(
                """SELECT id, company, position, salary, status, apply_date, follow_date, feedback, created_at
                   FROM job_applications WHERE user_id = %s AND status = %s
                   ORDER BY apply_date DESC NULLS LAST LIMIT %s OFFSET %s""",
                (user.id, status, page_size, offset),
            )
        else:
            cur.execute(
                """SELECT id, company, position, salary, status, apply_date, follow_date, feedback, created_at
                   FROM job_applications WHERE user_id = %s
                   ORDER BY apply_date DESC NULLS LAST LIMIT %s OFFSET %s""",
                (user.id, page_size, offset),
            )
        rows = cur.fetchall()
    return [JobApplicationOut(
        id=r[0], company=r[1], position=r[2], salary=r[3], status=r[4],
        apply_date=r[5], follow_date=r[6], feedback=r[7], created_at=r[8]
    ) for r in rows]


@router.get("/stats")
def job_stats(user: UserOut = Depends(get_current_user)):
    """求职统计：各状态数量"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT status, COUNT(*) FROM job_applications
               WHERE user_id = %s GROUP BY status""",
            (user.id,),
        )
        rows = cur.fetchall()
    stats = {"投递": 0, "笔试": 0, "面试": 0, "Offer": 0, "拒绝": 0, "已放弃": 0}
    for status, count in rows:
        stats[status] = count
    return stats


@router.post("", response_model=JobApplicationOut, status_code=201)
def create_job(body: JobApplicationCreate, user: UserOut = Depends(get_current_user)):
    """新增求职记录"""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO job_applications (user_id, company, position, salary, status, apply_date, follow_date, feedback)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id, company, position, salary, status, apply_date, follow_date, feedback, created_at""",
            (user.id, body.company, body.position, body.salary, body.status.value,
             body.apply_date, body.follow_date, body.feedback),
        )
        r = cur.fetchone()
    logger.info(f"求职记录新增: user={user.id} company={body.company} position={body.position}")
    return JobApplicationOut(
        id=r[0], company=r[1], position=r[2], salary=r[3], status=r[4],
        apply_date=r[5], follow_date=r[6], feedback=r[7], created_at=r[8]
    )


@router.put("/{job_id}", response_model=JobApplicationOut)
def update_job(job_id: int, body: JobApplicationUpdate, user: UserOut = Depends(get_current_user)):
    """编辑求职记录"""
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(400, "没有需要更新的字段")
    # status enum -> value
    if "status" in updates and hasattr(updates["status"], "value"):
        updates["status"] = updates["status"].value
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    params = list(updates.values()) + [job_id, user.id]
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"""UPDATE job_applications SET {set_clause}
                WHERE id = %s AND user_id = %s
                RETURNING id, company, position, salary, status, apply_date, follow_date, feedback, created_at""",
            params,
        )
        r = cur.fetchone()
    if r is None:
        raise HTTPException(404, "记录不存在")
    logger.info(f"求职记录更新: user={user.id} job_id={job_id} fields={list(updates.keys())}")
    return JobApplicationOut(
        id=r[0], company=r[1], position=r[2], salary=r[3], status=r[4],
        apply_date=r[5], follow_date=r[6], feedback=r[7], created_at=r[8]
    )


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, user: UserOut = Depends(get_current_user)):
    """删除求职记录"""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM job_applications WHERE id = %s AND user_id = %s",
            (job_id, user.id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "记录不存在")
    logger.info(f"求职记录删除: user={user.id} job_id={job_id}")
