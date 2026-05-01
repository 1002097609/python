<template>
  <div class="page">
    <div class="page-header">
      <h2>📚 素材库</h2>
      <p class="page-desc">管理所有原始素材，标记拆解状态</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-total">
        <div class="stat-icon">📦</div>
        <div class="stat-info">
          <div class="stat-num">{{ materials.length }}</div>
          <div class="stat-label">素材总数</div>
        </div>
      </div>
      <div class="stat-card stat-pending">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <div class="stat-num">{{ pendingCount }}</div>
          <div class="stat-label">待拆解</div>
        </div>
      </div>
      <div class="stat-card stat-done">
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
        <el-input
          v-model="searchKeyword"
          placeholder="搜索标题..."
          style="width:220px"
          clearable
          prefix-icon="Search"
        />
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
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">查看</el-button>
            <el-button type="success" link size="small" v-if="row.status === 0" @click="goDismantle(row)">拆解</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无素材，请先在「素材拆解」页面录入" :image-size="80" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const materials = ref([])
const searchKeyword = ref('')

const filteredMaterials = computed(() => {
  if (!searchKeyword.value) return materials.value
  const kw = searchKeyword.value.toLowerCase()
  return materials.value.filter(m => m.title.toLowerCase().includes(kw))
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
  ElMessage.info(`素材详情: ${row.title}`)
}

const goDismantle = (row) => {
  ElMessage.success(`请前往「素材拆解」页面，录入标题「${row.title}」进行拆解`)
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
}
.stat-icon { font-size: 28px; }
.stat-num { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 12px; color: #999; margin-top: 2px; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }
.text-muted { color: #ccc; }
</style>
