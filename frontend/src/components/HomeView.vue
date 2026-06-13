<script setup>
import { ref, computed } from 'vue'
import CalendarCard from './CalendarCard.vue'
import OutlineCard from './OutlineCard.vue'
import OutlineModal from './OutlineModal.vue'

const props = defineProps({
  progress: { type: Object, required: true },
  levelInfo: { type: Object, default: null },
})

const emit = defineEmits(['startLearning', 'relearnOutline'])

const showOutlineModal = ref(false)
const selectedOutline = ref(null)
const selectedOutlineIndex = ref(null)

// 模拟答题统计（后续可从后端获取）
const questionStats = computed(() => {
  const stats = {}
  props.progress.knowledgePoints.forEach((kp) => {
    // TODO: 从后端获取实际答题数据
    stats[kp.id] = { total: 24, wrong: Math.floor(Math.random() * 12) }
  })
  return stats
})

function handleOutlineSelect({ kp, index }) {
  selectedOutline.value = kp
  selectedOutlineIndex.value = index
  showOutlineModal.value = true
}

function handleRelearnOutline(index) {
  emit('relearnOutline', index)
}

function handleStartLearning() {
  emit('startLearning')
}
</script>

<template>
  <div class="home-view">
    <!-- 等级信息 -->
    <div v-if="levelInfo" class="level-summary">
      <span class="level-icon">{{ levelInfo.icon }}</span>
      <div class="level-info">
        <span class="level-title">{{ levelInfo.title }}</span>
        <div class="level-bar-wrap">
          <div
            class="level-bar"
            :style="{ width: levelInfo.progressPercent + '%' }"
          ></div>
        </div>
        <span class="level-next">
          {{ levelInfo.next ? `还需${levelInfo.nextCount}个知识点达到${levelInfo.next.title}` : '已达最高等级！' }}
        </span>
      </div>
    </div>

    <!-- 打卡日历 -->
    <CalendarCard
      :checkInRecords="progress.checkInRecords || {}"
      :currentStreak="progress.currentStreak || 0"
      :maxStreak="progress.maxStreak || 0"
    />

    <!-- 大纲答题 -->
    <OutlineCard
      :knowledgePoints="progress.knowledgePoints"
      :questionStats="questionStats"
      @select="handleOutlineSelect"
    />

    <!-- 开始学习按钮 -->
    <button class="btn-start-learning" @click="handleStartLearning">
      📖 开始学习
    </button>

    <!-- 大纲详情浮层 -->
    <OutlineModal
      :show="showOutlineModal"
      :selectedOutline="selectedOutline"
      :selectedOutlineIndex="selectedOutlineIndex"
      :questionStats="questionStats"
      @close="showOutlineModal = false"
      @relearn="handleRelearnOutline"
    />
  </div>
</template>

<style scoped>
.home-view {
  padding: 16px;
}

.level-summary {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-radius: var(--radius);
  margin-bottom: 16px;
}

.level-icon {
  font-size: 2.5rem;
}

.level-info {
  flex: 1;
}

.level-title {
  display: block;
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 6px;
}

.level-bar-wrap {
  height: 8px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}

.level-bar {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b, #d97706);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.level-next {
  font-size: 0.8rem;
  color: #92400e;
}

.btn-start-learning {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 16px;
}

.btn-start-learning:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);
}

.btn-start-learning:active {
  transform: translateY(0);
}
</style>
