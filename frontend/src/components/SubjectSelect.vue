<script setup>
defineProps({
  subjects: { type: Array, required: true },
})
defineEmits(['select', 'back'])
</script>

<template>
  <div class="select-screen">
    <button class="back-btn" @click="$emit('back')">← 返回</button>
    <h2>选择科目</h2>
    <p class="select-desc">请选择你想要学习的科目：</p>
    <div class="card-grid">
      <button
        v-for="s in subjects"
        :key="s"
        class="subject-card"
        @click="$emit('select', s)"
      >
        <span class="subject-icon">
          {{ s === '语文' ? '📖' : s === '数学' ? '🔢' : '🔤' }}
        </span>
        <span class="subject-name">{{ s }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.select-screen {
  padding: 20px 0;
}

.back-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 1rem;
  cursor: pointer;
  padding: 8px 0;
  margin-bottom: 16px;
}

.back-btn:hover {
  text-decoration: underline;
}

.select-desc {
  color: var(--text-secondary);
  margin: 8px 0 24px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.subject-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 20px;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.subject-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
  transform: translateY(-2px);
}

.subject-icon {
  font-size: 48px;
}

.subject-name {
  font-size: 1.2rem;
  font-weight: 600;
}
</style>
