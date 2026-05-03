<template>
  <div class="page">
    <div class="page-header">
      <h2>📋 裂变记录</h2>
      <p class="page-desc">查看历史裂变记录，录入投放效果数据</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-total">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-num">{{ totalCount }}</div>
          <div class="stat-label">裂变总数</div>
        </div>
      </div>
      <div class="stat-card stat-pending">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <div class="stat-num">{{ globalStats.draft }}</div>
          <div class="stat-label">{{ statusLabel(0) }}</div>
        </div>
      </div>
      <div class="stat-card stat-running">
        <div class="stat-icon">🚀</div>
        <div class="stat-info">
          <div class="stat-num">{{ globalStats.deployed }}</div>
          <div class="stat-label">{{ statusLabel(3) }}</div>
        </div>
      </div>
      <div class="stat-card stat-done">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-num">{{ globalStats.has_effect }}</div>
          <div class="stat-label">已回写效果</div>
        </div>
      </div>
    </div>

    <div class="card">
      <!-- 工具栏 -->
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">裂变记录列表</span>
        </div>
        <div class="toolbar-right">
          <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px">
            <el-option v-for="opt in options.fission_status" :key="opt.value" :label="opt.label" :value="Number(opt.value)" />
          </el-select>
          <el-select v-model="filterSkeleton" placeholder="骨架" clearable style="width:180px">
            <el-option v-for="sk in skeletonOptions" :key="sk.id" :label="sk.name" :value="sk.id" />
          </el-select>
          <el-select v-model="filterPlatform" placeholder="平台" clearable style="width:120px">
            <el-option v-for="opt in platforms" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <el-date-picker v-model="filterDateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" size="default" style="width:220px" value-format="YYYY-MM-DD" clearable />
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div class="batch-bar" v-if="batchSelection.length">
        <span class="batch-hint">已选择 {{ batchSelection.length }} 个裂变记录</span>
        <div class="batch-actions">
          <el-select v-model="batchTargetStatus" placeholder="批量流转到..." size="small" style="width:150px">
            <el-option v-for="opt in nextStatusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <el-button type="warning" size="small" @click="batchAdvanceStatus" :loading="batchLoading">批量流转</el-button>
          <el-button type="danger" size="small" @click="batchDelete" :loading="batchLoading">批量删除</el-button>
        </div>
      </div>

      <!-- 记录表格 -->
      <el-table :data="records" stripe style="width:100%" v-loading="loading" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="42" :selectable="row => row.output_status < 3" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="骨架" min-width="160">
          <template #default="{ row }">
            <span class="sk-name">{{ row.skeleton_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="裂变模式" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="modeType(row.fission_mode)">{{ modeLabel(row.fission_mode) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="output_title" label="产出标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="预测效果" min-width="200">
          <template #default="{ row }">
            <div class="prediction-cell">
              <span class="pred-item">CTR: {{ row.predicted_ctr || '—' }}</span>
              <span class="pred-item">ROI: {{ row.predicted_roi || '—' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="实际效果" min-width="160">
          <template #default="{ row }">
            <div v-if="row.actual_roi" class="actual-cell">
              <span class="actual-item ok">CTR: {{ row.actual_ctr }}%</span>
              <span class="actual-item ok">ROI: {{ row.actual_roi }}x</span>
            </div>
            <span v-else class="text-muted">未回写</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.output_status)" effect="dark">
              {{ statusLabel(row.output_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
            <el-button v-if="row.output_status < 3" type="warning" link size="small" @click="advanceStatus(row)">
              {{ nextStatusLabel(row.output_status) }}
            </el-button>
            <el-button type="success" link size="small" @click="openEffectDialog(row)">录入效果</el-button>
            <el-button type="danger" link size="small" @click="deleteRecord(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无裂变记录" :image-size="80" />
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
          @change="fetchRecords"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="裂变记录详情" width="720px" destroy-on-close>
      <div v-if="currentRecord" class="detail-body">
        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="section-title">📋 基本信息</div>
          <div class="detail-row">
            <span class="detail-label">产出标题</span>
            <span class="detail-value">{{ currentRecord.output_title }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">使用骨架</span>
            <span class="detail-value">{{ currentRecord.skeleton_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">裂变模式</span>
            <el-tag size="small" :type="modeType(currentRecord.fission_mode)">{{ modeLabel(currentRecord.fission_mode) }}</el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">新主题</span>
            <span class="detail-value">{{ currentRecord.new_topic || '—' }}</span>
          </div>
        </div>

        <!-- 效果对比 -->
        <div class="detail-section">
          <div class="section-title">📊 效果对比</div>
          <div class="effect-compare">
            <div class="compare-card">
              <div class="compare-title">预测效果</div>
              <div class="compare-item">
                <span class="compare-label">CTR</span>
                <span class="compare-value">{{ currentRecord.predicted_ctr || '—' }}</span>
              </div>
              <div class="compare-item">
                <span class="compare-label">ROI</span>
                <span class="compare-value">{{ currentRecord.predicted_roi || '—' }}</span>
              </div>
            </div>
            <div class="compare-arrow">→</div>
            <div class="compare-card compare-actual">
              <div class="compare-title">实际效果</div>
              <div v-if="currentRecord.actual_roi" class="compare-item">
                <span class="compare-label">CTR</span>
                <span class="compare-value ok">{{ currentRecord.actual_ctr }}%</span>
              </div>
              <div v-if="currentRecord.actual_roi" class="compare-item">
                <span class="compare-label">ROI</span>
                <span class="compare-value ok">{{ currentRecord.actual_roi }}x</span>
              </div>
              <div v-else class="compare-empty">暂未回写</div>
            </div>
          </div>
        </div>

        <!-- 效果数据趋势 -->
        <div class="detail-section" v-if="currentRecord.effects && currentRecord.effects.length > 0">
          <div class="section-title">
            📈 效果数据趋势
            <span class="effect-count">{{ currentRecord.effects.length }} 条记录</span>
          </div>
          <!-- 趋势折线图 -->
          <div ref="effectChartRef" class="effect-chart"></div>
          <!-- 数据表格 -->
          <el-table :data="currentRecord.effects" size="small" stripe style="margin-top:12px">
            <el-table-column prop="stat_date" label="日期" width="110" />
            <el-table-column prop="platform" label="平台" width="80" />
            <el-table-column prop="impressions" label="曝光" width="80" />
            <el-table-column prop="clicks" label="点击" width="70" />
            <el-table-column label="CTR" width="70">
              <template #default="{ row }">{{ row.ctr ? row.ctr + '%' : '—' }}</template>
            </el-table-column>
            <el-table-column prop="conversions" label="转化" width="70" />
            <el-table-column label="ROI" width="70">
              <template #default="{ row }">{{ row.roi ? row.roi + 'x' : '—' }}</template>
            </el-table-column>
            <el-table-column label="花费" width="80">
              <template #default="{ row }">{{ row.cost ? '¥' + row.cost : '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="editEffect(row)">编辑</el-button>
                <el-button type="danger" link size="small" @click="deleteEffect(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 产出内容 -->
        <div class="detail-section">
          <div class="section-title">📝 产出内容</div>
          <pre class="output-content">{{ currentRecord.output_content || '（空）' }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="saveAsMaterial" :loading="savingMaterial">📚 存为素材</el-button>
        <el-button type="success" @click="openEffectForDetail">录入效果数据</el-button>
      </template>
    </el-dialog>

    <!-- 录入/编辑效果数据弹窗 -->
    <el-dialog v-model="effectDialogVisible" :title="editingEffectId ? '编辑效果数据' : '录入效果数据'" width="560px" destroy-on-close @close="editingEffectId = null">
      <el-form ref="effectFormRef" :model="effectForm" :rules="effectRules" label-width="90px">
        <div class="form-calc-hint">💡 填写曝光/点击/转化/花费/收入后，CTR / CVR / ROI / CPA 将自动计算</div>
        <el-form-item label="投放平台" prop="platform">
          <el-select v-model="effectForm.platform" placeholder="选择平台" style="width:100%">
            <el-option v-for="opt in platforms" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="曝光量" prop="impressions">
              <el-input-number v-model="effectForm.impressions" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="点击量" prop="clicks">
              <el-input-number v-model="effectForm.clicks" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="CTR" prop="ctr">
              <el-input-number v-model="effectForm.ctr" :min="0" :precision="2" style="width:100%" />
              <span class="form-hint">%</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="转化量" prop="conversions">
              <el-input-number v-model="effectForm.conversions" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="CVR" prop="cvr">
              <el-input-number v-model="effectForm.cvr" :min="0" :precision="2" style="width:100%" />
              <span class="form-hint">%</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="花费" prop="cost">
              <el-input-number v-model="effectForm.cost" :min="0" :precision="2" style="width:100%" />
              <span class="form-hint">元</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="收入" prop="revenue">
              <el-input-number v-model="effectForm.revenue" :min="0" :precision="2" style="width:100%" />
              <span class="form-hint">元</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ROI" prop="roi">
              <el-input-number v-model="effectForm.roi" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="CPA" prop="cpa">
              <el-input-number v-model="effectForm.cpa" :min="0" :precision="2" style="width:100%" />
              <span class="form-hint">元</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="统计日期" prop="stat_date">
              <el-date-picker v-model="effectForm.stat_date" type="date" placeholder="选择日期" style="width:100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="effectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEffect" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import api, { getFissions, getFissionDetail, createEffect, getFissionEffects, getOptions, getOptionsByGroup, updateFissionStatus } from '../api'

const router = useRouter()
const route = useRoute()

// ============================================================
// 数据状态
// ============================================================
const records = ref([])
const loading = ref(false)
const skeletons = ref([])
const filterStatus = ref(null)
const filterSkeleton = ref(null)
const filterPlatform = ref(null)
const filterDateRange = ref(null)
const page = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const detailVisible = ref(false)
const currentRecord = ref(null)
const effectChartRef = ref(null)
let effectChart = null
const effectDialogVisible = ref(false)
const effectFissionId = ref(null)
const submitting = ref(false)
const savingMaterial = ref(false)
const effectFormRef = ref(null)

// 批量操作
const batchSelection = ref([])
const batchTargetStatus = ref(null)
const batchLoading = ref(false)

// 动态选项（从数据库加载）
const options = ref({
  fission_status: [],
  fission_mode: [],
})

const fetchOptions = async () => {
  try {
    const data = await getOptions()
    options.value = data
  } catch (e) {
    console.error('加载选项失败', e)
  }
}

const loadPlatformOptions = async () => {
  try {
    const data = await getOptionsByGroup('platform')
    platformOptions.value = data.map(o => ({ label: o.label, value: o.value || o.label }))
  } catch (e) {
    console.error('加载平台选项失败', e)
  }
}

// 效果数据录入表单
const effectForm = ref({
  platform: '',
  impressions: null,
  clicks: null,
  ctr: null,
  conversions: null,
  cvr: null,
  cost: null,
  revenue: null,
  roi: null,
  cpa: null,
  stat_date: '',
})

// 前端实时计算衍生指标（CTR / CVR / ROI / CPA）
const autoCalcEffect = () => {
  const f = effectForm.value
  const imp = f.impressions || 0
  const clk = f.clicks || 0
  const conv = f.conversions || 0
  const cost = f.cost || 0
  const rev = f.revenue || 0

  // CTR = clicks / impressions * 100
  if (imp > 0 && clk > 0) {
    f.ctr = parseFloat(((clk / imp) * 100).toFixed(2))
  }
  // CVR = conversions / clicks * 100
  if (clk > 0 && conv > 0) {
    f.cvr = parseFloat(((conv / clk) * 100).toFixed(2))
  }
  // ROI = revenue / cost
  if (cost > 0 && rev > 0) {
    f.roi = parseFloat((rev / cost).toFixed(2))
  }
  // CPA = cost / conversions
  if (conv > 0 && cost > 0) {
    f.cpa = parseFloat((cost / conv).toFixed(2))
  }
}

// 监听关键字段变化自动重算
watch(
  () => [effectForm.value.impressions, effectForm.value.clicks, effectForm.value.conversions, effectForm.value.cost, effectForm.value.revenue],
  () => { autoCalcEffect() },
)

// 表单校验规则
const effectRules = {
  platform: [{ required: true, message: '请选择投放平台', trigger: 'change' }],
  stat_date: [{ required: true, message: '请选择统计日期', trigger: 'change' }],
}

// 平台选项（从 option 表动态加载，避免只从当前页记录提取导致选项不全）
const platformOptions = ref([])
const platforms = computed(() => platformOptions.value)

// ============================================================
// 骨架选项（从骨架库获取）
// ============================================================
const skeletonOptions = computed(() => {
  const map = new Map()
  records.value.forEach(r => {
    if (!map.has(r.skeleton_id)) {
      map.set(r.skeleton_id, { id: r.skeleton_id, name: r.skeleton_name })
    }
  })
  return [...map.values()]
})

// ============================================================
// 统计数据（基于当前页数据；总数需翻页查看或等待后端聚合接口）
// ============================================================
// 全局统计数据（从后端聚合接口获取，不受分页影响）
const globalStats = ref({ total: 0, draft: 0, pending: 0, approved: 0, deployed: 0, has_effect: 0 })

const fetchGlobalStats = async () => {
  try {
    const { data } = await api.get('/fission/stats')
    globalStats.value = data
  } catch (e) {
    console.error('加载全局统计失败', e)
  }
}

// 标记是否有更多数据（用于提示用户当前统计仅为当前页）
const hasMorePages = computed(() => totalCount.value > pageSize.value)

// ============================================================
// 工具函数
// ============================================================
const statusLabel = (s) => {
  const opt = (options.value.fission_status || []).find(o => Number(o.value) === s)
  return opt ? opt.label : '未知'
}
const statusType = (s) => {
  const types = { 0: 'info', 1: 'warning', 2: 'success', 3: 'primary' }
  return types[s] || 'info'
}
const nextStatusLabel = (currentStatus) => {
  const labels = { 0: '提交审核', 1: '审核通过', 2: '标记已投放' }
  return labels[currentStatus] || ''
}

// 批量流转的下一个状态选项（当前状态 → 下一状态）
const nextStatusOptions = computed(() => {
  // 状态流转：0→1(待审核), 1→2(已采用), 2→3(已投放)
  // 根据选中记录的最小状态决定可选的下一状态
  if (!batchSelection.value.length) return []
  const statuses = batchSelection.value.map(r => r.output_status)
  const uniqueStatuses = [...new Set(statuses)]
  // 只允许同状态的记录一起流转
  if (uniqueStatuses.length !== 1) return []
  const cur = uniqueStatuses[0]
  if (cur >= 3) return []
  const labels = { 1: '待审核', 2: '已采用', 3: '已投放' }
  return [{ value: cur + 1, label: labels[cur + 1] }]
})
const modeLabel = (m) => {
  const opt = (options.value.fission_mode || []).find(o => o.value === m)
  if (!opt) return m
  // label 格式: "名称|图标|描述"，取第一部分作为显示名称
  return opt.label.split('|')[0] || opt.label
}
const modeType = (m) => {
  const types = { replace_leaf: 'success', replace_branch: 'warning', replace_style: 'primary' }
  return types[m] || 'info'
}
const formatDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleString('zh-CN', { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) } catch { return d }
}

// ============================================================
// 数据加载
// ============================================================
const fetchRecords = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value !== null && filterStatus.value !== '') params.output_status = filterStatus.value
    if (filterSkeleton.value !== null && filterSkeleton.value !== '') params.skeleton_id = filterSkeleton.value
    if (filterPlatform.value) params.platform = filterPlatform.value
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.start_date = filterDateRange.value[0]
      params.end_date = filterDateRange.value[1]
    }
    const data = await getFissions(params)
    if (Array.isArray(data)) {
      records.value = data
      totalCount.value = data.length
    } else {
      records.value = data.items || []
      totalCount.value = data.total || 0
    }
    // 每次加载列表时同步刷新全局统计
    await fetchGlobalStats()
  } catch (e) {
    ElMessage.error('加载裂变记录失败')
  }
  loading.value = false
}

// 筛选变化时重置页码
watch([filterStatus, filterSkeleton, filterPlatform, filterDateRange], () => {
  page.value = 1
})

// 详情弹窗关闭时清理图表
watch(detailVisible, (val) => {
  if (!val && effectChart) {
    effectChart.dispose()
    effectChart = null
  }
})

const fetchSkeletons = async () => {
  try {
    const { data } = await api.get('/skeleton/')
    skeletons.value = data
  } catch (e) {
    console.error('加载骨架列表失败', e)
  }
}

// ============================================================
// 操作：查看详情
// ============================================================
const viewDetail = async (row) => {
  try {
    const data = await getFissionDetail(row.id)
    currentRecord.value = data
    detailVisible.value = true
    // 等 DOM 渲染完成后初始化图表
    await nextTick()
    initEffectChart()
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

// ============================================================
// 效果趋势图表
// ============================================================
function initEffectChart() {
  if (!effectChartRef.value) return
  if (effectChart) {
    effectChart.dispose()
    effectChart = null
  }
  const effects = currentRecord.value?.effects || []
  if (effects.length === 0) return

  effectChart = echarts.init(effectChartRef.value)
  const dates = effects.map(e => e.stat_date)
  const roiData = effects.map(e => e.roi)
  const ctrData = effects.map(e => e.ctr)

  effectChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['ROI', 'CTR'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '36px', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30 } },
    yAxis: [
      { type: 'value', name: 'ROI (x)', position: 'left' },
      { type: 'value', name: 'CTR (%)', position: 'right' },
    ],
    series: [
      {
        name: 'ROI',
        type: 'line',
        smooth: true,
        data: roiData,
        itemStyle: { color: '#43e97b' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(67,233,123,.3)' }, { offset: 1, color: 'rgba(67,233,123,.02)' }] } },
      },
      {
        name: 'CTR',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: ctrData,
        itemStyle: { color: '#667eea' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(102,126,234,.3)' }, { offset: 1, color: 'rgba(102,126,234,.02)' }] } },
      },
    ],
  })
}

// ============================================================
// 操作：录入效果数据
// ============================================================
const openEffectDialog = (row) => {
  effectFissionId.value = row.id
  effectForm.value = {
    platform: '',
    impressions: null,
    clicks: null,
    ctr: null,
    conversions: null,
    cvr: null,
    cost: null,
    revenue: null,
    roi: null,
    cpa: null,
    stat_date: new Date().toISOString().split('T')[0],  // 默认今天
  }
  effectDialogVisible.value = true
}

const openEffectForDetail = () => {
  detailVisible.value = false
  openEffectDialog(currentRecord.value)
}

// ============================================================
// 操作：将裂变产出存为素材（飞轮闭环）
// ============================================================
const saveAsMaterial = async () => {
  if (!currentRecord.value) return
  try {
    await ElMessageBox.confirm(
      `将「${currentRecord.value.output_title}」保存为素材？保存后可立即进行拆解。`,
      '存为素材',
      { confirmButtonText: '保存', cancelButtonText: '取消', type: 'info' }
    )
  } catch {
    return
  }
  savingMaterial.value = true
  try {
    const { data } = await api.post('/material/', {
      title: currentRecord.value.output_title,
      content: currentRecord.value.output_content || '',
      platform: currentRecord.value.new_platform || '',
      category: currentRecord.value.new_category || '',
    })
    detailVisible.value = false
    ElMessage.success('已保存为素材，正在跳转到拆解页面...')
    // 短暂延迟后跳转，让用户看到成功提示
    setTimeout(() => {
      router.push({ path: '/', query: { material_id: data.id } })
    }, 800)
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
  savingMaterial.value = false
}

// 编辑模式
const editingEffectId = ref(null)

const submitEffect = async () => {
  const valid = await effectFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingEffectId.value) {
      // 编辑模式
      await api.put(`/effect/${editingEffectId.value}`, {
        ...effectForm.value,
        fission_id: effectFissionId.value,
      })
      ElMessage.success('效果数据已更新，骨架评分已自动刷新')
    } else {
      // 新增模式
      await createEffect({
        fission_id: effectFissionId.value,
        ...effectForm.value,
      })
      ElMessage.success('效果数据录入成功！骨架评分已自动更新')
    }
    effectDialogVisible.value = false
    editingEffectId.value = null
    await fetchRecords()
    // 如果详情弹窗打开着，刷新详情
    if (detailVisible.value && currentRecord.value) {
      const data = await getFissionDetail(currentRecord.value.id)
      currentRecord.value = data
      await nextTick()
      initEffectChart()
    }
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
  submitting.value = false
}

// 编辑效果数据
const editEffect = (row) => {
  editingEffectId.value = row.id
  effectFissionId.value = row.fission_id || currentRecord.value?.id
  effectForm.value = {
    platform: row.platform || '',
    impressions: row.impressions || null,
    clicks: row.clicks || null,
    ctr: row.ctr || null,
    conversions: row.conversions || null,
    cvr: row.cvr || null,
    cost: row.cost || null,
    revenue: row.revenue || null,
    roi: row.roi || null,
    cpa: row.cpa || null,
    stat_date: row.stat_date || new Date().toISOString().split('T')[0],
  }
  effectDialogVisible.value = true
}

// 删除效果数据
const deleteEffect = (row) => {
  ElMessageBox.confirm(
    `确认删除 ${row.stat_date} 的效果数据？删除后骨架评分将自动重新计算。`,
    '删除效果数据',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  ).then(async () => {
    try {
      await api.delete(`/effect/${row.id}`)
      ElMessage.success('效果数据已删除')
      await fetchRecords()
      // 刷新详情
      if (detailVisible.value && currentRecord.value) {
        const data = await getFissionDetail(currentRecord.value.id)
        currentRecord.value = data
        await nextTick()
        initEffectChart()
      }
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// ============================================================
// 操作：删除裂变记录
// ============================================================
const deleteRecord = (row) => {
  ElMessageBox.confirm(`确认删除裂变记录「${row.output_title}」？`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await api.delete(`/fission/${row.id}`)
      ElMessage.success('删除成功')
      await fetchRecords()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// ============================================================
// 操作：状态流转
// ============================================================
const advanceStatus = (row) => {
  const nextLabel = nextStatusLabel(row.output_status)
  ElMessageBox.confirm(
    `确认将「${row.output_title}」推进到「${nextLabel}」？`,
    '状态流转',
    { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
  ).then(async () => {
    try {
      const newStatus = row.output_status + 1
      await updateFissionStatus(row.id, newStatus)
      ElMessage.success(`已推进到「${nextLabel}」`)
      row.output_status = newStatus
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }).catch(() => {})
}

// ============================================================
// 批量操作
// ============================================================
const onSelectionChange = (sel) => {
  batchSelection.value = sel
  batchTargetStatus.value = null
}

const batchAdvanceStatus = async () => {
  if (!batchTargetStatus.value && batchTargetStatus.value !== 0) {
    ElMessage.warning('请选择目标状态')
    return
  }
  if (!batchSelection.value.length) return
  const targetLabel = { 1: '待审核', 2: '已采用', 3: '已投放' }[batchTargetStatus.value] || ''
  ElMessageBox.confirm(
    `确认将选中的 ${batchSelection.value.length} 个记录批量流转到「${targetLabel}」？\n（仅允许同状态记录一起流转）`,
    '批量状态流转',
    { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
  ).then(async () => {
    batchLoading.value = true
    let success = 0
    for (const row of batchSelection.value) {
      try {
        await updateFissionStatus(row.id, batchTargetStatus.value)
        row.output_status = batchTargetStatus.value
        success++
      } catch (e) { /* skip */ }
    }
    batchLoading.value = false
    ElMessage.success(`${success} 个记录已流转到「${targetLabel}」`)
    batchSelection.value = []
    batchTargetStatus.value = null
    await fetchRecords()
  }).catch(() => {})
}

const batchDelete = async () => {
  if (!batchSelection.value.length) return
  ElMessageBox.confirm(
    `确认删除选中的 ${batchSelection.value.length} 个裂变记录？删除后不可恢复。`,
    '批量删除',
    { confirmButtonText: '删除', cancelButtonText: '取消', type: 'danger' },
  ).then(async () => {
    batchLoading.value = true
    let success = 0
    for (const row of batchSelection.value) {
      try {
        await api.delete(`/fission/${row.id}`)
        success++
      } catch (e) { /* skip */ }
    }
    batchLoading.value = false
    ElMessage.success(`已删除 ${success} 个记录`)
    batchSelection.value = []
    await fetchRecords()
  }).catch(() => {})
}

// ============================================================
// 页面初始化
// ============================================================
onMounted(() => {
  // 从 URL 查询参数恢复筛选状态（Dashboard 图表下钻导航）
  const { output_status } = route.query
  if (output_status !== undefined && output_status !== null && output_status !== '') {
    filterStatus.value = Number(output_status)
  }
  fetchRecords()
  fetchSkeletons()
  fetchOptions()
  loadPlatformOptions()
})
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1400px; margin: 0 auto; }

.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border-radius: 12px; padding: 18px 22px;
  box-shadow: 0 2px 10px rgba(0,0,0,.06);
}
.stat-icon { font-size: 28px; }
.stat-num { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 12px; color: #999; margin-top: 2px; }
.stat-page-hint { font-size: 11px; color: #bbb; margin-left: 2px; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #f093fb, #f5576c); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }
.text-muted { color: #ccc; }
.sk-name { font-size: 13px; color: #667eea; }

/* 预测/实际效果单元格 */
.prediction-cell { display: flex; flex-direction: column; gap: 2px; }
.pred-item { font-size: 12px; color: #888; }
.actual-cell { display: flex; flex-direction: column; gap: 2px; }
.actual-item { font-size: 12px; }
.actual-item.ok { color: #27ae60; font-weight: 600; }

/* 详情弹窗 */
.detail-body { display: flex; flex-direction: column; gap: 20px; }
.detail-section { border: 1px solid #f0f0f0; border-radius: 8px; padding: 16px; }
.section-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 12px; }
.detail-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.detail-label { font-size: 13px; color: #999; min-width: 70px; flex-shrink: 0; }
.detail-value { font-size: 13px; color: #333; }

/* 效果对比 */
.effect-compare { display: flex; align-items: center; gap: 20px; }
.compare-card {
  flex: 1; padding: 16px; background: #f8f9fa; border-radius: 8px;
  border: 1px solid #e8e8e8;
}
.compare-card.compare-actual { background: #f0f9f4; border-color: #43e97b; }
.compare-title { font-size: 13px; font-weight: 600; color: #666; margin-bottom: 10px; }
.compare-item { display: flex; justify-content: space-between; margin-bottom: 6px; }
.compare-label { font-size: 12px; color: #999; }
.compare-value { font-size: 14px; font-weight: 600; color: #333; }
.compare-value.ok { color: #27ae60; }
.compare-arrow { font-size: 20px; color: #ccc; flex-shrink: 0; }
.compare-empty { font-size: 13px; color: #bbb; text-align: center; padding: 10px 0; }

/* 效果趋势图 */
.effect-chart { width: 100%; height: 240px; }
.effect-count { font-size: 12px; color: #999; font-weight: 400; margin-left: 8px; }
.form-calc-hint { font-size: 12px; color: #888; margin-bottom: 12px; padding: 6px 10px; background: #f0f9f4; border-radius: 6px; border-left: 3px solid #43e97b; }

/* 产出内容 */
.output-content {
  font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap;
  background: #f8f9fa; padding: 14px; border-radius: 8px;
  max-height: 300px; overflow-y: auto;
}

/* 表单提示 */
.form-hint { font-size: 12px; color: #bbb; margin-left: 4px; }

/* 批量操作栏 */
.batch-bar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px; padding: 10px 16px;
  background: #f0f4ff; border-radius: 8px; border: 1px solid #d0d8f0;
}
.batch-hint { font-size: 13px; color: #667eea; font-weight: 500; }
.batch-actions { display: flex; align-items: center; gap: 8px; }

/* 分页 */
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
