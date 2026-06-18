<script setup>
import { computed } from "vue";

const props = defineProps({
  progress: { type: Array, default: [] },
});

const today = new Date();
const currentYear = today.getFullYear();
const currentMonth = today.getMonth();

const monthData = computed(() =>
  getMonthData(props.progress, currentYear, currentMonth),
);

const countData = computed(() =>
  getCountData(props.progress, currentYear, currentMonth),
);

const weekDayNames = ["日", "一", "二", "三", "四", "五", "六"];

// 计算当月第一天是周几
const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();

// 获取月份打卡数据
function getMonthData(progress, year, month) {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const records = [];
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    let checkInCount = 0;
    for (let p of progress) {
      if (p.allComplete && p.check_in_date === dateStr) {
        checkInCount++;
      }
    }
    records.push({
      count: checkInCount,
    });
  }
  return records;
}

// 获取月份打卡数据
function getCountData(progress, year, month) {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  let streakCount = 0;
  let allCount = 0;
  let kpCount = 0;
  let open = false;
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    let exist = false;
    for (let p of progress) {
      if (p.allComplete && p.check_in_date === dateStr) {
        kpCount++;
        exist = true;
      }
    }
    if (exist) {
      if (!open) {
        streakCount = 1;
        open = true;
      } else {
        streakCount++;
      }
      allCount++;
    } else {
      open = false;
    }
  }
  return {
    streakCount,
    allCount,
    kpCount,
  };
}

// 获取打卡等级样式
function getCheckInClass(record) {
  if (record.count > 0) return "full";
  return "empty";
}

// 判断是否是今天
function isTodayDay(idx) {
  return idx === today.getDate() - 1;
}

const monthLabels = [
  "一月",
  "二月",
  "三月",
  "四月",
  "五月",
  "六月",
  "七月",
  "八月",
  "九月",
  "十月",
  "十一月",
  "十二月",
];
</script>

<template>
  <div class="calendar-card">
    <div class="calendar-header">
      <h3 class="calendar-title">打卡 {{ countData.allCount }}</h3>
      <div class="calendar-stats">
        <span class="streak-badge">
          🔥 连续 {{ countData.streakCount }} 天
        </span>
        <span class="level-badge">
          📚 本月完成 {{ countData.kpCount }} 个 知识点
        </span>
      </div>
    </div>

    <div class="calendar-grid">
      <!-- 星期标题 -->
      <div v-for="name in weekDayNames" :key="name" class="weekday-label">
        {{ name }}
      </div>

      <!-- 空白填充 -->
      <div
        v-for="i in firstDayOfWeek"
        :key="'empty-' + i"
        class="day-cell empty"
      ></div>

      <!-- 日期格子 -->
      <div
        v-for="(record, idx) in monthData"
        :key="idx"
        class="day-cell"
        :class="[getCheckInClass(record), { isToday: isTodayDay(idx) }]"
      >
        <span class="day-num">{{ idx + 1 }}</span>
        <span class="today-mark" v-if="isTodayDay(idx)"> 今天 </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.calendar-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
  border: 2px solid var(--border);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.calendar-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.calendar-stats {
  display: flex;
  gap: 12px;
}

.streak-badge {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #92400e;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.level-badge {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.weekday-label {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 4px 0;
}

.day-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 0.75rem;
  min-height: 48px;
  transition: all 0.2s;
}

.day-cell.empty {
  background: transparent;
}

.day-cell.some {
  background: #fef3c7;
  border: 1px solid #fcd34d;
}

.day-cell.most {
  background: #fde68a;
  border: 1px solid #fbbf24;
}

.day-cell.full {
  background: #fcd34d;
  border: 1px solid #f59e0b;
}

.day-cell.isToday {
  border: 2px solid var(--primary);
  position: relative;
}

.day-cell.isToday.empty::after {
  content: "";
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
}

.today-mark {
  font-size: 0.55rem;
  color: var(--primary);
  font-weight: 600;
  margin-top: 1px;
}

.day-num {
  font-weight: 600;
  margin-bottom: 2px;
}

.day-count {
  font-size: 0.65rem;
  color: #92400e;
  font-weight: 500;
}

@media (max-width: 480px) {
  .day-cell {
    min-height: 40px;
  }
  .day-num {
    font-size: 0.7rem;
  }
  .day-count {
    font-size: 0.6rem;
  }
}
</style>
