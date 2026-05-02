import axios from 'axios'

// 创建 axios 实例，统一配置 baseURL 和超时时间
const api = axios.create({
  baseURL: '/api',       // 通过 Vite 代理转发到后端
  timeout: 10000,        // 请求超时时间 10 秒
})

// ============================================================
// 全局响应拦截器 — 统一错误处理
// ============================================================
import { ElMessage } from 'element-plus'

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      // 401 未授权 → 提示登录（预留）
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
      }
      // 403 无权限
      else if (status === 403) {
        ElMessage.error('没有操作权限')
      }
      // 404 → 让组件自行处理（很多组件对 404 有特殊逻辑）
      else if (status === 404) {
        // 不弹全局提示，由组件判断
      }
      // 409 冲突 → 让组件自行处理
      else if (status === 409) {
        // 不弹全局提示，由组件判断
      }
      // 500 服务器错误
      else if (status >= 500) {
        ElMessage.error('服务器内部错误，请稍后重试')
      }
      // 其他错误（400 等）→ 让组件自行处理
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (!navigator.onLine) {
      ElMessage.error('网络已断开，请检查网络连接')
    } else {
      ElMessage.error('网络请求失败')
    }
    return Promise.reject(error)
  }
)

// ============================================================
// 选项数据（从数据库动态加载）
// ============================================================

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

// ============================================================
// 效果数据
// ============================================================

// 录入效果数据
export async function createEffect(payload) {
  const { data } = await api.post('/effect/', payload)
  return data
}

// 查询指定裂变素材的效果数据
export async function getFissionEffects(fissionId) {
  const { data } = await api.get(`/effect/fission/${fissionId}`)
  return data
}

// ============================================================
// 裂变记录
// ============================================================

// 查询裂变记录列表
export async function getFissions(params = {}) {
  const { data } = await api.get('/fission/', { params })
  return data
}

// 查询单条裂变记录详情
export async function getFissionDetail(fissionId) {
  const { data } = await api.get(`/fission/${fissionId}`)
  return data
}

// ============================================================
// 拆解
// ============================================================

// 查询素材的拆解记录
export async function getDismantleByMaterial(materialId) {
  const { data } = await api.get(`/dismantle/by-material/${materialId}`)
  return data
}

// 查询拆解详情
export async function getDismantle(dismantleId) {
  const { data } = await api.get(`/dismantle/${dismantleId}`)
  return data
}

// 创建拆解记录
export async function createDismantle(payload) {
  const { data } = await api.post('/dismantle/', payload)
  return data
}

// 更新拆解记录
export async function updateDismantle(dismantleId, payload) {
  const { data } = await api.put(`/dismantle/${dismantleId}`, payload)
  return data
}

// ============================================================
// 裂变记录状态
// ============================================================

// 更新裂变记录状态（状态流转：0草稿→1待审核→2已采用→3已投放）
export async function updateFissionStatus(fissionId, status) {
  const { data } = await api.put(`/fission/${fissionId}/status`, null, { params: { status } })
  return data
}

// ============================================================
// 标签
// ============================================================

// 获取所有标签列表
export async function getTags() {
  const { data } = await api.get('/tag/')
  return data
}

// 获取指定素材的标签列表
export async function getMaterialTags(materialId) {
  const { data } = await api.get(`/tag/material/${materialId}`)
  return data
}

// 为素材添加标签
export async function addMaterialTag(materialId, tagId) {
  const { data } = await api.post(`/tag/material/${materialId}/tags`, { tag_id: tagId })
  return data
}

// 移除素材的标签
export async function removeMaterialTag(materialId, tagId) {
  await api.delete(`/tag/material/${materialId}/tags/${tagId}`)
}

// 从已有 option 创建标签
export async function createTagFromOption(optionId) {
  const { data } = await api.post('/tag/from-option', { option_id: optionId })
  return data
}

// 创建标签（支持 option_id）
export async function createTag(payload) {
  const { data } = await api.post('/tag/', payload)
  return data
}

// 更新标签（支持 option_id）
export async function updateTag(tagId, payload) {
  const { data } = await api.put(`/tag/${tagId}`, payload)
  return data
}

// 删除标签
export async function deleteTag(tagId) {
  await api.delete(`/tag/${tagId}`)
}

// ============================================================
// 数据导入导出
// ============================================================

// 导入素材（JSON 文件）
export async function importMaterials(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/material/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// 导出素材（触发浏览器下载）
export function exportMaterials(format = 'json', params = {}) {
  const query = new URLSearchParams({ format, ...params }).toString()
  window.open(`/api/material/export?${query}`, '_blank')
}

// 导入骨架（JSON 文件）
export async function importSkeletons(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/skeleton/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// 导出骨架（触发浏览器下载）
export function exportSkeletons(format = 'json', params = {}) {
  const query = new URLSearchParams({ format, ...params }).toString()
  window.open(`/api/skeleton/export?${query}`, '_blank')
}

export default api
