<template>
  <div class="page">
    <div class="page-header">
      <h2>⚡ 素材裂变</h2>
      <p class="page-desc">选择骨架 + 新内容，批量产出新素材</p>
    </div>

    <div class="card">
      <!-- Step 1: 选择骨架 -->
      <div class="step-block">
        <div class="step-badge">1</div>
        <div class="step-content">
          <div class="step-title">选择骨架</div>
          <div class="step-desc">选择一个已提取的骨架作为裂变模板</div>
          <el-select
            v-model="selectedSkeleton"
            placeholder="🔍 选择骨架"
            @change="onSkeletonChange"
            style="width:100%; margin-top:12px"
            size="large"
            :loading="loadingOptions"
          >
            <el-option
              v-for="sk in skeletons"
              :key="sk.id"
              :label="sk.name"
              :value="sk.id"
            >
              <div class="skeleton-option">
                <span class="sk-name">{{ sk.name }}</span>
                <span class="sk-meta">
                  {{ sk.skeleton_type }} · 使用{{ sk.usage_count || 0 }}次
                  <template v-if="sk.avg_roi"> · ROI {{ Number(sk.avg_roi).toFixed(1) }}x</template>
                  <template v-if="sk.avg_ctr"> · CTR {{ Number(sk.avg_ctr).toFixed(1) }}%</template>
                </span>
              </div>
            </el-option>
          </el-select>
          <div v-if="skeletons.length === 0 && !loadingSkeleton" class="step-empty">
            暂无骨架，请先在「素材拆解」页面提取骨架
          </div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Step 2: 选择裂变模式 -->
      <div class="step-block">
        <div class="step-badge">2</div>
        <div class="step-content">
          <div class="step-title">选择裂变模式</div>
          <div class="step-desc">不同模式决定保留和替换的内容层级</div>
          <div class="mode-cards">
            <div
              class="mode-card"
              v-for="mode in fissionModes"
              :key="mode.value"
              :class="{ active: fissionMode === mode.value }"
              @click="fissionMode = mode.value"
            >
              <div class="mode-icon">{{ mode.icon }}</div>
              <div class="mode-name">{{ mode.label }}</div>
              <div class="mode-desc">{{ mode.desc }}</div>
              <div class="mode-rate" v-if="mode.rate">效果保留 {{ mode.rate }}</div>
              <div class="mode-recommend" v-if="fissionMode === mode.value">✓ 已选</div>
            </div>
          </div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Step 3: 填写替换内容 -->
      <div class="step-block">
        <div class="step-badge">3</div>
        <div class="step-content">
          <div class="step-title">填写替换内容</div>
          <div class="step-desc">输入新主题、品类、风格等替换信息</div>
          <el-form :model="fissionForm" label-width="100px" style="margin-top:16px">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="新主题">
                  <el-input v-model="fissionForm.new_topic" placeholder="例如：办公室解压零食推荐" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="新品类">
                  <el-select v-model="fissionForm.new_category" placeholder="选择品类" style="width:100%">
                    <el-option v-for="opt in options.category" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="新风格">
                  <el-select v-model="fissionForm.new_style" placeholder="选择风格" style="width:100%">
                    <el-option v-for="opt in options.style" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="金句">
                  <el-select v-model="fissionForm.replacement.L5.golden_sentences" multiple allow-create filterable placeholder="选择或输入金句" style="width:100%">
                    <el-option v-for="opt in options.golden_sentence" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="数据">
              <el-select v-model="fissionForm.replacement.L5.data_refs" multiple allow-create filterable placeholder="选择或输入数据" style="width:100%">
                <el-option v-for="opt in options.data_ref" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="executeFission" :loading="loading" size="large">
                ⚡ 开始裂变
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 裂变结果 -->
    <div class="card result-card" v-if="fissionResult">
      <div class="result-header">
        <div class="result-badge">✨ 裂变完成</div>
        <div class="result-title">{{ fissionResult.output_title }}</div>
      </div>

      <div class="result-prediction">
        <div class="prediction-item">
          <span class="prediction-label">预测 CTR</span>
          <span class="prediction-value">{{ fissionResult.predicted_ctr }}</span>
        </div>
        <div class="prediction-divider"></div>
        <div class="prediction-item">
          <span class="prediction-label">预测 ROI</span>
          <span class="prediction-value prediction-highlight">{{ fissionResult.predicted_roi }}</span>
        </div>
      </div>

      <div class="result-content-wrapper">
        <div class="result-content-label">📝 裂变产出内容</div>
        <pre class="result-content">{{ fissionResult.output_content }}</pre>
      </div>

      <div class="result-actions">
        <el-button type="primary" @click="copyResult" size="large">📋 复制文本</el-button>
        <el-button @click="resetFission" size="large">🔄 再来一次</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api, { getOptions } from '../api'

const loading = ref(false)
const loadingOptions = ref(false)
const loadingSkeleton = ref(false)
const skeletons = ref([])
const selectedSkeleton = ref(null)
const fissionMode = ref('replace_leaf')
const fissionResult = ref(null)

const options = ref({
  platform: [],
  category: [],
  style: [],
  strategy: [],
  skeleton_type: [],
  fission_mode: [],
  golden_sentence: [],
  data_ref: [],
  visual_desc: [],
})

