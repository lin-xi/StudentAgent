/**
 * IndexedDB 持久化工具（使用 idb 库）
 * 存储用户学习进度：科目、年级、知识点通关状态等。
 */
import { openDB } from 'idb'

const DB_NAME = 'LearningApp'
const DB_VERSION = 1
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
  upgrade(db) {
    if (!db.objectStoreNames.contains(STORE_NAME)) {
      db.createObjectStore(STORE_NAME, { keyPath: 'id' })
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
    })),
    currentKP: 0,
    currentDifficulty: 0, // 0=basic, 1=intermediate, 2=advanced
    completedKPCount: 0,
    overallComplete: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
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
  return (await db.get(STORE_NAME, 'userProgress')) || null
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
