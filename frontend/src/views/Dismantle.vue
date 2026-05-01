<template>
  <div class="page">
    <!-- 顶部说明 -->
    <div class="page-header">
      <h2>🔍 素材拆解</h2>
      <p class="page-desc">将优质素材按 L1-L5 五层模型拆解，提取可复用的骨架结构</p>
    </div>

    <div class="card">
      <!-- Step 1: 素材录入 -->
      <div class="step-block">
        <div class="step-badge">Step 1</div>
        <div class="step-title">录入原始素材</div>
      </div>
      <el-form :model="materialForm" label-width="100px" class="form-body">
        <el-form-item label="素材标题">
          <el-input v-model="materialForm.title" placeholder="例如：秋冬保湿面霜成分测评" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="平台">
              <el-select v-model="materialForm.platform" placeholder="选择平台" style="width:100%">
                <el-option label="抖音" value="抖音" />
                <el-option label="小红书" value="小红书" />
                <el-option label="快手" value="快手" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品类">
              <el-select v-model="materialForm.category" placeholder="选择品类" style="width:100%">
                <el-option label="护肤" value="护肤" />
                <el-option label="彩妆" value="彩妆" />
                <el-option label="零食" value="零食" />
                <el-option label="母婴" value="母婴" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="素材内容">
          <el-input
            v-model="materialForm.content"
            type="textarea"
            :rows="6"
            placeholder="粘贴完整的素材脚本/文案..."
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="createMaterial" :loading="loading" size="large">
            📝 录入素材
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Step 2: 五层拆解 -->
    <div class="card" v-if="currentMaterial">
      <div class="step-block">
        <div class="step-badge">Step 2</div>
        <div class="step-title">五层拆解 —— {{ currentMaterial.title }}</div>
      </div>

      <el-form :model="dismantleForm" label-width="100px" class="form-body">
        <!-- L1 主题层 -->
        <div class="layer-section">
          <div class="layer-header l1">
            <span class="layer-tag">L1</span>
            <span class="layer-name">主题层</span>
            <span class="layer-hint">枝干（可复用）— 素材讲什么</span>
          </div>
          <div class="layer-body">
            <el-form-item label="主题">
              <el-input v-model="dismantleForm.l1_topic" placeholder="素材讲什么" />
            </el-form-item>
            <el-form-item label="核心卖点">
              <el-input v-model="dismantleForm.l1_core_point" placeholder="核心卖点" />
            </el-form-item>
          </div>
        </div>

        <!-- L2 策略层 -->
        <div class="layer-section">
          <div class="layer-header l2">
            <span class="layer-tag">L2</span>
            <span class="layer-name">策略层</span>
            <span class="layer-hint">枝干（可复用）— 用什么策略打动用户</span>
          </div>
          <div class="layer-body">
            <el-form-item label="策略标签">
              <el-select v-model="dismantleForm.l2_strategy" multiple placeholder="选择策略" style="width:100%">
                <el-option label="共鸣型" value="共鸣型" />
                <el-option label="成分党" value="成分党" />
                <el-option label="对比测评" value="对比测评" />
                <el-option label="悬念型" value="悬念型" />
              </el-select>
            </el-form-item>
            <el-form-item label="情绪策略">
              <el-input v-model="dismantleForm.l2_emotion" placeholder="例如：踩坑共鸣→惊喜发现→效果证言" />
            </el-form-item>
          </div>
        </div>

        <!-- L3 结构层 -->
        <div class="layer-section">
          <div class="layer-header l3">
            <span class="layer-tag">L3</span>
            <span class="layer-name">结构层</span>
            <span class="layer-hint">枝干（可复用）— 内容骨架/段落逻辑</span>
          </div>
          <div class="layer-body">
            <div v-for="(section, idx) in dismantleForm.l3_structure" :key="idx" class="structure-row">
              <span class="structure-num">{{ idx + 1 }}</span>
              <el-input v-model="section.name" placeholder="段落名" style="width:120px" />
              <el-input v-model="section.function" placeholder="功能" style="width:200px" />
              <el-input-number v-model="section.ratio" :min="1" :max="100" :controls="false" style="width:60px" />
              <span class="ratio-unit">%</span>
              <el-button type="danger" link @click="removeSection(idx)">✕</el-button>
            </div>
            <el-button type="primary" link @click="addSection" class="add-section-btn">+ 添加段落</el-button>
          </div>
        </div>

        <!-- L4 元素层 -->
        <div class="layer-section">
          <div class="layer-header l4">
            <span class="layer-tag">L4</span>
            <span class="layer-name">元素层</span>
            <span class="layer-hint">枝杈（可插拔）— 标题公式、钩子句式等</span>
          </div>
          <div class="layer-body">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="标题公式">
                  <el-input v-model="dismantleForm.l4_elements.title_formula" placeholder="例如：情绪痛点+数字+结果" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="钩子句式">
                  <el-input v-model="dismantleForm.l4_elements.hook" placeholder="例如：我踩了N个坑才找到" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="转折方式">
                  <el-input v-model="dismantleForm.l4_elements.transition" placeholder="例如：对比XX牌...这款..." />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="互动设计">
                  <el-input v-model="dismantleForm.l4_elements.interaction" placeholder="例如：评论区告诉我XX，我帮你XX" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- L5 表达层 -->
        <div class="layer-section">
          <div class="layer-header l5">
            <span class="layer-tag">L5</span>
            <span class="layer-name">表达层</span>
            <span class="layer-hint">叶子（可替换）— 具体文字/视觉表达</span>
          </div>
          <div class="layer-body">
            <el-form-item label="金句">
              <el-select v-model="dismantleForm.l5_expressions.golden_sentences" multiple allow-create filterable placeholder="输入金句后回车" style="width:100%">
              </el-select>
            </el-form-item>
            <el-form-item label="数据">
              <el-select v-model="dismantleForm.l5_expressions.data_refs" multiple allow-create filterable placeholder="输入数据后回车" style="width:100%">
              </el-select>
            </el-form-item>
            <el-form-item label="视觉">
              <el-select v-model="dismantleForm.l5_expressions.visual_desc" multiple allow-create filterable placeholder="输入视觉描述后回车" style="width:100%">
              </el-select>
            </el-form-item>
          </div>
        </div>

        <div class="form-actions">
          <el-button type="primary" @click="submitDismantle" :loading="loading" size="large">
            💾 保存拆解结果
          </el-button>
          <el-button type="success" @click="submitDismantleAndExtract" :loading="loading" size="large">
            🦴 保存并提取骨架
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const currentMaterial = ref(null)

