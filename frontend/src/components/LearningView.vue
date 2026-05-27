<script setup>
import { ref, computed, watch } from "vue";
import { saveProgress, getLevelTitle } from "../db.js";
import { generateQuestion, evaluateAnswer } from "../api.js";
import ProgressMap from "./ProgressMap.vue";
import QuestionPanel from "./QuestionPanel.vue";

const props = defineProps({
    progress: { type: Object, required: true },
    levelInfo: { type: Object, default: null },
});
const emit = defineEmits(["update"]);

// 当前题目
const currentQuestion = ref(null);
const loading = ref(false);
const error = ref("");
const answered = ref(false);
const userAnswer = ref("");
const evaluation = ref(null);
const consecutiveFails = ref(0);
const showHint = ref(false);

// 当前知识点和难度
const currentKP = computed(() => {
    const kp = props.progress.knowledgePoints[props.progress.currentKP];
    return kp || null;
});
const difficultyLabels = ["basic", "intermediate", "advanced"];
const currentDifficultyLabel = computed(
    () => difficultyLabels[props.progress.currentDifficulty],
);

// 获取新题目
async function fetchQuestion() {
    if (!currentKP.value) return;
    loading.value = true;
    error.value = "";
    answered.value = false;
    userAnswer.value = "";
    evaluation.value = null;
    showHint.value = false;

    try {
        const q = await generateQuestion(
            props.progress.subject,
            props.progress.grade,
            currentKP.value.id,
            currentDifficultyLabel.value,
        );
        currentQuestion.value = q;
    } catch (e) {
        error.value = "获取题目失败，请检查后端服务是否启动。";
        console.error(e);
    } finally {
        loading.value = false;
    }
}

// 提交答案
async function submitAnswer(answer) {
    if (!currentQuestion.value || answered.value) return;

    userAnswer.value = answer;
    answered.value = true;
    loading.value = true;

    try {
        const result = await evaluateAnswer(
            props.progress.subject,
            props.progress.grade,
            currentKP.value.id,
            currentDifficultyLabel.value,
            currentQuestion.value.question,
            currentQuestion.value.options,
            answer,
            currentQuestion.value.answer,
        );
        evaluation.value = result;

        if (result.passed) {
            consecutiveFails.value = 0;
            await advanceProgress();
        } else {
            consecutiveFails.value++;
            if (consecutiveFails.value >= 3) {
                showHint.value = true;
            }
        }
    } catch (e) {
        // 后端不可用时本地判断
        const passed =
            answer.trim().toUpperCase() ===
            currentQuestion.value.answer.trim().toUpperCase();
        evaluation.value = {
            passed,
            explanation: passed
                ? "回答正确！"
                : `回答错误。正确答案是 ${currentQuestion.value.answer}。`,
        };
        if (passed) {
            consecutiveFails.value = 0;
            await advanceProgress();
        } else {
            consecutiveFails.value++;
            if (consecutiveFails.value >= 3) {
                showHint.value = true;
            }
        }
    } finally {
        loading.value = false;
    }
}

// 推进进度
async function advanceProgress() {
    const p = { ...props.progress };
    const kp = p.knowledgePoints[p.currentKP];
    const diff = difficultyLabels[p.currentDifficulty];

    // 标记当前难度通过
    kp[diff] = true;

    if (diff === "advanced") {
        // 全部通关此知识点
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

    // 保存进度
    await saveProgress(p);
    emit("update", p);

    // 若未全部通关，自动获取下一题
    if (!p.overallComplete) {
        // 让父组件更新 props 后重新 fetch
        await new Promise((r) => setTimeout(r, 50));
        fetchQuestion();
    }
}

// 下一题（答错后重新生成）
function nextQuestion() {
    fetchQuestion();
}

// 监听知识点变化，自动获取题目
watch(
    () => [props.progress.currentKP, props.progress.currentDifficulty],
    () => {
        if (!currentQuestion.value && !props.progress.overallComplete) {
            fetchQuestion();
        }
    },
    { immediate: true },
);
</script>

<template>
    <div class="learning-view">
        <!-- 进度与关卡地图 -->
        <ProgressMap
            :knowledgePoints="props.progress.knowledgePoints"
            :currentKP="props.progress.currentKP"
            :currentDifficulty="props.progress.currentDifficulty"
            :levelInfo="levelInfo"
        />

        <!-- 当前学习状态 -->
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
        </div>

        <!-- 加载中 -->
        <div v-if="loading && !currentQuestion" class="loading-area">
            <div class="spinner"></div>
            <p>AI 正在生成题目...</p>
        </div>

        <!-- 错误 -->
        <div v-else-if="error" class="error-area">
            <p>{{ error }}</p>
            <button class="btn btn-outline" @click="fetchQuestion">重试</button>
        </div>

        <!-- 题目面板 -->
        <QuestionPanel
            v-else-if="currentQuestion"
            :question="currentQuestion"
            :answered="answered"
            :evaluation="evaluation"
            :loading="loading"
            :show-hint="showHint"
            :consecutive-fails="consecutiveFails"
            @submit="submitAnswer"
            @next="nextQuestion"
        />

        <!-- 进度完成展示 -->
        <div v-if="progress.overallComplete" class="complete-banner">
            🎉 所有知识点已通关！你太棒了！
        </div>
    </div>
</template>

<style scoped>
.learning-view {
    padding: 0 0 20px;
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

.loading-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 48px 0;
    color: var(--text-secondary);
}

.error-area {
    text-align: center;
    padding: 40px 20px;
    color: var(--danger);
}

.error-area .btn {
    margin-top: 16px;
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
</style>
