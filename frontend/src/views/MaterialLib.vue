<template>
  <div class="page">
    <div class="page-header">
      <h2>📚 素材库</h2>
      <p class="page-desc">管理所有原始素材，查看拆解状态</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-total" :class="{ active: filterStatus === '' }" @click="filterStatus = ''">
        <div class="stat-icon">📦</div>
        <div class="stat-info">
          <div class="stat-num">{{ materials.length }}</div>
          <div class="stat-label">素材总数</div>
        </div>
      </div>
      <div class="stat-card stat-pending" :class="{ active: filterStatus === 0 }" @click="filterStatus = 0">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <div class="stat-num">{{ pendingCount }}</div>
          <div class="stat-label">待拆解</div>
        </div>
      </div>
      <div class="stat-card stat-done" :class="{ active: filterStatus === 1 }" @click="filterStatus = 1">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-num">{{ doneCount }}</div>
          <div class="stat-label">已拆解</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">素材列表</span>
        </div>
        <div class="toolbar-right">
          <el-select v-model="filterPlatform" placeholder="平台" clearable style="width:120px">
            <el-option v-for="p in platforms" :key="p" :label="p" :value="p" />
          </el-select>
          <el-input v-model="searchKeyword" placeholder="搜索标题..." style="width:200px" clearable />
        </div>
      </div>

      <el-table :data="filteredMaterials" stripe style="width:100%">
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
          <span class="detail-label">素材内容</span>
          <pre class="detail-content">{{ currentMaterial.content || '（空）' }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="success" v-if="currentMaterial && currentMaterial.status === 0" @click="goDismantleFromDetail">去拆解 →</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const router = useRouter()

const materials = ref([])
const searchKeyword = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')
const detailVisible = ref(false)
const currentMaterial = ref(null)

const platforms = computed(() => {
  const set = new Set(materials.value.map(m => m.platform).filter(Boolean))
  return [...set]
})

const filteredMaterials = computed(() => {
  let list = materials.value
  if (filterStatus.value !== '') list = list.filter(m => m.status === filterStatus.value)
  if (filterPlatform.value) list = list.filter(m => m.platform === filterPlatform.value)
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(m => m.title.toLowerCase().includes(kw))
  }
  return list
})

const pendingCount = computed(() => materials.value.filter(m => m.status === 0).length)
const doneCount = computed(() => materials.value.filter(m => m.status === 1).length)

const statusType = (s) => s === 0 ? 'info' : s === 1 ? 'success' : 'warning'
const statusText = (s) => ['未拆解', '已拆解', '已归档'][s] || '未知'
const formatDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleString('zh-CN', { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) } catch { return d }
}

const fetchMaterials = async () => {
  try {
    const { data } = await api.get('/material/')
    materials.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const viewDetail = (row) => {
  currentMaterial.value = row
  detailVisible.value = true
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

onMounted(fetchMaterials)
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

/* Detail dialog */
.detail-body { display: flex; flex-direction: column; gap: 14px; }
.detail-row { display: flex; align-items: center; gap: 12px; }
.detail-row.detail-block { flex-direction: column; align-items: flex-start; gap: 6px; }
.detail-label { font-size: 13px; color: #999; min-width: 60px; flex-shrink: 0; }
.detail-value { font-size: 14px; color: #333; }
.detail-content {
  font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap;
  background: #f8f9fa; padding: 14px; border-radius: 8px; width: 100%;
  max-height: 300px; overflow-y: auto;
}
</style>
