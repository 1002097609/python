import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// ========== 选项数据（从数据库动态加载）==========

// 获取所有选项，返回按分组的结构
export async function getOptions() {
  const { data } = await api.get('/options/')
  return data
}

// 获取指定分组的选项列表
export async function getOptionsByGroup(groupKey) {
  const { data } = await api.get('/option/', { params: { group_key: groupKey } })
  return data
}

// 创建一个新选项
export async function createOption(payload) {
  const { data } = await api.post('/option/', payload)
  return data
}

// 更新一个选项
export async function updateOption(optionId, payload) {
  const { data } = await api.put(`/option/${optionId}`, payload)
  return data
}

// 删除一个选项
export async function deleteOption(optionId) {
  await api.delete(`/option/${optionId}`)
}

export default api
