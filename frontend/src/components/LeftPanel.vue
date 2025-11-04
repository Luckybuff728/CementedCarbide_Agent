<template>
  <div class="left-panel">
    <!-- 顶部：快捷模板 -->
    <div class="panel-header">
      <h3>参数输入</h3>
      <div class="header-actions">
        <el-button 
          size="small" 
          type="primary" 
          @click="loadExampleData"
          plain
        >
          加载示例
        </el-button>
        <el-button 
          size="small" 
          @click="resetForm"
        >
          清空
        </el-button>
      </div>
    </div>

    <!-- 中间：表单内容 -->
    <div class="panel-content">
      <el-form
        ref="formRef"
        :model="formData"
        label-position="top"
        size="default"
      >
        <!-- 使用Collapse折叠面板 -->
        <el-collapse v-model="activeCollapse" accordion>
          <!-- 1. 涂层成分 -->
          <el-collapse-item name="composition">
            <template #title>
              <div class="collapse-title">
                <span class="title-icon">🧪</span>
                <span class="title-text">涂层成分</span>
                <el-tag v-if="compositionSum > 0" size="small" type="info">
                  {{ compositionSum.toFixed(1) }}%
                </el-tag>
              </div>
            </template>

            <div class="composition-grid">
              <el-form-item label="Al含量">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.al_content"
                    :min="0" 
                    :max="100" 
                    :precision="1"
                    :step="0.5"
                  />
                  <span class="unit">at.%</span>
                </div>
              </el-form-item>

              <el-form-item label="Ti含量">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.ti_content"
                    :min="0" 
                    :max="100" 
                    :precision="1"
                    :step="0.5"
                  />
                  <span class="unit">at.%</span>
                </div>
              </el-form-item>

              <el-form-item label="N含量">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.n_content"
                    :min="0" 
                    :max="100" 
                    :precision="1"
                    :step="0.5"
                  />
                  <span class="unit">at.%</span>
                </div>
              </el-form-item>
            </div>

            <!-- 成分总和 -->
            <div class="composition-sum" :class="{ 'warning': compositionSum > 100 }">
              成分总和: {{ compositionSum.toFixed(1) }}%
            </div>

            <!-- 其他元素动态添加 -->
            <div class="other-elements">
              <label class="sub-label">其他元素</label>
              <div v-for="(element, index) in formData.other_elements" :key="index" class="element-row">
                <el-input 
                  v-model="element.name" 
                  placeholder="元素名"
                  style="width: 90px;"
                  size="small"
                />
                <el-input-number 
                  v-model="element.content"
                  :min="0" 
                  :max="50" 
                  :precision="1"
                  :step="0.1"
                  size="small"
                  style="width: 90px;"
                />
                <span class="unit">at.%</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  icon="Delete" 
                  circle 
                  @click="removeElement(index)"
                />
              </div>
              <el-button 
                type="primary" 
                size="small" 
                icon="Plus" 
                @click="addElement"
                plain
              >
                添加元素
              </el-button>
            </div>
          </el-collapse-item>

          <!-- 2. 工艺参数 -->
          <el-collapse-item name="process">
            <template #title>
              <div class="collapse-title">
                <span class="title-icon">⚙️</span>
                <span class="title-text">工艺参数</span>
              </div>
            </template>

            <el-form-item label="工艺选择">
              <el-select v-model="formData.process_type" style="width: 100%">
                <el-option label="磁控溅射" value="magnetron_sputtering" />
                <el-option label="CVD" value="cvd" />
              </el-select>
            </el-form-item>

            <div class="param-grid">
              <el-form-item label="沉积气压">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.deposition_pressure"
                    :min="0" 
                    :max="10" 
                    :precision="1"
                    :step="0.1"
                  />
                  <span class="unit">Pa</span>
                </div>
              </el-form-item>

              <el-form-item label="沉积温度">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.deposition_temperature"
                    :min="200" 
                    :max="800" 
                    :step="10"
                  />
                  <span class="unit">℃</span>
                </div>
              </el-form-item>

              <el-form-item label="偏压">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.bias_voltage"
                    :min="0" 
                    :max="500" 
                    :step="5"
                  />
                  <span class="unit">V</span>
                </div>
              </el-form-item>

              <el-form-item label="N₂流量">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.n2_flow"
                    :min="0" 
                    :max="500" 
                    :step="5"
                  />
                  <span class="unit">sccm</span>
                </div>
              </el-form-item>
            </div>

            <!-- 其他气体动态添加 -->
            <div class="gas-section">
              <label class="sub-label">其他气体</label>
              <div v-for="(gas, index) in formData.other_gases" :key="index" class="gas-row">
                <el-input 
                  v-model="gas.type" 
                  placeholder="气体种类"
                  style="width: 90px;"
                  size="small"
                />
                <el-input-number 
                  v-model="gas.flow"
                  :min="0"
                  :max="1000"
                  :step="5"
                  size="small"
                  style="width: 90px;"
                />
                <span class="unit">sccm</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  icon="Delete" 
                  circle 
                  @click="removeGas(index)"
                />
              </div>
              <el-button 
                type="primary" 
                size="small" 
                icon="Plus" 
                @click="addGas"
                plain
              >
                添加气体
              </el-button>
            </div>
          </el-collapse-item>

          <!-- 3. 结构设计 -->
          <el-collapse-item name="structure">
            <template #title>
              <div class="collapse-title">
                <span class="title-icon">🏗️</span>
                <span class="title-text">结构设计</span>
                <el-tag v-if="formData.structure_type" size="small" type="info">
                  {{ formData.structure_type === 'multi' ? '多层' : '单层' }}
                </el-tag>
              </div>
            </template>

            <el-form-item label="结构类型">
              <el-select v-model="formData.structure_type" @change="onStructureChange" style="width: 100%">
                <el-option label="单层" value="single" />
                <el-option label="多层" value="multi" />
              </el-select>
            </el-form-item>

            <!-- 多层结构设计 -->
            <div v-if="formData.structure_type === 'multi'" class="multi-layer-design">
              <label class="sub-label">层结构设计</label>
              <div v-for="(layer, index) in formData.layers" :key="index" class="layer-row">
                <el-input 
                  v-model="layer.type" 
                  placeholder="层种类"
                  style="width: 100px;"
                  size="small"
                />
                <el-input-number 
                  v-model="layer.thickness"
                  :min="0"
                  :max="10"
                  :precision="2"
                  :step="0.1"
                  size="small"
                  style="width: 90px;"
                />
                <span class="unit">μm</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  icon="Delete" 
                  circle 
                  @click="removeLayer(index)"
                />
              </div>
              <el-button 
                type="primary" 
                size="small" 
                icon="Plus" 
                @click="addLayer"
                plain
              >
                添加层
              </el-button>
            </div>

            <!-- 单层厚度 -->
            <el-form-item v-else label="总厚度">
              <div class="input-with-unit">
                <el-input-number 
                  v-model="formData.total_thickness"
                  :min="0.1"
                  :max="20"
                  :precision="1"
                  :step="0.1"
                />
                <span class="unit">μm</span>
              </div>
            </el-form-item>
          </el-collapse-item>

          <!-- 4. 性能需求 -->
          <el-collapse-item name="performance">
            <template #title>
              <div class="collapse-title">
                <span class="title-icon">🎯</span>
                <span class="title-text">性能需求</span>
              </div>
            </template>

            <el-form-item label="基体材料">
              <el-input 
                v-model="formData.substrate_material" 
                placeholder="如：硬质合金(WC-Co)"
              />
            </el-form-item>

            <div class="param-grid">
              <el-form-item label="结合力">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.adhesion_strength"
                    :min="0"
                    :max="100"
                    :precision="1"
                  />
                  <span class="unit">N</span>
                </div>
              </el-form-item>

              <el-form-item label="弹性模量">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.elastic_modulus"
                    :min="100"
                    :max="800"
                    :step="10"
                  />
                  <span class="unit">GPa</span>
                </div>
              </el-form-item>

              <el-form-item label="工作温度">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.working_temperature"
                    :min="200"
                    :max="1200"
                    :step="50"
                  />
                  <span class="unit">℃</span>
                </div>
              </el-form-item>

              <el-form-item label="切削速度">
                <div class="input-with-unit">
                  <el-input-number 
                    v-model="formData.cutting_speed"
                    :min="50"
                    :max="1000"
                    :step="10"
                  />
                  <span class="unit">m/min</span>
                </div>
              </el-form-item>
            </div>

            <el-form-item label="应用场景">
              <el-input 
                v-model="formData.application_scenario"
                type="textarea"
                :rows="3"
                placeholder="描述具体应用场景，如：高温切削、钢材加工等"
                maxlength="200"
                show-word-limit
              />
              <!-- 场景提示词标签 -->
              <div class="scenario-hints">
                <span class="hint-label">快速选择：</span>
                <el-tag
                  v-for="hint in scenarioHints"
                  :key="hint"
                  size="small"
                  class="scenario-hint"
                  @click="addHintToScenario(hint)"
                  style="cursor: pointer;"
                >
                  {{ hint }}
                </el-tag>
              </div>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
      </el-form>
    </div>

    <!-- 底部：提交按钮 -->
    <div class="panel-footer">
      <el-button 
        type="primary" 
        size="large" 
        @click="handleSubmit" 
        :loading="workflowStore.isProcessing"
        :disabled="compositionSum > 100"
        block
      >
        开始分析
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '../stores/workflow'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['submit'])

