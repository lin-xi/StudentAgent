/**
 * 后端 API 调用封装。
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

export async function fetchSyllabus(subject, grade) {
  return request(`/syllabus?subject=${encodeURIComponent(subject)}&grade=${encodeURIComponent(grade)}`)
}

export async function generateQuestion(subject, grade, kpId, difficulty, questionIndex = 0) {
  return request('/generate-question', {
    method: 'POST',
    body: JSON.stringify({ subject, grade, kp_id: kpId, difficulty, question_index: questionIndex }),
  })
}

export async function generateQuestionBatch(subject, grade, kpId, difficulty) {
  const data = await request('/generate-question-batch', {
    method: 'POST',
    body: JSON.stringify({ subject, grade, kp_id: kpId, difficulty }),
  })
  return data.questions
}

export async function evaluateAnswer(subject, grade, kpId, difficulty, question, options, userAnswer, correctAnswer) {
  return request('/evaluate', {
    method: 'POST',
    body: JSON.stringify({
      subject,
      grade,
      kp_id: kpId,
      difficulty,
      question,
      options,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
    }),
  })
}
