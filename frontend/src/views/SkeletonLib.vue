<template>
  <div class="page">
    <div class="page-header">
      <h2>🦴 骨架库</h2>
      <p class="page-desc">管理从素材中提取的可复用骨架，效果数据持续积累</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-blue">
        <div class="stat-icon">🦴</div>
        <div class="stat-info">
          <div class="stat-num">{{ skeletons.length }}</div>
          <div class="stat-label">骨架总数</div>
        </div>
      </div>
      <div class="stat-card stat-green">
        <div class="stat-icon">🔥</div>
        <div class="stat-info">
          <div class="stat-num">{{ highUsageCount }}</div>
          <div class="stat-label">高复用骨架</div>
        </div>
      </div>
      <div class="stat-card stat-orange">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-num">{{ totalUsage }}</div>
          <div class="stat-label">累计裂变次数</div>
        </div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">骨架列表</span>
        </div>
        <el-select v-model="filterType" placeholder="按类型筛选" clearable style="width:160px">
          <el-option v-for="t in skeletonTypes" :key="t" :label="t" :value="t" />
        </el-select>
      </div>

      <div v-if="filteredSkeletons.length === 0" class="empty-state">
        <div class="empty-icon">🦴</div>
        <div class="empty-text">暂无骨架</div>
        <div class="empty-hint">在「素材拆解」页面完成拆解并提取骨架后，骨架会自动出现在这里</div>
      </div>

      <el-row :gutter="16" v-else>
        <el-col :span="8" v-for="sk in filteredSkeletons" :key="sk.id">
          <div class="skeleton-card" @click="viewDetail(sk)">
            <div class="sk-header">
              <div class="sk-title">{{ sk.name }}</div>
              <el-tag size="small" type="success" effect="plain">{{ sk.skeleton_type }}</el-tag>
            </div>
            <div class="sk-metrics">
              <div class="metric">
                <span class="metric-value">{{ sk.usage_count || 0 }}</span>
                <span class="metric-label">使用次数</span>
              </div>
              <div class="metric" v-if="sk.avg_roi">
                <span class="metric-value">{{ Number(sk.avg_roi).toFixed(1) }}x</span>
                <span class="metric-label">平均ROI</span>
              </div>
              <div class="metric" v-if="sk.avg_ctr">
                <span class="metric-value">{{ Number(sk.avg_ctr).toFixed(1) }}%</span>
                <span class="metric-label">平均CTR</span>
              </div>
            </div>
            <div class="sk-footer">
              <span class="sk-date">{{ formatDate(sk.created_at) }}</span>
              <div class="sk-actions" @click.stop>
                <el-button type="primary" link size="small" @click="goFission(sk)">去裂变 →</el-button>
                <el-button type="danger" link size="small" @click="handleDelete(sk)">删除</el-button>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 骨架详情弹窗 -->
    <el-dialog v-model="detailVisible" title="骨架详情" width="640px" destroy-on-close>
      <div v-if="currentSkeleton" class="detail-body">
        <div class="detail-row">
          <span class="detail-label">名称</span>
          <span class="detail-value">{{ currentSkeleton.name }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">类型</span>
          <el-tag size="small" type="success">{{ currentSkeleton.skeleton_type }}</el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">使用次数</span>
          <span class="detail-value">{{ currentSkeleton.usage_count || 0 }}</span>
        </div>
        <div class="detail-row" v-if="currentSkeleton.avg_roi">
          <span class="detail-label">平均ROI</span>
          <span class="detail-value highlight">{{ Number(currentSkeleton.avg_roi).toFixed(1) }}x</span>
        </div>
        <div class="detail-row" v-if="currentSkeleton.avg_ctr">
          <span class="detail-label">平均CTR</span>
          <span class="detail-value highlight">{{ Number(currentSkeleton.avg_ctr).toFixed(1) }}%</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">创建时间</span>
          <span class="detail-value">{{ formatDate(currentSkeleton.created_at) }}</span>
        </div>
        <div class="detail-row detail-block" v-if="currentSkeleton.strategy_desc">
          <span class="detail-label">策略描述</span>
          <div class="detail-content">{{ currentSkeleton.strategy_desc }}</div>
        </div>
        <div class="detail-row detail-block" v-if="currentSkeleton.structure_json">
          <span class="detail-label">结构 JSON</span>
          <pre class="detail-content code">{{ formatJson(currentSkeleton.structure_json) }}</pre>
        </div>
        <div class="detail-row detail-block" v-if="currentSkeleton.elements_json">
          <span class="detail-label">元素 JSON</span>
          <pre class="detail-content code">{{ formatJson(currentSkeleton.elements_json) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" v-if="currentSkeleton" @click="goFissionFromDetail">去裂变 →</el-button>
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

const skeletons = ref([])
const filterType = ref('')
const detailVisible = ref(false)
const currentSkeleton = ref(null)

const skeletonTypes = computed(() => {
  const set = new Set(skeletons.value.map(s => s.skeleton_type).filter(Boolean))
  return [...set]
})

const filteredSkeletons = computed(() => {
  if (!filterType.value) return skeletons.value
  return skeletons.value.filter(s => s.skeleton_type === filterType.value)
})

const highUsageCount = computed(() => {
  if (!skeletons.value.length) return 0
  // 动态计算：使用率超过平均值的骨架视为"高复用"
  const avgUsage = skeletons.value.reduce((sum, s) => sum + (s.usage_count || 0), 0) / skeletons.value.length
  return skeletons.value.filter(s => (s.usage_count || 0) > avgUsage).length
})
const totalUsage = computed(() => skeletons.value.reduce((sum, s) => sum + (s.usage_count || 0), 0))

const formatDate = (d) => {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString('zh-CN') } catch { return d }
}

const formatJson = (val) => {
  try {
    if (typeof val === 'string') val = JSON.parse(val)
    return JSON.stringify(val, null, 2)
  } catch { return String(val) }
}

const fetchSkeletons = async () => {
  try {
    const { data } = await api.get('/skeleton/')
    skeletons.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const viewDetail = async (sk) => {
  // 获取完整详情（包含 structure_json / elements_json）
  try {
    const { data } = await api.get(`/skeleton/${sk.id}`)
    currentSkeleton.value = data
    detailVisible.value = true
  } catch (e) {
    // 降级使用列表数据
    currentSkeleton.value = sk
    detailVisible.value = true
  }
}

const goFission = (sk) => {
  router.push({ path: '/fission', query: { skeleton_id: sk.id } })
}

const goFissionFromDetail = () => {
  detailVisible.value = false
  goFission(currentSkeleton.value)
}

const handleDelete = (sk) => {
  ElMessageBox.confirm(`确认删除骨架「${sk.name}」？删除后不可恢复。`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await api.delete(`/skeleton/${sk.id}`)
      ElMessage.success('删除成功')
      await fetchSkeletons()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(fetchSkeletons)
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
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #43e97b, #38f9d7); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }

.empty-state { text-align: center; padding: 48px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { font-size: 16px; font-weight: 600; color: #666; margin-bottom: 8px; }
.empty-hint { font-size: 13px; color: #aaa; }

.skeleton-card {
  border: 1px solid #e8e8e8; border-radius: 12px; padding: 18px;
  margin-bottom: 16px; transition: all .2s; cursor: pointer;
}
.skeleton-card:hover {
  border-color: #43e97b;
  box-shadow: 0 4px 16px rgba(67,233,123,.15);
  transform: translateY(-2px);
}
.sk-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 14px; }
.sk-title { font-size: 14px; font-weight: 600; color: #333; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sk-metrics { display: flex; gap: 16px; margin-bottom: 14px; padding: 12px; background: #f8f9fa; border-radius: 8px; }
.metric { display: flex; flex-direction: column; align-items: center; }
.metric-value { font-size: 16px; font-weight: 700; color: #27ae60; }
.metric-label { font-size: 11px; color: #999; margin-top: 2px; }

.sk-footer { display: flex; align-items: center; justify-content: space-between; }
.sk-date { font-size: 12px; color: #bbb; }
.sk-actions { display: flex; gap: 4px; }

/* Detail dialog */
.detail-body { display: flex; flex-direction: column; gap: 14px; }
.detail-row { display: flex; align-items: center; gap: 12px; }
.detail-row.detail-block { flex-direction: column; align-items: flex-start; gap: 6px; }
.detail-label { font-size: 13px; color: #999; min-width: 70px; flex-shrink: 0; }
.detail-value { font-size: 14px; color: #333; }
.detail-value.highlight { color: #27ae60; font-weight: 600; }
.detail-content {
  font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap;
  background: #f8f9fa; padding: 14px; border-radius: 8px; width: 100%;
  max-height: 200px; overflow-y: auto;
}
.detail-content.code {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px; line-height: 1.6;
}
</style>
