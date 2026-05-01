<template>
  <div class="page">
    <div class="page-header">
      <h2>🔍 素材拆解</h2>
      <p class="page-desc">将优质素材按 L1-L5 五层模型拆解，提取可复用的骨架结构</p>
    </div>

    <!-- 当前编辑的拆解（查看/编辑模式） -->
    <div class="card" v-if="existingDismantle && !showHistory">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <span class="dot"></span>
          <span class="card-title">当前拆解 —— {{ currentMaterial?.title || '未命名素材' }}</span>
          <el-tag size="small" type="success" effect="plain">已有拆解</el-tag>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" link size="small" @click="enterEditMode">✏️ 编辑拆解</el-button>
          <el-button type="success" link size="small" @click="extractSkeleton" :loading="extracting">🦴 提取骨架</el-button>
        </div>
      </div>

      <div class="dismantle-view">
        <!-- L1 -->
        <div class="layer-view">
          <div class="layer-header l1"><span class="layer-tag">L1</span><span class="layer-name">主题层</span></div>
          <div class="layer-body">
            <div class="view-row"><span class="view-label">主题</span><span class="view-value">{{ existingDismantle.l1_topic || '—' }}</span></div>
            <div class="view-row"><span class="view-label">核心卖点</span><span class="view-value">{{ existingDismantle.l1_core_point || '—' }}</span></div>
          </div>
        </div>
        <!-- L2 -->
        <div class="layer-view">
          <div class="layer-header l2"><span class="layer-tag">L2</span><span class="layer-name">策略层</span></div>
          <div class="layer-body">
            <div class="view-row"><span class="view-label">策略标签</span>
              <div class="view-tags">
                <el-tag v-for="s in (existingDismantle.l2_strategy || [])" :key="s" size="small" type="primary">{{ s }}</el-tag>
                <span v-if="!existingDismantle.l2_strategy?.length" class="text-muted">—</span>
              </div>
            </div>
            <div class="view-row"><span class="view-label">情绪策略</span><span class="view-value">{{ existingDismantle.l2_emotion || '—' }}</span></div>
          </div>
        </div>
        <!-- L3 -->
        <div class="layer-view">
          <div class="layer-header l3"><span class="layer-tag">L3</span><span class="layer-name">结构层</span></div>
          <div class="layer-body">
            <div v-for="(sec, idx) in (existingDismantle.l3_structure || [])" :key="idx" class="structure-view-row">
              <span class="structure-num">{{ idx + 1 }}</span>
              <span class="structure-name">{{ sec.name }}</span>
              <span class="structure-func">{{ sec.function }}</span>
              <span class="structure-ratio">{{ sec.ratio }}%</span>
            </div>
            <span v-if="!existingDismantle.l3_structure?.length" class="text-muted">—</span>
          </div>
        </div>
        <!-- L4 -->
        <div class="layer-view">
          <div class="layer-header l4"><span class="layer-tag">L4</span><span class="layer-name">元素层</span></div>
          <div class="layer-body">
            <div class="view-row"><span class="view-label">标题公式</span><span class="view-value">{{ existingDismantle.l4_elements?.title_formula || '—' }}</span></div>
            <div class="view-row"><span class="view-label">钩子句式</span><span class="view-value">{{ existingDismantle.l4_elements?.hook || '—' }}</span></div>
            <div class="view-row"><span class="view-label">转折方式</span><span class="view-value">{{ existingDismantle.l4_elements?.transition || '—' }}</span></div>
            <div class="view-row"><span class="view-label">互动设计</span><span class="view-value">{{ existingDismantle.l4_elements?.interaction || '—' }}</span></div>
          </div>
        </div>
        <!-- L5 -->
        <div class="layer-view">
          <div class="layer-header l5"><span class="layer-tag">L5</span><span class="layer-name">表达层</span></div>
          <div class="layer-body">
            <div class="view-row"><span class="view-label">金句</span>
              <div class="view-tags">
                <el-tag v-for="s in (existingDismantle.l5_expressions?.golden_sentences || [])" :key="s" size="small" type="warning">{{ s }}</el-tag>
                <span v-if="!existingDismantle.l5_expressions?.golden_sentences?.length" class="text-muted">—</span>
              </div>
            </div>
            <div class="view-row"><span class="view-label">数据</span>
              <div class="view-tags">
                <el-tag v-for="s in (existingDismantle.l5_expressions?.data_refs || [])" :key="s" size="small" type="info">{{ s }}</el-tag>
                <span v-if="!existingDismantle.l5_expressions?.data_refs?.length" class="text-muted">—</span>
              </div>
            </div>
            <div class="view-row"><span class="view-label">视觉</span>
              <div class="view-tags">
                <el-tag v-for="s in (existingDismantle.l5_expressions?.visual_desc || [])" :key="s" size="small" type="success">{{ s }}</el-tag>
                <span v-if="!existingDismantle.l5_expressions?.visual_desc?.length" class="text-muted">—</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑模式：五层拆解表单 -->
    <div class="card" v-if="editMode || (!existingDismantle && currentMaterial)">
      <div class="step-block">
        <div class="step-badge">Step 1</div>
        <div class="step-title">{{ editMode ? '编辑拆解' : '新增拆解' }} —— {{ currentMaterial?.title || '未命名素材' }}</div>
        <el-button v-if="editMode" link type="info" @click="cancelEdit">取消编辑</el-button>
      </div>

      <el-form :model="dismantleForm" label-width="100px" class="form-body">
        <!-- L1 主题层 -->
        <div class="layer-section">
          <div class="layer-header l1">
            <span class="layer-tag">L1</span><span class="layer-name">主题层</span>
            <span class="layer-hint">枝干（可复用）— 素材讲什么</span>
          </div>
          <div class="layer-body">
            <el-form-item label="主题"><el-input v-model="dismantleForm.l1_topic" placeholder="素材讲什么" /></el-form-item>
            <el-form-item label="核心卖点"><el-input v-model="dismantleForm.l1_core_point" placeholder="核心卖点" /></el-form-item>
          </div>
        </div>

        <!-- L2 策略层 -->
        <div class="layer-section">
          <div class="layer-header l2">
            <span class="layer-tag">L2</span><span class="layer-name">策略层</span>
            <span class="layer-hint">枝干（可复用）— 用什么策略打动用户</span>
          </div>
          <div class="layer-body">
            <el-form-item label="策略标签">
              <el-select v-model="dismantleForm.l2_strategy" multiple placeholder="选择策略" style="width:100%">
                <el-option v-for="opt in options.strategy" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="情绪策略"><el-input v-model="dismantleForm.l2_emotion" placeholder="例如：踩坑共鸣→惊喜发现→效果证言" /></el-form-item>
          </div>
        </div>

        <!-- L3 结构层 -->
        <div class="layer-section">
          <div class="layer-header l3">
            <span class="layer-tag">L3</span><span class="layer-name">结构层</span>
            <span class="layer-hint">枝干（可复用）— 内容骨架/段落逻辑</span>
          </div>
          <div class="layer-body">
            <div v-for="(section, idx) in dismantleForm.l3_structure" :key="idx" class="structure-row">
              <span class="structure-num">{{ idx + 1 }}</span>
              <el-input v-model="section.name" placeholder="段落名" style="width:120px" />
              <el-input v-model="section.function" placeholder="功能" style="width:200px" />
              <el-input-number v-model="section.ratio" :min="1" :max="100" :controls="false" style="width:60px" />
              <span class="ratio-unit">%</span>
              <el-input v-model="section.template" placeholder="句式模板（可选）" style="width:180px;font-size:12px" />
              <el-button type="danger" link @click="removeSection(idx)">✕</el-button>
            </div>
            <el-button type="primary" link @click="addSection" class="add-section-btn">+ 添加段落</el-button>
          </div>
        </div>

        <!-- L4 元素层 -->
        <div class="layer-section">
          <div class="layer-header l4">
            <span class="layer-tag">L4</span><span class="layer-name">元素层</span>
            <span class="layer-hint">枝杈（可插拔）— 标题公式、钩子句式等</span>
          </div>
          <div class="layer-body">
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="标题公式"><el-input v-model="dismantleForm.l4_elements.title_formula" placeholder="例如：情绪痛点+数字+结果" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="钩子句式"><el-input v-model="dismantleForm.l4_elements.hook" placeholder="例如：我踩了N个坑才找到" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="转折方式"><el-input v-model="dismantleForm.l4_elements.transition" placeholder="例如：对比XX牌...这款..." /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="互动设计"><el-input v-model="dismantleForm.l4_elements.interaction" placeholder="例如：评论区告诉我XX，我帮你XX" /></el-form-item></el-col>
            </el-row>
          </div>
        </div>

        <!-- L5 表达层 -->
        <div class="layer-section">
          <div class="layer-header l5">
            <span class="layer-tag">L5</span><span class="layer-name">表达层</span>
            <span class="layer-hint">叶子（可替换）— 具体文字/视觉表达</span>
          </div>
          <div class="layer-body">
            <el-form-item label="金句">
              <el-select v-model="dismantleForm.l5_expressions.golden_sentences" multiple allow-create filterable placeholder="选择或输入金句" style="width:100%">
                <el-option v-for="opt in options.golden_sentence" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="数据">
              <el-select v-model="dismantleForm.l5_expressions.data_refs" multiple allow-create filterable placeholder="选择或输入数据" style="width:100%">
                <el-option v-for="opt in options.data_ref" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="视觉">
              <el-select v-model="dismantleForm.l5_expressions.visual_desc" multiple allow-create filterable placeholder="选择或输入视觉描述" style="width:100%">
                <el-option v-for="opt in options.visual_desc" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </div>
        </div>

        <div class="form-actions">
          <el-button type="primary" @click="submitDismantle" :loading="loading" size="large">
            💾 {{ editMode ? '更新拆解' : '保存拆解结果' }}
          </el-button>
          <el-button type="success" @click="submitDismantleAndExtract" :loading="loading" size="large">
            🦴 保存并提取骨架
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- Step 0: 素材录入（没有选中素材时显示） -->
    <div class="card" v-if="!currentMaterial && !showHistory">
      <div class="step-block">
        <div class="step-badge">Step 0</div>
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
                <el-option v-for="opt in options.platform" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品类">
              <el-select v-model="materialForm.category" placeholder="选择品类" style="width:100%">
                <el-option v-for="opt in options.category" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="素材内容">
          <el-input v-model="materialForm.content" type="textarea" :rows="6" placeholder="粘贴完整的素材脚本/文案..." />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="createMaterial" :loading="loading" size="large">📝 录入素材</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { getOptions, getDismantleByMaterial, createDismantle, updateDismantle } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const extracting = ref(false)
