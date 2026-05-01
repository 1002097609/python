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
            <!-- 基础信息 -->
            <div class="form-section">
              <div class="form-section-title">📌 基础信息</div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="新主题" required>
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
                    <el-select v-model="fissionForm.new_style" placeholder="选择风格（可选）" clearable style="width:100%">
                      <el-option v-for="opt in options.style" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="投放平台">
                    <el-select v-model="fissionForm.new_platform" placeholder="选择平台（可选）" clearable style="width:100%">
                      <el-option v-for="opt in options.platform" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- L5 表达层 -->
            <div class="form-section">
              <div class="form-section-title">💬 L5 表达层 — 金句、数据、视觉</div>
              <el-form-item label="金句">
                <el-select v-model="fissionForm.replacement.L5.golden_sentences" multiple allow-create filterable placeholder="选择或输入金句（多条会均匀分配到各段落）" style="width:100%">
                  <el-option v-for="opt in options.golden_sentence" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="数据引用">
                <el-select v-model="fissionForm.replacement.L5.data_refs" multiple allow-create filterable placeholder="选择或输入数据（会嵌入到正文段落中）" style="width:100%">
                  <el-option v-for="opt in options.data_ref" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="视觉描述">
                <el-select v-model="fissionForm.replacement.L5.visual_desc" multiple allow-create filterable placeholder="选择或输入视觉描述（会生成画面指导）" style="width:100%">
                  <el-option v-for="opt in options.visual_desc" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
            </div>

            <!-- L4 元素层（可选覆盖） -->
            <div class="form-section">
              <div class="form-section-title">
                🧩 L4 元素层 — 可选覆盖
                <el-checkbox v-model="showL4Overrides" style="margin-left:12px;font-size:13px">自定义覆盖</el-checkbox>
              </div>
              <template v-if="showL4Overrides">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="钩子句式">
                      <el-input v-model="fissionForm.replacement.L4.hook" placeholder="覆盖骨架中的钩子句式" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="转折方式">
                      <el-input v-model="fissionForm.replacement.L4.transition" placeholder="覆盖骨架中的转折方式" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item label="互动设计">
                  <el-input v-model="fissionForm.replacement.L4.interaction" placeholder="覆盖骨架中的互动设计" />
                </el-form-item>
              </template>
            </div>

            <el-form-item style="margin-top:20px">
              <el-button type="primary" @click="executeFission" :loading="loading" size="large">
                ⚡ 开始裂变
              </el-button>
              <el-button @click="resetFissionForm" size="large">🔄 重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 裂变结果 -->
    <div class="card result-card" v-if="fissionResult">
      <div class="result-header">
        <div class="result-badge">✨ 裂变完成</div>
        <div class="result-meta">
          <el-tag size="small" type="success">{{ fissionModeLabel }}</el-tag>
          <span class="result-skeleton-name">基于：{{ selectedSkeletonName }}</span>
        </div>
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
        <div class="result-content-sections">
          <div v-for="(section, idx) in parsedResult" :key="idx" class="result-section" :class="section.type">
            <div class="section-header" v-if="section.header">
              <span class="section-icon">{{ section.icon }}</span>
              <span class="section-title-text">{{ section.header }}</span>
            </div>
            <div class="section-body" v-if="section.lines.length">
              <div v-for="(line, lidx) in section.lines" :key="lidx" class="section-line" :class="line.type">
                <span v-if="line.icon" class="line-icon">{{ line.icon }}</span>
                <span class="line-text">{{ line.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="result-actions">
        <el-button type="primary" @click="copyResult" size="large">📋 复制纯文本</el-button>
        <el-button @click="resetFission" size="large">🔄 再来一次</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { getOptions } from '../api'

const route = useRoute()

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
  // label 格式: "名称|图标|描述"，如 "换叶子|🍃|效果保留85%"
  return (options.value.fission_mode || []).map((m) => {
    const parts = (m.label || '').split('|')
    const displayName = parts[0] || m.label
    const icon = parts[1] || '⚡'
    const desc = parts[2] || m.desc || ''
    return {
      label: displayName,
      value: m.value,
      icon,
      desc,
    }
  })
})

const showL4Overrides = ref(false)

const fissionForm = reactive({
  skeleton_id: null,
  fission_mode: 'replace_leaf',
  new_topic: '',
  new_category: '',
  new_style: '',
  new_platform: '',
  replacement: {
    L5: { golden_sentences: [], data_refs: [], visual_desc: [], hook: '', interaction: '' },
    L4: { hook: '', transition: '', interaction: '' },
  },
})

const fissionModeLabel = computed(() => {
  const map = { replace_leaf: '换叶子', replace_branch: '换枝杈', replace_style: '换表达' }
  return map[fissionMode.value] || fissionMode.value
})

const selectedSkeletonName = computed(() => {
  const sk = skeletons.value.find(s => s.id === selectedSkeleton.value)
  return sk ? sk.name : ''
})