const fissionModes = computed(() => {
  const icons = { replace_leaf: '🍃', replace_style: '🎨', replace_branch: '🌿' }
  const rates = { replace_leaf: '~85%', replace_style: '~70%', replace_branch: '~65%' }
  return (options.value.fission_modes || []).map((m) => ({
    label: m.label,
    value: m.value,
    desc: m.desc || '',
    icon: icons[m.value] || '⚡',
    rate: rates[m.value] || '',
  }))
})

const fissionForm = reactive({
  skeleton_id: null,
  fission_mode: 'replace_leaf',
  new_topic: '',
  new_category: '',
  new_style: '',
  replacement: { L5: { golden_sentences: [], data_refs: [] } },
})

const fetchOptions = async () => {
  loadingOptions.value = true
  try {
    const data = await getOptions()
    options.value = data
  } catch (e) {
    ElMessage.error('加载选项数据失败')
  }
  loadingOptions.value = false
}

const fetchSkeletons = async () => {
  loadingSkeleton.value = true
  try {
    const { data } = await api.get('/skeleton/')
    skeletons.value = data
  } catch (e) {
    console.error('加载骨架失败', e)
  }
  loadingSkeleton.value = false
}

const onSkeletonChange = (val) => {
  fissionForm.skeleton_id = val
}

const executeFission = async () => {
  if (!fissionForm.skeleton_id) {
    ElMessage.warning('请先选择骨架')
    return
  }
  if (!fissionForm.new_topic) {
    ElMessage.warning('请填写新主题')
    return
  }
  loading.value = true
  try {
    const payload = { ...fissionForm, fission_mode: fissionMode.value }
    const { data } = await api.post('/fission/', payload)
    fissionResult.value = data
    ElMessage.success('裂变成功！')
  } catch (e) {
    ElMessage.error('裂变失败: ' + (e.response?.data?.detail || e.message))
  }
  loading.value = false
}

const copyResult = () => {
  if (fissionResult.value?.output_content) {
    navigator.clipboard.writeText(fissionResult.value.output_content)
    ElMessage.success('已复制到剪贴板')
  }
}

const resetFission = () => {
  fissionResult.value = null
  fissionForm.new_topic = ''
  fissionForm.new_category = ''
  fissionForm.new_style = ''
  fissionForm.replacement = { L5: { golden_sentences: [], data_refs: [] } }
}

onMounted(() => {
  fetchOptions()
  fetchSkeletons()
})
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 960px; margin: 0 auto; }

.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 28px; margin-bottom: 20px; }

/* Step blocks */
.step-block { display: flex; gap: 16px; }
.step-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: #fff; font-size: 14px; font-weight: 700; flex-shrink: 0; margin-top: 2px;
}
.step-content { flex: 1; }
.step-title { font-size: 16px; font-weight: 600; color: #333; }
.step-desc { font-size: 13px; color: #999; margin-top: 2px; }
.step-empty { margin-top: 12px; padding: 16px; background: #fff8e6; border-radius: 8px; font-size: 13px; color: #e6a700; text-align: center; }

/* Skeleton option in dropdown */
.skeleton-option { display: flex; flex-direction: column; gap: 2px; }
.sk-name { font-size: 14px; color: #333; }
.sk-meta { font-size: 12px; color: #999; }

.divider { height: 1px; background: #f0f0f0; margin: 24px 0; }

/* Mode cards */
.mode-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }
.mode-card {
  border: 2px solid #e8e8e8; border-radius: 12px; padding: 18px 14px; text-align: center;
  cursor: pointer; transition: all .2s;
}
.mode-card:hover { border-color: #f093fb; }
.mode-card.active { border-color: #f093fb; background: #fff5f8; }
.mode-icon { font-size: 28px; margin-bottom: 6px; }
.mode-name { font-size: 14px; font-weight: 600; color: #333; }
.mode-desc { font-size: 12px; color: #999; margin-top: 2px; }
.mode-rate { font-size: 12px; color: #e67e22; margin-top: 6px; font-weight: 500; }
.mode-recommend { font-size: 11px; color: #e74c3c; font-weight: 600; margin-top: 4px; }

/* Result card */
.result-card { border: 2px solid #43e97b; }
.result-header { text-align: center; margin-bottom: 20px; }
.result-badge {
  display: inline-block; padding: 4px 16px; border-radius: 20px;
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  color: #fff; font-size: 13px; font-weight: 600; margin-bottom: 8px;
}
.result-title { font-size: 18px; font-weight: 700; color: #1a1a2e; }

.result-prediction {
  display: flex; align-items: center; justify-content: center; gap: 24px;
  padding: 20px; background: #f0f9f4; border-radius: 10px; margin-bottom: 20px;
}
.prediction-item { text-align: center; }
.prediction-label { display: block; font-size: 12px; color: #999; margin-bottom: 4px; }
.prediction-value { font-size: 22px; font-weight: 700; color: #333; }
.prediction-highlight { color: #27ae60; }
.prediction-divider { width: 1px; height: 36px; background: #d0e8d8; }

.result-content-wrapper { margin-bottom: 20px; }
.result-content-label { font-size: 13px; font-weight: 600; color: #666; margin-bottom: 8px; }
.result-content {
  font-size: 13px; color: #555; line-height: 2; white-space: pre-wrap;
  background: #f8f9fa; padding: 20px; border-radius: 10px;
  border-left: 4px solid #43e97b;
}

.result-actions { display: flex; gap: 12px; justify-content: center; padding-top: 16px; border-top: 1px solid #f0f0f0; }
</style>
