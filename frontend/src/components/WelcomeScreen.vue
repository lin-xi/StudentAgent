<script setup>
import { useRouter } from "vue-router";
import { useLearningStore } from "../stores/learning";

const router = useRouter();
const learningStore = useLearningStore();

function handleStart() {
  const subject = learningStore.getSelectedSubject();
  const grade = learningStore.getSelectedGrade();

  console.log("subject>>>>", subject, "grade>>>>", grade);
  if (subject.id && grade.id) {
    router.push("/home");
  } else {
    router.push("/select-subject");
  }
}
</script>

<template>
  <div class="welcome-screen">
    <div class="welcome-icon">🎯</div>
    <h2>欢迎来到智能学习助手</h2>
    <p class="welcome-desc">
      选择科目与年级，AI 将为你生成个性化学习题目，<br />
      助你循序渐进掌握每一个知识点！
    </p>
    <button class="btn btn-primary btn-large" @click="handleStart">
      🚀 开始学习
    </button>
  </div>
</template>

<style scoped>
.welcome-screen {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-desc {
  color: var(--text-secondary);
  margin: 12px 0 32px;
  line-height: 1.8;
}

.btn-large {
  padding: 16px 48px;
  font-size: 1.15rem;
}
</style>
