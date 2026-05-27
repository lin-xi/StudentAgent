"""
学习 Agent：题目生成与答案评估。
使用 LangChain + LLM，当 LLM 不可用时回退到本地题库。
"""

import hashlib
import json
import logging
import random
from typing import Any, Optional

from pydantic import SecretStr

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LangChain 集成
# ---------------------------------------------------------------------------

_llm_available = None
_llm = None

# ---------------------------------------------------------------------------
# LLM 缓存（避免重复调用大模型）
# ---------------------------------------------------------------------------

_llm_cache: dict[str, Any] = {}
_LLM_CACHE_MAX = 256


def _cache_get(key: str) -> Optional[Any]:
    """从缓存中取值，同时将命中项移到末尾模拟 LRU。"""
    val = _llm_cache.get(key)
    if val is not None:
        del _llm_cache[key]
        _llm_cache[key] = val
    return val


def _cache_set(key: str, value: Any) -> None:
    """写入缓存，超限时淘汰最旧条目。"""
    if len(_llm_cache) >= _LLM_CACHE_MAX:
        oldest = next(iter(_llm_cache))
        del _llm_cache[oldest]
    _llm_cache[key] = value


def _make_question_batch_cache_key(
    subject: str, grade: int, kp_name: str, difficulty: str
) -> str:
    """生成出题批次缓存 key（一次 LLM 调用返回 8 题，整批缓存）。"""
    raw = f"batch:{subject}:{grade}:{kp_name}:{difficulty}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _make_eval_cache_key(
    subject: str,
    grade: int,
    kp_name: str,
    difficulty: str,
    question: str,
    user_answer: str,
    correct_answer: str,
) -> str:
    """生成评估缓存 key。"""
    raw = f"e:{subject}:{grade}:{kp_name}:{difficulty}:{question}:{user_answer}:{correct_answer}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


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


