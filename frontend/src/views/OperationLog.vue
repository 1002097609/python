<template>
  <div class="page">
    <div class="page-header">
      <h2>📋 操作日志</h2>
      <p class="page-desc">查看系统中的关键操作记录</p>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">操作记录</span>
          <el-tag size="small" type="info" style="margin-left:8px">共 {{ total }} 条</el-tag>
        </div>
        <div class="toolbar-right">
          <el-select v-model="filterEntityType" placeholder="对象类型" clearable style="width:130px">
            <el-option label="素材" value="material" />
            <el-option label="骨架" value="skeleton" />
            <el-option label="裂变" value="fission" />
            <el-option label="效果数据" value="effect" />
            <el-option label="标签" value="tag" />
            <el-option label="选项" value="option" />
          </el-select>
          <el-select v-model="filterAction" placeholder="操作类型" clearable style="width:130px">
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="状态变更" value="status_change" />
            <el-option label="删除" value="delete" />
            <el-option label="导入" value="import" />
            <el-option label="导出" value="export" />
          </el-select>
          <el-button size="small" @click="fetchLogs">刷新</el-button>
        </div>
      </div>

      <el-table :data="logs" v-loading="loading" stripe style="width:100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="detail-box">
              <div class="detail-row" v-for="(val, key) in row.detail" :key="key">
                <span class="detail-key">{{ key }}：</span>
                <span class="detail-val">{{ typeof val === 'object' ? JSON.stringify(val) : val }}</span>
              </div>
              <div v-if="!row.detail || !Object.keys(row.detail).length" class="detail-empty">无详情</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="ID" width="60" prop="id" />
        <el-table-column label="对象类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="entityTypeTag(row.entity_type)">{{ entityTypeLabel(row.entity_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="对象ID" width="80" prop="entity_id" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="actionTag(row.action)">{{ actionLabel(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作人" width="100" prop="operator" />
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getOperationLogs } from '../api'

const logs = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterEntityType = ref('')
const filterAction = ref('')

const entityTypeLabels = { material: '素材', skeleton: '骨架', fission: '裂变', effect: '效果数据', tag: '标签', option: '选项' }
const entityTypeTags = { material: 'primary', skeleton: 'success', fission: 'warning', effect: 'info', tag: '', option: '' }
const actionLabels = { create: '创建', update: '更新', status_change: '状态变更', delete: '删除', import: '导入', export: '导出' }
const actionTags = { create: 'success', update: 'primary', status_change: 'warning', delete: 'danger', import: 'info', export: '' }

const entityTypeLabel = (t) => entityTypeLabels[t] || t
const entityTypeTag = (t) => entityTypeTags[t] || ''
const actionLabel = (a) => actionLabels[a] || a
const actionTag = (a) => actionTags[a] || ''

const formatDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleString('zh-CN') } catch { return d }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterEntityType.value) params.entity_type = filterEntityType.value
    if (filterAction.value) params.action = filterAction.value
    const res = await getOperationLogs(params)
    logs.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    console.error('加载操作日志失败', e)
  } finally {
    loading.value = false
  }
}

watch([filterEntityType, filterAction], () => { page.value = 1; fetchLogs() })
onMounted(fetchLogs)
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1200px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }
.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 24px; }
.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 20px; }
.detail-box { padding: 12px 16px; background: #f8f9fa; border-radius: 8px; }
.detail-row { display: flex; gap: 8px; padding: 4px 0; font-size: 13px; }
.detail-key { color: #999; min-width: 80px; flex-shrink: 0; }
.detail-val { color: #333; word-break: break-all; }
.detail-empty { color: #ccc; font-size: 13px; }
</style>
