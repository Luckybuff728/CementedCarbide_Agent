<template>
  <div class="left-panel">
    <!-- 顶部：快捷模板 -->
    <div class="panel-header">
      <h3>参数输入</h3>
      <div class="header-actions">
	        <n-button 
          size="small" 
          type="primary" 
          @click="loadExampleData"
          secondary
        >
          <template #icon>
            <n-icon><VideoPlay /></n-icon>
          </template>
          加载示例
        </n-button>
	        <n-button 
          size="small" 
          @click="resetForm"
          secondary
        >
          <template #icon>
            <n-icon><RefreshLeft /></n-icon>
          </template>
          清空
        </n-button>
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
        <el-collapse v-model="activeCollapse">
          <!-- 1. 涂层成分 -->
          <el-collapse-item name="composition">
            <template #title>
              <div class="collapse-title">
                <el-icon class="title-icon"><Operation /></el-icon>
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
	            <n-button 
                type="primary" 
                size="small" 
                @click="addElement"
                dashed
              >
                <template #icon>
                  <n-icon><Plus /></n-icon>
                </template>
                添加元素
              </n-button>
            </div>
          </el-collapse-item>

          <!-- 2. 工艺参数 -->
          <el-collapse-item name="process">
            <template #title>
              <div class="collapse-title">
                <el-icon class="title-icon"><Setting /></el-icon>
                <span class="title-text">工艺参数</span>
              </div>
            </template>

            <el-form-item label="工艺选择">
              <el-select v-model="formData.process_type" style="width: 100%" placeholder="请选择工艺类型">
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
	            <n-button 
                type="primary" 
                size="small" 
                @click="addGas"
                dashed
              >
                <template #icon>
                  <n-icon><Plus /></n-icon>
                </template>
                添加气体
              </n-button>
            </div>
          </el-collapse-item>

          <!-- 3. 结构设计 -->
          <el-collapse-item name="structure">
            <template #title>
              <div class="collapse-title">
                <el-icon class="title-icon"><Tools /></el-icon>
                <span class="title-text">结构设计</span>
                <el-tag v-if="formData.structure_type" size="small" type="info">
                  {{ formData.structure_type === 'multi' ? '多层' : '单层' }}
                </el-tag>
              </div>
            </template>

            <el-form-item label="结构类型">
              <el-select v-model="formData.structure_type" @change="onStructureChange" style="width: 100%" placeholder="请选择结构类型">
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
	              <n-button 
                type="primary" 
                size="small" 
                @click="addLayer"
                dashed
              >
                <template #icon>
                  <n-icon><Plus /></n-icon>
                </template>
                添加层
              </n-button>
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
                <el-icon class="title-icon"><Odometer /></el-icon>
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
        style="width: 100%"
      >
        开始分析</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Operation,
  Setting,
  Tools,
  Odometer,
  Plus,
  Delete,
  RefreshLeft,
  VideoPlay
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '../stores/workflow'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['submit'])

// 表单引用
const formRef = ref(null)
const selectedTemplate = ref('custom')

// 折叠面板活动项（默认展开第一个，数组格式支持多个同时展开）
const activeCollapse = ref(['composition'])

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

