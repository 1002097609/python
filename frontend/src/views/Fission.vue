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
          <!-- 骨架筛选栏 -->
          <div class="skeleton-filter-bar">
            <el-select v-model="skeletonPlatformFilter" placeholder="全部平台" clearable style="width:140px" size="large" @change="fetchSkeletons">
              <el-option v-for="p in skeletonPlatforms" :key="p" :label="p" :value="p" />
            </el-select>
            <el-select v-model="skeletonTypeFilter" placeholder="全部类型" clearable style="width:140px" size="large" @change="fetchSkeletons">
              <el-option v-for="t in skeletonTypes" :key="t" :label="t" :value="t" />
            </el-select>
          </div>
          <el-select
            v-model="selectedSkeleton"
            placeholder="🔍 选择骨架"
            @change="onSkeletonChange"
            style="width:100%; margin-top:8px"
            size="large"
            :loading="loadingOptions"
            filterable
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
                  <el-tag size="small" type="primary" effect="plain" v-if="sk.platform">{{ sk.platform }}</el-tag>
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

          <!-- 骨架预览面板 -->
          <div class="skeleton-preview" v-if="selectedSkeletonData">
            <div class="preview-header">
              <span class="preview-icon">🔍</span>
              <span class="preview-title">骨架预览 — {{ selectedSkeletonData.name }}</span>
            </div>
            <!-- L2 策略 -->
            <div class="preview-row" v-if="selectedSkeletonData.strategy_desc">
              <span class="preview-label">L2 策略：</span>
              <span class="preview-val">{{ selectedSkeletonData.strategy_desc }}</span>
            </div>
            <!-- L3 结构 -->
            <div class="preview-row" v-if="selectedSkeletonData.structure_json && selectedSkeletonData.structure_json.length">
              <span class="preview-label">L3 结构：</span>
              <div class="preview-structures">
                <span
                  v-for="(s, i) in selectedSkeletonData.structure_json"
                  :key="i"
                  class="structure-chip"
                >
                  {{ s.name || s }}
                  <em v-if="s.ratio">({{ Math.round(s.ratio) }}%)</em>
                </span>
              </div>
            </div>
            <!-- L4 元素摘要 -->
            <div class="preview-row" v-if="selectedSkeletonData.elements_json">
              <span class="preview-label">L4 元素：</span>
              <div class="preview-elements">
                <span v-if="selectedSkeletonData.elements_json.hook" class="element-item">
                  🎣 钩子：{{ selectedSkeletonData.elements_json.hook }}
                </span>
                <span v-if="selectedSkeletonData.elements_json.transition" class="element-item">
                  🔀 转折：{{ selectedSkeletonData.elements_json.transition }}
                </span>
                <span v-if="selectedSkeletonData.elements_json.interaction" class="element-item">
                  💡 互动：{{ selectedSkeletonData.elements_json.interaction }}
                </span>
              </div>
            </div>
            <!-- 效果统计 -->
            <div class="preview-stats" v-if="selectedSkeletonData.avg_roi || selectedSkeletonData.avg_ctr || selectedSkeletonData.usage_count">
              <span v-if="selectedSkeletonData.avg_roi">💰 ROI {{ Number(selectedSkeletonData.avg_roi).toFixed(1) }}x</span>
              <span v-if="selectedSkeletonData.avg_ctr">📈 CTR {{ Number(selectedSkeletonData.avg_ctr).toFixed(1) }}%</span>
              <span v-if="selectedSkeletonData.usage_count">🔄 已使用 {{ selectedSkeletonData.usage_count }} 次</span>
            </div>
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

          <!-- 批量模式切换 -->
          <div class="batch-toggle">
            <el-checkbox v-model="batchMode" size="large">
              <span class="batch-toggle-label">🔄 批量模式 — 一次生成多个变体</span>
            </el-checkbox>
            <span class="batch-toggle-hint" v-if="batchMode">将替换内容拆分为多组，每组生成一个裂变结果</span>
          </div>
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
              <!-- 批量模式：多组输入 -->
              <template v-if="batchMode">
                <div v-for="(group, gIdx) in batchGroups" :key="gIdx" class="batch-group">
                  <div class="batch-group-header">
                    <span class="batch-group-num">变体 {{ gIdx + 1 }}</span>
                    <el-button v-if="batchGroups.length > 1" type="danger" link size="small" @click="removeBatchGroup(gIdx)">✕ 移除</el-button>
                  </div>
                  <el-form-item label="金句">
                    <el-select v-model="group.L5.golden_sentences" multiple allow-create filterable placeholder="金句（多条会均匀分配到各段落）" style="width:100%">
                      <el-option v-for="opt in options.golden_sentence" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="数据引用">
                    <el-select v-model="group.L5.data_refs" multiple allow-create filterable placeholder="数据（会嵌入到正文段落中）" style="width:100%">
                      <el-option v-for="opt in options.data_ref" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="视觉描述">
                    <el-select v-model="group.L5.visual_desc" multiple allow-create filterable placeholder="视觉描述（会生成画面指导）" style="width:100%">
                      <el-option v-for="opt in options.visual_desc" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                </div>
                <el-button type="primary" link @click="addBatchGroup" class="add-batch-btn">+ 添加变体组</el-button>
              </template>
              <!-- 单条模式 -->
              <template v-else>
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
              </template>
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
              <!-- L4 骨架默认值（未开启自定义覆盖时展示） -->
              <template v-else>
                <div class="l4-defaults" v-if="l4Defaults">
                  <div class="l4-defaults-hint">以下使用骨架默认 L4 元素，勾选「自定义覆盖」可修改</div>
                  <div class="l4-defaults-grid">
                    <div class="l4-default-item" v-if="l4Defaults.title_formula">
                      <span class="l4-default-label">📝 标题公式</span>
                      <span class="l4-default-val">{{ l4Defaults.title_formula }}</span>
                    </div>
                    <div class="l4-default-item" v-if="l4Defaults.hook">
                      <span class="l4-default-label">🎣 钩子句式</span>
                      <span class="l4-default-val">{{ l4Defaults.hook }}</span>
                    </div>
                    <div class="l4-default-item" v-if="l4Defaults.transition">
                      <span class="l4-default-label">🔀 转折方式</span>
                      <span class="l4-default-val">{{ l4Defaults.transition }}</span>
                    </div>
                    <div class="l4-default-item" v-if="l4Defaults.interaction">
                      <span class="l4-default-label">💡 互动设计</span>
                      <span class="l4-default-val">{{ l4Defaults.interaction }}</span>
                    </div>
                  </div>
                </div>
                <div class="l4-no-data" v-else>
                  当前骨架未配置 L4 元素，可勾选「自定义覆盖」手动填写
                </div>
              </template>
            </div>

            <!-- L3 结构替换（换枝杈模式） -->
            <div class="form-section" v-if="fissionMode === 'replace_branch'">
              <div class="form-section-title">🏗️ L3 结构替换 — 新段落结构</div>
              <div class="step-desc">为每个段落填写新的名称、功能和占比（总和需为 100%）</div>
              <div class="l3-sections-list">
                <div v-for="(sec, sIdx) in l3ReplacementSections" :key="sIdx" class="l3-section-item">
                  <div class="l3-section-header">
                    <span class="l3-section-num">段落 {{ sIdx + 1 }}</span>
                    <el-button v-if="l3ReplacementSections.length > 1" type="danger" link size="small" @click="removeL3Section(sIdx)">✕ 移除</el-button>
                  </div>
                  <el-row :gutter="12">
                    <el-col :span="8">
                      <el-form-item label="段落名称">
                        <el-input v-model="sec.name" placeholder="如：开场钩子" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="功能说明">
                        <el-input v-model="sec.function" placeholder="如：吸引注意" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="占比 (%)">
                        <el-input-number v-model="sec.ratio" :min="0" :max="100" :step="5" style="width:100%" />
                      </el-form-item>
                    </el-col>
                  </el-row>
                  <el-form-item label="模板句式">
                    <el-input v-model="sec.template" type="textarea" :rows="2" placeholder="该段落的模板句式，可用 {topic} 作为主题占位符" />
                  </el-form-item>
                </div>
                <el-button type="primary" link @click="addL3Section" class="add-l3-btn">+ 添加段落</el-button>
              </div>
              <div class="l3-ratio-hint" :class="{ 'l3-ratio-error': l3RatioSum !== 100 }">
                当前占比总和：{{ l3RatioSum }}% <span v-if="l3RatioSum !== 100">（需为 100%）</span>
              </div>
            </div>

            <!-- L2 策略替换（换表达模式） -->
            <div class="form-section" v-if="fissionMode === 'replace_style'">
              <div class="form-section-title">🎭 L2 策略替换 — 新策略风格</div>
              <div class="step-desc">定义新的策略标签和情绪描述</div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="新策略描述">
                    <el-input v-model="fissionForm.replacement.L2.strategy_desc" type="textarea" :rows="3" placeholder="如：专业测评+数据驱动，用实验数据说话" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="新钩子句式">
                    <el-input v-model="fissionForm.replacement.L2.hook" placeholder="如：90%的人都不知道的真相" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="新互动设计">
                    <el-input v-model="fissionForm.replacement.L2.interaction" placeholder="如：你遇到过这种情况吗？评论区聊聊" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="新情绪策略">
                    <el-input v-model="fissionForm.replacement.L2.emotion" placeholder="如：紧迫感+稀缺性" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- 模板预设 -->
            <div class="form-section">
              <div class="form-section-title">📋 模板预设</div>
              <div class="preset-bar">
                <el-select v-model="selectedPreset" placeholder="加载已保存的预设..." clearable style="width:260px" @change="applyPreset" :loading="loadingPresets">
                  <el-option v-for="p in presetList" :key="p.id" :label="p.name" :value="p.id" />
                </el-select>
                <el-button type="primary" link size="small" @click="openSavePreset">💾 保存当前为预设</el-button>
                <el-button type="warning" link size="small" @click="openEditPreset" :disabled="!selectedPreset">✏️ 编辑预设</el-button>
                <el-button type="danger" link size="small" @click="deletePreset" :disabled="!selectedPreset">🗑️ 删除预设</el-button>
              </div>
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
    <div class="card result-card" v-if="fissionResults.length > 0">
      <div class="result-header">
        <div class="result-badge">✨ 裂变完成</div>
        <div class="result-meta">
          <el-tag size="small" type="success">{{ fissionModeLabel }}</el-tag>
          <span class="result-skeleton-name">基于：{{ selectedSkeletonName }}</span>
          <el-tag v-if="fissionResults.length > 1" size="small" type="warning">{{ fissionResults.length }} 个变体</el-tag>
        </div>
      </div>

      <!-- 多结果 tabs -->
      <el-tabs v-if="fissionResults.length > 1" v-model="activeResultTab" type="card" class="result-tabs">
        <el-tab-pane v-for="(res, idx) in fissionResults" :key="idx" :label="`变体 ${idx + 1}`" :name="String(idx)">
          <div class="result-single" :data-result-idx="idx">
            <div class="result-prediction">
              <div class="prediction-item"><span class="prediction-label">预测 CTR</span><span class="prediction-value">{{ res.predicted_ctr }}</span></div>
              <div class="prediction-divider"></div>
              <div class="prediction-item"><span class="prediction-label">预测 ROI</span><span class="prediction-value prediction-highlight">{{ res.predicted_roi }}</span></div>
            </div>
            <div class="result-content-wrapper">
              <div class="result-content-label">📝 裂变产出内容</div>
              <div class="result-content-sections">
                <div v-for="(section, sidx) in parseFissionContent(res.output_content)" :key="sidx" class="result-section" :class="section.type">
                  <div class="section-header" v-if="section.header"><span class="section-icon">{{ section.icon }}</span><span class="section-title-text">{{ section.header }}</span></div>
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
              <el-button type="success" @click="saveAsMaterial(idx)" size="large">💾 保存为新素材</el-button>
              <el-button type="primary" @click="copyResult(idx)" size="large">📋 复制</el-button>
              <el-button @click="exportResultJson(idx)" size="large">📦 导出</el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 单结果 -->
      <template v-else-if="fissionResults.length === 1">
        <div class="result-prediction">
          <div class="prediction-item"><span class="prediction-label">预测 CTR</span><span class="prediction-value">{{ fissionResults[0].predicted_ctr }}</span></div>
          <div class="prediction-divider"></div>
          <div class="prediction-item"><span class="prediction-label">预测 ROI</span><span class="prediction-value prediction-highlight">{{ fissionResults[0].predicted_roi }}</span></div>
        </div>
        <div class="result-content-wrapper">
          <div class="result-content-label">📝 裂变产出内容</div>
          <div class="result-content-sections">
            <div v-for="(section, sidx) in parseFissionContent(fissionResults[0].output_content)" :key="sidx" class="result-section" :class="section.type">
              <div class="section-header" v-if="section.header"><span class="section-icon">{{ section.icon }}</span><span class="section-title-text">{{ section.header }}</span></div>
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
          <el-button type="success" @click="saveAsMaterial(0)" size="large">💾 保存为新素材</el-button>
          <el-button type="primary" @click="copyResult(0)" size="large">📋 复制纯文本</el-button>
          <el-button @click="exportResultJson(0)" size="large">📦 导出 JSON</el-button>
          <el-button @click="resetFission" size="large">🔄 再来一次</el-button>
        </div>
      </template>
    </div>

    <!-- 保存为素材弹窗 -->
    <el-dialog v-model="saveDialogVisible" title="💾 保存为新素材" width="520px" destroy-on-close>
      <el-form :model="saveForm" label-width="90px">
        <el-form-item label="素材标题" required>
          <el-input v-model="saveForm.title" placeholder="输入新素材标题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="平台">
              <el-select v-model="saveForm.platform" placeholder="选择平台" style="width:100%">
                <el-option v-for="opt in options.platform" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品类">
              <el-select v-model="saveForm.category" placeholder="选择品类" style="width:100%">
                <el-option v-for="opt in options.category" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="素材内容">
          <el-input v-model="saveForm.content" type="textarea" :rows="8" resize="vertical" placeholder="裂变产出的内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveMaterial" :loading="saveLoading">确认保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getOptions, getFissionPresets, createFissionPreset, updateFissionPreset, deleteFissionPreset } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const loadingOptions = ref(false)
