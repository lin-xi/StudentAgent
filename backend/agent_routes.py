"""
智能出题与评估 API 路由。
"""

import json
import logging

from agent import evaluate_answer, generate_question_batch
from app import app
from database import get_connection
from fastapi import HTTPException
from pydantic import BaseModel, Field
from syllabus import get_syllabus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------
class GenerateQuestionBatchRequest(BaseModel):
    subject: str = Field(..., description="科目，如 语文/数学/英语")
    grade: str = Field(..., description="年级")
    kp_id: str = Field(..., description="知识点")
    difficulty: str = Field(..., pattern="^(基础|进阶|高阶)$")


class EvaluateRequest(BaseModel):
    subject: str
    grade: str
    kp_id: str
    difficulty: str = Field(..., pattern="^(基础|进阶|高阶)$")
    question: str
    options: dict
    user_answer: str
    correct_answer: str


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------


@app.get("/api/syllabus", tags=["Learning"])
def get_syllabus_api(subject_id: int, grade_id: int):
    """获取指定学科和年级的大纲知识点（通过 ID 查询）。"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 从数据库查询学科名称和年级名称
        cursor.execute("SELECT name FROM subjects WHERE id = %s", (subject_id,))
        subject_row = cursor.fetchone()
        if not subject_row:
            raise HTTPException(status_code=404, detail="未找到该学科")
        subject_name = subject_row["name"]

        cursor.execute("SELECT name FROM grades WHERE id = %s", (grade_id,))
        grade_row = cursor.fetchone()
        if not grade_row:
            raise HTTPException(status_code=404, detail="未找到该年级")
        grade_name = grade_row["name"]

        # 调用原有的 get_syllabus 函数
        kps = get_syllabus(subject_name, grade_name)
        if not kps:
            raise HTTPException(status_code=404, detail="未找到该学科年级的大纲")
        return {"knowledgePoints": kps}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting syllabus")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.post("/api/generate-question-batch", tags=["Learning"])
def api_generate_question_batch(req: GenerateQuestionBatchRequest):
    """生成 8 道题目（一次 LLM 调用），并将结果写入 questions 表。"""
    try:
        questions = generate_question_batch(
            req.subject, req.grade, req.kp_id, req.difficulty
        )
        # 写入数据库
        conn = get_connection()
        cursor = conn.cursor()

        for q in questions:
            cursor.execute(
                """
                INSERT INTO questions (subject, grade, kp, difficulty, question, answer, options, explanation, question_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    req.subject,
                    req.grade,
                    req.kp_id,
                    req.difficulty,
                    q.get("question", ""),
                    q.get("answer", ""),
                    json.dumps(q.get("options")) if q.get("options") else None,
                    q.get("explanation", ""),
                    q.get("type", "MCQ"),
                ),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return {"questions": questions}
    except Exception as e:
        logger.exception("Error generating question batch")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate", tags=["Learning"])
def api_evaluate(req: EvaluateRequest):
    """评估用户答案。"""
    try:
        result = evaluate_answer(
            req.subject,
            req.grade,
            req.kp_id,
            req.difficulty,
            req.question,
            req.options,
            req.user_answer,
            req.correct_answer,
        )
        return result
    except Exception as e:
        logger.exception("Error evaluating answer")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok"}