// 示例场景数据
const exampleScenarios = {
  highSpeedSteel: {
    name: '高速钢材切削',
    description: '适用于钢材高速干式切削，要求高硬度和优异抗氧化性',
    data: {
      // 涂层成分 - 高Al含量提升抗氧化性
      al_content: 35.0,
      ti_content: 20.0,
      n_content: 45.0,
      other_elements: [],
      
      // 工艺参数 - 磁控溅射，中等温度
      process_type: 'magnetron_sputtering',
      deposition_pressure: 0.6,
      deposition_temperature: 450,
      bias_voltage: 100,
      n2_flow: 220,
      other_gases: [{ type: 'Ar', flow: 280 }],
      
      // 结构设计 - 多层结构增强韧性
      structure_type: 'multi',
      total_thickness: 3.5,
      layers: [
        { type: 'AlTiN', thickness: 2.2 },
        { type: 'TiN', thickness: 1.3 }
      ],
      
      // 性能需求 - 高速高温工况
      substrate_material: '硬质合金(WC-Co)',
      adhesion_strength: 55.0,
      elastic_modulus: 420,
      working_temperature: 900,
      cutting_speed: 280,
      application_scenario: '高速切削，钢材加工，干式加工环境，要求高硬度和优异抗氧化性能'
    }
  },
  precisionAluminum: {
    name: '铝合金精密加工',
    description: '适用于铝合金精密加工，要求低摩擦、高光洁度',
    data: {
      // 涂层成分 - 适中Al/Ti比，避免粘铝
      al_content: 28.0,
      ti_content: 27.0,
      n_content: 45.0,
      other_elements: [],
      
      // 工艺参数 - 低温低偏压，精细控制
      process_type: 'magnetron_sputtering',
      deposition_pressure: 0.4,
      deposition_temperature: 380,
      bias_voltage: 75,
      n2_flow: 180,
      other_gases: [{ type: 'Ar', flow: 320 }],
      
      // 结构设计 - 单层薄涂层，保持锋利度
      structure_type: 'single',
      total_thickness: 2.0,
      layers: [],
      
      // 性能需求 - 中低温精密加工
      substrate_material: '硬质合金(WC-Co)',
      adhesion_strength: 45.0,
      elastic_modulus: 380,
      working_temperature: 400,
      cutting_speed: 150,
      application_scenario: '铝合金加工，精密加工，湿式切削，要求低摩擦系数和优异表面光洁度'
    }
  },
  highTempWear: {
    name: '高温耐磨应用',
    description: '适用于超高温工况，要求极高热稳定性和耐磨性',
    data: {
      // 涂层成分 - 超高Al含量，极佳抗氧化
      al_content: 40.0,
      ti_content: 15.0,
      n_content: 45.0,
      other_elements: [],
      
      // 工艺参数 - CVD工艺，高温沉积
      process_type: 'cvd',
      deposition_pressure: 2.5,
      deposition_temperature: 680,
      bias_voltage: 0,
      n2_flow: 150,
      other_gases: [
        { type: 'H2', flow: 200 },
        { type: 'AlCl3', flow: 80 }
      ],
      
      // 结构设计 - 复杂多层结构
      structure_type: 'multi',
      total_thickness: 5.0,
      layers: [
        { type: 'TiN(过渡�?', thickness: 0.5 },
        { type: 'AlTiN', thickness: 3.0 },
        { type: 'Al2O3', thickness: 1.5 }
      ],
      
      // 性能需�?- 超高温极端工�?      substrate_material: '硬质合金(WC-Co)',
      adhesion_strength: 60.0,
      elastic_modulus: 450,
      working_temperature: 1100,
      cutting_speed: 180,
      application_scenario: '高温切削，钢材加工，干式加工，要求超高温稳定性和抗氧化性能'
    }
  }
}

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
  
  // 性能需�?  substrate_material: '硬质合金(WC-Co)',
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

