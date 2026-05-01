<template>
  <div class="page">
    <div class="page-header">
      <h2>🏷️ 标签管理</h2>
      <p class="page-desc">管理素材标签，支持按平台、品类、风格、策略分组管理，共 {{ totalCount }} 个标签</p>
    </div>

    <!-- 新增标签 -->
    <div class="card add-card">
      <div class="add-form">
        <el-input v-model="newTag.name" placeholder="输入标签名称" style="width:220px" />
        <el-select v-model="newTag.type" placeholder="选择类型" style="width:160px">
          <el-option label="平台 (platform)" value="platform" />
          <el-option label="品类 (category)" value="category" />
          <el-option label="风格 (style)" value="style" />
          <el-option label="策略 (strategy)" value="strategy" />
        </el-select>
        <el-button type="primary" @click="handleAdd" :loading="submitting" :disabled="!newTag.name.trim()">
          添加标签
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
import api, { getTags } from '../api'

const allTags = ref([])
const submitting = ref(false)
const editingId = ref(null)

const newTag = reactive({
  name: '',
  type: '',
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

const fetchTags = async () => {
  try {
    const data = await getTags()
    allTags.value = data
  } catch (e) {
    ElMessage.error('加载标签失败')
  }
}

const handleAdd = async () => {
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
    const { data } = await api.post('/tag/', {
      name: newTag.name.trim(),
      type: newTag.type,
    })
    allTags.value.push(data)
    ElMessage.success(`标签「${newTag.name}」添加成功`)
    newTag.name = ''
    newTag.type = ''
  } catch (e) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  }
  submitting.value = false
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
    const { data } = await api.put(`/tag/${tag.id}`, {
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
      await api.delete(`/tag/${tag.id}`)
      allTags.value = allTags.value.filter(t => t.id !== tag.id)
      ElMessage.success('标签已删除')
    } catch (e) {
      ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchTags()
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

/* 空状态 */
.empty-tips {
  font-size: 13px;
  color: #bbb;
  padding: 8px 0;
}
</style>
