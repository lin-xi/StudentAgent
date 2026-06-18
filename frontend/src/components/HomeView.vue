<script setup>
import { ref, computed, onMounted, watch, reactive } from "vue";
import CalendarCard from "./CalendarCard.vue";
import OutlineCard from "./OutlineCard.vue";
import OutlineModal from "./OutlineModal.vue";
import { useRouter, RouterView } from "vue-router";
import { useUserStore } from "../stores/user";
import { useLearningStore } from "../stores/learning";
import { getProgress } from "../progress-api";

const router = useRouter();
const userStore = useUserStore();
const learningStore = useLearningStore();

const progressList = ref([]);

const state = reactive({
  progress: 0,
});

onMounted(async () => {
  try {
    await userStore.checkAuth();
    const subject = learningStore.getSelectedSubject();
    const grade = learningStore.getSelectedGrade();

    const result = await getProgress(subject.id, grade.id);
    console.log("progressList>>>>", result);

    if (result && result.length > 0) {
      progressList.value = result;
      learningStore.setProgress(result);
      if (checkComplete()) {
        router.replace("/complete");
      }
      console.log("progressList.value>>>>", progressList.value);
    }
  } catch (e) {
    console.error("加载进度失败:", e);
  }
});

const emit = defineEmits(["startLearning", "relearnOutline"]);

const showOutlineModal = ref(false);
const selectedOutline = ref(null);
const selectedOutlineIndex = ref(null);

function handleOutlineSelect({ kp, index }) {
  alert("kp");
  selectedOutline.value = kp;
  selectedOutlineIndex.value = index;
  showOutlineModal.value = true;
}

function checkComplete() {
  let complete = true;
  let completeCount = 0;
  if (progressList.value && progressList.value.length > 0) {
    for (let item of progressList.value) {
      if (!item.allComplete) {
        complete = false;
      } else {
        completeCount++;
      }
    }
  }
  state.progress = Math.round(
    (completeCount * 100) / progressList.value.length,
  );
  return complete;
}

function handleRelearnOutline(index) {
  emit("relearnOutline", index);
}

function handleStartLearning() {
  router.push("/learning");
}
</script>

<template>
  <div class="home-view">
    <header class="app-header">
      <h1 class="app-title">📚 智能学习助手</h1>
      <p class="app-subtitle">AI 驱动的个性化学习平台</p>
    </header>
    <!-- 等级信息 -->
    <div class="level-summary">
      <div class="level-info">
        <span class="level-title">已完成 {{ state.progress }}%</span>
        <div class="level-bar-wrap">
          <div class="level-bar" :style="{ width: state.progress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- 打卡日历 -->
    <CalendarCard :progress="progressList" />

    <!-- 大纲答题 -->
    <OutlineCard
      :knowledgePoints="progressList"
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
