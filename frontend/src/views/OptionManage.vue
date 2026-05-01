<template>
  <div class="page">
    <div class="page-header">
      <h2>⚙️ 选项管理</h2>
      <p class="page-desc">管理所有下拉框选项数据，修改后即时生效</p>
    </div>

    <div class="card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-select v-model="filterGroup" placeholder="按分组筛选" clearable style="width:200px">
            <el-option v-for="g in groups" :key="g" :label="g" :value="g" />
          </el-select>
          <span class="count-badge">共 {{ filteredOptions.length }} 项</span>
        </div>
        <el-button type="primary" @click="openAddDialog">+ 新增选项</el-button>
      </div>

      <!-- 选项表格 -->
      <el-table :data="filteredOptions" stripe style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="group_key" label="分组" width="140">
          <template #default="{ row }">
            <el-tag size="small" type="primary" effect="plain">{{ row.group_key }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="label" label="显示文本" min-width="200" />
        <el-table-column prop="value" label="实际值" min-width="180" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="is_active" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'danger'" effect="dark">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              type="warning"
              link
              size="small"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无选项数据" :image-size="80" />
        </template>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑选项' : '新增选项'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="分组" prop="group_key">
          <el-select v-model="form.group_key" placeholder="选择或输入分组" filterable allow-create style="width:100%">
            <el-option v-for="g in groups" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="显示文本" prop="label">
          <el-input v-model="form.label" placeholder="用户看到的文本" />
        </el-form-item>
        <el-form-item label="实际值" prop="value">
          <el-input v-model="form.value" placeholder="程序使用的值" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" style="width:120px" />
          <span class="form-hint">越小越靠前</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getOptions, getOptionsByGroup, createOption, updateOption, deleteOption } from '../api'

const allOptions = ref([])
const groups = ref([])
const filterGroup = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  group_key: '',
  label: '',
  value: '',
  sort_order: 0,
})

const rules = {
  group_key: [{ required: true, message: '请选择分组', trigger: 'change' }],
  label: [{ required: true, message: '请输入显示文本', trigger: 'blur' }],
  value: [{ required: true, message: '请输入实际值', trigger: 'blur' }],
}

const filteredOptions = computed(() => {
  if (!filterGroup.value) return allOptions.value
  return allOptions.value.filter(o => o.group_key === filterGroup.value)
})

const fetchOptions = async () => {
  try {
    const data = await getOptionsByGroup()
    allOptions.value = data
  } catch (e) {
    ElMessage.error('加载选项失败')
  }
}

const fetchGroups = async () => {
  try {
    const { data } = await api.get('/option/groups')
    groups.value = data
  } catch (e) {
    console.error('加载分组失败', e)
  }
}

const openAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.value = { group_key: filterGroup.value || '', label: '', value: '', sort_order: 0 }
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    group_key: row.group_key,
    label: row.label,
    value: row.value,
    sort_order: row.sort_order,
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateOption(editingId.value, form.value)
      ElMessage.success('修改成功')
    } else {
      await createOption(form.value)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    await fetchOptions()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
  submitting.value = false
}

const toggleActive = async (row) => {
  try {
    await updateOption(row.id, { is_active: row.is_active ? 0 : 1 })
    row.is_active = row.is_active ? 0 : 1
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除「${row.label}」？`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await deleteOption(row.id)
      ElMessage.success('删除成功')
      await fetchOptions()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchOptions()
  fetchGroups()
})
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1100px; margin: 0 auto; }

.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }

.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 12px; }
.count-badge { font-size: 13px; color: #999; background: #f5f5f5; padding: 4px 10px; border-radius: 12px; }

.form-hint { font-size: 12px; color: #bbb; margin-left: 8px; }
</style>
