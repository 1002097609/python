<template>
  <div class="page">
    <div class="page-header">
      <div class="page-header-left">
        <h2>📊 数据统计</h2>
        <p class="page-desc">系统运营数据概览 — 素材、骨架、裂变、效果全链路监控</p>
      </div>
      <div class="page-header-right">
        <el-button type="primary" link @click="fetchAll" :loading="refreshing" title="刷新数据">
          🔄 刷新
        </el-button>
        <el-tooltip content="自动刷新间隔" placement="bottom">
          <el-select v-model="refreshInterval" style="width:100px" size="small" @change="restartAutoRefresh">
            <el-option label="关闭" :value="0" />
            <el-option label="30秒" :value="30" />
            <el-option label="60秒" :value="60" />
            <el-option label="5分钟" :value="300" />
          </el-select>
        </el-tooltip>
      </div>
    </div>

    <!-- 概览卡片 -->
    <div class="stats-grid">
      <div class="stat-card stat-blue">
        <div class="stat-icon">📦</div>
        <div class="stat-info">
          <div class="stat-num">{{ overview.material?.total ?? '—' }}</div>
          <div class="stat-label">素材总数</div>
          <div class="stat-sub">{{ overview.material?.pending ?? 0 }} 未拆解 / {{ overview.material?.done ?? 0 }} 已拆解</div>
        </div>
      </div>
      <div class="stat-card stat-purple">
        <div class="stat-icon">🦴</div>
        <div class="stat-info">
          <div class="stat-num">{{ overview.skeleton?.total ?? '—' }}</div>
          <div class="stat-label">骨架总数</div>
          <div class="stat-sub">{{ overview.fission?.total ?? 0 }} 次裂变产出</div>
        </div>
      </div>
      <div class="stat-card stat-green">
        <div class="stat-icon">⚡</div>
        <div class="stat-info">
          <div class="stat-num">{{ overview.fission?.total ?? '—' }}</div>
          <div class="stat-label">裂变总数</div>
          <div class="stat-sub">{{ overview.fission?.draft ?? 0 }} 草稿 / {{ overview.fission?.active ?? 0 }} 已投放</div>
        </div>
      </div>
      <div class="stat-card stat-orange">
        <div class="stat-icon">📈</div>
        <div class="stat-info">
          <div class="stat-num">{{ formatMoney(overview.effect?.total_revenue) }}</div>
          <div class="stat-label">累计收入</div>
          <div class="stat-sub">平均 ROI {{ overview.effect?.avg_roi?.toFixed(2) ?? '—' }}x</div>
        </div>
      </div>
    </div>

    <!-- 图表区域第一行 -->
    <div class="charts-row">
      <!-- 品类分布饼图 -->
      <div class="card chart-card">
        <div class="chart-title">🏪 品类分布 <span class="drill-hint">点击扇区跳转素材库</span></div>
        <div v-if="categoryData.length > 0" ref="categoryChartRef" class="chart-container"></div>
        <div v-else class="chart-empty"><el-empty description="暂无品类数据" :image-size="60" /></div>
      </div>

      <!-- 裂变漏斗 -->
      <div class="card chart-card">
        <div class="chart-title">⚡ 裂变状态漏斗 <span class="drill-hint">点击扇区跳转裂变记录</span></div>
        <div v-if="fissionData.length > 0" ref="fissionChartRef" class="chart-container"></div>
        <div v-else class="chart-empty"><el-empty description="暂无裂变数据" :image-size="60" /></div>
      </div>
    </div>

    <!-- 图表区域第二行 -->
    <div class="charts-row">
      <!-- 效果趋势折线图 -->
      <div class="card chart-card chart-wide">
        <div class="chart-title">
          📉 效果趋势
          <el-radio-group v-model="trendDays" size="small" class="trend-controls">
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="trendChartRef" class="chart-container chart-tall"></div>
      </div>
    </div>

    <!-- 骨架排行榜 -->
    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">🦴 骨架效果排行</span>
          <span style="font-size:12px;color:#bbb;margin-left:4px">点击行跳转骨架库</span>
        </div>
        <el-radio-group v-model="skeletonSort" size="small">
          <el-radio-button label="avg_roi">按 ROI</el-radio-button>
          <el-radio-button label="avg_ctr">按 CTR</el-radio-button>
          <el-radio-button label="usage_count">按使用次数</el-radio-button>
        </el-radio-group>
      </div>
      <el-table :data="skeletonRanking" stripe size="default" highlight-current-row @row-click="onSkeletonRowClick">
        <el-table-column type="index" label="排名" width="60" align="center">
          <template #default="{ $index }">
            <span class="rank-badge" :class="rankClass($index)">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="骨架名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="skeleton_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="primary" effect="plain">{{ row.skeleton_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column prop="usage_count" label="使用次数" width="100" align="center">
          <template #default="{ row }">
            <span class="usage-count">{{ row.usage_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_roi" label="平均 ROI" width="110" align="center">
          <template #default="{ row }">
            <span class="roi-value">{{ row.avg_roi?.toFixed(2) ?? '—' }}x</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_ctr" label="平均 CTR" width="110" align="center">
          <template #default="{ row }">
            <span class="ctr-value">{{ row.avg_ctr?.toFixed(2) ?? '—' }}%</span>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无骨架数据" :image-size="60" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import api from '../api'

const router = useRouter()

// ============================================================
// 数据状态
// ============================================================
const overview = ref({})
const categoryData = ref([])
const skeletonRanking = ref([])
const fissionData = ref([])
const trendData = ref([])

const skeletonSort = ref('avg_roi')
const trendDays = ref(30)

// ============================================================
// ECharts 实例和 DOM 引用
// ============================================================
const categoryChartRef = ref(null)
const fissionChartRef = ref(null)
const trendChartRef = ref(null)
let categoryChart = null
let fissionChart = null
let trendChart = null

// ============================================================
// 自动刷新
// ============================================================
const refreshInterval = ref(60)  // 默认 60 秒
const refreshing = ref(false)
let refreshTimer = null

const restartAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (refreshInterval.value > 0) {
    refreshTimer = setInterval(() => {
      fetchAll()
    }, refreshInterval.value * 1000)
  }
}

// ============================================================
// 工具函数
// ============================================================
function formatMoney(val) {
  if (!val) return '¥0'
  if (val >= 10000) return `¥${(val / 10000).toFixed(1)}w`
  return `¥${val.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`
}

function rankClass(index) {
  if (index === 0) return 'rank-gold'
  if (index === 1) return 'rank-silver'
  if (index === 2) return 'rank-bronze'
  return ''
}

const fissionStatusMap = { 0: '草稿', 1: '待审核', 2: '已采用', 3: '已投放' }
const fissionStatusTypes = { 0: 'info', 1: 'warning', 2: 'success', 3: 'primary' }
function fissionStatusLabel(s) { return fissionStatusMap[s] ?? `状态${s}` }
function fissionStatusType(s) { return fissionStatusTypes[s] ?? 'info' }

// ============================================================
// 数据加载
// ============================================================
async function fetchOverview() {
  const { data } = await api.get('/dashboard/overview')
  overview.value = data
}

async function fetchCategory() {
  const { data } = await api.get('/dashboard/category')
  categoryData.value = data
}

async function fetchSkeletonRanking() {
  const { data } = await api.get('/dashboard/skeleton', { params: { sort_by: skeletonSort.value, limit: 10 } })
  skeletonRanking.value = data
}

async function fetchFission() {
  const { data } = await api.get('/dashboard/fission')
  fissionData.value = data
}

async function fetchTrend() {
  const { data } = await api.get('/dashboard/trend', { params: { days: trendDays.value } })
  trendData.value = data
}

async function fetchAll() {
  refreshing.value = true
  try {
    await Promise.all([
      fetchOverview(),
      fetchCategory(),
      fetchSkeletonRanking(),
      fetchFission(),
      fetchTrend(),
    ])
  } finally {
    refreshing.value = false
  }
}

// ============================================================
// 图表下钻导航
// ============================================================
function drillCategoryMaterials(category) {
  router.push({ path: '/material-lib', query: { category } })
}

function drillFissionByStatus(status) {
  router.push({ path: '/fission-records', query: { output_status: String(status) } })
}

function onSkeletonRowClick(row) {
  if (row && row.id) {
    router.push({ path: `/skeleton-detail/${row.id}` })
  }
}

// ============================================================
// 图表初始化与更新
// ============================================================
function initCategoryChart() {
  if (!categoryChartRef.value) return
  categoryChart = echarts.init(categoryChartRef.value)
  updateCategoryChart()
}

function updateCategoryChart() {
  if (!categoryChart) return
  const data = categoryData.value.map(c => ({ name: c.category, value: c.count }))
  categoryChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 个 ({d}%)' },
    legend: { orient: 'vertical', right: '5%', top: 'center', itemWidth: 12, itemHeight: 12 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      cursor: 'pointer',
      data,
    }],
  })
  categoryChart.off('click')
  categoryChart.on('click', params => {
    drillCategoryMaterials(params.name)
  })
}

