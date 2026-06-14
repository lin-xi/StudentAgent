<script setup>
import { computed } from 'vue'

const props = defineProps({
  knowledgePoints: { type: Array, required: true },
  questionStats: { type: Object, default: () => ({}) }, // { kpId: { total: 24, wrong: 5 } }
})

const emit = defineEmits(['select'])

// 获取知识点答题样式
function getOutlineClass(kp) {
  const stats = props.questionStats[kp.id] || { total: 24, wrong: 0 }
  const wrongRate = stats.total > 0 ? stats.wrong / stats.total : 0

  if (wrongRate > 0.5) return 'high-wrong'
  if (wrongRate > 0.3) return 'mid-wrong'
  if (wrongRate > 0) return 'low-wrong'
  return 'all-correct'
}

function handleClick(kp, index) {
  emit('select', { kp, index })
}
</script>

<template>
  <div class="outline-card">
    <div class="outline-header">
      <h3 class="outline-title">大纲答题</h3>
      <span class="outline-desc">点击知识点查看详情</span>
    </div>

    <div class="outline-grid">
      <div
        v-for="(kp, idx) in knowledgePoints"
        :key="kp.id"
        class="outline-cell"
        :class="[getOutlineClass(kp)]"
        @click="handleClick(kp, idx)"
      >
        <span class="kp-id">{{ idx + 1 }}</span>
        <span class="kp-name">{{ kp.name }}</span>
        <span class="kp-stats" v-if="questionStats[kp.id]">
          {{ questionStats[kp.id].wrong }}/{{ questionStats[kp.id].total }}
        </span>
        <span class="kp-stats" v-else>
          0/24
        </span>
        <!-- 完成日期 -->
        <span class="kp-completed-date" v-if="kp.completedDate">
          {{ kp.completedDate }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.outline-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
  border: 2px solid var(--border);
}

.outline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.outline-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.outline-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.outline-grid {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
  -webkit-overflow-scrolling: touch;
}

.outline-grid::-webkit-scrollbar {
  height: 6px;
}

.outline-grid::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.outline-grid::-webkit-scrollbar-thumb {
  background: var(--primary);
  border-radius: 3px;
}

.outline-cell {
  flex: 0 0 auto;
  width: 100px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 2px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
  gap: 4px;
}

.outline-cell:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.outline-cell.all-correct {
  background: #f0fdf4;
  border-color: var(--success);
}

.outline-cell.low-wrong {
  background: #fef3c7;
  border-color: #fcd34d;
}

.outline-cell.mid-wrong {
  background: #fed7aa;
  border-color: #fdba74;
}

.outline-cell.high-wrong {
  background: #fecaca;
  border-color: #fca5a5;
}

.kp-id {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 8px;
  border-radius: 10px;
}

.kp-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text);
  text-align: center;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kp-stats {
  font-size: 0.7rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.high-wrong .kp-stats {
  color: #dc2626;
}

.kp-completed-date {
  font-size: 0.6rem;
  color: var(--success);
  font-weight: 600;
  background: #f0fdf4;
  padding: 2px 4px;
  border-radius: 4px;
  margin-top: 2px;
}
</style>
