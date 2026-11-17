const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function request(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return response.json()
}

export const api = {
  health: () => request('/api/health'),
  listAssessments: () => request('/api/assessments'),
  createAssessment: (data: object) => request('/api/assessments', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  }),
  uploadModel: (id: number, file: File) => {
    const form = new FormData(); form.append('file', file)
    return request(`/api/assessments/${id}/model`, { method: 'POST', body: form })
  },
  runAssessment: (id: number) => request(`/api/assessments/${id}/run`, { method: 'POST' }),
  uploadDataset: (id: number, kind: string, file: File) => {
    const form = new FormData(); form.append('file', file)
    return request(`/api/assessments/${id}/datasets/${kind}`, { method: 'POST', body: form })
  }
}
