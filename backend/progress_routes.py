"""
用户学习进度 API 路由（按难度等级分记录）。
"""

import logging
from typing import Any, Optional

from app import app
from database import get_connection
from fastapi import Cookie, HTTPException, Request
from pydantic import BaseModel, Field
from utils import aes_decrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------


class SaveProgressRequest(BaseModel):
    subject_id: int = Field(..., description="学科 ID")
    grade_id: int = Field(..., description="年级 ID")
    course_id: int = Field(..., description="课程 ID/KP ID")
    kp_level: str = Field(..., description="难度等级：basic/intermediate/advanced")
    check_in: bool = Field(..., description="是否完成打卡")
    wrong_count: int = Field(0, ge=0, description="错题数量")
    check_in_date: Optional[str] = Field(None, description="完成时间 YYYY-MM-DD")


class ProgressResponse(BaseModel):
    id: int
    kp: str
    subject_id: int
    grade_id: int
    course_id: int
    kp_level: int
    check_in: bool
    wrong_count: int
    check_in_date: Optional[str]


class ProgressListResponse(BaseModel):
    code: int
    error: Optional[str]
    data: Any


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------


@app.get("/api/progress", response_model=ProgressListResponse, tags=["Progress"])
def get_progress(request: Request, session_token: Optional[str] = Cookie(None)):
    """
    获取用户学习进度列表。
    需要提供 user_id（从认证上下文获取，当前从 header 传递）
    可选 subject_id 和 grade_id 参数用于过滤
    """
    subject_id = request.query_params.get("subject_id")
    grade_id = request.query_params.get("grade_id")

    user_id = ""
    if not session_token:
        raise HTTPException(status_code=401, detail="未登录")
    else:
        user_id = int(aes_decrypt(session_token))

    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if user_id and subject_id and grade_id:
            cursor.execute(
                """
                SELECT c.id, c.kp, p.subject_id, p.grade_id, p.kp_level, p.check_in, p.wrong_count, p.check_in_date
                                FROM courses c
                                left join progress p on p.user_id = %s and p.course_id = c.id
                                WHERE c.subject_id = %s and c.grade_id =%s
                                order by c.id, p.kp_level;
                """,
                (user_id, subject_id, grade_id),
            )

            rows = cursor.fetchall()
            progress_list = [
                ProgressResponse(
                    id=row["id"],
                    subject_id=int(row["subject_id"]) if row["subject_id"] else 0,
                    grade_id=int(row["grade_id"]) if row["grade_id"] else 0,
                    course_id=int(row["id"]) if row["id"] else 0,
                    kp=row["kp"],
                    kp_level=int(row["kp_level"]) if row["kp_level"] else 0,
                    check_in=bool(row["check_in"]),
                    wrong_count=int(row["wrong_count"]) if row["wrong_count"] else 0,
                    check_in_date=row["check_in_date"],
                )
                for row in rows
            ]
            return ProgressListResponse(code=200, error="", data=progress_list)
        else:
            return ProgressListResponse(code=400, error="参数错误", data=[])
    except Exception as e:
        logger.exception("Error getting progress")
        return ProgressListResponse(code=500, error=str(e), data=[])
    finally:
        cursor.close()
        conn.close()


@app.post("/api/saveProgress", response_model=ProgressListResponse, tags=["Progress"])
def save_progress(
    req: SaveProgressRequest, session_token: Optional[str] = Cookie(None)
):
    """保存用户学习进度（单个 KP 的难度等级进度）。"""
    user_id = ""
    if session_token:
        user_id = int(aes_decrypt(session_token))

    if not user_id:
        return ProgressListResponse(code=401, error="权限验证错误", data={})

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 使用 INSERT ... ON DUPLICATE KEY UPDATE 语法
        cursor.execute(
            """
            INSERT INTO progress (
                user_id, subject_id, grade_id, course_id, kp_level,
                check_in, wrong_count, check_in_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                kp_level = VALUES(kp_level),
                check_in = VALUES(check_in),
                wrong_count = VALUES(wrong_count),
                check_in_date = VALUES(check_in_date)
        """,
            (
                user_id,
                req.subject_id,
                req.grade_id,
                req.course_id,
                req.kp_level,
                req.check_in,
                req.wrong_count,
                req.check_in_date,
            ),
        )
        conn.commit()
        return ProgressListResponse(code=200, error="", data={})

    except Exception as e:
        logger.exception("Error saving progress")
        return ProgressListResponse(code=500, error=str(e), data={})
    finally:
        cursor.close()
        conn.close()
