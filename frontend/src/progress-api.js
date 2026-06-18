/**
 * 用户学习进度 API 封装（按难度等级分记录）。
 */
const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

/**
 * 获取学科列表
 */
export async function getSubjects() {
  return request('/subjects', {method: "GET"})
}

/**
 * 获取指定学科的年级列表
 */
export async function getGradesBySubject(subjectId) {
  return request(`/subjects/${subjectId}/grades`)
}

export async function saveSubjectGrade(subjectId, subject, gradeId, grade) {
  return request('/save_subject_grade', {
    method: 'POST',
    body: JSON.stringify({
      subject,
      subject_id: subjectId,
      grade_id: gradeId,
      grade,
    }),
  })
}

/**
 * 获取用户学习进度列表
 * @param {number} subjectId - 可选，过滤条件
 * @param {number} gradeId - 可选，过滤条件
 * check_in :  false
 * check_in_date:  null
 * course_id:  61
 * grade_id: 0
 * id: 61
 * kp: "计算机系统：计算机系统概述"
 * kp_level: 0
 * subject_id: 0
 * wrong_count: 0
 */
export async function getProgress(subjectId, gradeId) {
  const result = await request(`/progress?subject_id=${subjectId}&grade_id=${gradeId}`, { method: 'GET' });
  console.log("getProgress>>>", result)
  const progressList = [];
  const progressMap = new Map();
  if (result.code == 200 && result.data && result.data.length > 0) {

    for (let item of result.data) {
      if (!progressMap.has(item.kp)) {
        progressList.push({
          id: item.id,
          kp: item.kp,
          subject_id: item.subject_id,
          grade_id: item.grade_id,
          status: {1: false, 2: false, 3: false},
          check_in_date: "",
          allComplete: false,
          wrong_count: 0
        })
        progressMap.set(item.kp, progressList.length - 1);
      }
      const pItem = progressList[progressMap.get(item.kp)];
      pItem.status[item.kp_level] = item.check_in;
      pItem.wrong_count += item.wrong_count;
      if (item.kp_level === 3 && item.check_in) {
        pItem.allComplete = true;
        pItem.check_in_date = item.check_in_date;
      }
    }
  }
  return progressList;
}

/**
 * 保存单个 KP 的难度等级进度
 * @param {Object} progressData - 进度数据
 * @param {number} progressData.subject_id - 学科 ID
 * @param {number} progressData.grade_id - 年级 ID
 * @param {number} progressData.course_id - 课程 ID/KP ID
 * @param {string} progressData.kp_level - 难度等级 'basic'|'intermediate'|'advanced'
 * @param {boolean} progressData.check_in - 是否完成打卡
 * @param {number} progressData.wrong_count - 错题数量
 * @param {string} progressData.check_in_date - 完成时间 YYYY-MM-DD
 */
export async function saveProgress(progressData) {
  return request('/saveProgress', {
    method: 'POST',
    body: JSON.stringify({
      subject_id: progressData.subject_id,
      grade_id: progressData.grade_id,
      course_id: progressData.course_id,
      kp_level: progressData.kp_level,
      check_in: progressData.check_in,
      wrong_count: progressData.wrong_count,
      check_in_date: progressData.check_in_date,
    }),
  })
}

/**
 * 删除用户学习进度
 */
export async function deleteProgress(subjectId, gradeId, courseId) {
  const params = new URLSearchParams()
  if (subjectId) params.append('subject_id', subjectId)
  if (gradeId) params.append('grade_id', gradeId)
  if (courseId) params.append('course_id', courseId)
  return request(`/progress?${params.toString()}`, {
    method: 'DELETE',
  })
}
