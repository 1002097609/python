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
          <div class="stat-num">{{ records.length }}</div>
          <div class="stat-label">裂变总数</div>
        </div>
      </div>
      <div class="stat-card stat-pending">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <div class="stat-num">{{ draftCount }}</div>
          <div class="stat-label">草稿</div>
        </div>
      </div>
      <div class="stat-card stat-running">
        <div class="stat-icon">🚀</div>
        <div class="stat-info">
          <div class="stat-num">{{ runningCount }}</div>
          <div class="stat-label">投放中</div>
        </div>
      </div>
      <div class="stat-card stat-done">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-num">{{ hasEffectCount }}</div>
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
            <el-option label="草稿" :value="0" />
            <el-option label="待审核" :value="1" />
            <el-option label="已采用" :value="2" />
            <el-option label="已投放" :value="3" />
          </el-select>
          <el-select v-model="filterSkeleton" placeholder="骨架" clearable style="width:180px">
            <el-option v-for="sk in skeletonOptions" :key="sk.id" :label="sk.name" :value="sk.id" />
          </el-select>
        </div>
      </div>

      <!-- 记录表格 -->
      <el-table :data="filteredRecords" stripe style="width:100%">
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
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
            <el-button type="success" link size="small" @click="openEffectDialog(row)">录入效果</el-button>
            <el-button type="danger" link size="small" @click="deleteRecord(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无裂变记录" :image-size="80" />
        </template>
      </el-table>
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
          <div class="section-title">📈 效果数据趋势</div>
          <el-table :data="currentRecord.effects" size="small" stripe>
            <el-table-column prop="stat_date" label="日期" width="120" />
            <el-table-column prop="platform" label="平台" width="90" />
            <el-table-column prop="impressions" label="曝光" width="90" />
            <el-table-column prop="clicks" label="点击" width="80" />
            <el-table-column label="CTR" width="80">
              <template #default="{ row }">{{ row.ctr ? row.ctr + '%' : '—' }}</template>
            </el-table-column>
            <el-table-column prop="conversions" label="转化" width="80" />
            <el-table-column label="ROI" width="80">
              <template #default="{ row }">{{ row.roi ? row.roi + 'x' : '—' }}</template>
            </el-table-column>
            <el-table-column label="花费" width="90">
              <template #default="{ row }">{{ row.cost ? '¥' + row.cost : '—' }}</template>
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
        <el-button type="success" @click="openEffectForDetail">录入效果数据</el-button>
      </template>
    </el-dialog>

    <!-- 录入效果数据弹窗 -->
    <el-dialog v-model="effectDialogVisible" title="录入效果数据" width="560px" destroy-on-close>
      <el-form ref="effectFormRef" :model="effectForm" :rules="effectRules" label-width="90px">
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getFissions, getFissionDetail, createEffect, getFissionEffects } from '../api'

// ============================================================
// 数据状态
// ============================================================
const records = ref([])
const skeletons = ref([])
const filterStatus = ref(null)
const filterSkeleton = ref(null)
const detailVisible = ref(false)
const currentRecord = ref(null)
const effectDialogVisible = ref(false)
const effectFissionId = ref(null)
const submitting = ref(false)
const effectFormRef = ref(null)

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

// 表单校验规则
const effectRules = {
  platform: [{ required: true, message: '请选择投放平台', trigger: 'change' }],
  stat_date: [{ required: true, message: '请选择统计日期', trigger: 'change' }],
}

// 平台选项（从数据库动态加载）
const platforms = computed(() => {
  // 从已有记录中提取平台列表
  const set = new Set(records.value.map(r => r.platform).filter(Boolean))
  return [...set].map(p => ({ label: p, value: p }))
})

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
// 筛选后的记录列表
// ============================================================
const filteredRecords = computed(() => {
  let list = records.value
  if (filterStatus.value !== null && filterStatus.value !== '') {
    list = list.filter(r => r.output_status === filterStatus.value)
  }
  if (filterSkeleton.value !== null && filterSkeleton.value !== '') {
    list = list.filter(r => r.skeleton_id === filterSkeleton.value)
  }
  return list
})

// ============================================================
// 统计数据
// ============================================================
const draftCount = computed(() => records.value.filter(r => r.output_status === 0).length)
const runningCount = computed(() => records.value.filter(r => r.output_status === 3).length)
const hasEffectCount = computed(() => records.value.filter(r => r.actual_roi).length)

// ============================================================
// 工具函数
// ============================================================
const statusLabel = (s) => ['草稿', '待审核', '已采用', '已投放'][s] || '未知'
const statusType = (s) => ['info', 'warning', 'success', 'primary'][s] || 'info'
const modeLabel = (m) => ({ replace_leaf: '换叶子', replace_branch: '换枝杈', replace_style: '换表达' }[m] || m)
const modeType = (m) => ({ replace_leaf: 'success', replace_branch: 'warning', replace_style: 'primary' }[m] || 'info')
const formatDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleString('zh-CN', { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) } catch { return d }
}

// ============================================================
// 数据加载
// ============================================================
const fetchRecords = async () => {
  try {
    const data = await getFissions()
    records.value = data
  } catch (e) {
    ElMessage.error('加载裂变记录失败')
  }
}

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
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
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

const submitEffect = async () => {
  const valid = await effectFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    // 提交效果数据，关联到裂变记录
    await createEffect({
      fission_id: effectFissionId.value,
      ...effectForm.value,
    })
    ElMessage.success('效果数据录入成功！骨架评分已自动更新')
    effectDialogVisible.value = false
    await fetchRecords()  // 刷新列表，更新实际效果列
  } catch (e) {
    ElMessage.error('录入失败: ' + (e.response?.data?.detail || e.message))
  }
  submitting.value = false
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
// 页面初始化
// ============================================================
onMounted(() => {
  fetchRecords()
  fetchSkeletons()
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

/* 产出内容 */
.output-content {
  font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap;
  background: #f8f9fa; padding: 14px; border-radius: 8px;
  max-height: 300px; overflow-y: auto;
}

/* 表单提示 */
.form-hint { font-size: 12px; color: #bbb; margin-left: 4px; }
</style>
