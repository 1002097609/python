<template>
  <div class="page">
    <div class="page-header">
      <h2>📋 裂变预设管理</h2>
      <p class="page-desc">管理裂变模板预设，在裂变页面可一键加载</p>
    </div>

    <div class="card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input v-model="keyword" placeholder="搜索预设名称..." clearable style="width:220px" prefix-icon="Search" />
          <el-checkbox v-model="showInactive" style="margin-left:12px">显示已禁用</el-checkbox>
          <span class="count-badge">共 {{ filteredPresets.length }} 项</span>
        </div>
        <el-button type="primary" @click="openAddDialog">+ 新增预设</el-button>
      </div>

      <!-- 预设表格 -->
      <el-table :data="filteredPresets" stripe style="width:100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="预设名称" min-width="140">
          <template #default="{ row }">
            <strong>{{ row.name }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180">
          <template #default="{ row }">
            {{ row.description || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="品类" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.config_json?.new_category" size="small" type="primary" effect="plain">
              {{ row.config_json.new_category }}
            </el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="风格" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.config_json?.new_style" size="small" type="success" effect="plain">
              {{ row.config_json.new_style }}
            </el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" sortable />
        <el-table-column prop="is_active" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'danger'" effect="dark">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openViewDialog(row)">查看配置</el-button>
            <el-button type="warning" link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="toggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无预设数据" :image-size="80" />
        </template>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="680px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="预设名称" prop="name">
          <el-input v-model="form.name" placeholder="如：零食推荐" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="预设用途说明（可选）" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="品类">
              <el-input v-model="form.config_json.new_category" placeholder="如：零食" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="风格">
              <el-input v-model="form.config_json.new_style" placeholder="如：亲和力" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="平台">
              <el-input v-model="form.config_json.new_platform" placeholder="如：抖音（可选）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" :max="999" style="width:120px" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- L5 替换内容 -->
        <div class="config-section">
          <div class="config-section-title">L5 替换内容（金句 / 数据 / 视觉）</div>
          <el-form-item label="金句">
            <el-input v-model="goldenInput" type="textarea" :rows="2" placeholder="每行一句，填写后自动转为数组" @blur="syncGolden" />
          </el-form-item>
          <el-form-item label="数据">
            <el-input v-model="dataInput" type="textarea" :rows="2" placeholder="每行一条数据引用" @blur="syncData" />
          </el-form-item>
          <el-form-item label="视觉">
            <el-input v-model="visualInput" type="textarea" :rows="2" placeholder="每行一条视觉描述" @blur="syncVisual" />
          </el-form-item>
        </div>

        <!-- L4 替换内容 -->
        <div class="config-section">
          <div class="config-section-title">L4 替换内容（钩子 / 过渡 / 互动）</div>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="钩子">
                <el-input v-model="form.config_json.replacement.L4.hook" placeholder="如：我踩了N个坑" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="过渡">
                <el-input v-model="form.config_json.replacement.L4.transition" placeholder="如：但是重点来了" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="互动">
                <el-input v-model="form.config_json.replacement.L4.interaction" placeholder="如：评论区告诉我" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看配置弹窗 -->
    <el-dialog v-model="viewDialogVisible" title="预设配置详情" width="680px" destroy-on-close>
      <div v-if="viewingPreset" class="view-config">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="预设名称">{{ viewingPreset.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ viewingPreset.description || '—' }}</el-descriptions-item>
          <el-descriptions-item label="品类">{{ viewingPreset.config_json?.new_category || '—' }}</el-descriptions-item>
          <el-descriptions-item label="风格">{{ viewingPreset.config_json?.new_style || '—' }}</el-descriptions-item>
          <el-descriptions-item label="平台">{{ viewingPreset.config_json?.new_platform || '—' }}</el-descriptions-item>
          <el-descriptions-item label="排序">{{ viewingPreset.sort_order }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="viewingPreset.config_json?.replacement" class="view-replacement">
          <div class="view-replacement-title">替换内容</div>
          <template v-if="viewingPreset.config_json.replacement.L5">
            <div v-if="viewingPreset.config_json.replacement.L5.golden_sentences?.length" class="view-group">
              <span class="view-label">金句：</span>
              <el-tag v-for="(s, i) in viewingPreset.config_json.replacement.L5.golden_sentences" :key="i" size="small" class="view-tag">{{ s }}</el-tag>
            </div>
            <div v-if="viewingPreset.config_json.replacement.L5.data_refs?.length" class="view-group">
              <span class="view-label">数据：</span>
              <el-tag v-for="(s, i) in viewingPreset.config_json.replacement.L5.data_refs" :key="i" size="small" type="success" class="view-tag">{{ s }}</el-tag>
            </div>
            <div v-if="viewingPreset.config_json.replacement.L5.visual_desc?.length" class="view-group">
              <span class="view-label">视觉：</span>
              <el-tag v-for="(s, i) in viewingPreset.config_json.replacement.L5.visual_desc" :key="i" size="small" type="warning" class="view-tag">{{ s }}</el-tag>
            </div>
          </template>
          <template v-if="viewingPreset.config_json.replacement.L4">
            <div v-if="viewingPreset.config_json.replacement.L4.hook" class="view-group">
              <span class="view-label">钩子：</span>{{ viewingPreset.config_json.replacement.L4.hook }}
            </div>
            <div v-if="viewingPreset.config_json.replacement.L4.transition" class="view-group">
              <span class="view-label">过渡：</span>{{ viewingPreset.config_json.replacement.L4.transition }}
            </div>
            <div v-if="viewingPreset.config_json.replacement.L4.interaction" class="view-group">
              <span class="view-label">互动：</span>{{ viewingPreset.config_json.replacement.L4.interaction }}
            </div>
          </template>
        </div>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getFissionPresets, createFissionPreset, updateFissionPreset, deleteFissionPreset } from '../api'

// 列表
const loading = ref(false)
const presets = ref([])
const keyword = ref('')
const showInactive = ref(false)

const filteredPresets = computed(() => {
  let list = presets.value
  if (!showInactive.value) list = list.filter(p => p.is_active)
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(p => (p.name || '').toLowerCase().includes(kw))
  }
  return list
})

const fetchPresets = async () => {
  loading.value = true
  try {
    presets.value = await getFissionPresets()
  } catch (e) {
    ElMessage.error('加载预设列表失败')
  }
  loading.value = false
}

// 弹窗
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const emptyForm = () => ({
  name: '',
  description: '',
  sort_order: 0,
  config_json: {
    new_category: '',
    new_style: '',
    new_platform: '',
    replacement: {
      L5: { golden_sentences: [], data_refs: [], visual_desc: [] },
      L4: { hook: '', transition: '', interaction: '' },
    },
  },
})

const form = reactive(emptyForm())

// L5 文本输入（多行文本，blur 时同步到数组）
const goldenInput = ref('')
const dataInput = ref('')
const visualInput = ref('')

function arrayToText(arr) { return (arr || []).join('\n') }
function textToArray(text) { return text.split('\n').map(s => s.trim()).filter(Boolean) }

function syncGolden() { form.config_json.replacement.L5.golden_sentences = textToArray(goldenInput.value) }
function syncData() { form.config_json.replacement.L5.data_refs = textToArray(dataInput.value) }
function syncVisual() { form.config_json.replacement.L5.visual_desc = textToArray(visualInput.value) }

const rules = {
  name: [{ required: true, message: '请输入预设名称', trigger: 'blur' }],
}

const dialogTitle = computed(() => isEdit.value ? '编辑预设' : '新增预设')

function openAddDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, emptyForm())
  goldenInput.value = ''
  dataInput.value = ''
  visualInput.value = ''
  dialogVisible.value = true
}

function openEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  const cfg = row.config_json || {}
  const rep = cfg.replacement || {}
  const L5 = rep.L5 || {}
  const L4 = rep.L4 || {}
  Object.assign(form, {
    name: row.name || '',
    description: row.description || '',
    sort_order: row.sort_order || 0,
    config_json: {
      new_category: cfg.new_category || '',
      new_style: cfg.new_style || '',
      new_platform: cfg.new_platform || '',
      replacement: {
        L5: {
          golden_sentences: L5.golden_sentences || [],
          data_refs: L5.data_refs || [],
          visual_desc: L5.visual_desc || [],
        },
        L4: {
          hook: L4.hook || '',
          transition: L4.transition || '',
          interaction: L4.interaction || '',
        },
      },
    },
  })
  goldenInput.value = arrayToText(L5.golden_sentences)
  dataInput.value = arrayToText(L5.data_refs)
  visualInput.value = arrayToText(L5.visual_desc)
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  syncGolden(); syncData(); syncVisual()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateFissionPreset(editingId.value, { ...form })
      ElMessage.success('预设已更新')
    } else {
      await createFissionPreset({ ...form })
      ElMessage.success('预设已创建')
    }
    dialogVisible.value = false
    await fetchPresets()
  } catch (e) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
  submitting.value = false
}

async function toggleActive(row) {
  try {
    await updateFissionPreset(row.id, {
      is_active: row.is_active ? 0 : 1,
    })
    row.is_active = row.is_active ? 0 : 1
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除预设「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteFissionPreset(row.id)
    ElMessage.success('已删除')
    await fetchPresets()
  } catch (e) {
    // cancelled
  }
}

// 查看配置弹窗
const viewDialogVisible = ref(false)
const viewingPreset = ref(null)

function openViewDialog(row) {
  viewingPreset.value = row
  viewDialogVisible.value = true
}

onMounted(fetchPresets)
</script>

<style scoped>
.page { padding: 24px; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.page-desc { color: #666; font-size: 14px; margin-top: 4px; }
.card {
  background: #fff; border-radius: 12px; padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,.06);
}
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.count-badge { color: #999; font-size: 13px; margin-left: 4px; }

.config-section {
  border: 1px solid #ebeef5; border-radius: 8px; padding: 16px; margin-top: 8px;
}
.config-section-title {
  font-size: 14px; font-weight: 600; color: #667eea; margin-bottom: 12px;
}

.view-config { }
.view-replacement { margin-top: 16px; }
.view-replacement-title { font-size: 15px; font-weight: 600; margin-bottom: 10px; color: #333; }
.view-group { margin-bottom: 8px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.view-label { font-weight: 600; color: #666; min-width: 40px; }
.view-tag { margin: 0; }
</style>
