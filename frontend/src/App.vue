<script setup>
import { ref, onMounted } from "vue";
import {
    loadProgress,
    clearProgress,
    saveProgress,
    createInitialProgress,
    getLevelTitle,
} from "./db.js";
import { fetchSyllabus, generateQuestion, evaluateAnswer } from "./api.js";
import WelcomeScreen from "./components/WelcomeScreen.vue";
import SubjectSelect from "./components/SubjectSelect.vue";
import GradeSelect from "./components/GradeSelect.vue";
import LearningView from "./components/LearningView.vue";

const view = ref("loading"); // loading | welcome | subject | grade | learning | complete
const progress = ref(null);
const levelInfo = ref(null);
const subjects = ["数学", "英语"];
const grades = [4, 5, 6];

// 学习流程中的临时选择
const selectedSubject = ref("");
const selectedGrade = ref(null);
const showConfirmReset = ref(false);

onMounted(async () => {
    const saved = await loadProgress();
    if (saved) {
        progress.value = saved;
        levelInfo.value = getLevelTitle(saved.completedKPCount);
        view.value = saved.overallComplete ? "complete" : "learning";
    } else {
        view.value = "welcome";
    }
});

function handleStart() {
    view.value = "subject";
}

function handleSubjectSelect(subject) {
    selectedSubject.value = subject;
    view.value = "grade";
}

function handleGradeSelect(grade) {
    selectedGrade.value = grade;
    startLearning();
}

async function startLearning() {
    try {
        const syllabus = await fetchSyllabus(
            selectedSubject.value,
            selectedGrade.value,
        );
        console.log("syllabus>>>>", syllabus);
        if (
            !syllabus.knowledgePoints ||
            syllabus.knowledgePoints.length === 0
        ) {
            alert("该科目年级暂无可学习的大纲内容");
            view.value = "subject";
            return;
        }
        progress.value = createInitialProgress(
            selectedSubject.value,
            selectedGrade.value,
            syllabus.knowledgePoints,
        );
        levelInfo.value = getLevelTitle(0);
        await saveProgress(progress.value);
        view.value = "learning";
    } catch (e) {
        console.error("获取大纲失败:", e);
        // 降级：使用默认知识点
        const defaultKPs = [
            { id: 0, name: `${selectedSubject.value}基础` },
            { id: 1, name: `${selectedSubject.value}进阶` },
            { id: 2, name: `${selectedSubject.value}拓展` },
        ];
        progress.value = createInitialProgress(
            selectedSubject.value,
            selectedGrade.value,
            defaultKPs,
        );
        levelInfo.value = getLevelTitle(0);
        await saveProgress(progress.value);
        view.value = "learning";
    }
}

async function handleProgressUpdate(updatedProgress) {
    progress.value = updatedProgress;
    levelInfo.value = getLevelTitle(updatedProgress.completedKPCount);
    await saveProgress(updatedProgress);

    if (updatedProgress.overallComplete) {
        view.value = "complete";
    }
}

async function handleReset() {
    await clearProgress();
    progress.value = null;
    selectedSubject.value = "";
    selectedGrade.value = null;
    view.value = "welcome";
    showConfirmReset.value = false;
}

function handleBackToStart() {
    view.value = "welcome";
}
</script>