def _try_langchain_question_batch(
    subject: str, grade: int, kp_name: str, difficulty: str
) -> Optional[list[dict]]:
    """一次 LLM 调用生成 8 道题目（带缓存）。"""
    if not _try_init_llm():
        return None

    # ---- 1. 查缓存 ----
    cache_key = _make_question_batch_cache_key(subject, grade, kp_name, difficulty)
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("Q batch cache HIT %s/%s", subject, kp_name)
        return cached

    # ---- 2. 未命中，调大模型 ----
    logger.info("Q batch cache MISS %s/%s — calling LLM", subject, kp_name)

    difficulty_label = {
        "basic": "基础",
        "intermediate": "进阶",
        "advanced": "高阶",
    }.get(difficulty, difficulty)

    math_prompt = f"""
    【角色设定】
    你是一位拥有20年教龄的小学特级数学教师，曾获全国教学大赛一等奖，深谙儿童认知发展规律。你出题的特点是：题目生活化、思维有梯度、陷阱设置巧妙、能诊断学生真实水平。

    【任务】
    请为小学【{grade}年级】数学的知识点【{kp_name}】设计一套{difficulty_label}难度的应用题。

    【出题要求 - 必须逐条执行】

    1. 学情诊断前置
        - 先分析该知识点学生的3个典型认知误区
        - 列出该年级学生已具备的前置知识
        - 说明本题要检测的核心能力（知识记忆/理解应用/迁移创新）

    2. 题目结构设计（共8题）
        - 基础巩固层 第1，2题：直接应用公式/概念，90%学生应能独立完成
        - 理解辨析层 第3，4题：设置1-2个"形似神不似"的干扰项，专门狙击常见错误
        - 综合应用层 第5，6题：结合2个以上知识点，或嵌入真实生活场景
        - 思维拓展层 第7，8题：开放性问题，允许不同解法，考察元认知
        - 每道题不能相同

    3. 每道题必须包含
        - 题目正文（语言生动，避免"小明小红"刻板情境）
        - 答案，详细的解题步骤
        - 金牌批注：
            * 每个错误选项对应的真实思维路径
            * 这道题诊断的具体漏洞
            * 一句话点醒话术

    4. 返回严格的 JSON 格式，不要包含其他文字
    5. JSON 格式：[
        {{"question": "题目正文1", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文2", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文3", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文4", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文5", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文6", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文7", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}},
        {{"question": "题目正文8", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和简短解析"}}
    ]
    """

    english_prompt = f"""
    【角色设定】
    你是一位拥有25年教龄的小学英语特级教师，全国英语教学大赛金奖得主，人教版/外研版教材核心编委。你深谙中国小学生英语学习的母语负迁移规律，擅长用选择题精准"钓鱼"——每个错误选项都对应一个真实的错误思维路径。你的题目特点是：语境真实、干扰项有心理学依据、题干本身就是语言输入。

    【任务】
    请为小学【{grade}年级】英语的知识点【{kp_name}】设计一套{difficulty_label}难度的选择题诊断练习。

    【出题铁律 - 逐条执行】

    1. 学情诊断前置（先输出这部分）
        - "{kp_name}"中国小学生的3个母语负迁移错误
        - 学习该知识点前，学生必须已掌握的2个前置知识
        - 该知识点在课标中的能力层级要求（一级/二级/三级）

    2. 题目结构（共8题，全部为单项选择，每题4个选项）
        □ 形式识别层（2题）：考察"{kp_name}"的形式本身
            - 选项设计为"形式辨析"型
            - 至少1题含视觉/听觉陷阱（如：形近词、同音词）

        □ 语境辨析层（2题）：嵌入真实对话/短文片段
            - 题干为20-30词的微语境
            - 错误选项对应"似是而非"的真实错误
            - 至少2题的错误选项来自中文直译思维

        □ 语用得体层（2题）：考察场合、身份、礼貌程度
            - 错误选项为"语法对但不得体"

        □ 综合陷阱层（1题）："金牌陷阱题"
            - "{kp_name}"与其他知识点交叉
            - 4个选项都看似合理
            - 预估错误率60%

    3. 每道题必须包含
    - 题目正文（语言生动，真实场景：课堂/家庭/操场/食堂/春游）
    - 选项A/B/C/D（正确选项位置随机）
    - 答案，A/B/C/D中的正确选项字母
    - 金牌批注：
            * 每个错误选项对应的真实思维路径
            * 这道题诊断的具体漏洞
            * 一句话点醒话术

    4. 干扰项心理学模板
    - 选项A：机械操练错误（漏形式标记）
    - 选项B：母语直译陷阱（中式英语）
    - 选项C：过度泛化错误（规则滥用）
    - 选项D：正确答案
    - 至少3题打破"三长一短"等应试技巧

    5. 语境真实性
    - 人名：Mike, Sarah, Wu Binbin, Chen Jie, Robin等教材人物
    - 场景：小学生真实生活
    - 拒绝真空语法题

    6. 返回严格的 JSON 格式，不要包含其他文字
    7. JSON 格式：[
        {{"question": "题目正文1", "type": "MCQ", "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文2", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文3", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文4", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文5", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文6", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文7", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}},
        {{"question": "题目正文8", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "金牌批注和简短解析"}}
    ]

    【自检】
    1. A、B、C、D四个答案是否都一样
    2. 题目中是否包含英语的问题
    """

    try:
        from langchain_core.messages import HumanMessage

        subject_prompt = math_prompt if subject == "数学" else english_prompt
        response = _llm.invoke([HumanMessage(content=subject_prompt)])
        result = response.content

        # 尝试解析 JSON
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            result = result.rsplit("```", 1)[0]
        result = result.strip()

        data = json.loads(result)
        if not isinstance(data, list):
            logger.warning("LLM did not return a list, got %s", type(data))
            return None

        questions = []
        for item in data:
            q = {
                "question": item["question"],
                "type": item.get("type", "MCQ"),
                "answer": item["answer"].strip(),
                "explanation": item.get("explanation", ""),
            }
            if "options" in item and item["options"]:
                q["options"] = item["options"]
            questions.append(q)

        # ---- 3. 写缓存 ----
        _cache_set(cache_key, questions)
        return questions
    except Exception as e:
        logger.warning(f"LangChain question batch generation failed: {e}")
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
    """尝试使用 LangChain 评估答案（带缓存）。"""
    if not _try_init_llm():
        return None

    # ---- 1. 查缓存 ----
    cache_key = _make_eval_cache_key(
        subject, grade, kp_name, difficulty, question, user_answer, correct_answer
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("E cache HIT %s/%s", subject, kp_name)
        return cached

    # ---- 2. 未命中，调大模型 ----
    logger.info("E cache MISS %s/%s — calling LLM", subject, kp_name)

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
        eval_data = {
            "passed": data["correct"],
            "explanation": data.get("explanation", ""),
        }

        # ---- 3. 写缓存 ----
        _cache_set(cache_key, eval_data)
        return eval_data
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


def generate_question(
    subject: str, grade: int, kp_id: int, difficulty: str, question_index: int = 0
) -> dict:
    """生成一道题目（用于重试错题）。先尝试 LangChain，失败则使用本地题库。"""
    from syllabus import get_knowledge_point

    kp = get_knowledge_point(subject, grade, kp_id)
    kp_name = kp["name"] if kp else ""

    # 尝试 LangChain — 用 question_index 生成不同题目
    result = _try_langchain_question_batch(subject, grade, kp_name, difficulty)
    if result and question_index < len(result):
        return result[question_index]

    # 回退到本地题库
    bank = _get_question_bank(subject, grade)
    if kp_id in bank and difficulty in bank[kp_id] and bank[kp_id][difficulty]:
        return random.choice(bank[kp_id][difficulty])
    return {}


def generate_question_batch(
    subject: str, grade: int, kp_id: int, difficulty: str
) -> list[dict]:
    """生成 8 道题目。先尝试 LangChain，失败则使用本地题库。"""
    from syllabus import get_knowledge_point

    kp = get_knowledge_point(subject, grade, kp_id)
    kp_name = kp["name"] if kp else ""

    # 尝试 LangChain 批量生成
    result = _try_langchain_question_batch(subject, grade, kp_name, difficulty)
    if result:
        return result

    # 回退到本地题库（逐题随机选取）
    bank = _get_question_bank(subject, grade)
    questions = []
    if kp_id in bank and difficulty in bank[kp_id] and bank[kp_id][difficulty]:
        pool = bank[kp_id][difficulty]
        for i in range(min(8, len(pool))):
            questions.append(random.choice(pool))
    return questions


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

    # 应用题模式（无选项）：文本相似度比较
    if not options or options == {}:
        norm_answer = correct_answer.strip().lower()
        norm_user = user_answer.strip().lower()
        # 检查学生答案是否包含正确答案的关键数字/词
        passed = norm_user == norm_answer or (
            len(norm_answer) > 5 and norm_answer in norm_user
        )
        return {
            "passed": passed,
            "explanation": "回答正确！" if passed else f"参考答案：{correct_answer}",
        }

    # 选择题模式：尝试 LangChain 评估
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