// 表单引用
const formRef = ref(null)
const selectedTemplate = ref('custom')

// 折叠面板活动项（默认展开第一个）
const activeCollapse = ref('composition')

// 应用场景快速提示词
const scenarioHints = [
  '高温切削',
  '钢材加工',
  '铝合金加工',
  '干式切削',
  '湿式切削',
  '精密加工',
  '粗加工',
  '高速加工'
]

// 表单数据
const formData = ref({
  // 涂层成分
  al_content: 30.0,
  ti_content: 25.0,
  n_content: 45.0,
  other_elements: [],
  
  // 工艺参数
  process_type: 'magnetron_sputtering',
  deposition_pressure: 0.6,
  deposition_temperature: 400,
  bias_voltage: 90,
  n2_flow: 210,
  other_gases: [],
  
  // 结构设计
  structure_type: 'single',
  total_thickness: 3.0,
  layers: [],
  
  // 性能需求
  substrate_material: '硬质合金(WC-Co)',
  adhesion_strength: 50.0,
  elastic_modulus: 400,
  working_temperature: 800,
  cutting_speed: 200,
  application_scenario: ''
})

// 计算成分总和
const compositionSum = computed(() => {
  let sum = formData.value.al_content + formData.value.ti_content + formData.value.n_content
  formData.value.other_elements.forEach(elem => {
    sum += elem.content || 0
  })
  return sum
})

