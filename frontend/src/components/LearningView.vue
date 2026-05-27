<script setup>
import { ref, computed, watch } from "vue"
import { saveProgress, QUESTIONS_PER_ROUND } from "../db.js"
import { generateQuestion, generateQuestionBatch, evaluateAnswer } from "../api.js"
import ProgressMap from "./ProgressMap.vue"

const props = defineProps({
  progress: { type: Object, required: true },
  levelInfo: { type: Object, default: null },
})
const emit = defineEmits(["update"])

// ---- 批次状态 ----
const questions = ref([])          // [{ id, question, options, answer, explanation, userAnswer, answered?, evaluation?, passed? }]
const loading = ref(false)
const error = ref("")
const allChecked = ref(false)      // 是否已检查全部答案

const difficultyLabels = ["basic", "intermediate", "advanced"]
const currentKP = computed(() => props.progress.knowledgePoints[props.progress.currentKP] || null)
const currentDifficultyLabel = computed(() => difficultyLabels[props.progress.currentDifficulty])

// 统计数据
const answeredCount = computed(() => questions.value.filter((q) => q.answered).length)
const passedCount = computed(() => questions.value.filter((q) => q.passed).length)
const allPassed = computed(() => allChecked.value && passedCount.value === questions.value.length)
const hasWrong = computed(() => allChecked.value && passedCount.value < questions.value.length)

