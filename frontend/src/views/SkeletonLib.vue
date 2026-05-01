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
          <div class="stat-num">{{ totalCount }}</div>
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

    <!-- 筛选 + 排序 -->
    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">骨架列表</span>
        </div>
        <div class="toolbar-right">
          <el-select v-model="filterPlatform" placeholder="平台" clearable style="width:120px">
            <el-option v-for="p in platforms" :key="p" :label="p" :value="p" />
          </el-select>
          <el-select v-model="filterType" placeholder="类型" clearable style="width:140px">
            <el-option v-for="t in skeletonTypes" :key="t" :label="t" :value="t" />
          </el-select>
          <el-select v-model="sortBy" placeholder="排序" style="width:130px">
            <el-option label="使用次数" value="usage_count" />
            <el-option label="平均 ROI" value="avg_roi" />
            <el-option label="平均 CTR" value="avg_ctr" />
            <el-option label="创建时间" value="created_at" />
          </el-select>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="skeletons.length === 0" class="empty-state">
        <div class="empty-icon">🦴</div>
        <div class="empty-text">暂无骨架</div>
        <div class="empty-hint">在「素材拆解」页面完成拆解并提取骨架后，骨架会自动出现在这里</div>
      </div>

      <el-row :gutter="16" v-else>
        <el-col :span="8" v-for="sk in skeletons" :key="sk.id">
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

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="totalCount > pageSize">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[12, 24, 36]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next"
          @change="fetchSkeletons"
        />
      </div>
    </div>

    <!-- 骨架详情弹窗 -->
    <el-dialog v-model="detailVisible" title="骨架详情" width="720px" destroy-on-close>
      <div v-if="currentSkeleton" class="detail-body">
        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="section-title">📋 基本信息</div>
          <div class="detail-row">
            <span class="detail-label">名称</span>
            <span class="detail-value">{{ currentSkeleton.name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">类型</span>
            <el-tag size="small" type="success">{{ currentSkeleton.skeleton_type }}</el-tag>
          </div>
          <div class="detail-row" v-if="currentSkeleton.platform">
            <span class="detail-label">平台</span>
            <el-tag size="small" type="primary">{{ currentSkeleton.platform }}</el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">效果</span>
            <div class="detail-metrics">
              <span class="dm-item">使用 <strong>{{ currentSkeleton.usage_count || 0 }}</strong> 次</span>
              <span class="dm-item" v-if="currentSkeleton.avg_roi">ROI <strong>{{ Number(currentSkeleton.avg_roi).toFixed(1) }}x</strong></span>
              <span class="dm-item" v-if="currentSkeleton.avg_ctr">CTR <strong>{{ Number(currentSkeleton.avg_ctr).toFixed(1) }}%</strong></span>
            </div>
          </div>
          <div class="detail-row" v-if="currentSkeleton.style_tags && currentSkeleton.style_tags.length">
            <span class="detail-label">风格</span>
            <div class="detail-tags">
              <el-tag v-for="tag in currentSkeleton.style_tags" :key="tag" size="small" type="warning" effect="plain">{{ tag }}</el-tag>
            </div>
          </div>
        </div>

        <!-- L2 策略层 -->
        <div class="detail-section" v-if="currentSkeleton.strategy_desc">
          <div class="section-title">🎯 L2 策略层</div>
          <div class="strategy-box">{{ currentSkeleton.strategy_desc }}</div>
        </div>

        <!-- L3 结构层 -->
        <div class="detail-section" v-if="currentSkeleton.structure_json && currentSkeleton.structure_json.length">
          <div class="section-title">🏗️ L3 结构层</div>
          <div class="structure-timeline">
            <div class="structure-step" v-for="(section, idx) in currentSkeleton.structure_json" :key="idx">
              <div class="step-line">
                <div class="step-dot">{{ idx + 1 }}</div>
                <div class="step-connector" v-if="idx < currentSkeleton.structure_json.length - 1"></div>
              </div>
              <div class="step-card">
                <div class="step-name">{{ section.name }}</div>
                <div class="step-function">{{ section.function }}</div>
                <div class="step-ratio">
                  <el-progress :percentage="section.ratio" :color="ratioColor(section.ratio)" :stroke-width="6" :show-text="false" />
                  <span class="ratio-text">{{ section.ratio }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- L4 元素层 -->
        <div class="detail-section" v-if="currentSkeleton.elements_json">
          <div class="section-title">🧩 L4 元素层</div>
          <div class="elements-grid">
            <div class="element-card" v-if="currentSkeleton.elements_json.title_formula">
              <div class="element-icon">📝</div>
              <div class="element-label">标题公式</div>
              <div class="element-value">{{ currentSkeleton.elements_json.title_formula }}</div>
            </div>
            <div class="element-card" v-if="currentSkeleton.elements_json.hook">
              <div class="element-icon">🪝</div>
              <div class="element-label">钩子句式</div>
              <div class="element-value">{{ currentSkeleton.elements_json.hook }}</div>
            </div>
            <div class="element-card" v-if="currentSkeleton.elements_json.transition">
              <div class="element-icon">🔀</div>
              <div class="element-label">转折方式</div>
              <div class="element-value">{{ currentSkeleton.elements_json.transition }}</div>
            </div>
            <div class="element-card" v-if="currentSkeleton.elements_json.interaction">
              <div class="element-icon">💬</div>
              <div class="element-label">互动设计</div>
              <div class="element-value">{{ currentSkeleton.elements_json.interaction }}</div>
            </div>
          </div>
        </div>

        <!-- 适用场景 -->
        <div class="detail-section" v-if="currentSkeleton.suitable_for && currentSkeleton.suitable_for.length">
          <div class="section-title">🎬 适用场景</div>
          <div class="detail-tags">
            <el-tag v-for="s in currentSkeleton.suitable_for" :key="s" size="small" type="info" effect="plain">{{ s }}</el-tag>
          </div>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const router = useRouter()

const skeletons = ref([])
const loading = ref(false)
const filterType = ref('')
const filterPlatform = ref('')
const sortBy = ref('usage_count')
const page = ref(1)
const pageSize = ref(12)
const totalCount = ref(0)
const allSkeletons = ref([])  // 用于统计卡片（总数、高复用等）

const detailVisible = ref(false)
const currentSkeleton = ref(null)

// 骨架类型从当前加载的数据中提取
const skeletonTypes = computed(() => {
  const set = new Set(allSkeletons.value.map(s => s.skeleton_type).filter(Boolean))
  return [...set]
})

// 平台列表从所有骨架中提取
const platforms = computed(() => {
  const set = new Set(allSkeletons.value.map(s => s.platform).filter(Boolean))
  return [...set]
})

// 统计数字基于全量数据
const highUsageCount = computed(() => {
  if (!allSkeletons.value.length) return 0
  const avgUsage = allSkeletons.value.reduce((sum, s) => sum + (s.usage_count || 0), 0) / allSkeletons.value.length
  return allSkeletons.value.filter(s => (s.usage_count || 0) > avgUsage).length
})
const totalUsage = computed(() => allSkeletons.value.reduce((sum, s) => sum + (s.usage_count || 0), 0))

const formatDate = (d) => {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString('zh-CN') } catch { return d }
}

const ratioColor = (ratio) => {
  if (ratio >= 50) return '#27ae60'
  if (ratio >= 25) return '#667eea'
  return '#f093fb'
}

// 加载全量数据（用于统计卡片和筛选列表）
const fetchAllSkeletons = async () => {
  try {
    const { data } = await api.get('/skeleton/', { params: { page: 1, page_size: 1000 } })
    if (Array.isArray(data)) {
      allSkeletons.value = data
    } else {
      allSkeletons.value = data.items || []
    }
  } catch (e) {
    console.error('加载全量骨架失败', e)
  }
}

// 分页加载列表数据
const fetchSkeletons = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      sort_by: sortBy.value,
    }
    if (filterType.value) params.skeleton_type = filterType.value
    if (filterPlatform.value) params.platform = filterPlatform.value
    const { data } = await api.get('/skeleton/', { params })
    // 兼容旧格式（纯数组）和新格式（分页对象）
    if (Array.isArray(data)) {
      skeletons.value = data
      totalCount.value = data.length
    } else {
      skeletons.value = data.items || []
      totalCount.value = data.total || 0
    }
  } catch (e) {
    ElMessage.error('加载失败')
  }
  loading.value = false
}

