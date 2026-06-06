<script setup>
import { ref, computed, watch } from "vue";
import { saveProgress, QUESTIONS_PER_ROUND } from "../db.js";
import {
    generateQuestion,
    generateQuestionBatch,
    evaluateAnswer,
} from "../api.js";
import ProgressMap from "./ProgressMap.vue";

const props = defineProps({
    progress: { type: Object, required: true },
    levelInfo: { type: Object, default: null },
});
const emit = defineEmits(["update"]);

const questions = ref([]);
const loading = ref(false);
const error = ref("");
const allChecked = ref(false);

const difficultyLabels = ["basic", "intermediate", "advanced"];
const currentKP = computed(
    () => props.progress.knowledgePoints[props.progress.currentKP] || null,
);
const currentDifficultyLabel = computed(
    () => difficultyLabels[props.progress.currentDifficulty],
);

const answeredCount = computed(
    () => questions.value.filter((q) => q.answered).length,
);
const passedCount = computed(
    () => questions.value.filter((q) => q.passed).length,
);
const allPassed = computed(
    () => allChecked.value && passedCount.value === questions.value.length,
);

// ---- 获取一轮题目 ----
async function fetchRound() {
    const kp = currentKP.value;
    if (!kp) return;

    loading.value = true;
    error.value = "";
    allChecked.value = false;

    try {
        const raw = await generateQuestionBatch(
            props.progress.subject,
            props.progress.grade,
            kp.id,
            currentDifficultyLabel.value,
        );
        questions.value = raw.map((q, i) => ({
            id: i,
            type: q.type || "MCQ",
            question: q.question,
            options: q.options || {},
            answer: q.answer,
            explanation: q.explanation || "",
            userAnswer: "",
            answered: false,
            evaluation: null,
            passed: false,
        }));
    } catch (e) {
        error.value = "获取题目失败，请检查后端服务是否启动。";
        console.error(e);
    } finally {
        loading.value = false;
    }
}

// ---- 回答某题（MCQ：点选项；应用题：输入文本后点提交）----
async function answerQuestion(qId, answer) {
    const q = questions.value.find((x) => x.id === qId);
    if (!q || q.answered) return;

    q.userAnswer = answer;
    q.answered = true;
    loading.value = true;

    try {
        const result = await evaluateAnswer(
            props.progress.subject,
            props.progress.grade,
            currentKP.value.id,
            currentDifficultyLabel.value,
            q.question,
            q.type === "MCQ" ? q.options : {},
            answer,
            q.answer,
        );
        q.evaluation = result;
        q.passed = result.passed;
    } catch {
        const passed =
            answer.trim().toUpperCase() === q.answer.trim().toUpperCase();
        q.evaluation = {
            passed,
            explanation: passed
                ? "回答正确！"
                : `回答错误。参考答案：${q.answer}`,
        };
        q.passed = passed;
    } finally {
        loading.value = false;
    }

    if (answeredCount.value === questions.value.length) {
        allChecked.value = true;
        if (allPassed.value) {
            await advanceDifficulty();
        }
    }
}

// ---- 晋级 ----
async function advanceDifficulty() {
    const p = { ...props.progress };
    const kp = p.knowledgePoints[p.currentKP];
    const diff = difficultyLabels[p.currentDifficulty];

    kp[diff] = true;

    if (diff === "advanced") {
        p.completedKPCount++;
        if (p.completedKPCount >= p.knowledgePoints.length) {
            p.overallComplete = true;
        } else {
            p.currentKP++;
            p.currentDifficulty = 0;
        }
    } else {
        p.currentDifficulty++;
    }

    await saveProgress(p);
    emit("update", p);
    questions.value = [];
    allChecked.value = false;
}

// ---- 重试错题 ----
async function retryWrong() {
    const wrong = questions.value.filter((q) => !q.passed);
    loading.value = true;
    allChecked.value = false;

    try {
        const results = await Promise.all(
            wrong.map((q) =>
                generateQuestion(
                    props.progress.subject,
                    props.progress.grade,
                    currentKP.value.id,
                    currentDifficultyLabel.value,
                    q.id,
                ),
            ),
        );
        for (let i = 0; i < wrong.length; i++) {
            const newQ = results[i];
            if (newQ) {
                wrong[i].question = newQ.question;
                wrong[i].options = newQ.options || {};
                wrong[i].answer = newQ.answer;
                wrong[i].explanation = newQ.explanation || "";
                wrong[i].userAnswer = "";
                wrong[i].answered = false;
                wrong[i].evaluation = null;
                wrong[i].passed = false;
            }
        }
    } catch {
        error.value = "重试获取题目失败";
    } finally {
        loading.value = false;
    }
}

// ---- 监听 ----
watch(
    () => [props.progress.currentKP, props.progress.currentDifficulty],
    () => {
        if (questions.value.length === 0 && !props.progress.overallComplete) {
            fetchRound();
        }
    },
    { immediate: true },
);