function initFissionChart() {
  if (!fissionChartRef.value) return
  fissionChart = echarts.init(fissionChartRef.value)
  updateFissionChart()
}

function updateFissionChart() {
  if (!fissionChart) return
  const data = fissionData.value.map(f => ({ name: f.label, value: f.count, status: f.status }))
  fissionChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 个' },
    series: [{
      type: 'funnel',
      left: '10%',
      top: 20,
      bottom: 20,
      width: '80%',
      min: 0,
      max: Math.max(...data.map(d => d.value), 1),
      minSize: '20%',
      maxSize: '100%',
      sort: 'descending',
      gap: 4,
      label: { show: true, position: 'inside', formatter: '{b}: {c}' },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      emphasis: { label: { fontSize: 16 } },
      cursor: 'pointer',
      data: data.map((d, i) => ({
        ...d,
        itemStyle: { color: ['#667eea', '#f093fb', '#43e97b', '#fa709a'][i % 4] },
      })),
    }],
  })
  fissionChart.off('click')
  fissionChart.on('click', params => {
    const item = data.find(d => d.name === params.name)
    drillFissionByStatus(item?.status ?? 0)
  })
}

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()
}

function updateTrendChart() {
  if (!trendChart) return
  const dates = trendData.value.map(t => t.date.slice(5)) // 取 MM-DD
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['ROI', 'CTR'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45 } },
    yAxis: [
      { type: 'value', name: 'ROI', position: 'left', axisLabel: { formatter: '{value}x' } },
      { type: 'value', name: 'CTR', position: 'right', axisLabel: { formatter: '{value}%' } },
    ],
    series: [
      {
        name: 'ROI',
        type: 'line',
        smooth: true,
        data: trendData.value.map(t => t.avg_roi),
        itemStyle: { color: '#667eea' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(102,126,234,.3)' }, { offset: 1, color: 'rgba(102,126,234,.02)' }] } },
      },
      {
        name: 'CTR',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: trendData.value.map(t => t.avg_ctr),
        itemStyle: { color: '#43e97b' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(67,233,123,.3)' }, { offset: 1, color: 'rgba(67,233,123,.02)' }] } },
      },
    ],
  })
}