const currentMaterial = ref(null)
const existingDismantle = ref(null)
const editMode = ref(false)
const showHistory = ref(false)

const options = ref({
  platform: [], category: [], style: [], strategy: [],
  skeleton_type: [], fission_mode: [],
  golden_sentence: [], data_ref: [], visual_desc: [],
})

const fetchOptions = async () => {
  try {
    const data = await getOptions()
    options.value = data
  } catch (e) {
    console.error('加载选项失败', e)
  }
}

// 加载已有拆解记录
const fetchExistingDismantle = async (materialId) => {
  if (!materialId) return
  try {
    const data = await getDismantleByMaterial(materialId)
    if (data) {
      existingDismantle.value = data
      // 同步填充编辑表单
      fillDismantleForm(data)
    }
  } catch (e) {
    // 404 = 尚未拆解，不需要报错
    if (e.response?.status !== 404) {
      console.error('加载拆解记录失败', e)
    }
    existingDismantle.value = null
  }
}

// 将拆解数据填充到编辑表单
const fillDismantleForm = (data) => {
  dismantleForm.material_id = data.material_id
  dismantleForm.l1_topic = data.l1_topic || ''
  dismantleForm.l1_core_point = data.l1_core_point || ''
  dismantleForm.l2_strategy = data.l2_strategy || []
  dismantleForm.l2_emotion = data.l2_emotion || ''
  dismantleForm.l3_structure = (data.l3_structure || []).map(s => ({
    name: s.name || '',
    function: s.function || '',
    ratio: Number(s.ratio) || 0,
    template: s.template || '',
  }))
  dismantleForm.l4_elements = {
    title_formula: data.l4_elements?.title_formula || '',
    hook: data.l4_elements?.hook || '',
    transition: data.l4_elements?.transition || '',
    interaction: data.l4_elements?.interaction || '',
  }
  dismantleForm.l5_expressions = {
    golden_sentences: data.l5_expressions?.golden_sentences || [],
    data_refs: data.l5_expressions?.data_refs || [],
    visual_desc: data.l5_expressions?.visual_desc || [],
  }
}