const loadingSkeleton = ref(false)
const skeletons = ref([])
const selectedSkeleton = ref(null)
const skeletonPlatformFilter = ref('')
const skeletonTypeFilter = ref('')
const fissionMode = ref('replace_leaf')
const fissionResults = ref([])
const activeResultTab = ref('0')
const batchMode = ref(false)

// 批量变体组
const newEmptyGroup = () => ({
  L5: { golden_sentences: [], data_refs: [], visual_desc: [] },
})
const batchGroups = ref([newEmptyGroup()])

const addBatchGroup = () => { batchGroups.value.push(newEmptyGroup()) }
const removeBatchGroup = (idx) => { batchGroups.value.splice(idx, 1) }

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
  source_material_id: null,
  fission_mode: 'replace_leaf',
  new_topic: '',
  new_category: '',
  new_style: '',
  new_platform: '',
  replacement: {
    L5: { golden_sentences: [], data_refs: [], visual_desc: [], hook: '', interaction: '' },
    L4: { hook: '', transition: '', interaction: '' },
    L3: [],   // replace_branch 模式：新段落结构 [{name, function, ratio, template}]
    L2: { strategy_desc: '', hook: '', interaction: '', emotion: '' },  // replace_style 模式
  },
})

// L3 段落结构（replace_branch 模式）
const l3ReplacementSections = ref([{ name: '', function: '', ratio: 25, template: '' }])
const l3RatioSum = computed(() => l3ReplacementSections.value.reduce((sum, s) => sum + (s.ratio || 0), 0))

