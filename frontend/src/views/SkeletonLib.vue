<template>
  <div class="page">
    <div class="stats">
      <div class="stat-card">
        <div class="stat-num purple">{{ skeletons.length }}</div>
        <div class="stat-label">骨架总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-num green">{{ highUsageCount }}</div>
        <div class="stat-label">高复用骨架</div>
      </div>
      <div class="stat-card">
        <div class="stat-num orange">{{ totalUsage }}</div>
        <div class="stat-label">累计使用</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">
        <span class="dot" style="background:linear-gradient(135deg,#43e97b,#38f9d7)"></span>
        骨架库
      </div>
      <el-row :gutter="16">
        <el-col :span="8" v-for="sk in skeletons" :key="sk.id">
          <div class="skeleton-card">
            <div class="sk-title">{{ sk.name }}</div>
            <div class="sk-type">{{ sk.skeleton_type }}</div>
            <div class="sk-stats">
              <span>使用 {{ sk.usage_count || 0 }} 次</span>
              <span v-if="sk.avg_roi">ROI {{ sk.avg_roi }}x</span>
            </div>
            <div class="sk-platform" v-if="sk.platform">{{ sk.platform }}</div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const skeletons = ref([])

const highUsageCount = computed(() => skeletons.value.filter(s => (s.usage_count || 0) > 5).length)
const totalUsage = computed(() => skeletons.value.reduce((sum, s) => sum + (s.usage_count || 0), 0))

const fetchSkeletons = async () => {
  try {
    const { data } = await api.get('/skeleton/')
    skeletons.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

onMounted(fetchSkeletons)
</script>

<style scoped>
.page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.stat-num { font-size: 30px; font-weight: 700; }
.purple { color: #667eea; }
.green { color: #27ae60; }
.orange { color: #e67e22; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 24px; }
.card-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.skeleton-card { border: 1px solid #e8e8e8; border-radius: 10px; padding: 18px; margin-bottom: 16px; cursor: pointer; transition: all .2s; }
.skeleton-card:hover { border-color: #667eea; box-shadow: 0 3px 12px rgba(102,126,234,.15); transform: translateY(-2px); }
.sk-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sk-type { font-size: 12px; color: #667eea; margin-bottom: 8px; }
.sk-stats { font-size: 12px; color: #999; display: flex; justify-content: space-between; }
.sk-platform { font-size: 11px; color: #bbb; margin-top: 6px; }
</style>
