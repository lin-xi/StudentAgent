<script setup>
import { DIFFICULTY_LABELS } from "../db.js";

const props = defineProps({
    knowledgePoints: { type: Array, required: true },
    currentKP: { type: Number, required: true },
    currentDifficulty: { type: Number, required: true },
    levelInfo: { type: Object, default: null },
});

function getKPStatus(kp) {
    const completed = kp.basic && kp.intermediate && kp.advanced;
    if (completed) return "completed";
    if (kp.advanced) return "advanced-done";
    if (kp.intermediate) return "intermediate-done";
    if (kp.basic) return "basic-done";
    return "locked";
}

function isActive(kp) {
    return kp.id === props.currentKP;
}

function getDifficultyLabel(index) {
    return (
        DIFFICULTY_LABELS[["basic", "intermediate", "advanced"][index]] || ""
    );
}
</script>

<template>
    <div class="progress-map">
        <!-- 等级称号 -->
        <div v-if="levelInfo" class="level-badge">
            <span class="level-icon">{{ levelInfo.icon }}</span>
            <div class="level-info">
                <span class="level-title">{{ levelInfo.title }}</span>
                <div class="level-bar-wrap">
                    <div
                        class="level-bar"
                        :style="{ width: levelInfo.progressPercent + '%' }"
                    ></div>
                </div>
                <span v-if="levelInfo.next" class="level-next">
                    还需 {{ levelInfo.nextCount }} 知识点达到
                    {{ levelInfo.next.title }}
                </span>
                <span v-else class="level-next">已达最高等级！</span>
            </div>
        </div>

        <!-- 关卡地图 -->
        <div class="kp-map">
            <div
                v-for="(kp, idx) in knowledgePoints"
                :key="kp.id"
                class="kp-node"
                :class="[getKPStatus(kp), { active: isActive(kp) }]"
            >
                <div class="kp-connector" v-if="idx > 0"></div>
                <div class="kp-badge" :class="{ 'badge-active': isActive(kp) }">
                    <span
                        v-if="getKPStatus(kp) === 'completed'"
                        class="badge-icon"
                        >✅</span
                    >
                    <span v-else-if="isActive(kp)" class="badge-icon">⚔️</span>
                    <span v-else class="badge-icon">🔒</span>
                </div>
                <div class="kp-info">
                    <div class="kp-name">{{ kp.name }}</div>
                    <div class="kp-difficulties">
                        <span
                            v-for="diff in [
                                'basic',
                                'intermediate',
                                'advanced',
                            ]"
                            :key="diff"
                            class="diff-dot"
                            :class="{
                                done: kp[diff],
                                current:
                                    isActive(kp) &&
                                    ['basic', 'intermediate', 'advanced'][
                                        currentDifficulty
                                    ] === diff,
                                locked: !kp.basic && diff !== 'basic',
                            }"
                            :title="DIFFICULTY_LABELS[diff]"
                        ></span>
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
    width: 688px;
    display: flex;
    flex-wrap: nowrap;
    gap: 0;
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
