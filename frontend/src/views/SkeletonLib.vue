<template>
  <div class="page">
    <div class="page-header">
      <h2>🦴 骨架库</h2>
      <p class="page-desc">管理从素材中提取的可复用骨架，效果数据持续积累</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-blue">
        <div class="stat-icon">🦴</div>
        <div class="stat-info">
          <div class="stat-num">{{ skeletons.length }}</div>
          <div class="stat-label">骨架总数</div>
        </div>
      </div>
      <div class="stat-card stat-green">
        <div class="stat-icon">🔥</div>
        <div class="stat-info">
          <div class="stat-num">{{ highUsageCount }}</div>
          <div class="stat-label">高复用骨架</div>
        </div>
      </div>
      <div class="stat-card stat-orange">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-num">{{ totalUsage }}</div>
          <div class="stat-label">累计裂变次数</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">骨架列表</span>
        </div>
      </div>

      <div v-if="skeletons.length === 0" class="empty-state">
        <div class="empty-icon">🦴</div>
        <div class="empty-text">暂无骨架</div>
        <div class="empty-hint">在「素材拆解」页面完成拆解并提取骨架后，骨架会自动出现在这里</div>
      </div>

      <el-row :gutter="16" v-else>
        <el-col :span="8" v-for="sk in skeletons" :key="sk.id">
          <div class="skeleton-card">
            <div class="sk-header">
              <div class="sk-title">{{ sk.name }}</div>
              <el-tag size="small" type="success" effect="plain">{{ sk.skeleton_type }}</el-tag>
            </div>
            <div class="sk-metrics">
              <div class="metric">
                <span class="metric-value">{{ sk.usage_count || 0 }}</span>
                <span class="metric-label">使用次数</span>
              </div>
              <div class="metric" v-if="sk.avg_roi">
                <span class="metric-value">{{ Number(sk.avg_roi).toFixed(1) }}x</span>
                <span class="metric-label">平均ROI</span>
              </div>
              <div class="metric" v-if="sk.avg_ctr">
                <span class="metric-value">{{ Number(sk.avg_ctr).toFixed(1) }}%</span>
                <span class="metric-label">平均CTR</span>
              </div>
            </div>
            <div class="sk-footer">
              <span class="sk-date">{{ formatDate(sk.created_at) }}</span>
              <el-button type="primary" link size="small" @click="goFission(sk)">去裂变 →</el-button>
            </div>
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

const formatDate = (d) => {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString('zh-CN') } catch { return d }
}

const fetchSkeletons = async () => {
  try {
    const { data } = await api.get('/skeleton/')
    skeletons.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const goFission = (sk) => {
  ElMessage.success(`请前往「素材裂变」页面，选择「${sk.name}」进行裂变`)
}

onMounted(fetchSkeletons)
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 1200px; margin: 0 auto; }

.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
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
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #43e97b, #38f9d7); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }

.empty-state { text-align: center; padding: 48px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { font-size: 16px; font-weight: 600; color: #666; margin-bottom: 8px; }
.empty-hint { font-size: 13px; color: #aaa; }

.skeleton-card {
  border: 1px solid #e8e8e8; border-radius: 12px; padding: 18px;
  margin-bottom: 16px; transition: all .2s; cursor: pointer;
}
.skeleton-card:hover {
  border-color: #43e97b;
  box-shadow: 0 4px 16px rgba(67,233,123,.15);
  transform: translateY(-2px);
}
.sk-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 14px; }
.sk-title { font-size: 14px; font-weight: 600; color: #333; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sk-metrics { display: flex; gap: 16px; margin-bottom: 14px; padding: 12px; background: #f8f9fa; border-radius: 8px; }
.metric { display: flex; flex-direction: column; align-items: center; }
.metric-value { font-size: 16px; font-weight: 700; color: #27ae60; }
.metric-label { font-size: 11px; color: #999; margin-top: 2px; }

.sk-footer { display: flex; align-items: center; justify-content: space-between; }
.sk-date { font-size: 12px; color: #bbb; }
</style>