onMounted(async () => {
  fetchOptions()
  // 从素材库跳转过来时自动填充
  const materialId = route.query.material_id
  if (materialId) {
    const id = Number(materialId)
    currentMaterial.value = {
      id,
      title: route.query.title || '',
      platform: route.query.platform || '',
      category: route.query.category || '',
    }
    materialForm.title = route.query.title || ''
    materialForm.platform = route.query.platform || ''
    materialForm.category = route.query.category || ''
    materialForm.content = route.query.content || ''
    dismantleForm.material_id = id

    // 检查是否已有拆解记录
    await fetchExistingDismantle(id)
  }
})

const materialForm = reactive({ title: '', platform: '', category: '', content: '' })

const dismantleForm = reactive({
  material_id: null,
  l1_topic: '',
  l1_core_point: '',
  l2_strategy: [],
  l2_emotion: '',
  l3_structure: [],
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

const enterEditMode = () => {
  editMode.value = true
}

const cancelEdit = () => {
  editMode.value = false
}

const buildDismantlePayload = () => ({
  material_id: dismantleForm.material_id,
  l1_topic: dismantleForm.l1_topic || null,
  l1_core_point: dismantleForm.l1_core_point || null,
  l2_strategy: dismantleForm.l2_strategy || [],
  l2_emotion: dismantleForm.l2_emotion || null,
  l3_structure: (dismantleForm.l3_structure || []).map(s => ({
    name: s.name || '',
    function: s.function || '',
    ratio: Number(s.ratio) || 0,
    template: s.template || '',
  })),
  l4_elements: dismantleForm.l4_elements || {},
  l5_expressions: dismantleForm.l5_expressions || {},
})

const submitDismantle = async () => {
  if (!dismantleForm.material_id) {
    ElMessage.warning('请先录入素材')
    return
  }
  loading.value = true
  try {
    const payload = buildDismantlePayload()
    if (existingDismantle.value) {
      // 更新已有拆解
      await updateDismantle(existingDismantle.value.id, payload)
      ElMessage.success('拆解更新成功')
      editMode.value = false
    } else {
      // 新建拆解
      const { data } = await createDismantle(payload)
      existingDismantle.value = data
      ElMessage.success('拆解结果保存成功')
    }
    // 重新加载确保数据同步
    await fetchExistingDismantle(dismantleForm.material_id)
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
    const payload = buildDismantlePayload()
    let dismantleId

    if (existingDismantle.value) {
      await updateDismantle(existingDismantle.value.id, payload)
      dismantleId = existingDismantle.value.id
      editMode.value = false
    } else {
      const { data } = await createDismantle(payload)
      dismantleId = data.id
      existingDismantle.value = data
    }

    // 自动提取骨架
    extracting.value = true
    await api.post(`/skeleton/from-dismantle/${dismantleId}`)
    ElMessage.success('拆解完成，骨架已自动提取！')
    await fetchExistingDismantle(dismantleForm.material_id)
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
  loading.value = false
  extracting.value = false
}

const extractSkeleton = async () => {
  if (!existingDismantle.value) return
  extracting.value = true
  try {
    await api.post(`/skeleton/from-dismantle/${existingDismantle.value.id}`)
    ElMessage.success('骨架提取成功！')
  } catch (e) {
    if (e.response?.status === 409) {
      ElMessage.warning('该拆解已提取过骨架')
    } else {
      ElMessage.error('提取失败: ' + (e.response?.data?.detail || e.message))
    }
  }
  extracting.value = false
}

const addSection = () => {
  dismantleForm.l3_structure.push({ name: '', function: '', ratio: 10, template: '' })
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

.card { background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.06); padding: 28px; margin-bottom: 20px; }

.card-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); }
.card-title { font-size: 15px; font-weight: 600; color: #333; }

.step-block { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0; }
.step-badge { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.step-title { font-size: 16px; font-weight: 600; color: #333; }

.form-body { margin-top: 8px; }

.layer-section { margin-bottom: 20px; border-radius: 10px; overflow: hidden; border: 1px solid #e8e8e8; }
.layer-header { display: flex; align-items: center; gap: 10px; padding: 10px 18px; color: #fff; font-size: 13px; }
.layer-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255,255,255,.25);
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.layer-name { font-weight: 600; font-size: 14px; }
.layer-hint { font-size: 12px; opacity: .8; margin-left: 4px; }

.l1 { background: linear-gradient(135deg, #667eea, #764ba2); }
.l2 { background: linear-gradient(135deg, #f093fb, #f5576c); }
.l3 { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.l4 { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.l5 { background: linear-gradient(135deg, #fa709a, #fee140); }

.layer-body { padding: 16px 18px; }

.dismantle-view { display: flex; flex-direction: column; gap: 12px; }

.layer-view { border-radius: 10px; overflow: hidden; border: 1px solid #e8e8e8; }
.layer-view .layer-header { color: #fff; }

.view-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}
.view-row:last-child { border-bottom: none; }
.view-label {
  font-size: 13px;
  color: #888;
  min-width: 80px;
  flex-shrink: 0;
  padding-top: 2px;
}
.view-value { font-size: 14px; color: #333; flex: 1; }
.view-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.structure-view-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}
.structure-view-row:last-child { border-bottom: none; }
.structure-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #4facfe;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.structure-name { font-size: 14px; font-weight: 600; color: #333; min-width: 80px; }
.structure-func { font-size: 13px; color: #666; flex: 1; }
.structure-ratio { font-size: 13px; color: #4facfe; font-weight: 600; }

.structure-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ratio-unit { font-size: 13px; color: #888; }
.add-section-btn { margin-top: 4px; }

.form-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.text-muted { color: #bbb; font-size: 13px; }

@media (max-width: 768px) {
  .page { padding: 16px; }
  .card { padding: 16px; }
  .form-actions { flex-direction: column; }
  .structure-row { flex-wrap: wrap; }
}
</style>