<template>
    <div class="app-container">
        <header class="app-header">
            <h1 class="app-title">📚 智能学习助手</h1>
            <p class="app-subtitle">AI 驱动的个性化学习平台</p>
        </header>

        <main class="app-main">
            <!-- 加载中 -->
            <div v-if="view === 'loading'" class="loading-screen">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>

            <!-- 欢迎 / 进度恢复 -->
            <WelcomeScreen
                v-else-if="view === 'welcome'"
                @start="handleStart"
            />

            <!-- 选择科目 -->
            <SubjectSelect
                v-else-if="view === 'subject'"
                :subjects="subjects"
                @select="handleSubjectSelect"
                @back="handleBackToStart"
            />

            <!-- 选择年级 -->
            <GradeSelect
                v-else-if="view === 'grade'"
                :subject="selectedSubject"
                :grades="grades"
                @select="handleGradeSelect"
                @back="
                    () => {
                        view = 'subject';
                    }
                "
            />

            <!-- 学习主界面 -->
            <LearningView
                v-else-if="view === 'learning'"
                :progress="progress"
                :level-info="levelInfo"
                @update="handleProgressUpdate"
            />

            <!-- 全部通关 -->
            <div v-else-if="view === 'complete'" class="complete-screen">
                <div class="complete-icon">🎉</div>
                <h2>恭喜完成所有学习任务！</h2>
                <p class="complete-desc">
                    你已掌握 {{ progress.subject }}
                    {{ progress.grade }} 年级的全部知识点
                </p>
                <div class="level-badge large">
                    <span class="level-icon">{{ levelInfo?.icon }}</span>
                    <span class="level-title">{{ levelInfo?.title }}</span>
                </div>
                <button class="btn btn-primary" @click="handleBackToStart">
                    返回首页
                </button>
                <button
                    class="btn btn-outline"
                    @click="showConfirmReset = true"
                >
                    重置进度
                </button>
            </div>
        </main>

        <!-- 重置确认弹窗 -->
        <div
            v-if="showConfirmReset"
            class="modal-overlay"
            @click="showConfirmReset = false"
        >
            <div class="modal" @click.stop>
                <h3>确认重置进度？</h3>
                <p>所有学习记录将被清除，此操作不可撤销。</p>
                <div class="modal-actions">
                    <button
                        class="btn btn-outline"
                        @click="showConfirmReset = false"
                    >
                        取消
                    </button>
                    <button class="btn btn-danger" @click="handleReset">
                        确认重置
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<style>
/* ========== Reset & 全局 ========== */
*,
*::before,
*::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

:root {
    --primary: #4f46e5;
    --primary-light: #818cf8;
    --primary-dark: #3730a3;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --bg: #f0f4ff;
    --card-bg: #ffffff;
    --text: #1e293b;
    --text-secondary: #64748b;
    --border: #e2e8f0;
    --radius: 12px;
    --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

body {
    font-family:
        -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
}

.app-container {
    max-width: 720px;
    margin: 0 auto;
    padding: 20px 16px 40px;
}

.app-header {
    text-align: center;
    margin-bottom: 32px;
}

.app-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--primary);
}

.app-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-top: 4px;
}

.app-main {
    min-height: 60vh;
}

/* ========== 通用组件 ========== */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 28px;
    border: 2px solid transparent;
    border-radius: var(--radius);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn:active {
    transform: scale(0.97);
}

.btn-primary {
    background: var(--primary);
    color: #fff;
}
.btn-primary:hover {
    background: var(--primary-dark);
}

.btn-outline {
    background: transparent;
    border-color: var(--border);
    color: var(--text);
}
.btn-outline:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.btn-danger {
    background: var(--danger);
    color: #fff;
}
.btn-danger:hover {
    background: #dc2626;
}

/* ========== 加载 ========== */
.loading-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 80px 0;
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

/* ========== 通关界面 ========== */
.complete-screen {
    text-align: center;
    padding: 60px 20px;
}

.complete-icon {
    font-size: 64px;
    margin-bottom: 16px;
}

.complete-desc {
    color: var(--text-secondary);
    margin: 12px 0 24px;
}

.level-badge.large {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 16px 32px;
    border-radius: 50px;
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 32px;
}

.level-badge.large .level-icon {
    font-size: 1.8rem;
}

.complete-screen .btn {
    margin: 8px;
}

/* ========== 弹窗 ========== */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
}

.modal {
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 28px;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal h3 {
    margin-bottom: 8px;
}

.modal p {
    color: var(--text-secondary);
    margin-bottom: 20px;
}

.modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
}

/* ========== 响应式 ========== */
@media (max-width: 480px) {
    .app-container {
        padding: 12px 10px 32px;
    }
    .app-title {
        font-size: 1.4rem;
    }
}
</style>