const addL3Section = () => {
  l3ReplacementSections.value.push({ name: '', function: '', ratio: 0, template: '' })
}
const removeL3Section = (idx) => {
  if (l3ReplacementSections.value.length > 1) l3ReplacementSections.value.splice(idx, 1)
}

const fissionModeLabel = computed(() => {
  const map = { replace_leaf: '换叶子', replace_branch: '换枝杈', replace_style: '换表达' }
  return map[fissionMode.value] || fissionMode.value
})

const selectedSkeletonName = computed(() => {
  const sk = skeletons.value.find(s => s.id === selectedSkeleton.value)
  return sk ? sk.name : ''
})

// 当前选中的骨架完整数据（用于预览面板）
const selectedSkeletonData = computed(() => {
  if (!selectedSkeleton.value) return null
  return skeletons.value.find(s => s.id === selectedSkeleton.value) || null
})

// L4 默认值（从当前骨架的 elements_json 中提取）
const l4Defaults = computed(() => {
  const sk = selectedSkeletonData.value
  if (!sk || !sk.elements_json) return null
  const el = sk.elements_json
  const hasAny = el.title_formula || el.hook || el.transition || el.interaction
  return hasAny ? { title_formula: el.title_formula || '', hook: el.hook || '', transition: el.transition || '', interaction: el.interaction || '' } : null
})

