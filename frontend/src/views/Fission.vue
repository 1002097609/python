<template>
  <div class="page">
    <div class="card">
      <div class="card-title">
        <span class="dot" style="background:linear-gradient(135deg,#f093fb,#f5576c)"></span>
        素材裂变
      </div>

      <!-- Step 1: 选择骨架 -->
      <div class="section-title">Step 1: 选择骨架</div>
      <el-select v-model="selectedSkeleton" placeholder="选择骨架" @change="onSkeletonChange" style="width:100%">
        <el-option v-for="sk in skeletons" :key="sk.id" :label="`${sk.name} (使用${sk.usage_count||0}次)`" :value="sk.id" />
      </el-select>

      <!-- Step 2: 选择裂变模式 -->
      <div class="section-title">Step 2: 选择裂变模式</div>
      <el-radio-group v-model="fissionMode">
        <el-radio label="replace_leaf">换叶子（同构异内容）— 推荐</el-radio>
        <el-radio label="replace_branch">换枝杈（同内容异结构）</el-radio>
        <el-radio label="replace_style">换表达（跨风格移植）</el-radio>
      </el-radio-group>

      <!-- Step 3: 填写替换内容 -->
      <div class="section-title">Step 3: 填写替换内容</div>
      <el-form :model="fissionForm" label-width="100px">
        <el-form-item label="新主题">
          <el-input v-model="fissionForm.new_topic" placeholder="例如：办公室解压零食推荐" />
        </el-form-item>
        <el-form-item label="新品类">
          <el-select v-model="fissionForm.new_category" placeholder="选择品类">
            <el-option label="护肤" value="护肤" />
            <el-option label="彩妆" value="彩妆" />
            <el-option label="零食" value="零食" />
            <el-option label="母婴" value="母婴" />
          </el-select>
        </el-form-item>
        <el-form-item label="新风格">
          <el-select v-model="fissionForm.new_style" placeholder="选择风格">
            <el-option label="成分党" value="成分党" />
            <el-option label="闺蜜聊天" value="闺蜜聊天" />
            <el-option label="毒舌测评" value="毒舌测评" />
            <el-option label="温柔种草" value="温柔种草" />
          </el-select>
        </el-form-item>
        <el-form-item label="金句">
          <el-select v-model="fissionForm.replacement.L5.golden_sentences" multiple allow-create filterable placeholder="输入金句后回车">
          </el-select>
        </el-form-item>
        <el-form-item label="数据">
          <el-select v-model="fissionForm.replacement.L5.data_refs" multiple allow-create filterable placeholder="输入数据后回车">
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="executeFission" :loading="loading">
            开始裂变
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 裂变结果 -->
    <div class="card" v-if="fissionResult">
      <div class="card-title">
        <span class="dot" style="background:linear-gradient(135deg,#43e97b,#38f9d7)"></span>
        裂变结果
      </div>
      <div class="result-box">
        <div class="result-title">{{ fissionResult.output_title }}</div>
        <div class="result-prediction">
          <el-tag type="info">预测CTR: {{ fissionResult.predicted_ctr }}</el-tag>
          <el-tag type="success">预测ROI: {{ fissionResult.predicted_roi }}</el-tag>
        </div>
        <pre class="result-content">{{ fissionResult.output_content }}</pre>
        <el-button type="primary" @click="copyResult">复制文本</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const skeletons = ref([])
const selectedSkeleton = ref(null)
const fissionMode = ref('replace_leaf')
const fissionResult = ref(null)

const fissionForm = reactive({
  skeleton_id: null,
  fission_mode: 'replace_leaf',
  new_topic: '',
  new_category: '',
  new_style: '',
  replacement: { L5: { golden_sentences: [], data_refs: [] } },
})

const fetchSkeletons = async () => {
  try {
    const { data } = await api.get('/skeleton/')
    skeletons.value = data
  } catch (e) {
    console.error('加载骨架失败', e)
  }
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
    const payload = {
      ...fissionForm,
      fission_mode: fissionMode.value,
    }
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

onMounted(fetchSkeletons)
</script>

<style scoped>
.page { padding: 24px; max-width: 900px; margin: 0 auto; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 24px; margin-bottom: 20px; }
.card-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.section-title { font-size: 14px; font-weight: 600; color: #666; margin: 20px 0 12px; padding-left: 12px; border-left: 3px solid #667eea; }
.result-box { border: 1px solid #e8e8e8; border-radius: 10px; padding: 20px; }
.result-title { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 12px; }
.result-prediction { display: flex; gap: 8px; margin-bottom: 16px; }
.result-content { font-size: 13px; color: #555; line-height: 1.8; white-space: pre-wrap; background: #f8f9fa; padding: 16px; border-radius: 8px; margin: 12px 0; }
</style>
