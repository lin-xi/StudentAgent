<script setup>
import { onMounted, ref, computed, watch, reactive } from "vue";
import { saveProgress as saveProgressApi } from "../progress-api.js";
import { generateQuestionBatch, evaluateAnswer } from "../api.js";
import ProgressMap from "./ProgressMap.vue";
import { useRouter, RouterView } from "vue-router";
import { useUserStore } from "../stores/user";
import { useLearningStore } from "../stores/learning";
import { getProgress } from "../progress-api";

const emit = defineEmits(["update", "backToHome"]);

const router = useRouter();
const userStore = useUserStore();
const learningStore = useLearningStore();

const DIFFICULTY_LABELS = {
  0: "",
  1: "基础",
  2: "进阶",
  3: "高阶",
};

const knowledgePoints = ref([]);

const state = reactive({
  subject: {},
  grade: {},
  currentKP: {},
  currentDifficulty: 0,
  allDone: false,
  loading: false,
  error: "",
  allChecked: false,
  questions: [],
  wrongCount: -1,
});

const answeredCount = computed(
  () => state.questions.filter((q) => q.answered).length,
);
const passedCount = computed(
  () => state.questions.filter((q) => q.passed).length,
);
const allPassed = computed(() => passedCount.value === state.questions.length);

onMounted(() => {
  init();
});

async function init() {
  await userStore.checkAuth();
  const subject = learningStore.getSelectedSubject();
  const grade = learningStore.getSelectedGrade();

  state.subject = subject;
  state.grade = grade;

  // 加载学习进度
  const result = await getProgress(subject.id, grade.id);
  knowledgePoints.value = result;
  console.log("progressList>>>>", result);
  if (checkComplete()) {
    state.allDone = true;
  } else {
    //获取题目
    fetchRound();
  }
}

function checkComplete() {
  let complete = true;
  let completeCount = 0;
  let currentKP = Infinity;
  if (knowledgePoints.value && knowledgePoints.value.length > 0) {
    for (let [idx, item] of knowledgePoints.value.entries()) {
      if (!item.allComplete) {
        complete = false;
        if (idx < currentKP) {
          currentKP = idx;
        }
      } else {
        completeCount++;
      }
    }
  }
  state.progress = Math.round(
    (completeCount * 100) / knowledgePoints.value.length,
  );
  state.currentKP = currentKP;
  state.currentDifficulty = getCurrentDifficulty();
  return complete;
}

function getCurrentDifficulty() {
  const kp = knowledgePoints.value[state.currentKP];
  for (let i of [1, 2, 3]) {
    if (!kp.status[i]) {
      return i;
    }
  }
}

