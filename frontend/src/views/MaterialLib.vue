<template>
  <div class="page">
    <div class="page-header">
      <h2>📚 素材库</h2>
      <p class="page-desc">管理所有原始素材，查看拆解状态</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-total" :class="{ active: filterStatus === null }" @click="filterStatus = null">
        <div class="stat-icon">📦</div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.total }}</div>
          <div class="stat-label">素材总数</div>
        </div>
      </div>
      <div class="stat-card stat-pending" :class="{ active: filterStatus === 0 }" @click="filterStatus = 0">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.pending }}</div>
          <div class="stat-label">{{ statusText(0) }}</div>
        </div>
      </div>
      <div class="stat-card stat-done" :class="{ active: filterStatus === 1 }" @click="filterStatus = 1">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.done }}</div>
          <div class="stat-label">{{ statusText(1) }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">素材列表</span>
          <el-tag v-if="selection.length" size="small" type="primary" style="margin-left:8px">已选 {{ selection.length }} 个</el-tag>
        </div>
        <div class="toolbar-right">
          <el-select v-model="filterPlatform" placeholder="平台" clearable style="width:120px">
            <el-option v-for="p in platforms" :key="p" :label="p" :value="p" />
          </el-select>
          <el-select v-model="filterTagIds" placeholder="按标签筛选" clearable multiple collapse-tags style="width:160px">
            <el-option v-for="t in allTags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-input v-model="searchKeyword" placeholder="搜索标题或内容..." style="width:220px" clearable />
          <el-button type="primary" size="small" @click="openCreateDialog">➕ 新建素材</el-button>
          <el-button size="small" @click="triggerImportMaterial">📥 导入</el-button>
          <el-dropdown size="small" @command="handleExportMaterial">
            <el-button size="small">📤 导出 ▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
                <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <input ref="materialFileInput" type="file" accept=".json" style="display:none" @change="handleImportMaterial" />
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div class="batch-bar" v-if="selection.length">
        <span class="batch-hint">已选择 {{ selection.length }} 个素材</span>
        <div class="batch-actions">
          <el-select v-model="batchTagId" placeholder="批量添加标签" size="small" style="width:160px">
            <el-option v-for="t in allTags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-button type="primary" size="small" @click="batchAddTag" :loading="batchLoading">添加标签</el-button>
          <el-select v-model="batchStatus" placeholder="批量改状态" size="small" style="width:140px">
            <el-option v-for="opt in options.material_status" :key="opt.value" :label="opt.label" :value="Number(opt.value)" />
          </el-select>
          <el-button type="warning" size="small" @click="batchUpdateStatus" :loading="batchLoading">更新状态</el-button>
          <el-button type="danger" size="small" @click="batchDelete" :loading="batchLoading">批量删除</el-button>
        </div>
      </div>

      <el-table :data="materials" stripe style="width:100%" @selection-change="onSelectionChange" ref="tableRef">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="row-expand-content">
              <div class="expand-label">素材内容：</div>
              <div class="expand-text">{{ row.content || '（无内容）' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column type="selection" width="42" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="platform" label="平台" width="100">
          <template #default="{ row }">
            <el-tag size="small" v-if="row.platform">{{ row.platform }}</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="品类" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="success" v-if="row.category">{{ row.category }}</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="140">
          <template #default="{ row }">
            <el-tag v-for="t in materialTagsMap[row.id]" :key="t.id" size="small" type="warning" effect="plain" style="margin:0 3px 3px 0">{{ t.name }}</el-tag>
            <span v-if="!materialTagsMap[row.id] || !materialTagsMap[row.id].length" class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)" effect="dark">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">查看</el-button>
            <el-button type="success" link size="small" v-if="row.status === 0" @click="goDismantle(row)">拆解</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无素材" :image-size="80" />
        </template>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="totalCount > pageSize">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next"
          @change="fetchMaterials"
        />
      </div>
    </div>

    <!-- 素材详情弹窗 -->
    <el-dialog v-model="detailVisible" title="素材详情" width="640px" destroy-on-close>
      <div v-if="currentMaterial" class="detail-body">
        <div class="detail-row">
          <span class="detail-label">标题</span>
          <span class="detail-value">{{ currentMaterial.title }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">平台</span>
          <el-tag size="small" v-if="currentMaterial.platform">{{ currentMaterial.platform }}</el-tag>
          <span v-else class="text-muted">—</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">品类</span>
          <el-tag size="small" type="success" v-if="currentMaterial.category">{{ currentMaterial.category }}</el-tag>
          <span v-else class="text-muted">—</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">状态</span>
          <el-tag size="small" :type="statusType(currentMaterial.status)" effect="dark">
            {{ statusText(currentMaterial.status) }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">创建时间</span>
          <span class="detail-value">{{ formatDate(currentMaterial.created_at) }}</span>
        </div>
        <div class="detail-row detail-block">
          <span class="detail-label">标签</span>
          <div class="detail-tags">
            <el-tag
              v-for="t in currentMaterialTags" :key="t.id"
              closable size="small" type="warning" effect="plain"
              @close="removeTag(currentMaterial.id, t.id)"
              style="margin:0 4px 4px 0"
            >{{ t.name }}</el-tag>
            <span v-if="!currentMaterialTags.length" class="text-muted">暂无标签</span>
            <el-select v-model="selectedTagForAdd" placeholder="添加标签" size="small" style="width:130px" @change="() => { if(selectedTagForAdd){ addTag(currentMaterial.id, selectedTagForAdd); selectedTagForAdd = null } }">
              <el-option v-for="t in allTags.filter(t2 => !currentMaterialTags.some(ct => ct.id === t2.id))" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </div>
        </div>
        <!-- 关联拆解 -->
        <div class="detail-row detail-block" v-if="linkedDismantle">
          <span class="detail-label">关联拆解</span>
          <div class="linked-info">
            <div class="linked-row"><span class="linked-label">L1 主题：</span><span class="linked-val">{{ linkedDismantle.l1_topic || '—' }}</span></div>
            <div class="linked-row"><span class="linked-label">L2 策略：</span>
              <el-tag v-for="s in (linkedDismantle.l2_strategy || [])" :key="s" size="small" type="primary" style="margin-right:4px">{{ s }}</el-tag>
              <span v-if="!linkedDismantle.l2_strategy?.length" class="text-muted">—</span>
            </div>
            <div class="linked-row"><span class="linked-label">L3 结构：</span><span class="linked-val">{{ (linkedDismantle.l3_structure || []).map(s => s.name).join(' → ') || '—' }}</span></div>
            <el-button type="primary" link size="small" @click="goDismantleFromDetail" style="margin-top:4px">查看完整拆解 →</el-button>
          </div>
        </div>

        <!-- 关联裂变记录 -->
        <div class="detail-row detail-block" v-if="linkedFissions.length > 0">
          <span class="detail-label">关联裂变 ({{ linkedFissions.length }})</span>
          <div class="linked-fissions">
            <div v-for="f in linkedFissions" :key="f.id" class="fission-item">
              <span class="fission-title">{{ f.output_title || '未命名' }}</span>
              <el-tag size="small" :type="f.actual_roi ? 'success' : 'info'">
                {{ f.actual_roi ? `ROI ${f.actual_roi}x` : '未回写' }}
              </el-tag>
              <span class="fission-date">{{ f.created_at ? f.created_at.substring(0, 10) : '' }}</span>
            </div>
          </div>
        </div>

        <div class="detail-row detail-block">
          <span class="detail-label">素材内容</span>
          <pre class="detail-content" :class="{ collapsed: contentCollapsed }">{{ currentMaterial.content || '（空）' }}</pre>
          <el-button v-if="currentMaterial.content && currentMaterial.content.length > 200" type="primary" link size="small" @click="contentCollapsed = !contentCollapsed" style="margin-top:4px">
            {{ contentCollapsed ? '展开全部' : '收起' }}
          </el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="success" v-if="currentMaterial && currentMaterial.status === 0" @click="goDismantleFromDetail">去拆解 →</el-button>
      </template>
    </el-dialog>

    <!-- 新建素材弹窗 -->
    <el-dialog v-model="createDialogVisible" title="新建素材" width="560px" destroy-on-close>
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="素材标题" required>
          <el-input v-model="createForm.title" placeholder="例如：秋冬保湿面霜成分测评" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="平台">
              <el-select v-model="createForm.platform" placeholder="选择平台" style="width:100%">
                <el-option v-for="opt in options.platform" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品类">
              <el-select v-model="createForm.category" placeholder="选择品类" style="width:100%">
                <el-option v-for="opt in options.category" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="素材内容" required>
          <el-input v-model="createForm.content" type="textarea" :rows="8" resize="vertical" placeholder="粘贴完整的素材脚本/文案..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateMaterial" :loading="createLoading">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getOptions, getTags, getMaterialTags, addMaterialTag, removeMaterialTag, importMaterials, exportMaterials, getOptionsByGroup } from '../api'

const router = useRouter()

const materials = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const filterPlatform = ref('')
const filterStatus = ref(null)
const filterTagIds = ref([])
const page = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const allTags = ref([])
const materialTagsMap = ref({})
const detailVisible = ref(false)
const currentMaterial = ref(null)
const currentMaterialTags = ref([])
const selectedTagForAdd = ref(null)
const contentCollapsed = ref(true)
const linkedDismantle = ref(null)
const linkedFissions = ref([])

// 批量操作
const selection = ref([])
const batchTagId = ref(null)
const batchStatus = ref(null)
const batchLoading = ref(false)
const tableRef = ref(null)

// 新建素材弹窗
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createForm = ref({ title: '', platform: '', category: '', content: '' })

const options = ref({
  material_status: [],
  platform: [],
  category: [],
})

const fetchOptions = async () => {
  try {
    const data = await getOptions()
    options.value = { ...options.value, ...data }
  } catch (e) {
    console.error('加载选项失败', e)
  }
}

const platforms = computed(() => {
  // 从选项表加载完整平台列表，确保筛选不受当前页数据限制
  const opts = options.value.platform || []
  return opts.map(o => o.value || o.label).filter(Boolean)
})

const stats = ref({ total: 0, pending: 0, done: 0 })

const fetchStats = async () => {
  try {
    const { data } = await api.get('/dashboard/overview')
    const mat = data?.material || {}
    stats.value = {
      total: mat.total ?? 0,
      pending: mat.pending ?? 0,
      done: mat.done ?? 0,
    }
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

const statusText = (s) => {
  const opt = (options.value.material_status || []).find(o => Number(o.value) === s)
  return opt ? opt.label : '未知'
}
const statusType = (s) => {
  const types = { 0: 'info', 1: 'success', 2: 'warning' }
  return types[s] || 'info'
}
const formatDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleString('zh-CN', { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) } catch { return d }
}

const fetchMaterials = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterPlatform.value) params.platform = filterPlatform.value
    if (filterStatus.value !== null) params.status = filterStatus.value
    if (filterTagIds.value.length > 0) params.tag_ids = filterTagIds.value.join(',')
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const { data } = await api.get('/material/', { params })
    if (Array.isArray(data)) {
      materials.value = data
      totalCount.value = data.length
    } else {
      materials.value = data.items || []
      totalCount.value = data.total || 0
    }
    // 加载标签
    for (const m of materials.value) {
      fetchMaterialTagsList(m.id)
    }
  } catch (e) {
    ElMessage.error('加载失败')
  }
  loading.value = false
}

// 筛选变化时重新加载
watch([filterPlatform, filterStatus, filterTagIds, searchKeyword], () => {
  page.value = 1
  fetchMaterials()
})

const onSelectionChange = (sel) => {
  selection.value = sel
}

const viewDetail = async (row) => {
  currentMaterial.value = row
  detailVisible.value = true
  contentCollapsed.value = true
  const tags = await getMaterialTags(row.id)
  currentMaterialTags.value = tags
  materialTagsMap.value[row.id] = tags
  // 加载关联拆解
  linkedDismantle.value = null
  linkedFissions.value = []
  try {
    const { data } = await api.get(`/dismantle/by-material/${row.id}`)
    linkedDismantle.value = data
  } catch { /* 未拆解 */ }
  // 加载关联裂变
  try {
    const { data } = await api.get('/fission/', { params: { source_material_id: row.id, page_size: 100 } })
    linkedFissions.value = Array.isArray(data) ? data : (data.items || [])
  } catch { /* 无裂变记录 */ }
}

const goDismantle = (row) => {
  router.push({ path: '/', query: { material_id: row.id, title: row.title, platform: row.platform, category: row.category, content: row.content } })
}

const goDismantleFromDetail = () => {
  detailVisible.value = false
  goDismantle(currentMaterial.value)
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除素材「${row.title}」？删除后不可恢复。`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await api.delete(`/material/${row.id}`)
      ElMessage.success('删除成功')
      await fetchMaterials()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// ---- 批量操作 ----
const batchAddTag = async () => {
  if (!batchTagId.value) {
    ElMessage.warning('请选择标签')
    return
  }
  if (!selection.value.length) return
  batchLoading.value = true
  let success = 0
  for (const row of selection.value) {
    try {
      await addMaterialTag(row.id, batchTagId.value)
      await fetchMaterialTagsList(row.id)
      success++
    } catch (e) {
      // skip
    }
  }
  batchLoading.value = false
  ElMessage.success(`已为 ${success} 个素材添加标签`)
  batchTagId.value = null
}

const batchUpdateStatus = async () => {
  if (batchStatus.value === null) {
    ElMessage.warning('请选择目标状态')
    return
  }
  if (!selection.value.length) return
  batchLoading.value = true
  try {
    const ids = selection.value.map(r => r.id)
    const res = await api.put('/material/batch/status', { ids, status: batchStatus.value })
    ElMessage.success(`已更新 ${res.updated} 个素材的状态`)
    batchStatus.value = null
    selection.value = []
    await fetchMaterials()
  } catch (e) {
    ElMessage.error('状态更新失败')
  }
  batchLoading.value = false
}

const batchDelete = async () => {
  if (!selection.value.length) return
  ElMessageBox.confirm(`确认删除选中的 ${selection.value.length} 个素材？`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    batchLoading.value = true
    let success = 0
    for (const row of selection.value) {
      try {
        await api.delete(`/material/${row.id}`)
        success++
      } catch (e) { /* skip */ }
    }
    batchLoading.value = false
    ElMessage.success(`已删除 ${success} 个素材`)
    selection.value = []
    await fetchMaterials()
  }).catch(() => {})
}

// ---- Tags ----
const fetchTags = async () => {
  try {
    allTags.value = await getTags()
  } catch (e) {
    console.error('加载标签失败', e)
  }
}

const fetchMaterialTagsList = async (materialId) => {
  try {
    const tags = await getMaterialTags(materialId)
    materialTagsMap.value[materialId] = tags
  } catch (e) {
    console.error('加载素材标签失败', e)
  }
}

const addTag = async (materialId, tagId) => {
  try {
    await addMaterialTag(materialId, tagId)
    await fetchMaterialTagsList(materialId)
    if (currentMaterial.value && currentMaterial.value.id === materialId) {
      currentMaterialTags.value = materialTagsMap.value[materialId] || []
    }
    ElMessage.success('标签已添加')
  } catch (e) {
    ElMessage.error('添加标签失败')
  }
}

const removeTag = async (materialId, tagId) => {
  try {
    await removeMaterialTag(materialId, tagId)
    await fetchMaterialTagsList(materialId)
    if (currentMaterial.value && currentMaterial.value.id === materialId) {
      currentMaterialTags.value = materialTagsMap.value[materialId] || []
    }
    ElMessage.success('标签已移除')
  } catch (e) {
    ElMessage.error('移除标签失败')
  }
}

// ---- 导入导出 ----
const materialFileInput = ref(null)

const triggerImportMaterial = () => {
  materialFileInput.value?.click()
}

const handleImportMaterial = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  try {
    const res = await importMaterials(file)
    ElMessage.success(res.message || '导入成功')
    await fetchMaterials()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '导入失败')
  } finally {
    e.target.value = ''
  }
}

const handleExportMaterial = (format) => {
  const params = {}
  if (filterPlatform.value) params.platform = filterPlatform.value
  if (filterStatus.value !== null) params.status = filterStatus.value
  exportMaterials(format, params)
}

const openCreateDialog = () => {
  createForm.value = { title: '', platform: '', category: '', content: '' }
  createDialogVisible.value = true
}

const submitCreateMaterial = async () => {
  if (!createForm.value.title) {
    ElMessage.warning('请输入素材标题')
    return
  }
  if (!createForm.value.content) {
    ElMessage.warning('请输入素材内容')
    return
  }
  createLoading.value = true
  try {
    await api.post('/material/', createForm.value)
    ElMessage.success('素材创建成功')
    createDialogVisible.value = false
    await fetchMaterials()
    await fetchStats()
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  }
  createLoading.value = false
}

onMounted(() => {
  fetchMaterials()
  fetchOptions()
  fetchTags()
  fetchStats()
})
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1200px; margin: 0 auto; }

.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border-radius: 12px; padding: 18px 22px;
  box-shadow: 0 2px 10px rgba(0,0,0,.06);
  cursor: pointer; transition: all .2s;
  border: 2px solid transparent;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.stat-card.active { border-color: #667eea; }
.stat-icon { font-size: 28px; }
.stat-num { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 12px; color: #999; margin-top: 2px; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }
.text-muted { color: #ccc; }

/* 批量操作栏 */
.batch-bar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px; padding: 10px 16px;
  background: #f0f4ff; border-radius: 8px; border: 1px solid #d0d8f0;
}
.batch-hint { font-size: 13px; color: #667eea; font-weight: 500; }
.batch-actions { display: flex; align-items: center; gap: 8px; }

/* 行展开内容 */
.row-expand-content { padding: 12px 16px; background: #f8f9fa; }
.expand-label { font-size: 13px; color: #999; margin-bottom: 6px; }
.expand-text { font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; }

/* 分页 */
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 20px; }

/* Detail dialog */
.detail-body { display: flex; flex-direction: column; gap: 14px; }
.detail-row { display: flex; align-items: center; gap: 12px; }
.detail-row.detail-block { flex-direction: column; align-items: flex-start; gap: 6px; }
.detail-label { font-size: 13px; color: #999; min-width: 60px; flex-shrink: 0; }
.detail-value { font-size: 14px; color: #333; }
.detail-tags { display: flex; align-items: center; flex-wrap: wrap; gap: 0; }
.detail-content {
  font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap;
  background: #f8f9fa; padding: 14px; border-radius: 8px; width: 100%;
  max-height: 300px; overflow-y: auto;
}
.detail-content.collapsed { max-height: 120px; overflow-y: hidden; position: relative; }
.detail-content.collapsed::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 40px;
  background: linear-gradient(transparent, #f8f9fa);
}
.linked-info { display: flex; flex-direction: column; gap: 6px; }
.linked-row { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.linked-label { color: #999; min-width: 60px; flex-shrink: 0; }
.linked-val { color: #333; }
.linked-fissions { display: flex; flex-direction: column; gap: 6px; }
.fission-item { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #f8f9fa; border-radius: 6px; }
.fission-title { flex: 1; font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fission-date { font-size: 12px; color: #bbb; }
</style>
