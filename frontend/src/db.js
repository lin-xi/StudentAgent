/**
 * IndexedDB 持久化工具（使用 idb 库）
 * 存储用户学习进度：科目、年级、知识点通关状态等。
 */
import { openDB } from 'idb'

const DB_NAME = 'LearningApp'
const DB_VERSION = 2  // 升级为 v2，增加打卡和完成日期支持
const STORE_NAME = 'progress'

export const DIFFICULTIES = ['basic', 'intermediate', 'advanced']
export const DIFFICULTY_LABELS = {
  basic: '基础',
  intermediate: '进阶',
  advanced: '高阶',
}

// 每轮批次的题目数量
export const QUESTIONS_PER_ROUND = 8

const dbPromise = openDB(DB_NAME, DB_VERSION, {
  async upgrade(db, oldVersion, newVersion, transaction) {
    if (!db.objectStoreNames.contains(STORE_NAME)) {
      db.createObjectStore(STORE_NAME, { keyPath: 'id' })
    }
    // v2: 增加打卡记录和完成日期字段
    if (oldVersion < 2) {
      const store = transaction.objectStore(STORE_NAME)
      const allData = await store.getAll()
      for (const data of allData) {
        // 迁移 knowledgePoints: 增加 completedDate 字段
        if (data.knowledgePoints) {
          data.knowledgePoints = data.knowledgePoints.map(kp => ({
            ...kp,
            completedDate: kp.completedDate || null,
          }))
        }
        // 迁移：增加打卡相关字段
        if (!data.checkInRecords) data.checkInRecords = {}
        if (!data.currentStreak) data.currentStreak = 0
        if (!data.maxStreak) data.maxStreak = 0
        if (!data.lastCheckInDate) data.lastCheckInDate = null

        await store.put(data)
      }
    }
  },
})

export function createInitialProgress(subject, grade, knowledgePoints) {
  return {
    id: 'userProgress',
    subject,
    grade,
    knowledgePoints: knowledgePoints.map((kp) => ({
      id: kp.id,
      name: kp.name,
      basic: false,
      intermediate: false,
      advanced: false,
      completedDate: null,  // 知识点完成日期
    })),
    currentKP: 0,
    currentDifficulty: 0, // 0=basic, 1=intermediate, 2=advanced
    completedKPCount: 0,
    overallComplete: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    // 打卡记录
    checkInRecords: {},  // { "2026-06-13": { count: 8, levelCompleted: 1 } }
    currentStreak: 0,
    maxStreak: 0,
    lastCheckInDate: null,
  }
}

export async function saveProgress(progress) {
  const db = await dbPromise
  // 深拷贝：避免 Vue reactive proxy 导致 DataCloneError
  const clone = JSON.parse(JSON.stringify(progress))
  clone.updatedAt = Date.now()
  await db.put(STORE_NAME, clone)
}

export async function loadProgress() {
  const db = await dbPromise
  const data = await db.get(STORE_NAME, 'userProgress')
  if (!data) return null

  // 数据迁移：补全旧版本缺失的字段
  const migrated = { ...data }

  // v2 字段迁移
  if (!migrated.checkInRecords) migrated.checkInRecords = {}
  if (!migrated.currentStreak) migrated.currentStreak = 0
  if (!migrated.maxStreak) migrated.maxStreak = 0
  if (!migrated.lastCheckInDate) migrated.lastCheckInDate = null

  // knowledgePoints 增加 completedDate
  if (migrated.knowledgePoints) {
    migrated.knowledgePoints = migrated.knowledgePoints.map(kp => ({
      ...kp,
      completedDate: kp.completedDate || null,
    }))
  }

  return migrated
}

export async function clearProgress() {
  const db = await dbPromise
  await db.delete(STORE_NAME, 'userProgress')
}

export function getKPStatus(progress, kpId) {
  const kp = progress.knowledgePoints.find((k) => k.id === kpId)
  if (!kp) return { completed: false, currentDiff: 'basic' }
  const completed = kp.basic && kp.intermediate && kp.advanced
  let currentDiff = 'basic'
  if (!kp.basic) currentDiff = 'basic'
  else if (!kp.intermediate) currentDiff = 'intermediate'
  else if (!kp.advanced) currentDiff = 'advanced'
  return { completed, currentDiff, kp }
}

export function getLevelTitle(completedCount) {
  const levels = [
    { min: 0, title: '学前萌新', icon: '🌱' },
    { min: 1, title: '青铜学员', icon: '🥉' },
    { min: 2, title: '白银学员', icon: '🥈' },
    { min: 3, title: '黄金学员', icon: '🥇' },
    { min: 4, title: '钻石学霸', icon: '💎' },
    { min: 6, title: '王者大师', icon: '👑' },
  ]
  let current = levels[0]
  let next = null
  for (let i = levels.length - 1; i >= 0; i--) {
    if (completedCount >= levels[i].min) {
      current = levels[i]
      next = i < levels.length - 1 ? levels[i + 1] : null
      break
    }
  }
  const nextCount = next ? next.min - completedCount : 0
  const progress = next && levels.indexOf(next) > 0
    ? ((completedCount - current.min) / (next.min - current.min)) * 100
    : completedCount > 0 ? 100 : 0

  return { ...current, next, nextCount, progressPercent: Math.min(100, Math.max(0, progress)) }
}

// 获取当前日期字符串 YYYY-MM-DD
export function getTodayStr() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// 记录打卡
export async function recordCheckIn(progress, countToday, levelCompletedToday = 0) {
  const today = getTodayStr()
  const p = JSON.parse(JSON.stringify(progress))

  if (!p.checkInRecords) p.checkInRecords = {}

  // 更新今日记录
  const prev = p.checkInRecords[today] || { count: 0, levelCompleted: 0 }
  p.checkInRecords[today] = {
    count: Math.max(prev.count, countToday),
    levelCompleted: prev.levelCompleted + levelCompletedToday,
  }

  // 计算连续打卡
  if (p.lastCheckInDate !== today) {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`

    if (p.lastCheckInDate === yesterdayStr) {
      p.currentStreak = (p.currentStreak || 0) + 1
    } else {
      p.currentStreak = 1
    }
    p.maxStreak = Math.max(p.maxStreak, p.currentStreak)
    p.lastCheckInDate = today
  }

  await saveProgress(p)
  return p
}

// 标记知识点完成
export async function markKPCompleted(progress, kpIndex) {
  const p = JSON.parse(JSON.stringify(progress))
  const today = getTodayStr()
  p.knowledgePoints[kpIndex].completedDate = today
  await saveProgress(p)
  return p
}

// 重置知识点进度（用于重新学习）
export async function resetKPProgress(progress, kpIndex) {
  const p = JSON.parse(JSON.stringify(progress))
  const kp = p.knowledgePoints[kpIndex]
  kp.basic = false
  kp.intermediate = false
  kp.advanced = false
  kp.completedDate = null
  p.currentKP = kpIndex
  p.currentDifficulty = 0
  p.overallComplete = false
  await saveProgress(p)
  return p
}



// 计算月份总完成 level 数
export function getMonthTotalLevel(checkInRecords, year, month) {
  const records = getMonthData(checkInRecords, year, month)
  return records.reduce((sum, r) => sum + (r.levelCompleted || 0), 0)
}
