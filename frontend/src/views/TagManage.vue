<template>
  <div class="page">
    <div class="page-header">
      <h2>🏷️ 标签管理</h2>
      <p class="page-desc">管理素材标签，支持按平台、品类、风格、策略分组管理，共 {{ totalCount }} 个标签</p>
    </div>

    <!-- 新增标签 -->
    <div class="card add-card">
      <div class="add-form">
        <!-- 方式1：直接输入 -->
        <template v-if="!useOptionImport">
          <el-input v-model="newTag.name" placeholder="输入标签名称" style="width:220px" />
          <el-select v-model="newTag.type" placeholder="选择类型" style="width:160px">
            <el-option label="平台 (platform)" value="platform" />
            <el-option label="品类 (category)" value="category" />
            <el-option label="风格 (style)" value="style" />
            <el-option label="策略 (strategy)" value="strategy" />
          </el-select>
        </template>

        <!-- 方式2：从 option 导入 -->
        <template v-else>
          <el-select v-model="newTag.option_id" placeholder="选择选项导入为标签" filterable style="width:300px">
            <el-option-group v-for="group in optionGroups" :key="group.groupKey" :label="group.label">
              <el-option v-for="opt in group.options" :key="opt.id" :label="`${opt.label} (${opt.group_key})`" :value="opt.id" />
            </el-option-group>
          </el-select>
        </template>

        <el-button type="primary" @click="handleAdd" :loading="submitting" :disabled="!canAdd">
          添加标签
        </el-button>

        <!-- 切换导入方式 -->
        <el-button link type="info" @click="useOptionImport = !useOptionImport">
          {{ useOptionImport ? '✏️ 手动输入' : '📋 从选项导入' }}
        </el-button>
      </div>
    </div>

    <!-- 标签分组展示 -->
    <div v-for="section in tagSections" :key="section.key" class="card section-card">
      <div class="section-header">
        <div class="section-title">
          <span class="section-icon">{{ section.icon }}</span>
          <span class="section-label">{{ section.label }}</span>
          <span class="section-key">({{ section.key }})</span>
        </div>
        <span class="count-badge">{{ section.tags.length }} 个</span>
      </div>

      <div class="tag-list" v-if="section.tags.length">
        <span
          v-for="tag in section.tags"
          :key="tag.id"
          class="tag-chip-wrapper"
        >
          <!-- 编辑态：显示输入框 -->
          <template v-if="editingId === tag.id">
            <div class="tag-edit-row">
              <el-input v-model="editForm.name" size="small" style="width:120px" @keyup.enter="handleSaveEdit(tag)" />
              <el-select v-model="editForm.type" size="small" style="width:130px">
                <el-option label="platform" value="platform" />
                <el-option label="category" value="category" />
                <el-option label="style" value="style" />
                <el-option label="strategy" value="strategy" />
              </el-select>
              <el-button type="success" size="small" link @click="handleSaveEdit(tag)">保存</el-button>
              <el-button type="info" size="small" link @click="cancelEdit">取消</el-button>
            </div>
          </template>

          <!-- 展示态：显示标签 chip -->
          <template v-else>
            <el-tag
              :type="section.tagType"
              size="large"
              closable
              effect="light"
              @close="handleDelete(tag)"
            >
              {{ tag.name }}
              <span v-if="tag.option_id" class="option-linked" title="已关联选项">🔗</span>
            </el-tag>
            <el-button type="primary" link size="small" @click="openEdit(tag)">编辑</el-button>
          </template>
        </span>
      </div>
      <div v-else class="empty-tips">
        <span>暂无{{ section.label }}标签，请在上方添加</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getTags, getOptionsByGroup, createTag, updateTag, deleteTag, createTagFromOption } from '../api'

const allTags = ref([])
const allOptions = ref([])
const submitting = ref(false)
const editingId = ref(null)
const useOptionImport = ref(false)

const newTag = reactive({
  name: '',
  type: '',
  option_id: null,
})

const editForm = reactive({
  name: '',
  type: '',
})

const tagSections = computed(() => {
  const sections = [
    { key: 'platform', label: '平台', icon: '📱', tagType: 'primary', tags: [] },
    { key: 'category', label: '品类', icon: '🏪', tagType: 'success', tags: [] },
    { key: 'style', label: '风格', icon: '🎨', tagType: 'warning', tags: [] },
    { key: 'strategy', label: '策略', icon: '🧠', tagType: 'danger', tags: [] },
  ]
  for (const tag of allTags.value) {
    const section = sections.find(s => s.key === tag.type)
    if (section) {
      section.tags.push(tag)
    }
  }
  return sections
})

