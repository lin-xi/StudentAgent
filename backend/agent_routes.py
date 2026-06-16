"""
智能出题与评估 API 路由。
"""
import json
import logging

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app import app
from agent import generate_question, generate_question_batch, evaluate_answer
from syllabus import get_syllabus
from database import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------

class GenerateQuestionRequest(BaseModel):
    subject: str = Field(..., description="科目，如 语文/数学/英语")
    grade: int = Field(..., ge=1, le=12, description="年级")
    kp_id: int = Field(..., ge=0, description="知识点 ID")
    difficulty: str = Field(..., pattern="^(basic|intermediate|advanced)$")
    question_index: int = Field(0, ge=0, le=20, description="同一知识点难度下的题号，用于生成不同题目")

class GenerateQuestionBatchRequest(BaseModel):
    subject: str = Field(..., description="科目，如 语文/数学/英语")
    grade: int = Field(..., ge=1, le=12, description="年级")
    kp_id: int = Field(..., ge=0, description="知识点 ID")
    difficulty: str = Field(..., pattern="^(basic|intermediate|advanced)$")

class EvaluateRequest(BaseModel):
    subject: str
    grade: int
    kp_id: int
    difficulty: str = Field(..., pattern="^(basic|intermediate|advanced)$")
    question: str
    options: dict
    user_answer: str
    correct_answer: str

# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@app.get("/api/syllabus", tags=["Learning"])
def get_syllabus_api(subject: str, grade: int):
    """获取指定科目和年级的大纲知识点。"""
    kps = get_syllabus(subject, grade)
    if not kps:
        raise HTTPException(status_code=404, detail="未找到该科目和年级的大纲")
    return {"knowledgePoints": kps}


@app.post("/api/generate-question", tags=["Learning"])
def api_generate_question(req: GenerateQuestionRequest):
    """生成一道题目。"""
    try:
        question = generate_question(
            req.subject, req.grade, req.kp_id, req.difficulty,
            question_index=req.question_index,
        )
        return question
    except Exception as e:
        logger.exception("Error generating question")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-question-batch", tags=["Learning"])
def api_generate_question_batch(req: GenerateQuestionBatchRequest):
    """生成 8 道题目（一次 LLM 调用），并将结果写入 questions 表。"""
    try:
        questions = generate_question_batch(req.subject, req.grade, req.kp_id, req.difficulty)

        # 获取知识点名称
        kps = get_syllabus(req.subject, req.grade)
        kp_name = kps[req.kp_id]["name"] if req.kp_id < len(kps) else ""

        # 写入数据库
        conn = get_connection()
        cursor = conn.cursor()

        for q in questions:
            cursor.execute("""
                INSERT INTO questions (subject, grade, kp, difficulty, question, answer, options, explanation, question_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                req.subject,
                req.grade,
                kp_name,
                req.difficulty,
                q.get("question", ""),
                q.get("answer", ""),
                json.dumps(q.get("options")) if q.get("options") else None,
                q.get("explanation", ""),
                q.get("type", "MCQ"),
            ))

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
            req.subject, req.grade, req.kp_id, req.difficulty,
            req.question, req.options, req.user_answer, req.correct_answer,
        )
        return result
    except Exception as e:
        logger.exception("Error evaluating answer")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok"}