// 加载示例数据
const loadExampleData = () => {
  formData.value = {
    // 涂层成分
    al_content: 32.0,
    ti_content: 23.0,
    n_content: 45.0,
    other_elements: [],
    
    // 工艺参数
    process_type: 'magnetron_sputtering',
    deposition_pressure: 0.6,
    deposition_temperature: 450,
    bias_voltage: 100,
    n2_flow: 210,
    other_gases: [{ type: 'Ar', flow: 280 }],
    
    // 结构设计
    structure_type: 'multi',
    total_thickness: 3.5,
    layers: [
      { type: 'AlTiN', thickness: 2.0 },
      { type: 'TiN', thickness: 1.5 }
    ],
    
    // 性能需求
    substrate_material: '硬质合金(WC-Co)',
    adhesion_strength: 50.0,
    elastic_modulus: 400,
    working_temperature: 900,
    cutting_speed: 250,
    application_scenario: '高速切削，钢材加工，干式加工环境，要求高硬度和优异抗氧化性能'
  }
  ElMessage.success('已加载示例数据')
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  formData.value.other_elements = []
  formData.value.other_gases = []
  formData.value.layers = []
  ElMessage.success('已清空表单')
}

// 添加/删除元素
const addElement = () => {
  formData.value.other_elements.push({ name: '', content: 0 })
}

const removeElement = (index) => {
  formData.value.other_elements.splice(index, 1)
}