const totalCount = computed(() => allTags.value.length)

// 按分组组织的 option 列表（用于"从选项导入"下拉框）
const optionGroups = computed(() => {
  const groupMap = {
    platform: { label: '平台', options: [] },
    category: { label: '品类', options: [] },
    style: { label: '风格', options: [] },
    strategy: { label: '策略', options: [] },
  }
  for (const opt of allOptions.value) {
    if (groupMap[opt.group_key]) {
      groupMap[opt.group_key].options.push(opt)
    }
  }
  return Object.entries(groupMap).map(([key, val]) => ({
    groupKey: key,
    label: val.label,
    options: val.options,
  })).filter(g => g.options.length > 0)
})

const canAdd = computed(() => {
  if (useOptionImport.value) {
    return !!newTag.option_id
  }
  return !!newTag.name.trim() && !!newTag.type
})

const fetchTags = async () => {
  try {
    const data = await getTags()
    allTags.value = data
  } catch (e) {
    ElMessage.error('加载标签失败')
  }
}

const fetchOptions = async () => {
  try {
    const data = await getOptionsByGroup()
    allOptions.value = data
  } catch (e) {
    console.error('加载选项失败', e)
  }
}

const handleAdd = async () => {
  if (useOptionImport.value) {
    // 从 option 导入
    if (!newTag.option_id) {
      ElMessage.warning('请选择要导入的选项')
      return
    }
    submitting.value = true
    try {
      await createTagFromOption(newTag.option_id)
      ElMessage.success('标签创建成功')
      newTag.option_id = null
      await fetchTags()
    } catch (e) {
      ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
    }
    submitting.value = false
  } else {
    // 直接创建
    if (!newTag.name.trim()) {
      ElMessage.warning('请输入标签名称')
      return
    }
    if (!newTag.type) {
      ElMessage.warning('请选择标签类型')
      return
    }
    submitting.value = true
    try {
      await createTag({ name: newTag.name.trim(), type: newTag.type })
      ElMessage.success(`标签「${newTag.name}」添加成功`)
      newTag.name = ''
      newTag.type = ''
      await fetchTags()
    } catch (e) {
      ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
    }
    submitting.value = false
  }
}

const openEdit = (tag) => {
  editingId.value = tag.id
  editForm.name = tag.name
  editForm.type = tag.type
}

const cancelEdit = () => {
  editingId.value = null
  editForm.name = ''
  editForm.type = ''
}

const handleSaveEdit = async (tag) => {
  if (!editForm.name.trim()) {
    ElMessage.warning('标签名称不能为空')
    return
  }
  if (!editForm.type) {
    ElMessage.warning('请选择标签类型')
    return
  }
  try {
    const { data } = await updateTag(tag.id, {
      name: editForm.name.trim(),
      type: editForm.type,
    })
    tag.name = data.name
    tag.type = data.type
    ElMessage.success('标签更新成功')
    editingId.value = null
  } catch (e) {
    ElMessage.error('更新失败: ' + (e.response?.data?.detail || e.message))
  }
}

const handleDelete = (tag) => {
  ElMessageBox.confirm(`确认删除标签「${tag.name}」？`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await deleteTag(tag.id)
      allTags.value = allTags.value.filter(t => t.id !== tag.id)
      ElMessage.success('标签已删除')
    } catch (e) {
      ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchTags()
  fetchOptions()
})
</script>

<style scoped>
.page {
  padding: 24px 32px;
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}
.page-desc {
  font-size: 14px;
  color: #888;
}

.card {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, .06);
  padding: 24px;
  margin-bottom: 16px;
}

/* 新增表单 */
.add-card {
  padding: 20px 24px;
}
.add-form {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* 分组区块 */
.section-card {
  padding: 20px 24px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-icon {
  font-size: 18px;
}
.section-label {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.section-key {
  font-size: 13px;
  color: #999;
}

.count-badge {
  font-size: 13px;
  color: #999;
  background: #f5f5f5;
  padding: 4px 10px;
  border-radius: 12px;
}

/* 标签列表 */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-chip-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag-edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 选项关联标识 */
.option-linked {
  font-size: 10px;
  margin-left: 4px;
  opacity: .7;
}

/* 空状态 */
.empty-tips {
  font-size: 13px;
  color: #bbb;
  padding: 8px 0;
}
</style>
