<script setup>
import { ref, computed, watch, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const props = defineProps({
  knowledgePoints: { type: Array, required: true },
  currentKP: { type: Number, required: true },
  currentDifficulty: { type: Number, required: true },
  progress: { type: Number, required: true },
});

const scrollContainer = ref(null);

function getKPStatus(kp) {
  if (kp.status[3]) {
    return "completed";
  } else if (kp.status[2]) {
    return "intermediate-done";
  } else if (kp.status[1]) {
    return "basic-done";
  } else {
    return "";
  }
}

function getDifficultyStutus(kp, kpIdx, diffIdx) {
  if (kpIdx === props.currentKP) {
    console.log(kpIdx, diffIdx, props.currentDifficulty);
    return diffIdx == props.currentDifficulty
      ? "current"
      : kp.status[diffIdx]
        ? "done"
        : "locked";
  } else {
    return kp.status[diffIdx] ? "done" : "locked";
  }
}

function isActive(idx) {
  return idx === props.currentKP;
}

function goBack() {
  router.replace({ path: "/home" });
}

// 自动滚动到当前知识点
watch(
  () => props.currentKP,
  (newVal) => {
    if (scrollContainer.value) {
      const node = scrollContainer.value.children[newVal];
      if (node) {
        node.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "center",
        });
      }
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="progress-map">
    <!-- 等级称号 -->
    <div class="level-badge">
      <div class="back" @click="goBack">← 返回</div>
      <div class="level-info">
        <span class="level-title">已完成{{ props.progress }}</span>
        <div class="level-bar-wrap">
          <div class="level-bar" :style="{ width: props.progress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- 关卡地图 -->
    <div class="kp-map" ref="scrollContainer">
      <div
        v-for="(kp, idx) in knowledgePoints"
        :key="kp.id"
        class="kp-node"
        :class="[getKPStatus(kp), { active: isActive(idx) }]"
      >
        <div class="kp-connector" v-if="idx > 0"></div>
        <div class="kp-badge" :class="{ 'badge-active': isActive(idx) }">
          <span v-if="kp.allCompleted" class="badge-icon">✅</span>
          <span v-else-if="isActive(idx)" class="badge-icon">⚔️</span>
          <span v-else class="badge-icon">🔒</span>
        </div>
        <div class="kp-info">
          <div class="kp-id">#{{ idx + 1 }}</div>
          <div class="kp-name">{{ kp.kp }}</div>
          <div class="kp-difficulties">
            <span
              v-for="diff in ['1', '2', '3']"
              :key="'difficulty-' + kp.id + '' + diff"
              class="diff-dot"
              :class="[getDifficultyStutus(kp, idx, diff)]"
            ></span>
          </div>
          <!-- 完成日期 -->
          <div
            v-if="getKPStatus(kp) === 'completed' && kp.completedDate"
            class="completed-date"
          >
            {{ kp.completedDate }}
          </div>
        </div>
        <div v-if="isActive(kp)" class="current-diff-label">
          {{ getDifficultyLabel(currentDifficulty) }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progress-map {
  margin-bottom: 24px;
}

/* 等级 */
.level-badge {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-radius: var(--radius);
  margin-bottom: 20px;
}

.level-icon {
  font-size: 2rem;
}
.back {
  background: linear-gradient(0deg, #d972bd 0%, #8080fe 100%);
  padding: 10px 20px;
  border-radius: 8px;
  margin-right: 30px;
  cursor: pointer;
  color: #ffffff;
}
.level-info {
  flex: 1;
}

.level-title {
  font-weight: 700;
  font-size: 1.05rem;
}

.level-bar-wrap {
  height: 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
  margin: 6px 0;
  overflow: hidden;
}

.level-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--warning), #d97706);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.level-next {
  font-size: 0.8rem;
  color: #92400e;
}

/* 关卡地图 */
.kp-map {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  overflow: scroll;
}

.kp-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 200px;
  gap: 15px;
  padding: 14px 16px;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  position: relative;
  transition: all 0.3s;
}

.kp-node + .kp-node {
  margin-top: 2px;
}

.kp-node.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.kp-node.completed {
  border-color: var(--success);
  background: #f0fdf4;
}

.badge-icon {
  font-size: 1.4rem;
}

.kp-info {
  flex: 1;
}

.kp-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.kp-id {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 8px;
  border-radius: 10px;
  margin-bottom: 4px;
}

.completed-date {
  font-size: 0.65rem;
  color: var(--success);
  font-weight: 600;
  margin-top: 4px;
  padding: 2px 6px;
  background: #f0fdf4;
  border-radius: 4px;
}

.kp-difficulties {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.diff-dot {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  background: #fff;
  transition: all 0.3s;
}

.diff-dot.done {
  background: var(--success);
  border-color: var(--success);
}

.diff-dot.current {
  background: var(--primary);
  border-color: var(--primary);
  animation: pulse 1.5s infinite;
}

.diff-dot.locked {
  opacity: 0.4;
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(79, 70, 229, 0);
  }
}

.current-diff-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary);
  padding: 4px 10px;
  background: #eef2ff;
  border-radius: 20px;
  white-space: nowrap;
}
</style>
