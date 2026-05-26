import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 10000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

export const login = (username, password) =>
  api.post('/api/login', { username, password })

export const getMe = () => api.get('/api/me')

export const getSubnets = () => api.get('/api/subnets')

export const getSubnetIps = (subnetId) =>
  api.get(`/api/subnets/${subnetId}/ips`)

export const getIpDetail = (ipId) => api.get(`/api/ips/${ipId}`)

export const occupyIp = (ipId, data) =>
  api.put(`/api/ips/${ipId}/occupy`, data)

export const releaseIp = (ipId) => api.put(`/api/ips/${ipId}/release`)

export const updateIp = (ipId, data) =>
  api.put(`/api/ips/${ipId}`, data)

export const searchIps = (q) => api.get('/api/search', { params: { q } })

export const exportUrl = '/api/export'

export const reimport = () => api.post('/api/reimport')

export default api
