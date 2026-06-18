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
    subject: str, grade: str, kp_name: str, difficulty: str
) -> str:
    """生成出题批次缓存 key（一次 LLM 调用返回 8 题，整批缓存）。"""
    raw = f"batch:{subject}:{grade}:{kp_name}:{difficulty}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _make_eval_cache_key(
    subject: str,
    grade: str,
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
    subject: str, grade: str, kp_name: str, difficulty: str
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

    math_prompt = f"""
    【角色设定】
    你是一位拥有20年教龄的小学特级数学教师，曾获全国教学大赛一等奖，深谙儿童认知发展规律。你出题的特点是：题目生活化、思维有梯度、陷阱设置巧妙、能诊断学生真实水平。

    【任务】
    请为小学【{grade}年级】数学的知识点【{kp_name}】设计一套{difficulty}难度的应用题。

    【出题要求 - 必须逐条执行】

    1. 题目结构设计（共8题）
        - 基础巩固层 第1，2题：直接应用公式/概念，90%学生应能独立完成
        - 理解辨析层 第3，4题：设置1-2个"形似神不似"的干扰项，专门狙击常见错误
        - 综合应用层 第5，6题：结合2个以上知识点，或嵌入真实生活场景
        - 思维拓展层 第7，8题：开放性问题，允许不同解法，考察元认知
        - 每道题不能相同

    2. 每道题必须包含
        - 题目正文（语言生动，避免"小明小红"刻板情境）
        - 答案，详细的解题步骤
        - 教师批注和解析：
            * 这道考察的知识点的解析
            * 每个错误选项对应的真实思维路径
            * 这道题诊断的具体漏洞
            * 一句话点醒话术

    3. 返回严格的 JSON 格式，不要包含其他文字

    ```Json
    [
          {{"question": "题目正文1", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文2", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文3", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文4", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文5", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文6", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文7", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}},
          {{"question": "题目正文8", "type": "problem-solving", "answer": "解题步骤和答案", "explanation": "教师批注和解析"}}
      ]
      ```

     【自检】
     请你在生成题目后，逐条核对以下项目并输出结果：
     1. 解析是否分别说明了正确与错误的原因？若缺少任一项，请补充。
     2. 难度标签与题目实际难度是否匹配？若不匹配，请调整题干或选项。
    """

    english_prompt = f"""
    【角色设定】
    你是一位拥有25年教龄的小学英语特级教师，全国英语教学大赛金奖得主，人教版/外研版教材核心编委。你深谙中国小学生英语学习的母语负迁移规律，擅长用选择题精准"钓鱼"——每个错误选项都对应一个真实的错误思维路径。你的题目特点是：语境真实、干扰项有心理学依据、题干本身就是语言输入。

    【任务】
    请为小学【{grade}年级】英语的知识点【{kp_name}】设计一套{difficulty}难度的选择题诊断练习。

    【出题铁律 - 逐条执行】


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
    - 教师批注和解析：
            * 这道考察的知识点的解析
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
        {{"question": "题目正文1", "type": "MCQ", "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文2", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文3", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文4", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文5", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文6", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文7", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文8", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}}
    ]

    【自检】
    请你在生成题目后，逐条核对以下项目并输出结果：
    1. A、B、C、D四个答案是否都一样
    2. 选项中是否包含正确答案，如果不在，更换选项
    3. 题目中是否包含英语的问题
    4. 难度标签与题目实际难度是否匹配？若不匹配，请调整题干或选项。
    """

    ruankao_prompt = f"""
    【角色设定】
    你是一位拥有多年教龄的软考【高级系统架构师】特级教师，精通考试命题规律、考点分布及常见学生误区。

    【任务】
    请为软考【高级系统架构师】的知识点【{kp_name}】设计一套{difficulty}难度的选择题诊断练习。

    【出题铁律 - 逐条执行】
    1. 题目结构（共8题，全部为6单项选择，每题4个选项，2个应用题。）
        □ 考察"{kp_name}"核心概念、定义、区分度高的基础知识，3道选择题
        □ 考察"{kp_name}"理解应用、简单场景分析、易混淆点对比，3道选择题
        □ 考查"{kp_name}"综合分析、架构选型决策、多知识点融合、隐含陷阱，2道应用题

    2. 题干要求：
       - 题干必须自包含、无歧义。

    4. 选项设计：
        - 每个题目提供 A、B、C、D 四个选项。
        - 正确项必须唯一，且必须出现在选项中
        - 干扰项应源于常见错误理解或真实考试中出现的混淆点，不能明显荒谬。
        - 选项长度尽量保持一致，不出现“以上都对/都错”等绝对化表述（除非考点就是这种逻辑）。

    5. 教师批注和解析：
        - 每题后给出教师批注和解析。
        - 批注和解析必须包含：
            - 这道考察的知识点的解析
            - 为什么正确（对应哪个原理/教材原文/架构原则）
            - 为什么错误（指出每个错误选项的错因或典型误区）

    6. 返回严格的 JSON 格式，不要包含其他文字
      ```JSON
      [
        {{"question": "题目正文1", "type": "MCQ", "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文2", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文3", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文4", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文5", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文6", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文7", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}},
        {{"question": "题目正文8", "type": "MCQ",  "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}}, "answer": "A/B/C/D中的正确选项字母", "explanation": "教师批注和解析"}}
    ]
    ```

    【自检】
    请你在生成题目后，逐条核对以下项目并输出结果：
    □ 每道题题干是否包含业务场景？若没有，请修改。
    □ 选项中是否包含正确答案，如果不在，更换选项
    □ 解析是否分别说明了正确与错误的原因？若缺少任一项，请补充。
    □ 难度标签与题目实际难度是否匹配？若不匹配，请调整题干或选项。

    """

    try:
        from langchain_core.messages import HumanMessage

        subject_prompt = ""
        if subject == "数学":
            subject_prompt = math_prompt
        elif subject == "英语":
            subject_prompt = english_prompt
        elif subject == "软考":
            subject_prompt = ruankao_prompt

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
    grade: str,
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

请判断学生的答案是否正确（考虑答案字母大小写），并给出简短解析。
解析必须包含：
- 当前考察的知识点的简介
- 为什么正确（对应哪个原理/教材原文/架构原则）
- 为什么错误（指出每个错误选项的错因或典型误区）
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


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------


def generate_question_batch(
    subject: str, grade: str, kp_id: str, difficulty: str
) -> list[dict]:
    """生成 8 道题目。先尝试 LangChain，失败则使用本地题库。"""
    # 尝试 LangChain 批量生成
    result = _try_langchain_question_batch(subject, grade, kp_id, difficulty)
    if result:
        return result
    return []


def evaluate_answer(
    subject: str,
    grade: str,
    kp_id: str,
    difficulty: str,
    question: str,
    options: dict,
    user_answer: str,
    correct_answer: str,
) -> dict:
    """评估用户答案。先尝试 LangChain，失败则本地判断。"""

    # 应用题模式（无选项）：文本相似度比较
    if not options or options == {}:
        # 应用题模式（无选项）
        # 选择题模式：尝试 LangChain 评估
        result = _try_langchain_evaluation(
            subject,
            grade,
            kp_id,
            difficulty,
            question,
            options,
            user_answer,
            correct_answer,
        )
        if result:
            return result

    else:
        # 本地评估：比较答案字母（忽略大小写和空白）
        passed = user_answer.strip().upper() == correct_answer.strip().upper()

        return {
            "passed": passed,
            "explanation": "回答正确！" if passed else f"参考答案：{correct_answer}",
        }