const viewDetail = async (sk) => {
  loading.value = true
  try {
    const { data } = await api.get(`/skeleton/${sk.id}`)
    currentSkeleton.value = data
    detailVisible.value = true
  } catch (e) {
    currentSkeleton.value = sk
    detailVisible.value = true
  }
  loading.value = false
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
      await Promise.all([fetchSkeletons(), fetchAllSkeletons()])
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 筛选条件变化时重置到第一页
watch([filterType, filterPlatform, sortBy], () => {
  page.value = 1
})

onMounted(async () => {
  await fetchAllSkeletons()
  await fetchSkeletons()
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
}
.stat-icon { font-size: 28px; }
.stat-num { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 12px; color: #999; margin-top: 2px; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #43e97b, #38f9d7); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }

.loading-state { padding: 20px 0; }

.empty-state { text-align: center; padding: 48px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { font-size: 16px; font-weight: 600; color: #666; margin-bottom: 8px; }
.empty-hint { font-size: 13px; color: #aaa; }

.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 20px; }

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
.detail-body { display: flex; flex-direction: column; gap: 16px; }
.detail-section { border: 1px solid #f0f0f0; border-radius: 10px; padding: 16px; }
.section-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #f5f5f5; }
.detail-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.detail-label { font-size: 13px; color: #999; min-width: 60px; flex-shrink: 0; }
.detail-value { font-size: 14px; color: #333; }
.detail-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.detail-metrics { display: flex; gap: 16px; flex-wrap: wrap; }
.dm-item { font-size: 13px; color: #666; }
.dm-item strong { color: #27ae60; margin: 0 2px; }

/* Strategy box */
.strategy-box {
  font-size: 14px; color: #444; line-height: 1.8;
  background: linear-gradient(135deg, #f5f7fa, #e8ecf1);
  padding: 14px 18px; border-radius: 8px;
  border-left: 4px solid #667eea;
}

/* Structure timeline */
.structure-timeline { display: flex; flex-direction: column; gap: 0; }
.structure-step { display: flex; gap: 12px; }
.step-line { display: flex; flex-direction: column; align-items: center; width: 28px; flex-shrink: 0; }
.step-dot {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: #fff; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.step-connector { width: 2px; flex: 1; background: #e0e8f0; margin: 4px 0; }
.step-card {
  flex: 1; background: #f8f9fa; border-radius: 8px; padding: 12px 16px;
  margin-bottom: 8px;
}
.step-name { font-size: 14px; font-weight: 600; color: #333; }
.step-function { font-size: 12px; color: #888; margin-top: 2px; }
.step-ratio { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex: 1; }
.ratio-text { font-size: 12px; color: #667eea; font-weight: 600; white-space: nowrap; }

/* Elements grid */
.elements-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.element-card {
  background: #f8f9fa; border-radius: 8px; padding: 12px 14px;
  border: 1px solid #eee;
}
.element-icon { font-size: 20px; margin-bottom: 4px; }
.element-label { font-size: 12px; color: #999; }
.element-value { font-size: 13px; color: #333; margin-top: 4px; line-height: 1.6; }
</style>