// 骨架筛选选项（从已加载骨架中提取）
const skeletonPlatforms = computed(() => {
  const set = new Set(skeletons.value.map(s => s.platform).filter(Boolean))
  return [...set]
})
const skeletonTypes = computed(() => {
  const set = new Set(skeletons.value.map(s => s.skeleton_type).filter(Boolean))
  return [...set]
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
    const params = {}
    if (skeletonPlatformFilter.value) params.platform = skeletonPlatformFilter.value
    if (skeletonTypeFilter.value) params.skeleton_type = skeletonTypeFilter.value
    const { data } = await api.get('/skeleton/', { params })
    skeletons.value = Array.isArray(data) ? data : (data.items || data)
  } catch (e) {
    console.error('加载骨架失败', e)
  }
  loadingSkeleton.value = false
}

const onSkeletonChange = (val) => {
  fissionForm.skeleton_id = val
  // 若尚未设置 source_material_id，自动从骨架的来源素材填充
  if (!fissionForm.source_material_id) {
    const sk = skeletons.value.find(s => s.id === val)
    if (sk && sk.source_material_id) {
      fissionForm.source_material_id = sk.source_material_id
    }
  }
}

// 内容完整性校验
const validateFissionForm = () => {
  const warnings = []
  const mode = fissionMode.value
  const hasGolden = fissionForm.replacement.L5.golden_sentences.length > 0
  const hasData = fissionForm.replacement.L5.data_refs.length > 0
  const hasVisual = fissionForm.replacement.L5.visual_desc.length > 0
  const hasAnyL5 = hasGolden || hasData || hasVisual

  if (!fissionForm.new_topic) warnings.push('请填写新主题')
  if (!fissionForm.new_category) warnings.push('建议填写新品类以便后续筛选')

  if (mode === 'replace_leaf' && !hasAnyL5) {
    warnings.push('「换叶子」模式建议至少填写 L5 表达层（金句/数据/视觉）中的一项')
  }
	  if (mode === 'replace_branch') {
	    if (!fissionForm.new_category) warnings.push('「换枝杈」模式需要填写新品类')
	    const l3Sections = fissionForm.replacement.L3 || []
	    if (l3Sections.length === 0) { warnings.push('「换枝杈」模式需要至少定义一个 L3 段落') } else {
	      const emptyName = l3Sections.findIndex(s => !s.name?.trim())
	      if (emptyName >= 0) warnings.push(`L3 段落 ${emptyName + 1} 缺少名称`)
	      const ratioSum = l3Sections.reduce((sum, s) => sum + (s.ratio || 0), 0)
	      if (ratioSum !== 100) warnings.push(`L3 段落占比总和为 ${ratioSum}%，需为 100%`)
	    }
	  }
	  if (mode === 'replace_style') {
	    if (!fissionForm.replacement.L2?.strategy_desc) warnings.push('「换表达」模式建议填写新策略描述')
	  }

  return warnings
}

