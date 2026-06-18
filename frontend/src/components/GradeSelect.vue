<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useLearningStore } from "../stores/learning";

const router = useRouter();
const learningStore = useLearningStore();

const grades = ref([]);
const subject = ref(null);

// 如果没有选中的学科，返回学科选择页
onMounted(async () => {
  subject.value = learningStore.getSelectedSubject();
  if (!subject.value) {
    router.replace("/select-subject");
  }
  grades.value = await learningStore.loadGradesBySubject(subject.value.id);
});

function handleBack() {
  router.back();
}

async function handleSelect(grade) {
  console.log("handleSelect>>>", grade);
  await learningStore.setSelectedGrade(subject.value, grade);
  // 选择年级后，开始学习
  router.push("/home");
}
</script>

<template>
  <div class="select-screen">
    <button class="back-btn" @click="handleBack">← 返回</button>
    <h2>选择年级</h2>
    <p class="select-desc">
      已选科目：<strong>{{ subject?.name }}</strong
      >，请选择年级：
    </p>
    <div class="card-grid">
      <button
        v-for="g in grades"
        :key="g.id"
        class="grade-card"
        @click="handleSelect(g)"
      >
        <span class="grade-num">{{ g.name }}</span>
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
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 14px;
}

.grade-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 24px 16px;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.grade-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
  transform: translateY(-2px);
}

.grade-num {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
}

.grade-label {
  font-size: 0.95rem;
  color: var(--text-secondary);
}
</style>
