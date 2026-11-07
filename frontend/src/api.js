import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
export const api = axios.create({ baseURL: API_URL, timeout: 70000 })

export const errMsg = (e) =>
  e?.response?.data?.detail
    ? typeof e.response.data.detail === 'string' ? e.response.data.detail : JSON.stringify(e.response.data.detail)
    : e?.message || 'Request failed'
