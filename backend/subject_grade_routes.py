"""
学科和年级 API 路由。
"""

import logging
import traceback
from typing import Any, Optional

from app import app
from database import get_connection
from fastapi import Cookie, HTTPException
from pydantic import BaseModel
from utils import aes_decrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------------------


class SubjectResponse(BaseModel):
    id: int
    name: str


class ApiResponse(BaseModel):
    code: int
    error: str
    data: Any


class SubjectGradeRequest(BaseModel):
    subject: str
    subject_id: int
    grade: str  # 验证码 ID
    grade_id: int  # 滑动验证码值 (0-1)


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------


@app.get("/api/subjects", response_model=list[SubjectResponse], tags=["Subject/Grade"])
def get_subjects():
    """获取学科列表。"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, name FROM subjects ORDER BY id")
        subjects = cursor.fetchall()
        return [SubjectResponse(**s) for s in subjects]
    except Exception as e:
        logger.exception("Error getting subjects")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get(
    "/api/subjects/{subject_id}/grades",
    response_model=ApiResponse,
    tags=["Subject/Grade"],
)
def get_grades_by_subject(subject_id: int):
    """获取指定学科可选的年级列表。"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if subject_id:
            cursor.execute(
                "SELECT g.id, g.name FROM grades g JOIN subject_grade sg ON g.id = sg.grade_id WHERE sg.subject_id = %s ORDER BY g.id",
                (subject_id,),
            )
            grades = cursor.fetchall()
            return ApiResponse(code=200, error="", data=[{**g} for g in grades])
        else:
            return ApiResponse(
                code=200,
                error="",
                data=[],
            )
    except Exception as e:
        traceback.print_exc()
        logger.exception("Error getting grades")
        return ApiResponse(
            code=500,
            error=str(e),
            data=[],
        )
    finally:
        cursor.close()
        conn.close()


@app.post(
    "/api/save_subject_grade",
    response_model=ApiResponse,
    tags=["Save_Subject/Grade"],
)
def save_subject_grade(
    req: SubjectGradeRequest, session_token: Optional[str] = Cookie(None)
):

    user_id = ""
    if not session_token:
        raise HTTPException(status_code=401, detail="未登录")
    else:
        user_id = int(aes_decrypt(session_token))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if req.subject_id and req.grade_id and user_id:
            cursor.execute(
                """
            INSERT INTO user_subject_grade (subject_id, subject, grade_id, grade, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """,
                (req.subject_id, req.subject, req.grade_id, req.grade, user_id),
            )
            conn.commit()
            return ApiResponse(
                code=200,
                error="",
                data={
                    "subject_id": req.subject_id,
                    "subject": req.subject,
                    "grade_id": req.grade_id,
                    "grade": req.grade,
                    "user_id": user_id,
                },
            )
    except Exception as e:
        traceback.print_exc()

        return ApiResponse(
            code=500,
            error=str(e),
            data={},
        )
    finally:
        cursor.close()
        conn.close()
