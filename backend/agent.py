"""
学习 Agent：题目生成与答案评估。
使用 LangChain + LLM，当 LLM 不可用时回退到本地题库。
"""

import json
import logging
import random
from typing import Optional

from pydantic import SecretStr

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LangChain 集成
# ---------------------------------------------------------------------------

_llm_available = None
_llm = None


def _try_init_llm():
    """尝试初始化 LangChain LLM，失败时标记为不可用。"""
    global _llm_available, _llm
    if _llm_available is not None:
        return _llm_available

    try:
        import os
        from pathlib import Path

        from dotenv import load_dotenv
        from langchain_openai import ChatOpenAI

        # 加载 .env 文件（优先于系统环境变量）
        env_path = Path(__file__).resolve().parent / ".env"
        load_dotenv(dotenv_path=env_path, override=True)

        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
            "ANTHROPIC_AUTH_TOKEN"
        )
        base_url = os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com"

        if not api_key:
            logger.warning("No API key found, falling back to local question bank")
            _llm_available = False
            return False

        _llm = ChatOpenAI(
            model=os.environ.get("LLM_MODEL", "deepseek-chat"),
            api_key=SecretStr(api_key),
            base_url=base_url,
            temperature=0.7,
        )
        _llm_available = True
        logger.info("LangChain LLM initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize LangChain LLM: {e}, falling back")
        _llm_available = False
        return False


def _try_langchain_question(
    subject: str, grade: int, kp_name: str, difficulty: str
) -> Optional[dict]:
    """尝试使用 LangChain 生成题目。"""
    if not _try_init_llm():
        return None

    difficulty_label = {
        "basic": "基础",
        "intermediate": "进阶",
        "advanced": "高阶",
    }.get(difficulty, difficulty)

    prompt = f"""你是一个智能出题老师。请为{subject}科目、{grade}年级的学生生成一道关于"{kp_name}"的{difficulty_label}难度的选择题。

要求：
1. 题目必须是选择题，4个选项 A、B、C、D
2. 返回严格的 JSON 格式，不要包含其他文字
3. JSON 格式：{{"question": "题目文本", "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "简短解析"}}
"""

    try:
        from langchain_core.messages import HumanMessage

        response = _llm.invoke([HumanMessage(content=prompt)])
        result = response.content

        # 尝试解析 JSON
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            result = result.rsplit("```", 1)[0]
        result = result.strip()

        data = json.loads(result)
        return {
            "question": data["question"],
            "options": data["options"],
            "answer": data["answer"].upper().strip(),
            "explanation": data.get("explanation", ""),
        }
    except Exception as e:
        logger.warning(f"LangChain question generation failed: {e}")
        return None


def _try_langchain_evaluation(
    subject: str,
    grade: int,
    kp_name: str,
    difficulty: str,
    question: str,
    options: dict,
    user_answer: str,
    correct_answer: str,
) -> Optional[dict]:
    """尝试使用 LangChain 评估答案。"""
    if not _try_init_llm():
        return None

    options_text = "\n".join([f"{k}. {v}" for k, v in options.items()])

    prompt = f"""你是一个智能学习评估助手。请评估学生的答案是否正确。

题目（{subject}，{grade}年级，{kp_name}）：
{question}

选项：
{options_text}

标准答案：{correct_answer}
学生答案：{user_answer}

请判断学生的答案是否正确（考虑答案字母大小写），并给出简短评价。
返回严格的 JSON 格式：{{"correct": true/false, "explanation": "评价文字"}}
"""

    try:
        from langchain_core.messages import HumanMessage

        response = _llm.invoke([HumanMessage(content=prompt)])
        result = response.content

        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            result = result.rsplit("```", 1)[0]
        result = result.strip()

        data = json.loads(result)
        return {"passed": data["correct"], "explanation": data.get("explanation", "")}
    except Exception as e:
        logger.warning(f"LangChain evaluation failed: {e}")
        return None


# ---------------------------------------------------------------------------
# 本地题库（降级方案）
# ---------------------------------------------------------------------------

DIFFICULTY_LABELS = {"basic": "基础", "intermediate": "进阶", "advanced": "高阶"}
DIFFICULTY_LEVELS = ["basic", "intermediate", "advanced"]

_question_cache: dict = {}


def _get_question_bank(subject: str, grade: int) -> dict:
    """获取或生成某个科目年级的本地题库。"""
    cache_key = f"{subject}_{grade}"
    if cache_key in _question_cache:
        return _question_cache[cache_key]
    bank = _generate_question_bank(subject, grade)
    _question_cache[cache_key] = bank
    return bank


def _generate_question_bank(subject: str, grade: int) -> dict:
    """为指定科目和年级生成题库。"""
    from syllabus import get_syllabus

    kps = get_syllabus(subject, grade)
    bank = {}

    for kp in kps:
        kp_id = kp["id"]
        kp_name = kp["name"]
        bank[kp_id] = {}
        for diff in DIFFICULTY_LEVELS:
            questions = _generate_questions(subject, grade, kp_name, diff, count=5)
            bank[kp_id][diff] = questions

    return bank


def _generate_questions(
    subject: str, grade: int, kp_name: str, difficulty: str, count: int = 5
) -> list:
    """生成指定条件的题目列表。"""
    generator_name = f"_gen_{subject}_{difficulty}"
    generator = globals().get(generator_name) or globals().get(f"_gen_{subject}")
    if generator:
        return generator(grade, kp_name, count)


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------


def generate_question(subject: str, grade: int, kp_id: int, difficulty: str) -> dict:
    """生成一道题目。先尝试 LangChain，失败则使用本地题库。"""
    from syllabus import get_knowledge_point

    kp = get_knowledge_point(subject, grade, kp_id)
    kp_name = kp["name"] if kp else ""

    # 尝试 LangChain
    result = _try_langchain_question(subject, grade, kp_name, difficulty)
    if result:
        return result

    # 回退到本地题库
    bank = _get_question_bank(subject, grade)
    if kp_id in bank and difficulty in bank[kp_id] and bank[kp_id][difficulty]:
        return random.choice(bank[kp_id][difficulty])


def evaluate_answer(
    subject: str,
    grade: int,
    kp_id: int,
    difficulty: str,
    question: str,
    options: dict,
    user_answer: str,
    correct_answer: str,
) -> dict:
    """评估用户答案。先尝试 LangChain，失败则本地判断。"""
    from syllabus import get_knowledge_point

    kp = get_knowledge_point(subject, grade, kp_id)
    kp_name = kp["name"] if kp else str(kp_id)

    # 尝试 LangChain 评估
    result = _try_langchain_evaluation(
        subject,
        grade,
        kp_name,
        difficulty,
        question,
        options,
        user_answer,
        correct_answer,
    )
    if result:
        return result

    # 本地评估：比较答案字母（忽略大小写和空白）
    passed = user_answer.strip().upper() == correct_answer.strip().upper()
    return {
        "passed": passed,
        "explanation": "回答正确！"
        if passed
        else f"回答错误。正确答案是 {correct_answer}。",
    }
