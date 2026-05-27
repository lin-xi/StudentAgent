<script setup>
defineProps({
    subject: { type: String, required: true },
    grades: { type: Array, required: true },
});
defineEmits(["select", "back"]);

const gradeLabels = {
    4: "四年级",
};
</script>

<template>
    <div class="select-screen">
        <button class="back-btn" @click="$emit('back')">← 返回</button>
        <h2>选择年级</h2>
        <p class="select-desc">
            已选科目：<strong>{{ subject }}</strong
            >，请选择年级：
        </p>
        <div class="card-grid">
            <button
                v-for="g in grades"
                :key="g"
                class="grade-card"
                @click="$emit('select', g)"
            >
                <span class="grade-num">{{ g }}</span>
                <span class="grade-label">{{
                    gradeLabels[g] || g + "年级"
                }}</span>
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