// ============================================================
// 生命周期与监听
// ============================================================
watch(skeletonSort, fetchSkeletonRanking)
watch(trendDays, fetchTrend)

function resizeCharts() {
  categoryChart?.resize()
  fissionChart?.resize()
  trendChart?.resize()
}

onMounted(async () => {
  await fetchAll()
  restartAutoRefresh()
  await nextTick()
  initCategoryChart()
  initFissionChart()
  initTrendChart()
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('resize', resizeCharts)
  categoryChart?.dispose()
  fissionChart?.dispose()
  trendChart?.dispose()
})
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1400px; margin: 0 auto; }

.page-header { margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
.page-header-left { flex: 1; }
.page-header-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

/* 概览卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, .06);
  border-left: 4px solid transparent;
}
.stat-card.stat-blue { border-left-color: #667eea; }
.stat-card.stat-purple { border-left-color: #764ba2; }
.stat-card.stat-green { border-left-color: #43e97b; }
.stat-card.stat-orange { border-left-color: #fa709a; }
.stat-icon { font-size: 32px; }
.stat-num { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 13px; color: #999; margin-top: 2px; }
.stat-sub { font-size: 12px; color: #bbb; margin-top: 4px; }

/* 图表空状态 */
.chart-empty { display: flex; align-items: center; justify-content: center; height: 240px; }

/* 图表区域 */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.chart-card { padding: 20px; }
.chart-wide { grid-column: 1 / -1; }
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.drill-hint {
  font-size: 12px;
  color: #bbb;
  font-weight: normal;
}
.chart-container { height: 300px; }
.chart-tall { height: 350px; }
.trend-controls { margin-left: auto; }

/* 排行榜 */
.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f0f0f0;
  font-size: 13px;
  font-weight: 600;
  color: #666;
}
.rank-gold { background: linear-gradient(135deg, #f5af19, #f12711); color: #fff; }
.rank-silver { background: linear-gradient(135deg, #bdc3c7, #7f8c8d); color: #fff; }
.rank-bronze { background: linear-gradient(135deg, #e67e22, #d35400); color: #fff; }

.usage-count { font-weight: 600; color: #667eea; }
.roi-value { font-weight: 600; color: #27ae60; }
.ctr-value { font-weight: 600; color: #43e97b; }
</style>
