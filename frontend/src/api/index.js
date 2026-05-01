import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function getOptions() {
  const { data } = await api.get('/options/')
  return data
}

export default api