// ---- 选项样式（MCQ） ----
function optionClass(q, opt) {
    if (!q.answered) return {};
    const isCorrect = opt === q.answer;
    const isUserChoice = opt === q.userAnswer;
    return {
        correct: isCorrect,
        wrong: isUserChoice && !q.passed,
        disabled: q.answered,
    };
}
</script>

<template>
    <div class="learning-view">
        <ProgressMap
            :knowledgePoints="props.progress.knowledgePoints"
            :currentKP="props.progress.currentKP"
            :currentDifficulty="props.progress.currentDifficulty"
            :levelInfo="levelInfo"
        />

        <!-- 状态栏 -->
        <div class="learning-status">
            <span class="status-badge subject">{{ progress.subject }}</span>
            <span class="status-badge grade">{{ progress.grade }}年级</span>
            <span class="status-badge kp" v-if="currentKP">{{
                currentKP.name
            }}</span>
            <span
                class="status-badge difficulty"
                :class="currentDifficultyLabel"
            >
                {{
                    currentDifficultyLabel === "basic"
                        ? "基础"
                        : currentDifficultyLabel === "intermediate"
                          ? "进阶"
                          : "高阶"
                }}
            </span>
            <span v-if="questions.length" class="status-badge count">
                {{ answeredCount }}/{{ questions.length }} 已答
            </span>
        </div>

        <!-- 加载中 -->
        <div v-if="loading && questions.length === 0" class="loading-area">
            <div class="spinner"></div>
            <p>AI 正在生成 8 道题目...</p>
        </div>

        <!-- 错误 -->
        <div v-else-if="error && questions.length === 0" class="error-area">
            <p>{{ error }}</p>
            <button class="btn btn-outline" @click="fetchRound">重试</button>
        </div>

        <!-- 题目列表 -->
        <div v-else-if="questions.length" class="question-list">
            <div
                v-for="q in questions"
                :key="q.id"
                class="q-card"
                :class="{
                    answered: q.answered,
                    correct: q.passed,
                    wrong: q.answered && !q.passed,
                }"
            >
                <!-- 题号 + 题型标记 -->
                <div class="q-header">
                    <span class="q-num">第 {{ q.id + 1 }} 题</span>
                    <span class="q-type" :class="q.type">
                        {{ q.type === "MCQ" ? "选择题" : "应用题" }}
                    </span>
                    <span v-if="q.answered && q.passed" class="q-status correct"
                        >✓</span
                    >
                    <span
                        v-else-if="q.answered && !q.passed"
                        class="q-status wrong"
                        >✗</span
                    >
                </div>

                <p class="q-text">{{ q.question }}</p>

                <!-- 选择题：选项按钮 -->
                <div v-if="q.type === 'MCQ'" class="q-options">
                    <button
                        v-for="(text, key) in q.options"
                        :key="key"
                        class="q-opt"
                        :class="optionClass(q, key)"
                        :disabled="q.answered"
                        @click="answerQuestion(q.id, key)"
                    >
                        <span class="opt-key">{{ key }}</span>
                        <span class="opt-text">{{ text }}</span>
                        <span
                            v-if="q.answered && key === q.answer"
                            class="opt-mark"
                            >✓</span
                        >
                    </button>
                </div>

                <!-- 应用题：文本输入 -->
                <div v-else class="q-input-area">
                    <textarea
                        v-if="!q.answered"
                        class="q-textarea"
                        :placeholder="'请输入你的答案...'"
                        rows="3"
                        @keydown.ctrl.enter="
                            (e) => {
                                if (e.target.value.trim())
                                    answerQuestion(q.id, e.target.value.trim());
                            }
                        "
                        @keydown.meta.enter="
                            (e) => {
                                if (e.target.value.trim())
                                    answerQuestion(q.id, e.target.value.trim());
                            }
                        "
                    ></textarea>
                    <div v-else class="q-answer-display">
                        <strong>你的答案：</strong>{{ q.userAnswer }}
                    </div>
                </div>

                <!-- 单题反馈 -->
                <div
                    v-if="q.answered && q.evaluation"
                    class="q-feedback"
                    :class="{ correct: q.passed, wrong: !q.passed }"
                >
                    <div
                        v-if="q.type === 'problem-solving' && !q.passed"
                        class="q-ref-answer"
                    >
                        <strong>参考答案：</strong>{{ q.answer }}
                    </div>
                    <div>{{ q.evaluation.explanation }}</div>
                    <div>{{ q.explanation }}</div>
                </div>
            </div>
        </div>

        <!-- 全部通关后 -->
        <div v-if="progress.overallComplete" class="complete-banner">
            🎉 所有知识点已通关！你太棒了！
        </div>

        <!-- 底部状态 -->
        <div v-if="allChecked" class="round-summary">
            <div v-if="allPassed" class="summary-pass">
                ✅ 全部答对！即将进入下一关...
            </div>
            <div v-else class="summary-fail">
                ❌ {{ passedCount }}/{{ questions.length }} 正确，继续加油！
                <button
                    class="btn btn-primary"
                    @click="retryWrong"
                    :disabled="loading"
                >
                    {{ loading ? "加载中..." : "重做错题" }}
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.learning-view {
    padding: 0 0 40px;
}

