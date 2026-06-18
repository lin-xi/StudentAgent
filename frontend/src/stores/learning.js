import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSubjects, getGradesBySubject, saveSubjectGrade } from '../progress-api.js'

export const useLearningStore = defineStore('learning', () => {
  // 学习进度
  const progress = ref(null)
  // 等级信息
  const levelInfo = ref(null)
  // 学科列表
  const subjectsList = ref([])
  // 年级列表（当前选中学科对应的）
  const gradesList = ref([])
  // 临时选择
  const selectedSubject = ref(null)
  const selectedGrade = ref(null)
  // 弹窗状态
  const showConfirmReset = ref(false)
  const showConfirmModal = ref(false)
  const confirmModalConfig = ref({
    title: '',
    message: '',
    onConfirm: null,
  })

  // 设置进度
  function setProgress(newProgress) {
    progress.value = newProgress
  }

  function getProgress(newProgress) {
    return progress.value
  }

  // 设置等级信息
  function setLevelInfo(info) {
    levelInfo.value = info
  }

  // 更新进度
  function updateProgress(newProgress) {
    progress.value = newProgress
  }

  // 设置学科列表
  async function loadSubjects() {
    try {
      subjectsList.value = await getSubjects()
    } catch (e) {
      console.error('加载学科列表失败:', e)
      throw e
    }
  }

  // 获取年级列表
  async function loadGradesBySubject(subjectId) {
    try {
      const result = await getGradesBySubject(subjectId);
      console.log("loadGradesBySubject>>>>>>>", result);
      gradesList.value = result.data;
      return gradesList.value
    } catch (e) {
      console.error('加载年级列表失败:', e)
      throw e
    }
  }

  // 设置选中的学科
  function setSelectedSubject(subject) {
    selectedSubject.value = subject
  }

  function getSelectedSubject() {
    return selectedSubject.value
  }

  // 设置选中的年级
  function setSelectedGrade(subject, grade) {
    selectedGrade.value = grade
    return saveSubjectGrade(subject.id, subject.name, grade.id, grade.name)
  }

  // 设置选中的年级
  function setGrade(grade) {
    selectedGrade.value = grade
  }


  function getSelectedGrade() {
    return selectedGrade.value
  }

  // 清除选择
  function clearSelection() {
    selectedSubject.value = null
    selectedGrade.value = null
    gradesList.value = []
  }

  // 重置所有学习进度
  function resetAll() {
    progress.value = null
    levelInfo.value = null
    selectedSubject.value = null
    selectedGrade.value = null
    gradesList.value = []
  }

  // 显示确认弹窗
  function showConfirmModalFn(title, message, onConfirm) {
    confirmModalConfig.value = { title, message, onConfirm }
    showConfirmModal.value = true
  }

  // 关闭确认弹窗
  function closeConfirmModal() {
    showConfirmModal.value = false
    confirmModalConfig.value = {
      title: '',
      message: '',
      onConfirm: null,
    }
  }

  // 确认操作
  function confirmAction() {
    if (confirmModalConfig.value.onConfirm) {
      confirmModalConfig.value.onConfirm()
    }
    closeConfirmModal()
  }

  return {
    progress,
    levelInfo,
    subjectsList,
    gradesList,
    selectedSubject,
    selectedGrade,
    showConfirmReset,
    showConfirmModal,
    confirmModalConfig,
    setProgress,
    getProgress,
    setLevelInfo,
    updateProgress,
    loadSubjects,
    loadGradesBySubject,
    setSelectedSubject,
    getSelectedSubject,
    setSelectedGrade,
    setGrade,
    getSelectedGrade,
    clearSelection,
    resetAll,
    showConfirmModalFn,
    closeConfirmModal,
    confirmAction,
  }
})