const executeFission = async () => {
  if (!fissionForm.skeleton_id) {
    ElMessage.warning('请先选择骨架')
    return
  }
  // 完整性校验（仅警告，不阻止）
  const warnings = validateFissionForm()
  if (warnings.length > 0) {
    const critical = warnings.filter(w => w.startsWith('请'))
    if (critical.length > 0) {
      ElMessage.warning(critical[0])
      return
    }
    // 非关键警告：提示但允许继续
    try {
      await ElMessageBox.confirm(
        warnings.join('\n'),
        '内容完整性提醒',
        { confirmButtonText: '继续裂变', cancelButtonText: '去补充', type: 'warning' }
      )
    } catch { return }
  }
  loading.value = true
  try {
    if (batchMode.value && batchGroups.value.length > 1) {
      // 批量模式：逐组调用，收集结果
      const results = []
      for (let i = 0; i < batchGroups.value.length; i++) {
        const group = batchGroups.value[i]
        const payload = {
          ...fissionForm,
          fission_mode: fissionMode.value,
          replacement: {
            L5: group.L5,
            L4: fissionForm.replacement.L4,
            L3: fissionForm.replacement.L3,
            L2: fissionForm.replacement.L2,
          },
        }
        const { data } = await api.post('/fission/', payload)
        results.push(data)
      }
      fissionResults.value = results
      activeResultTab.value = '0'
      ElMessage.success(`裂变完成，已生成 ${results.length} 个变体！`)
    } else {
      // 单条模式
      const payload = { ...fissionForm, fission_mode: fissionMode.value }
      const { data } = await api.post('/fission/', payload)
      fissionResults.value = [data]
      activeResultTab.value = '0'
      ElMessage.success('裂变成功！')
    }
  } catch (e) {
    ElMessage.error('裂变失败: ' + (e.response?.data?.detail || e.message))
  }
  loading.value = false
}