.learning-status {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
}
.status-badge {
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}
.status-badge.subject {
    background: #dbeafe;
    color: #1d4ed8;
}
.status-badge.grade {
    background: #f3e8ff;
    color: #7c3aed;
}
.status-badge.kp {
    background: #fce7f3;
    color: #db2777;
}
.status-badge.difficulty {
    background: #fef3c7;
    color: #92400e;
}
.status-badge.difficulty.advanced {
    background: #fecaca;
    color: #991b1b;
}
.status-badge.count {
    background: #e0f2fe;
    color: #0369a1;
}

.loading-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 48px 0;
    color: var(--text-secondary);
}
.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
.error-area {
    text-align: center;
    padding: 40px 20px;
    color: var(--danger);
}
.error-area .btn {
    margin-top: 16px;
}

.question-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.q-card {
    background: var(--card-bg);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    transition: border-color 0.3s;
}
.q-card.correct {
    border-color: var(--success);
    background: #f0fdf4;
}
.q-card.wrong {
    border-color: var(--danger);
    background: #fef2f2;
}

.q-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}
.q-num {
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--primary);
}
.q-type {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    background: #e2e8f0;
    color: #475569;
}
.q-type.MCQ {
    background: #dbeafe;
    color: #1d4ed8;
}
.q-type.problem-solving {
    background: #fef3c7;
    color: #92400e;
}
.q-status {
    font-size: 1.2rem;
    font-weight: 700;
    margin-left: auto;
}
.q-status.correct {
    color: var(--success);
}
.q-status.wrong {
    color: var(--danger);
}

.q-text {
    font-size: 1rem;
    line-height: 1.7;
    margin-bottom: 14px;
}

/* MCQ 选项 */
.q-options {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.q-opt {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    border: 2px solid var(--border);
    border-radius: var(--radius);
    background: #fafafa;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    font-size: 0.9rem;
}
.q-opt:not(:disabled):hover {
    border-color: var(--primary);
    background: #eef2ff;
}
.q-opt:disabled {
    cursor: default;
}
.q-opt.correct {
    border-color: var(--success);
    background: #f0fdf4;
}
.q-opt.wrong {
    border-color: var(--danger);
    background: #fef2f2;
}
.opt-key {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--border);
    font-weight: 700;
    font-size: 0.8rem;
    flex-shrink: 0;
}
.q-opt.correct .opt-key {
    background: var(--success);
    color: #fff;
}
.opt-text {
    flex: 1;
}
.opt-mark {
    font-size: 1rem;
    font-weight: 700;
    color: var(--success);
}

/* 应用题输入 */
.q-input-area {
    margin-bottom: 4px;
}
.q-textarea {
    width: 100%;
    padding: 12px;
    border: 2px solid var(--border);
    border-radius: var(--radius);
    font-size: 0.95rem;
    font-family: inherit;
    resize: vertical;
    transition: border-color 0.2s;
}
.q-textarea:focus {
    outline: none;
    border-color: var(--primary);
}
.q-answer-display {
    padding: 10px 14px;
    background: #f8fafc;
    border-radius: var(--radius);
    font-size: 0.9rem;
}

/* 反馈 */
.q-feedback {
    margin-top: 12px;
    padding: 10px 14px;
    border-radius: var(--radius);
    font-size: 0.85rem;
    line-height: 1.5;
}
.q-feedback.correct {
    background: #f0fdf4;
    color: #166534;
    border: 1px solid var(--success);
}
.q-feedback.wrong {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid var(--danger);
}
.q-ref-answer {
    margin-bottom: 6px;
    padding-bottom: 6px;
    border-bottom: 1px dashed rgba(153, 27, 27, 0.2);
}

.complete-banner {
    text-align: center;
    padding: 24px;
    background: #f0fdf4;
    border: 2px solid var(--success);
    border-radius: var(--radius);
    font-size: 1.15rem;
    font-weight: 700;
    color: #166534;
    margin-top: 20px;
}

.round-summary {
    position: sticky;
    bottom: 0;
    margin-top: 20px;
    padding: 16px 20px;
    border-radius: var(--radius);
    text-align: center;
    font-weight: 600;
}
.summary-pass {
    background: #f0fdf4;
    border: 2px solid var(--success);
    color: #166534;
}
.summary-fail {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    background: #fef2f2;
    border: 2px solid var(--danger);
    color: #991b1b;
}
.summary-fail .btn {
    margin-top: 4px;
}
</style>