// 加载示例数据 - 显示场景选择对话框
const loadExampleData = async () => {
  try {
    const { value } = await ElMessageBox({
      title: '选择示例场景',
      message: `
        <div style="padding: 10px 0;">
          <p style="margin-bottom: 15px; color: #606266;">请选择一个符合实际应用的示例场景：</p>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <label style="display: flex; align-items: start; padding: 12px; border: 1px solid #dcdfe6; border-radius: 6px; cursor: pointer; transition: all 0.2s;" class="scenario-option" onmouseover="this.style.borderColor='#409eff'; this.style.backgroundColor='#ecf5ff'" onmouseout="this.style.borderColor='#dcdfe6'; this.style.backgroundColor='transparent'">
              <input type="radio" name="scenario" value="highSpeedSteel" style="margin-top: 3px; margin-right: 10px;" checked />
              <div>
                <div style="font-weight: 600; color: #303133; margin-bottom: 4px;">🔧 高速钢材切削</div>
                <div style="font-size: 13px; color: #606266;">多层AlTiN涂层，磁控溅射工艺，适用于钢材高速干式切削</div>
              </div>
            </label>
            <label style="display: flex; align-items: start; padding: 12px; border: 1px solid #dcdfe6; border-radius: 6px; cursor: pointer; transition: all 0.2s;" class="scenario-option" onmouseover="this.style.borderColor='#409eff'; this.style.backgroundColor='#ecf5ff'" onmouseout="this.style.borderColor='#dcdfe6'; this.style.backgroundColor='transparent'">
              <input type="radio" name="scenario" value="precisionAluminum" style="margin-top: 3px; margin-right: 10px;" />
              <div>
                <div style="font-weight: 600; color: #303133; margin-bottom: 4px;">⚙️ 铝合金精密加工</div>
                <div style="font-size: 13px; color: #606266;">单层薄涂层，低温工艺，适用于铝合金精密加工和高光洁度要求</div>
              </div>
            </label>
            <label style="display: flex; align-items: start; padding: 12px; border: 1px solid #dcdfe6; border-radius: 6px; cursor: pointer; transition: all 0.2s;" class="scenario-option" onmouseover="this.style.borderColor='#409eff'; this.style.backgroundColor='#ecf5ff'" onmouseout="this.style.borderColor='#dcdfe6'; this.style.backgroundColor='transparent'">
              <input type="radio" name="scenario" value="highTempWear" style="margin-top: 3px; margin-right: 10px;" />
              <div>
                <div style="font-weight: 600; color: #303133; margin-bottom: 4px;">🔥 高温耐磨应用</div>
                <div style="font-size: 13px; color: #606266;">CVD多层结构，超高温工艺，适用于极端高温工况和耐磨要求</div>
              </div>
            </label>
          </div>
        </div>
      `,
      dangerouslyUseHTMLString: true,
      showCancelButton: true,
      confirmButtonText: '加载',
      cancelButtonText: '取消',
      beforeClose: (action, instance, done) => {
        if (action === 'confirm') {
          const selected = document.querySelector('input[name="scenario"]:checked')
          if (selected) {
            instance.confirmButtonLoading = false
            done()
          } else {
            ElMessage.warning('请选择一个场景')
            instance.confirmButtonLoading = false
          }
        } else {
          done()
        }
      }
    })
    
    // 获取选中的场景
    const selectedScenario = document.querySelector('input[name="scenario"]:checked')?.value
    if (selectedScenario && exampleScenarios[selectedScenario]) {
      const scenario = exampleScenarios[selectedScenario]
      formData.value = { ...scenario.data }
      ElMessage.success(`已加载「${scenario.name}」示例数据`)
    }
  } catch (error) {
    // 用户取消选择
    console.log('用户取消了场景选择')
  }
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
  min-width: 280px;
  max-width: 600px;
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--border-color);
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-secondary);
}

.panel-footer {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  background: white;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
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

/* 涂层成分改为单列布局，避免过�?*/
.composition-grid {
  grid-template-columns: 1fr;
}

/* 工艺参数保持两列，在窄宽度下也会自动换行 */
.param-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

/* 带单位的输入�?*/
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
  padding: 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  background: var(--success-light);
  color: var(--success);
  border: 1px solid var(--success);
  transition: all var(--transition-fast);
}

.composition-sum.warning {
  background: var(--danger-light);
  color: var(--danger);
  border-color: var(--danger);
}

/* Element Plus 表单项样式调�?*/
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

/* 动态配置区�?*/
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

/* 应用场景提示�?*/
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
  font-size: 20px;
  color: var(--primary);
}

.title-text {
  flex: 1;
}

/* Element Plus Collapse样式覆盖 */
:deep(.el-collapse-item__header) {
  height: 52px;
  padding: 0 16px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  margin-bottom: 12px;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-xs);
}

:deep(.el-collapse-item__header:hover) {
  border-color: var(--primary-light);
  background: var(--primary-lighter);
}

:deep(.el-collapse-item__header.is-active) {
  background: var(--primary-lighter);
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-lighter);
}

:deep(.el-collapse-item__wrap) {
  border: none;
}

:deep(.el-collapse-item__content) {
  padding: 20px 16px;
  background: white;
  border: 1px solid var(--border-color);
  border-top: none;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  margin-top: -12px;
  margin-bottom: 12px;
}
</style>
