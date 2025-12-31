import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Projects
export const createProject = async (formData) => {
  const response = await api.post('/projects/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getProject = async (projectId) => {
  const response = await api.get(`/projects/${projectId}`)
  return response.data
}

export const listProjects = async (params = {}) => {
  const response = await api.get('/projects/', { params })
  return response.data
}

// Trades
export const getSupportedTrades = async () => {
  const response = await api.get('/projects/trades/supported')
  return response.data
}

// Takeoffs
export const processTakeoff = async (projectId) => {
  const response = await api.post(`/takeoffs/${projectId}/process`)
  return response.data
}

export const getTakeoff = async (projectId) => {
  const response = await api.get(`/takeoffs/${projectId}`)
  return response.data
}

export const cancelTakeoff = async (projectId) => {
  const response = await api.post(`/takeoffs/${projectId}/cancel`)
  return response.data
}

// Reviews
export const getReviewQueue = async () => {
  const response = await api.get('/reviews/queue')
  return response.data
}

export const getReview = async (reviewId) => {
  const response = await api.get(`/reviews/${reviewId}`)
  return response.data
}

export const approveReview = async (reviewId, expertData) => {
  const response = await api.post(`/reviews/${reviewId}/approve`, expertData)
  return response.data
}

// Exports
export const exportTakeoff = async (projectId, format = 'excel') => {
  const response = await api.get(`/exports/${projectId}/${format}`, {
    responseType: 'blob'
  })
  return response.data
}

// Legacy endpoints (for backward compatibility)
export const processDocument = async (formData) => {
  const response = await api.post('/process-document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const generateReport = async (results, format = 'html') => {
  const response = await api.post(
    '/generate-report',
    { results, format },
    { responseType: 'blob' }
  )
  return response.data
}

export default api
