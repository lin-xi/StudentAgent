<script setup>
import { ref } from 'vue'

const props = defineProps({
  question: { type: Object, required: true },
  answered: { type: Boolean, default: false },
  evaluation: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  showHint: { type: Boolean, default: false },
  consecutiveFails: { type: Number, default: 0 },
})
const emit = defineEmits(['submit', 'next'])

const selectedOption = ref('')

function selectOption(opt) {
  if (props.answered) return
  selectedOption.value = opt
  emit('submit', opt)
}

function getOptionClass(opt) {
  if (!props.answered) {
    return { selected: selectedOption.value === opt }
  }
  const isCorrect = opt === props.question.answer
  const isUserChoice = opt === selectedOption.value
  return {
    correct: isCorrect,
    wrong: isUserChoice && !props.evaluation?.passed,
    selected: isUserChoice,
  }
}
</script>

<template>
  <div class="question-panel">
    <!-- 题目 -->
    <div class="question-header">
      <h3 class="question-text">{{ question.question }}</h3>
    </div>

    <!-- 选项 -->
    <div class="options-list">
      <button
        v-for="(text, key) in question.options"
        :key="key"
        class="option-btn"
        :class="getOptionClass(key)"
        :disabled="answered"
        @click="selectOption(key)"
      >
        <span class="option-key">{{ key }}</span>
        <span class="option-text">{{ text }}</span>
        <span v-if="answered && key === question.answer" class="option-mark">✓</span>
        <span v-if="answered && key === selectedOption && evaluation && !evaluation.passed" class="option-mark wrong-mark">✗</span>
      </button>
    </div>

    <!-- 反馈 -->
    <div v-if="answered && evaluation" class="feedback" :class="{ correct: evaluation.passed, wrong: !evaluation.passed }">
      <div class="feedback-icon">{{ evaluation.passed ? '✅' : '❌' }}</div>
      <div class="feedback-content">
        <div class="feedback-title">{{ evaluation.passed ? '回答正确！' : '回答错误' }}</div>
        <div class="feedback-explanation">
          {{ evaluation.explanation || (evaluation.passed ? '太棒了，继续加油！' : `正确答案是 ${question.answer}`) }}
        </div>
      </div>
    </div>

    <!-- 提示（连续3次失败） -->
    <div v-if="showHint" class="hint-box">
      <strong>💡 小提示：</strong>
      这道题已经连续答错 {{ consecutiveFails }} 次了，建议回顾一下相关知识点，<br />
      理解 {{ question.explanation }}
    </div>

    <!-- 操作按钮 -->
    <div v-if="answered" class="question-actions">
      <button
        v-if="!evaluation?.passed"
        class="btn btn-primary"
        :disabled="loading"
        @click="$emit('next')"
      >
        {{ loading ? '加载中...' : '重新出题' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.question-panel {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}

.question-header {
  margin-bottom: 20px;
}

.question-text {
  font-size: 1.05rem;
  line-height: 1.7;
  font-weight: 500;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  font-size: 0.95rem;
}

.option-btn:not(:disabled):hover {
  border-color: var(--primary);
  background: #eef2ff;
}

.option-btn:disabled {
  cursor: default;
}

.option-btn.selected {
  border-color: var(--primary);
  background: #eef2ff;
}

.option-btn.correct {
  border-color: var(--success);
  background: #f0fdf4;
}

.option-btn.wrong {
  border-color: var(--danger);
  background: #fef2f2;
}

.option-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--border);
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.option-btn.correct .option-key {
  background: var(--success);
  color: #fff;
}

.option-text {
  flex: 1;
}

.option-mark {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--success);
}

.option-mark.wrong-mark {
  color: var(--danger);
}

/* 反馈 */
.feedback {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius);
  margin-top: 16px;
}

.feedback.correct {
  background: #f0fdf4;
  border: 1px solid var(--success);
}

.feedback.wrong {
  background: #fef2f2;
  border: 1px solid var(--danger);
}

.feedback-icon {
  font-size: 1.5rem;
}

.feedback-title {
  font-weight: 700;
  font-size: 1rem;
}

.feedback.correct .feedback-title {
  color: #166534;
}

.feedback.wrong .feedback-title {
  color: #991b1b;
}

.feedback-explanation {
  margin-top: 4px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 提示 */
.hint-box {
  padding: 14px 16px;
  background: #fffbeb;
  border: 1px solid var(--warning);
  border-radius: var(--radius);
  margin-top: 16px;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #92400e;
}

/* 操作按钮 */
.question-actions {
  margin-top: 20px;
  text-align: center;
}
</style>
