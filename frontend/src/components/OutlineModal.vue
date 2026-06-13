<script setup>
defineProps({
  show: { type: Boolean, default: false },
  selectedOutline: { type: Object, default: null },
  selectedOutlineIndex: { type: Number, default: null },
  questionStats: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'relearn'])

function handleClose() {
  emit('close')
}

function handleRelearn() {
  emit('relearn', props.selectedOutlineIndex)
  emit('close')
}
</script>

<template>
  <transition name="modal-fade">
    <div v-if="show" class="modal-overlay" @click="handleClose">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3 v-if="selectedOutline" class="modal-title">
            知识点 {{ selectedOutlineIndex + 1 }}: {{ selectedOutline.name }}
          </h3>
          <button class="modal-close" @click="handleClose">×</button>
        </div>

        <div class="modal-body">
          <div class="stats-card">
            <div class="stat-row">
              <span class="stat-label">总题数</span>
              <span class="stat-value">{{ questionStats[selectedOutline?.id]?.total || 24 }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">错题数</span>
              <span class="stat-value wrong">{{ questionStats[selectedOutline?.id]?.wrong || 0 }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">正确率</span>
              <span class="stat-value" :class="{
                wrong: (questionStats[selectedOutline?.id]?.wrong || 0) / (questionStats[selectedOutline?.id]?.total || 24) > 0.5
              }">
                {{ Math.round((1 - (questionStats[selectedOutline?.id]?.wrong || 0) / (questionStats[selectedOutline?.id]?.total || 24)) * 100) }}%
              </span>
            </div>
          </div>

          <div class="warning-box" v-if="(questionStats[selectedOutline?.id]?.wrong || 0) / (questionStats[selectedOutline?.id]?.total || 24) > 0.5">
            ⚠️ 错题率超过 50%，建议重新学习
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-outline" @click="handleClose">关闭</button>
          <button class="btn btn-primary" @click="handleRelearn">
            🔄 重新学习
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-container {
  background: var(--card-bg);
  border-radius: var(--radius);
  max-width: 400px;
  width: 100%;
  max-height: 80vh;
  overflow: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.modal-close:hover {
  background: var(--border);
}

.modal-body {
  padding: 16px;
}

.stats-card {
  background: #f8fafc;
  border-radius: var(--radius);
  padding: 16px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
}

.stat-value.wrong {
  color: var(--danger);
}

.warning-box {
  margin-top: 16px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: var(--radius);
  color: #dc2626;
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
}

.modal-actions {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--border);
}

.modal-actions .btn {
  flex: 1;
}
</style>