const materialForm = reactive({
  title: '',
  platform: '',
  category: '',
  content: '',
})

const dismantleForm = reactive({
  material_id: null,
  l1_topic: '',
  l1_core_point: '',
  l2_strategy: [],
  l2_emotion: '',
  l3_structure: [
    { name: '开头', function: '痛点共鸣', ratio: 15 },
    { name: '主体', function: '价值输出', ratio: 60 },
    { name: '结尾', function: '引导行动', ratio: 25 },
  ],
  l4_elements: { title_formula: '', hook: '', transition: '', interaction: '' },
  l5_expressions: { golden_sentences: [], data_refs: [], visual_desc: [] },
})

const createMaterial = async () => {
  if (!materialForm.title || !materialForm.content) {
    ElMessage.warning('请填写素材标题和内容')
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/material/', materialForm)
    currentMaterial.value = data
    dismantleForm.material_id = data.id
    ElMessage.success('素材录入成功，请继续拆解')
  } catch (e) {
    ElMessage.error('录入失败: ' + (e.response?.data?.detail || e.message))
  }
  loading.value = false
}

const submitDismantle = async () => {
  if (!dismantleForm.material_id) {
    ElMessage.warning('请先录入素材')
    return
  }
  loading.value = true
  try {
    await api.post('/dismantle/', dismantleForm)
    ElMessage.success('拆解结果保存成功')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
  loading.value = false
}

const submitDismantleAndExtract = async () => {
  if (!dismantleForm.material_id) {
    ElMessage.warning('请先录入素材')
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/dismantle/', dismantleForm)
    // 自动提取骨架
    if (data.id) {
      await api.post(`/skeleton/from-dismantle/${data.id}`)
      ElMessage.success('拆解完成，骨架已自动提取！')
    }
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
  loading.value = false
}

const addSection = () => {
  dismantleForm.l3_structure.push({ name: '', function: '', ratio: 10 })
}
const removeSection = (idx) => {
  dismantleForm.l3_structure.splice(idx, 1)
}
</script>

<style scoped>
.page { padding: 24px 32px; max-width: 960px; margin: 0 auto; }

.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #888; }

.card {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,.06);
  padding: 28px;
  margin-bottom: 20px;
}

/* Step badge */
.step-block { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0; }
.step-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff; font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.step-title { font-size: 16px; font-weight: 600; color: #333; }

.form-body { margin-top: 8px; }

/* Layer sections */
.layer-section { margin-bottom: 20px; border-radius: 10px; overflow: hidden; border: 1px solid #e8e8e8; }
.layer-header {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 18px; color: #fff; font-size: 13px;
}
.layer-tag {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 6px;
  background: rgba(255,255,255,.25);
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.layer-name { font-weight: 600; font-size: 14px; }
.layer-hint { font-size: 12px; opacity: .8; margin-left: auto; }
.l1 { background: linear-gradient(135deg, #667eea, #764ba2); }
.l2 { background: linear-gradient(135deg, #f093fb, #f5576c); }
.l3 { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.l4 { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.l5 { background: linear-gradient(135deg, #fa709a, #fee140); }

.layer-body { padding: 16px 20px 8px; background: #fafbfc; }
.layer-body .el-form-item { margin-bottom: 12px; }

.structure-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.structure-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: #e8f4fd; color: #4facfe; font-size: 12px; font-weight: 600; flex-shrink: 0;
}
.ratio-unit { color: #999; font-size: 13px; }
.add-section-btn { margin-top: 4px; }

.form-actions {
  display: flex; gap: 12px; margin-top: 24px; padding-top: 20px; border-top: 1px solid #f0f0f0;
}
</style>