// 添加/删除气体
const addGas = () => {
  formData.value.other_gases.push({ type: '', flow: 0 })
}

const removeGas = (index) => {
  formData.value.other_gases.splice(index, 1)
}

// 添加/删除层
const addLayer = () => {
  formData.value.layers.push({ type: '', thickness: 1.0 })
}

const removeLayer = (index) => {
  formData.value.layers.splice(index, 1)
}

// 结构类型变化处理
const onStructureChange = (value) => {
  if (value === 'multi' && formData.value.layers.length === 0) {
    addLayer()
  }
}

// 添加提示词到应用场景
const addHintToScenario = (hint) => {
  if (!formData.value.application_scenario.includes(hint)) {
    formData.value.application_scenario += (formData.value.application_scenario ? '，' : '') + hint
  }
}

// 提交表单
const handleSubmit = () => {
  if (compositionSum.value > 100.1) {
    ElMessage.error('成分总和不能超过100%')
    return
  }
  
  // 转换数据格式
  const submitData = {
    composition: {
      al_content: formData.value.al_content,
      ti_content: formData.value.ti_content,
      n_content: formData.value.n_content,
      other_elements: formData.value.other_elements
    },
    process_params: {
      process_type: formData.value.process_type,
      deposition_pressure: formData.value.deposition_pressure,
      deposition_temperature: formData.value.deposition_temperature,
      bias_voltage: formData.value.bias_voltage,
      n2_flow: formData.value.n2_flow,
      other_gases: formData.value.other_gases
    },
    structure_design: {
      structure_type: formData.value.structure_type,
      total_thickness: formData.value.total_thickness,
      layers: formData.value.layers
    },
    target_requirements: {
      substrate_material: formData.value.substrate_material,
      adhesion_strength: formData.value.adhesion_strength,
      elastic_modulus: formData.value.elastic_modulus,
      working_temperature: formData.value.working_temperature,
      cutting_speed: formData.value.cutting_speed,
      application_scenario: formData.value.application_scenario
    }
  }
  
  emit('submit', submitData)
}
</script>

<style scoped>
.left-panel {
  min-width: 200px;
  max-width: 600px;
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  background: white;
}

/* 表单分节 */
.form-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 网格布局 */
.composition-grid,
.param-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

/* 涂层成分改为单列布局，避免过挤 */
.composition-grid {
  grid-template-columns: 1fr;
}

/* 工艺参数保持两列，在窄宽度下也会自动换行 */
.param-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

/* 带单位的输入框 */
.input-with-unit {
  display: flex;
  align-items: center;
  gap: 6px;
}

.input-with-unit :deep(.el-input-number) {
  flex: 1;
}

.unit {
  font-size: 13px;
  color: var(--text-secondary);
  flex-shrink: 0;
  min-width: 40px;
}

/* 成分总和 */
.composition-sum {
  text-align: center;
  padding: 8px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  background: #d1fae5;
  color: var(--success);
  border: 1px solid #a7f3d0;
}

.composition-sum.warning {
  background: #fee2e2;
  color: var(--danger);
  border-color: #fecaca;
}

/* Element Plus 表单项样式调整 */
:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
  padding-bottom: 6px;
}

:deep(.el-input-number) {
  width: 100%;
}

/* 动态配置区域 */
.other-elements,
.gas-section,
.multi-layer-design {
  margin-top: 16px;
}

.sub-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 8px;
}

/* 动态行项目 */
.element-row,
.gas-row,
.layer-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

/* 应用场景提示词 */
.scenario-hints {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.hint-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-right: 4px;
}

.scenario-hint {
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-hint:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 折叠面板标题 */
.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  font-size: 15px;
  font-weight: 600;
}

.title-icon {
  font-size: 18px;
}

.title-text {
  flex: 1;
}

/* Element Plus Collapse样式覆盖 */
:deep(.el-collapse-item__header) {
  height: 48px;
  padding: 0 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}

:deep(.el-collapse-item__header.is-active) {
  background: var(--bg-secondary);
}

:deep(.el-collapse-item__wrap) {
  border: none;
}

:deep(.el-collapse-item__content) {
  padding: 16px 12px;
}
</style>