// ---- 获取一轮题目 ----
async function fetchRound() {
  state.loading = true;
  state.error = "";
  state.allChecked = false;
  try {
    const raw = await generateQuestionBatch(
      state.subject.name,
      state.grade.name,
      knowledgePoints.value[state.currentKP].kp,
      DIFFICULTY_LABELS[state.currentDifficulty],
    );
    state.questions = raw.map((q, i) => ({
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
    state.loading = false;
  }
}

// ---- 回答某题（MCQ：点选项；应用题：输入文本后点提交）----
async function answerQuestion(qId, answer) {
  const q = state.questions.find((x) => x.id === qId);
  if (!q || q.answered) return;

  q.userAnswer = answer;
  q.answered = true;
  state.loading = true;

  try {
    const result = await evaluateAnswer(
      state.subject.name,
      state.grade.name,
      knowledgePoints.value[state.currentKP].kp,
      DIFFICULTY_LABELS[state.currentDifficulty],
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
      explanation: passed ? "回答正确！" : `回答错误。参考答案：${q.answer}`,
    };
    q.passed = passed;
  } finally {
    state.loading = false;
  }

  if (answeredCount.value === state.questions.length) {
    state.allChecked = true;

    if (passedCount.value === state.questions.length) {
      await saveKpLevelProgress();
      advanceDifficulty();
    } else {
      if (state.wrongCount == -1) {
        state.wrongCount = state.questions.length - passedCount.value;
      }
    }
  }
}

// ---- 保存单个 KP 难度等级的进度 ----
async function saveKpLevelProgress() {
  const today = new Date();
  const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  const kp = knowledgePoints.value[state.currentKP];
  return saveProgressApi({
    subject_id: state.subject.id,
    grade_id: state.grade.id,
    course_id: kp.id,
    kp_level: state.currentKP,
    check_in: true,
    wrong_count: state.wrongCount,
    check_in_date: dateStr,
  });
}

// ---- 晋级 ----
async function advanceDifficulty() {
  state.currentDifficulty++;
  if (state.currentDifficulty > 3) {
    state.currentKP++;
    state.currentDifficulty = 0;
  }
  if (state.currentKP >= knowledgePoints.length) {
    state.allDone = true;
  } else {
    fetchRound();
  }
}

// ---- 重试错题：只重置状态，不重新生成题目 ----
function retryWrong() {
  const wrong = state.questions.filter((q) => !q.passed);

  for (const q of wrong) {
    q.userAnswer = "";
    q.answered = false;
    q.evaluation = null;
    q.passed = false;
  }

  state.allChecked = false;
}

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
      :knowledgePoints="knowledgePoints"
      :currentKP="state.currentKP"
      :currentDifficulty="state.currentDifficulty"
    />

    <!-- 状态栏 -->
    <div class="learning-status">
      <span class="status-badge subject">{{ state.subject.name }}</span>
      <span class="status-badge grade">{{ state.grade.name }}</span>
      <span
        class="status-badge kp"
        v-if="state.currentKP && knowledgePoints.length > 0"
        >{{ knowledgePoints[state.currentKP].kp }}</span
      >
      <span class="status-badge difficulty">
        {{ DIFFICULTY_LABELS[state.currentDifficulty] }}
      </span>
      <span v-if="state.questions.length" class="status-badge count">
        {{ answeredCount }}/{{ state.questions.length }} 已答
      </span>
    </div>

    <!-- 加载中 -->
    <div
      v-if="state.loading && state.questions.length === 0"
      class="loading-area"
    >
      <div class="spinner"></div>
      <p>AI 正在生成 8 道题目...</p>
    </div>

    <!-- 错误 -->
    <div
      v-else-if="state.error && state.questions.length === 0"
      class="error-area"
    >
      <p>{{ state.error }}</p>
      <button class="btn btn-outline" @click="fetchRound">重试</button>
    </div>

    <!-- 题目列表 -->
    <div v-else-if="state.questions.length" class="question-list">
      <div
        v-for="q in state.questions"
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
          <span v-if="q.answered && q.passed" class="q-status correct">✓</span>
          <span v-else-if="q.answered && !q.passed" class="q-status wrong"
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
            <span v-if="q.answered && key === q.answer" class="opt-mark"
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
    <div class="complete-banner" v-if="state.allDone">
      🎉 所有知识点已通关！你太棒了！
    </div>

    <!-- 底部状态 -->
    <div v-if="state.allChecked" class="round-summary">
      <div v-if="allPassed" class="summary-pass">
        ✅ 全部答对！即将进入下一关
      </div>
      <div v-else class="summary-fail">
        ❌ {{ passedCount }}/{{ state.questions.length }} 正确，继续加油！
        <button
          class="btn btn-primary"
          @click="retryWrong"
          :disabled="state.loading"
        >
          {{ state.loading ? "加载中..." : "重做错题" }}
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
  padding: 16px 20px;
  border-radius: var(--radius);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  font-weight: 600;
  height: 400px;
  background: linear-gradient(
    0deg,
    #ffffff 0%,
    rgba(255, 255, 255, 0.9) 70%,
    rgba(255, 255, 255, 0) 100%
  );
}
.summary-pass {
  background: #f0fdf4;
  border: 2px solid var(--success);
  border-radius: 16px;
  color: #166534;
  flex: 1;
  padding: 20px;
  margin-bottom: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.summary-fail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  background: #fef2f2;
  border: 2px solid var(--danger);
  border-radius: 16px;
  color: #991b1b;
  padding: 20px;
  flex: 1;
  margin-bottom: 60px;
}
.summary-fail .btn {
  margin-top: 4px;
}
</style>