// ---- 获取一轮题目 ----
async function fetchRound() {
  const kp = currentKP.value
  if (!kp) return

  loading.value = true
  error.value = ""
  allChecked.value = false

  try {
    const raw = await generateQuestionBatch(
      props.progress.subject,
      props.progress.grade,
      kp.id,
      currentDifficultyLabel.value,
      QUESTIONS_PER_ROUND,
    )
    questions.value = raw.map((q, i) => ({
      id: i,
      question: q.question,
      options: q.options,
      answer: q.answer,
      explanation: q.explanation || "",
      userAnswer: "",
      answered: false,
      evaluation: null,
      passed: false,
    }))
  } catch (e) {
    error.value = "获取题目失败，请检查后端服务是否启动。"
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ---- 回答某题 ----
async function answerQuestion(qId, option) {
  const q = questions.value.find((x) => x.id === qId)
  if (!q || q.answered) return

  q.userAnswer = option
  q.answered = true
  loading.value = true

  try {
    const result = await evaluateAnswer(
      props.progress.subject,
      props.progress.grade,
      currentKP.value.id,
      currentDifficultyLabel.value,
      q.question,
      q.options,
      option,
      q.answer,
    )
    q.evaluation = result
    q.passed = result.passed
  } catch {
    // 后端不可用时本地判断
    const passed = option.trim().toUpperCase() === q.answer.trim().toUpperCase()
    q.evaluation = {
      passed,
      explanation: passed ? "回答正确！" : `回答错误。正确答案是 ${q.answer}。`,
    }
    q.passed = passed
  } finally {
    loading.value = false
  }

  // 全部答完时自动检查
  if (answeredCount.value === questions.value.length) {
    allChecked.value = true
    if (allPassed.value) {
      await advanceDifficulty()
    }
  }
}

// ---- 晋级 ----
async function advanceDifficulty() {
  const p = { ...props.progress }
  const kp = p.knowledgePoints[p.currentKP]
  const diff = difficultyLabels[p.currentDifficulty]

  kp[diff] = true  // 标记当前难度通关

  if (diff === "advanced") {
    p.completedKPCount++
    if (p.completedKPCount >= p.knowledgePoints.length) {
      p.overallComplete = true
    } else {
      p.currentKP++
      p.currentDifficulty = 0
    }
  } else {
    p.currentDifficulty++
  }

  await saveProgress(p)
  emit("update", p)
  questions.value = []
  allChecked.value = false
}

// ---- 重试错题 ----
async function retryWrong() {
  const wrong = questions.value.filter((q) => !q.passed)
  loading.value = true
  allChecked.value = false

  try {
    const results = await Promise.all(
      wrong.map((q, i) =>
        generateQuestion(
          props.progress.subject,
          props.progress.grade,
          currentKP.value.id,
          currentDifficultyLabel.value,
          q.id,  // 用原题号作为 question_index 以获取不同题目
        ),
      ),
    )
    // 替换错题
    for (const q of wrong) {
      const newQ = results.shift()
      if (newQ) {
        q.question = newQ.question
        q.options = newQ.options
        q.answer = newQ.answer
        q.explanation = newQ.explanation || ""
        q.userAnswer = ""
        q.answered = false
        q.evaluation = null
        q.passed = false
      }
    }
  } catch {
    error.value = "重试获取题目失败"
  } finally {
    loading.value = false
  }
}

// ---- 监听知识点/难度变化 ----
watch(
  () => [props.progress.currentKP, props.progress.currentDifficulty],
  () => {
    if (questions.value.length === 0 && !props.progress.overallComplete) {
      fetchRound()
    }
  },
  { immediate: true },
)

// ---- 选项样式 ----
function optionClass(q, opt) {
  if (!q.answered) return {}
  const isCorrect = opt === q.answer
  const isUserChoice = opt === q.userAnswer
  return {
    correct: isCorrect,
    wrong: isUserChoice && !q.passed,
    disabled: q.answered,
  }
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
      <span class="status-badge kp" v-if="currentKP">{{ currentKP.name }}</span>
      <span class="status-badge difficulty" :class="currentDifficultyLabel">
        {{ currentDifficultyLabel === "basic" ? "基础" : currentDifficultyLabel === "intermediate" ? "进阶" : "高阶" }}
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
        <div class="q-header">
          <span class="q-num">第 {{ q.id + 1 }} 题</span>
          <span v-if="q.answered && q.passed" class="q-status correct">✓</span>
          <span v-else-if="q.answered && !q.passed" class="q-status wrong">✗</span>
        </div>

        <p class="q-text">{{ q.question }}</p>

        <div class="q-options">
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
            <span v-if="q.answered && key === q.answer" class="opt-mark">✓</span>
          </button>
        </div>

        <!-- 单题反馈 -->
        <div v-if="q.answered && q.evaluation" class="q-feedback" :class="{ correct: q.passed, wrong: !q.passed }">
          {{ q.evaluation.explanation }}
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
        <button class="btn btn-primary" @click="retryWrong" :disabled="loading">
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

/* 状态 */
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
.status-badge.subject { background: #dbeafe; color: #1d4ed8; }
.status-badge.grade { background: #f3e8ff; color: #7c3aed; }
.status-badge.kp { background: #fce7f3; color: #db2777; }
.status-badge.difficulty { background: #fef3c7; color: #92400e; }
.status-badge.difficulty.advanced { background: #fecaca; color: #991b1b; }
.status-badge.count { background: #e0f2fe; color: #0369a1; }

/* 加载 */
.loading-area {
  display: flex; flex-direction: column; align-items: center;
  gap: 12px; padding: 48px 0; color: var(--text-secondary);
}
.spinner {
  width: 40px; height: 40px;
  border: 4px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-area { text-align: center; padding: 40px 20px; color: var(--danger); }
.error-area .btn { margin-top: 16px; }

/* 题目卡片列表 */
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
.q-card.correct { border-color: var(--success); background: #f0fdf4; }
.q-card.wrong { border-color: var(--danger); background: #fef2f2; }

.q-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.q-num { font-weight: 700; font-size: 0.85rem; color: var(--primary); }
.q-status { font-size: 1.2rem; font-weight: 700; }
.q-status.correct { color: var(--success); }
.q-status.wrong { color: var(--danger); }

.q-text { font-size: 1rem; line-height: 1.7; margin-bottom: 14px; }

.q-options { display: flex; flex-direction: column; gap: 8px; }

.q-opt {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left; font-size: 0.9rem;
}
.q-opt:not(:disabled):hover { border-color: var(--primary); background: #eef2ff; }
.q-opt:disabled { cursor: default; }
.q-opt.correct { border-color: var(--success); background: #f0fdf4; }
.q-opt.wrong { border-color: var(--danger); background: #fef2f2; }

.opt-key {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--border); font-weight: 700; font-size: 0.8rem;
  flex-shrink: 0;
}
.q-opt.correct .opt-key { background: var(--success); color: #fff; }
.opt-text { flex: 1; }
.opt-mark { font-size: 1rem; font-weight: 700; color: var(--success); }

/* 单题反馈 */
.q-feedback {
  margin-top: 12px; padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 0.85rem; line-height: 1.5;
}
.q-feedback.correct { background: #f0fdf4; color: #166534; border: 1px solid var(--success); }
.q-feedback.wrong { background: #fef2f2; color: #991b1b; border: 1px solid var(--danger); }

/* 全部通关 */
.complete-banner {
  text-align: center; padding: 24px;
  background: #f0fdf4; border: 2px solid var(--success);
  border-radius: var(--radius); font-size: 1.15rem;
  font-weight: 700; color: #166534; margin-top: 20px;
}

/* 底部总结 */
.round-summary {
  position: sticky; bottom: 0; margin-top: 20px;
  padding: 16px 20px; border-radius: var(--radius);
  text-align: center; font-weight: 600;
}
.summary-pass { background: #f0fdf4; border: 2px solid var(--success); color: #166534; }
.summary-fail {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  background: #fef2f2; border: 2px solid var(--danger); color: #991b1b;
}
.summary-fail .btn { margin-top: 4px; }
</style>