const copyResult = async (idx) => {
  const res = fissionResults.value[idx ?? 0]
  if (!res?.output_content) return
  const text = res.output_content
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

const exportResultJson = (idx) => {
  const res = fissionResults.value[idx ?? 0]
  if (!res) return
  const exportData = {
    skeleton: { id: selectedSkeletonData.value?.id || null, name: selectedSkeletonName.value },
    fission_mode: fissionMode.value,
    fission_mode_label: fissionModeLabel.value,
    form: {
      new_topic: fissionForm.new_topic,
      new_category: fissionForm.new_category,
      new_style: fissionForm.new_style,
      new_platform: fissionForm.new_platform,
      replacement: fissionForm.replacement,
    },
    result: {
      id: res.id,
      output_content: res.output_content,
      predicted_ctr: res.predicted_ctr,
      predicted_roi: res.predicted_roi,
      created_at: res.created_at,
    },
  }
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const safeName = (selectedSkeletonName.value || 'fission').replace(/[\\/:*?"<>|]/g, '_')
  const suffix = fissionResults.value.length > 1 ? `_variant${idx + 1}` : ''
  a.download = `fission_${safeName}${suffix}_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('已导出 JSON 文件')
}

const resetFission = () => {
  fissionResults.value = []
  activeResultTab.value = '0'
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

const resetFissionForm = async () => {
  try {
    await ElMessageBox.confirm('重置将清空所有已填写内容，确定继续吗？', '确认重置', { type: 'warning' })
  } catch { return }
  fissionForm.new_topic = ''
  fissionForm.new_category = ''
  fissionForm.new_style = ''
  fissionForm.new_platform = ''
  fissionForm.replacement = {
    L5: { golden_sentences: [], data_refs: [], visual_desc: [], hook: '', interaction: '' },
    L4: { hook: '', transition: '', interaction: '' },
    L3: [],
    L2: { strategy_desc: '', hook: '', interaction: '', emotion: '' },
  }
  l3ReplacementSections.value = [{ name: '', function: '', ratio: 25, template: '' }]
  showL4Overrides.value = false
  batchMode.value = false
  batchGroups.value = [newEmptyGroup()]
  selectedPreset.value = ''
}

// 模板预设（后端动态加载）
const selectedPreset = ref('')
const presetList = ref([])
const loadingPresets = ref(false)

const fetchPresets = async () => {
  loadingPresets.value = true
  try {
    presetList.value = await getFissionPresets()
  } catch (e) {
    console.error('加载预设失败', e)
  }
  loadingPresets.value = false
}

const openSavePreset = async () => {
  if (!fissionForm.new_topic) { ElMessage.warning('请先填写新主题再保存预设'); return }
  let name = ''
  try {
    const { value } = await ElMessageBox.prompt('输入预设名称：', '保存预设', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: fissionForm.new_topic,
      inputValidator: (v) => v?.trim() ? true : '名称不能为空',
    })
    name = value?.trim()
  } catch { return }
  if (!name) return
  try {
    await createFissionPreset({
      name,
      description: '',
      config_json: {
        new_category: fissionForm.new_category,
        new_style: fissionForm.new_style,
        new_platform: fissionForm.new_platform,
        replacement: fissionForm.replacement,
      },
    })
    ElMessage.success(`预设「${name}」已保存`)
    await fetchPresets()
  } catch (e) {
    ElMessage.error('保存预设失败')
  }
}

const openEditPreset = async () => {
  if (!selectedPreset.value) return
  const preset = presetList.value.find(p => String(p.id) === String(selectedPreset.value))
  if (!preset) return
  const config = preset.config_json || {}
  try {
    await updateFissionPreset(preset.id, {
      name: preset.name,
      config_json: {
        new_category: fissionForm.new_category ?? config.new_category,
        new_style: fissionForm.new_style ?? config.new_style,
        new_platform: fissionForm.new_platform ?? config.new_platform,
        replacement: fissionForm.replacement ?? config.replacement,
      },
    })
    ElMessage.success(`预设「${preset.name}」已更新`)
    await fetchPresets()
  } catch (e) {
    ElMessage.error('更新预设失败')
  }
}

const applyPreset = (key) => {
  if (!key) return
  const preset = presetList.value.find(p => String(p.id) === String(key) || p._key === key)
  if (!preset) return
  const config = preset.config_json || {}
  if (config.new_category) fissionForm.new_category = config.new_category
  if (config.new_style) fissionForm.new_style = config.new_style
  if (config.new_platform) fissionForm.new_platform = config.new_platform
  if (config.replacement) {
    fissionForm.replacement = JSON.parse(JSON.stringify(config.replacement))
  }
  ElMessage.success(`已加载预设「${preset.name}」`)
}

const deletePreset = async () => {
  if (!selectedPreset.value) return
  try {
    await deleteFissionPreset(selectedPreset.value)
    ElMessage.success('预设已删除')
    selectedPreset.value = ''
    await fetchPresets()
  } catch (e) {
    ElMessage.error('删除预设失败')
  }
}

// 保存为新素材
const saveDialogVisible = ref(false)
const saveLoading = ref(false)
const saveForm = reactive({
  title: '',
  platform: '',
  category: '',
  content: '',
})

const saveAsMaterial = (idx) => {
  const res = fissionResults.value[idx ?? 0]
  if (!res?.output_content) return
  saveForm.title = fissionForm.new_topic ? `【裂变】${fissionForm.new_topic}` : ''
  if (fissionResults.value.length > 1) saveForm.title += ` - 变体${idx + 1}`
  saveForm.platform = fissionForm.new_platform || ''
  saveForm.category = fissionForm.new_category || ''
  saveForm.content = res.output_content
  saveDialogVisible.value = true
}

const confirmSaveMaterial = async () => {
  if (!saveForm.title) { ElMessage.warning('请输入素材标题'); return }
  if (!saveForm.content) { ElMessage.warning('素材内容不能为空'); return }
  saveLoading.value = true
  try {
    await api.post('/material/', saveForm)
    ElMessage.success('已保存为新素材，可在素材库查看')
    saveDialogVisible.value = false
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
  saveLoading.value = false
}

// 同步单条模式和批量模式的数据
watch(batchMode, (val) => {
  if (val) {
    // 切换到批量：将当前单条数据复制到第一组
    if (batchGroups.value.length === 0) batchGroups.value.push(newEmptyGroup())
    batchGroups.value[0].L5 = JSON.parse(JSON.stringify(fissionForm.replacement.L5))
  } else {
    // 切换到单条：将第一组数据合并回单条
    if (batchGroups.value.length > 0) {
      fissionForm.replacement.L5 = JSON.parse(JSON.stringify(batchGroups.value[0].L5))
    }
  }
})

// L3 段落数据同步到表单
watch(l3ReplacementSections, (val) => {
  fissionForm.replacement.L3 = val.map(s => ({ ...s }))
}, { deep: true })

onMounted(() => {
  fetchOptions()
  fetchPresets()
  // 从路由参数获取 source_material_id（从素材库/骨架库跳转过来时携带）
  if (route.query.source_material_id) {
    fissionForm.source_material_id = Number(route.query.source_material_id)
  }
  fetchSkeletons().then(() => {
    const skeletonId = route.query.skeleton_id
    if (skeletonId) {
      const id = Number(skeletonId)
      const sk = skeletons.value.find(s => s.id === id)
      if (sk) {
        selectedSkeleton.value = id
        fissionForm.skeleton_id = id
        // 若未通过路由参数传入 source_material_id，则使用骨架的来源素材 ID
        if (!fissionForm.source_material_id && sk.source_material_id) {
          fissionForm.source_material_id = sk.source_material_id
        }
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

/* Skeleton preview panel */
.skeleton-preview {
  margin-top: 16px; padding: 16px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border-radius: 10px; border: 1px solid #e0e7ff;
}
.preview-header { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.preview-icon { font-size: 16px; }
.preview-title { font-size: 13px; font-weight: 600; color: #4338ca; }
.preview-row { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; font-size: 13px; }
.preview-row:last-child { margin-bottom: 0; }
.preview-label { color: #6366f1; font-weight: 500; white-space: nowrap; flex-shrink: 0; padding-top: 1px; }
.preview-val { color: #444; line-height: 1.6; }
.preview-structures { display: flex; flex-wrap: wrap; gap: 6px; }
.structure-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; border-radius: 12px;
  background: #e0e7ff; color: #4338ca; font-size: 12px;
}
.structure-chip em { font-style: normal; color: #818cf8; font-size: 11px; }
.preview-elements { display: flex; flex-direction: column; gap: 4px; }
.element-item { font-size: 12px; color: #555; line-height: 1.5; }
.preview-stats {
  display: flex; align-items: center; gap: 16px;
  margin-top: 10px; padding-top: 10px; border-top: 1px dashed #c7d2fe;
  font-size: 12px; color: #6366f1;
}

/* L4 defaults display */
.l4-defaults { margin-top: 4px; }
.l4-defaults-hint {
  font-size: 12px; color: #8b8b8b; margin-bottom: 10px;
  padding: 6px 10px; background: #fff8e6; border-radius: 6px; border-left: 3px solid #e6a700;
}
.l4-defaults-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.l4-default-item {
  padding: 8px 12px; background: #f8f9fa; border-radius: 8px;
  border: 1px solid #eee; display: flex; flex-direction: column; gap: 2px;
}
.l4-default-label { font-size: 12px; color: #888; font-weight: 500; }
.l4-default-val { font-size: 13px; color: #333; }
.l4-no-data {
  margin-top: 4px; padding: 10px 14px;
  background: #f8f9fa; border-radius: 8px;
  font-size: 13px; color: #aaa; text-align: center;
}

/* L3 section replacement (replace_branch mode) */
.l3-sections-list { margin-top: 12px; }
.l3-section-item {
  padding: 14px; margin-bottom: 12px;
  background: #f8f9fa; border-radius: 10px;
  border: 1px solid #ebeef5;
}
.l3-section-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.l3-section-num { font-size: 13px; font-weight: 600; color: #667eea; }
.add-l3-btn { margin-top: 4px; }
.l3-ratio-hint {
  margin-top: 8px; padding: 6px 12px; border-radius: 6px;
  font-size: 13px; color: #555; background: #fff8e6; border-left: 3px solid #e6a700;
}
.l3-ratio-error { background: #fef0f0; border-left-color: #f56c6c; color: #c00; }

/* Skeleton option in dropdown */
.skeleton-filter-bar { display: flex; gap: 8px; margin-top: 12px; }
.skeleton-option { display: flex; flex-direction: column; gap: 2px; }
.sk-name { font-size: 14px; color: #333; }
.sk-meta { font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

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

/* Batch mode */
.batch-toggle { margin-top: 12px; padding: 10px 14px; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #f093fb; }
.batch-toggle-label { font-size: 14px; font-weight: 500; color: #333; }
.batch-toggle-hint { font-size: 12px; color: #999; margin-left: 8px; }
.batch-group { padding: 12px; margin-bottom: 12px; background: #fafbfc; border-radius: 8px; border: 1px solid #eee; }
.batch-group-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.batch-group-num { font-size: 13px; font-weight: 600; color: #f093fb; }
.add-batch-btn { margin-top: 4px; }

/* Result tabs */
.result-tabs { margin-top: 16px; }
.result-tabs :deep(.el-tabs__item) { font-size: 13px; }

/* Preset bar */
.preset-bar { display: flex; align-items: center; gap: 12px; }
</style>
