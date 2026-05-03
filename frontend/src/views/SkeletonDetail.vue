<template>
  <div class="page">
    <div class="page-header">
      <div class="page-header-left">
        <el-button link @click="goBack" class="back-btn">← 返回骨架库</el-button>
        <h2>🦴 骨架评分详情</h2>
        <p class="page-desc" v-if="skeleton">{{ skeleton.name }} — 效果趋势与裂变对比</p>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="8" animated />
    </div>

    <template v-else-if="skeleton">
      <!-- 骨架概览卡片 -->
      <div class="card overview-card">
        <div class="overview-header">
          <div class="overview-title">
            <span class="overview-icon">🦴</span>
            <span>{{ skeleton.name }}</span>
          </div>
          <div class="overview-tags">
            <el-tag type="success" effect="plain">{{ skeleton.skeleton_type }}</el-tag>
            <el-tag v-if="skeleton.platform" type="primary" effect="plain">{{ skeleton.platform }}</el-tag>
          </div>
        </div>
        <div class="overview-metrics">
          <div class="metric-box">
            <div class="metric-num">{{ skeleton.usage_count || 0 }}</div>
            <div class="metric-label">使用次数</div>
          </div>
          <div class="metric-box">
            <div class="metric-num">{{ skeleton.avg_roi ? Number(skeleton.avg_roi).toFixed(2) + 'x' : '—' }}</div>
            <div class="metric-label">平均 ROI</div>
          </div>
          <div class="metric-box">
            <div class="metric-num">{{ skeleton.avg_ctr ? Number(skeleton.avg_ctr).toFixed(2) + '%' : '—' }}</div>
            <div class="metric-label">平均 CTR</div>
          </div>
          <div class="metric-box">
            <div class="metric-num">{{ effectList.length }}</div>
            <div class="metric-label">效果数据点</div>
          </div>
        </div>
        <!-- L2-L4 结构摘要 -->
        <div class="structure-summary" v-if="skeleton.strategy_desc || (skeleton.structure_json && skeleton.structure_json.length) || skeleton.elements_json">
          <div class="summary-row" v-if="skeleton.strategy_desc">
            <span class="summary-label">L2 策略：</span>
            <span class="summary-val">{{ skeleton.strategy_desc }}</span>
          </div>
          <div class="summary-row" v-if="skeleton.structure_json && skeleton.structure_json.length">
            <span class="summary-label">L3 结构：</span>
            <div class="summary-structures">
              <span v-for="(s, i) in skeleton.structure_json" :key="i" class="struct-chip">
                {{ s.name }} <em v-if="s.ratio">({{ Math.round(s.ratio) }}%)</em>
              </span>
            </div>
          </div>
          <div class="summary-row" v-if="skeleton.elements_json">
            <span class="summary-label">L4 元素：</span>
            <div class="summary-elements">
              <span v-if="skeleton.elements_json.title_formula" class="elem-chip">📝 {{ skeleton.elements_json.title_formula }}</span>
              <span v-if="skeleton.elements_json.hook" class="elem-chip">🎣 {{ skeleton.elements_json.hook }}</span>
              <span v-if="skeleton.elements_json.transition" class="elem-chip">🔀 {{ skeleton.elements_json.transition }}</span>
              <span v-if="skeleton.elements_json.interaction" class="elem-chip">💡 {{ skeleton.elements_json.interaction }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 效果趋势图 -->
      <div class="card chart-card">
        <div class="chart-title">📈 效果趋势 — ROI & CTR 变化</div>
        <div v-if="effectList.length > 0" ref="trendChartRef" class="chart-container"></div>
        <el-empty v-else description="暂无效果数据" :image-size="80" />
      </div>

      <!-- 裂变记录对比表 -->
      <div class="card">
        <div class="card-toolbar">
          <div class="toolbar-left">
            <span class="dot"></span>
            <span class="card-title">🧬 裂变记录对比</span>
          </div>
          <el-radio-group v-model="compareSort" size="small">
            <el-radio-button label="date">按日期</el-radio-button>
            <el-radio-button label="roi">按 ROI</el-radio-button>
            <el-radio-button label="ctr">按 CTR</el-radio-button>
          </el-radio-group>
        </div>
        <el-table :data="sortedFissionList" stripe size="default" v-if="fissionList.length > 0">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column label="裂变模式" width="120">
            <template #default="{ row }">
              <el-tag size="small" type="warning" effect="plain">{{ modeLabel(row.fission_mode) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="new_topic" label="新主题" min-width="160" show-overflow-tooltip />
          <el-table-column prop="new_category" label="品类" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="statusType(row.output_status)">{{ statusLabel(row.output_status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="预测效果" width="160">
            <template #default="{ row }">
              <span v-if="row.predicted_ctr || row.predicted_roi">
                CTR {{ row.predicted_ctr ?? '—' }} / ROI {{ row.predicted_roi ?? '—' }}
              </span>
              <span v-else style="color:#ccc">—</span>
            </template>
          </el-table-column>
          <el-table-column label="实际效果" width="180">
            <template #default="{ row }">
              <template v-if="row.effect_summary">
                <span class="effect-cell">
                  ROI <strong>{{ row.effect_summary.roi ? row.effect_summary.roi + 'x' : '—' }}</strong>
                  / CTR <strong>{{ row.effect_summary.ctr ? row.effect_summary.ctr + '%' : '—' }}</strong>
                </span>
              </template>
              <span v-else style="color:#ccc">未回写</span>
            </template>
          </el-table-column>
          <el-table-column label="花费 / 收入" width="160">
            <template #default="{ row }">
              <template v-if="row.effect_summary">
                <span>¥{{ row.effect_summary.cost?.toLocaleString() }} → ¥{{ row.effect_summary.revenue?.toLocaleString() }}</span>
              </template>
              <span v-else style="color:#ccc">—</span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="150">
            <template #default="{ row }">{{ row.created_at ? row.created_at.substring(0, 16) : '—' }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无裂变记录" :image-size="80" />
      </div>
    </template>

    <div v-else class="card empty-card">
      <el-empty description="骨架不存在或已被删除" :image-size="120" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import api from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const skeleton = ref(null)
const fissionList = ref([])
const effectList = ref([])
const compareSort = ref('date')
const trendChartRef = ref(null)
let trendChart = null

const statusLabelMap = { 0: '草稿', 1: '待审核', 2: '已采用', 3: '已投放' }
const statusTypeMap = { 0: 'info', 1: 'warning', 2: 'success', 3: 'primary' }
const modeLabelMap = { replace_leaf: '换叶子', replace_branch: '换枝杈', replace_style: '换表达' }

function statusLabel(s) { return statusLabelMap[s] ?? `状态${s}` }
function statusType(s) { return statusTypeMap[s] ?? 'info' }
function modeLabel(m) { return modeLabelMap[m] ?? m }

function goBack() { router.push('/skeleton-lib') }

const sortedFissionList = computed(() => {
  const list = [...fissionList.value]
  if (compareSort.value === 'roi') {
    list.sort((a, b) => (b.effect_summary?.roi ?? 0) - (a.effect_summary?.roi ?? 0))
  } else if (compareSort.value === 'ctr') {
    list.sort((a, b) => (b.effect_summary?.ctr ?? 0) - (a.effect_summary?.ctr ?? 0))
  } else {
    list.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  }
  return list
})

async function fetchData() {
  loading.value = true
  try {
    const skeletonId = Number(route.params.id || route.query.skeleton_id)
    if (!skeletonId) return

    // 加载骨架详情
    const { data: sk } = await api.get(`/skeleton/${skeletonId}`)
    skeleton.value = sk

    // 一次性加载所有裂变记录 + 效果数据（后端聚合，替代前端 N+1 查询）
    const { data: agg } = await api.get(`/skeleton/${skeletonId}/effects`)
    fissionList.value = agg.fissions || []
    effectList.value = (agg.trend || []).map(t => ({
      stat_date: t.date,
      roi: t.avg_roi,
      ctr: t.avg_ctr,
      cost: t.total_cost,
      revenue: t.total_revenue,
    }))

    await nextTick()
    initTrendChart()
  } catch (e) {
    console.error('加载骨架详情失败', e)
  }
  loading.value = false
}

function initTrendChart() {
  if (!trendChartRef.value || effectList.value.length === 0) return
  if (trendChart) { trendChart.dispose(); trendChart = null }
  trendChart = echarts.init(trendChartRef.value)

  // effectList 已经是按日期聚合的后端数据
  const sorted = [...effectList.value].sort((a, b) => (a.stat_date || '').localeCompare(b.stat_date || ''))
  const displayDates = sorted.map(e => (e.stat_date || '').slice(5))
  const roiData = sorted.map(e => e.roi ?? null)
  const ctrData = sorted.map(e => e.ctr ?? null)

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['ROI', 'CTR'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
    xAxis: { type: 'category', data: displayDates, axisLabel: { rotate: 30 } },
    yAxis: [
      { type: 'value', name: 'ROI (x)', position: 'left' },
      { type: 'value', name: 'CTR (%)', position: 'right' },
    ],
    series: [
      {
        name: 'ROI', type: 'line', smooth: true, data: roiData,
        itemStyle: { color: '#43e97b' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(67,233,123,.3)' }, { offset: 1, color: 'rgba(67,233,123,.02)' }] } },
      },
      {
        name: 'CTR', type: 'line', smooth: true, yAxisIndex: 1, data: ctrData,
        itemStyle: { color: '#667eea' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(102,126,234,.3)' }, { offset: 1, color: 'rgba(102,126,234,.02)' }] } },
      },
    ],
  })
}

function resizeChart() { trendChart?.resize() }

onMounted(() => {
  fetchData()
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  trendChart?.dispose()
})
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1300px; margin: 0 auto; }

.page-header { margin-bottom: 20px; }
.back-btn { font-size: 14px; color: #667eea; margin-bottom: 4px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.loading-wrap { padding: 40px; background: #fff; border-radius: 14px; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; margin-bottom: 16px; }
.empty-card { text-align: center; padding: 60px; }

/* 概览卡片 */
.overview-card { padding: 28px; }
.overview-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.overview-title { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700; color: #1a1a2e; }
.overview-icon { font-size: 28px; }
.overview-tags { display: flex; gap: 8px; }

.overview-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.metric-box {
  text-align: center; padding: 16px; background: #f8f9fa; border-radius: 10px;
  border: 1px solid #eee;
}
.metric-num { font-size: 22px; font-weight: 700; color: #27ae60; }
.metric-label { font-size: 12px; color: #999; margin-top: 4px; }

/* 结构摘要 */
.structure-summary { border-top: 1px solid #f0f0f0; padding-top: 16px; display: flex; flex-direction: column; gap: 10px; }
.summary-row { display: flex; align-items: flex-start; gap: 10px; }
.summary-label { font-size: 13px; color: #999; min-width: 65px; flex-shrink: 0; padding-top: 2px; }
.summary-val { font-size: 13px; color: #444; line-height: 1.6; }
.summary-structures, .summary-elements { display: flex; flex-wrap: wrap; gap: 6px; }
.struct-chip {
  display: inline-block; padding: 3px 10px; background: #e8f4fd; border-radius: 12px;
  font-size: 12px; color: #2196f3; border: 1px solid #bbdefb;
}
.struct-chip em { font-style: normal; color: #999; margin-left: 2px; }
.elem-chip {
  display: inline-block; padding: 3px 10px; background: #f3e5f5; border-radius: 12px;
  font-size: 12px; color: #7b1fa2; border: 1px solid #e1bee7;
}

/* 图表 */
.chart-card { padding: 20px; }
.chart-title { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 12px; }
.chart-container { height: 320px; }

/* 对比表工具栏 */
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #43e97b, #38f9d7); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }

/* 效果数据 */
.effect-cell strong { color: #27ae60; margin: 0 2px; }
</style>
