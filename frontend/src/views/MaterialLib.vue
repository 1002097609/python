<template>
  <div class="page">
    <div class="card">
      <div class="card-title">
        <span class="dot" style="background:linear-gradient(135deg,#667eea,#764ba2)"></span>
        素材库
      </div>
      <el-table :data="materials" stripe style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="platform" label="平台" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="purple">{{ row.platform }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="品类" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="success">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 0 ? 'info' : row.status === 1 ? 'success' : 'warning'">
              {{ ['未拆解', '已拆解', '已归档'][row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const materials = ref([])

const fetchMaterials = async () => {
  try {
    const { data } = await api.get('/material/')
    materials.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const viewDetail = (row) => {
  ElMessage.info(`素材详情: ${row.title}`)
}

onMounted(fetchMaterials)
</script>

<style scoped>
.page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 24px; }
.card-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
</style>