// 解析裂变结果为结构化段落
const parsedResult = computed(() => {
  if (!fissionResult.value?.output_content) return []
  return parseFissionContent(fissionResult.value.output_content)
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

const copyResult = async () => {
  if (!fissionResult.value?.output_content) return
  const text = fissionResult.value.output_content
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      // 降级方案：使用 textarea + execCommand
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

const resetFission = () => {
  fissionResult.value = null
  resetFissionForm()
}

// 解析裂变输出内容为结构化数据
function parseFissionContent(raw) {
  if (!raw) return []
  const lines = raw.split('\n')
  const sections = []
  let current = null

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    // 段落标题 【xxx】
    const headerMatch = trimmed.match(/^【(.+?)】/)
    if (headerMatch) {
      // 判断段落类型
      const header = headerMatch[1]
      let type = 'section'
      let icon = '📄'
      if (header.startsWith('标题')) { type = 'title'; icon = '📌' }
      else if (header.startsWith('备用')) { type = 'backup'; icon = '📦' }
      else if (header.includes('开头') || header.includes('痛点')) { type = 'hook'; icon = '🎣' }
      else if (header.includes('主体') || header.includes('卖点')) { type = 'body'; icon = '💪' }
      else if (header.includes('转折') || header.includes('过渡')) { type = 'transition'; icon = '🔀' }
      else if (header.includes('结尾') || header.includes('互动')) { type = 'ending'; icon = '🎯' }

      current = { header, type, icon, lines: [] }
      sections.push(current)
      continue
    }

    // 内容行
    if (current) {
      let lineType = 'text'
      let icon = ''
      const content = trimmed

      if (content.startsWith('💬')) { lineType = 'quotation'; icon = '💬' }
      else if (content.startsWith('📊')) { lineType = 'data'; icon = '📊' }
      else if (content.startsWith('📷')) { lineType = 'visual'; icon = '📷' }
      else if (content.startsWith('🔀')) { lineType = 'transition'; icon = '🔀' }
      else if (content.startsWith('[')) { lineType = 'placeholder'; icon = '✏️' }

      const text = icon ? content.slice(icon.length).trim() : content
      current.lines.push({ type: lineType, icon, text })
    }
  }

  return sections
}

const resetFissionForm = () => {
  fissionForm.new_topic = ''
  fissionForm.new_category = ''
  fissionForm.new_style = ''
  fissionForm.new_platform = ''
  fissionForm.replacement = {
    L5: { golden_sentences: [], data_refs: [], visual_desc: [], hook: '', interaction: '' },
    L4: { hook: '', transition: '', interaction: '' },
  }
  showL4Overrides.value = false
}

onMounted(() => {
  fetchOptions()
  fetchSkeletons().then(() => {
    const skeletonId = route.query.skeleton_id
    if (skeletonId) {
      const id = Number(skeletonId)
      if (skeletons.value.find(s => s.id === id)) {
        selectedSkeleton.value = id
        fissionForm.skeleton_id = id
      }
    }
  })
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

/* Form sections */
.form-section { margin-bottom: 20px; padding: 16px; background: #fafbfc; border-radius: 10px; border: 1px solid #eee; }
.form-section-title { font-size: 14px; font-weight: 600; color: #555; margin-bottom: 12px; display: flex; align-items: center; }

/* Result card */
.result-card { border: 2px solid #43e97b; }
.result-header { text-align: center; margin-bottom: 20px; }
.result-badge {
  display: inline-block; padding: 4px 16px; border-radius: 20px;
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  color: #fff; font-size: 13px; font-weight: 600; margin-bottom: 8px;
}
.result-meta { display: flex; align-items: center; justify-content: center; gap: 10px; }
.result-skeleton-name { font-size: 13px; color: #999; }

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
.result-content-sections { background: #f8f9fa; border-radius: 10px; border-left: 4px solid #43e97b; overflow: hidden; }
.result-section { border-bottom: 1px solid #eee; }
.result-section:last-child { border-bottom: none; }
.result-section .section-header { display: flex; align-items: center; gap: 8px; padding: 10px 16px 4px; }
.result-section .section-icon { font-size: 16px; }
.result-section .section-title-text { font-size: 13px; font-weight: 600; color: #333; }
.result-section .section-body { padding: 0 16px 10px 40px; }
.result-section .section-line { font-size: 13px; line-height: 1.8; display: flex; align-items: flex-start; gap: 6px; }
.result-section .line-icon { flex-shrink: 0; }
.result-section .line-text { color: #444; }
.result-section .section-line.quotation .line-text { color: #27ae60; }
.result-section .section-line.data .line-text { color: #667eea; }
.result-section .section-line.visual .line-text { color: #f093fb; }
.result-section .section-line.placeholder .line-text { color: #bbb; font-style: italic; }
.result-section.title .section-title-text { font-size: 15px; color: #1a1a2e; }
.result-section.hook .section-title-text { color: #f093fb; }
.result-section.body .section-title-text { color: #27ae60; }
.result-section.transition .section-title-text { color: #667eea; }
.result-section.ending .section-title-text { color: #e67e22; }
.result-section.backup { background: #fff8e6; }
.result-section.backup .section-title-text { color: #e6a700; }

.result-actions { display: flex; gap: 12px; justify-content: center; padding-top: 16px; border-top: 1px solid #f0f0f0; }
</style>
