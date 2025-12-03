<template>
  <div class="left-panel-content">
    <!-- 顶部：快捷模板 -->
    <div class="panel-header">
      <div class="header-title">参数输入</div>
      <div class="header-actions">
        <el-button 
          text
          circle
          size="small" 
          @click="resetForm"
          title="清空表单"
        >
          <component :is="Icon" :component="CloseCircleOutline" :size="20" />
        </el-button>
      </div>
    </div>

    <!-- 场景快速切换 -->
    <div class="scenario-selector">
      <div class="selector-label">示例场景</div>
      <div class="scenario-grid">
        <div 
          v-for="option in scenarioOptions" 
          :key="option.value"
          class="scenario-card"
          :class="{ active: selectedScenario === option.value }"
          @click="handleScenarioSelect(option.value)"
        >
          <component :is="Icon" :component="option.icon" :size="18" />
          <span>{{ option.label }}</span>
        </div>
      </div>
    </div>

    <!-- 中间：表单内容 -->
    <div class="form-content">
      <el-form
        ref="formRef"
        :model="formData"
        label-position="top"
        size="default"
      >
        <!-- 使用Collapse折叠面板 -->
        <el-collapse v-model="activeCollapse">
          <!-- 使用拆分后的表单子组件 -->
          <CompositionForm v-model="formData" />
          
          <ProcessParametersForm v-model="formData" />
          
          <StructureDesignForm v-model="formData" />
          
          <PerformanceRequirementsForm v-model="formData" />
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
        class="submit-btn"
      >
        开始分析
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'
import { ElMessage, ElMessageBox, ElButton } from 'element-plus'
import { 
  CloseCircleOutline,
  PlayOutline,
  HammerOutline,
  SettingsOutline,
  BuildOutline,
  FlameOutline
} from '@vicons/ionicons5'
import { useWorkflowStore } from '../../stores/workflow'

// 导入表单子组件
import CompositionForm from '../forms/CompositionForm.vue'
import ProcessParametersForm from '../forms/ProcessParametersForm.vue'
import StructureDesignForm from '../forms/StructureDesignForm.vue'
import PerformanceRequirementsForm from '../forms/PerformanceRequirementsForm.vue'

// Icon包装器
const Icon = (props) => {
  return h('span', { 
    class: 'icon-wrapper',
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, h(props.component))
}

const workflowStore = useWorkflowStore()
const emit = defineEmits(['submit'])

// 表单引用
const formRef = ref(null)
const selectedScenario = ref('')

// 折叠面板活动项（默认展开第一个，数组格式支持多个同时展开）
const activeCollapse = ref(['composition'])

const scenarioOptions = [
  { label: '高速钢', value: 'highSpeedSteel', icon: HammerOutline },
  { label: '铝合金', value: 'precisionAluminum', icon: SettingsOutline },
  { label: '钛合金', value: 'titaniumAlloy', icon: BuildOutline },
  { label: '高温耐磨', value: 'highTempWear', icon: FlameOutline }
]

// 示例场景数据
const exampleScenarios = {
  highSpeedSteel: {
    name: '高速钢材切削',
    description: '适用于钢材高速干式切削，要求高硬度和优异抗氧化性',
    data: {
      // 涂层成分 - 高Al含量提升抗氧化性，Al/(Al+Ti)≈0.64
      al_content: 35.0,
      ti_content: 20.0,
      n_content: 45.0,
      other_elements: [],
      
      // 工艺参数 - 磁控溅射，中等温度，Ar/N2比例1.3:1
      process_type: 'magnetron_sputtering',
      deposition_pressure: 0.5,
      deposition_temperature: 450,
      bias_voltage: 100,
      n2_flow: 200,
      other_gases: [{ type: 'Ar', flow: 260 }],
      
      // 结构设计 - 多层结构增强韧性，总厚度3.5μm
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
      // 涂层成分 - 适中Al/Ti比约0.51，避免粘铝
      al_content: 28.0,
      ti_content: 27.0,
      n_content: 45.0,
      other_elements: [],
      
      // 工艺参数 - 低温低偏压精细控制，Ar/N2比例1.7:1
      process_type: 'magnetron_sputtering',
      deposition_pressure: 0.4,
      deposition_temperature: 380,
      bias_voltage: 70,
      n2_flow: 170,
      other_gases: [{ type: 'Ar', flow: 290 }],
      
      // 结构设计 - 单层薄涂层2.0μm，保持锋利度
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
  titaniumAlloy: {
    name: '钛合金切削',
    description: '适用于钛合金加工工况，兼顾耐磨与耐高温',
    data: {
      // 涂层成分 - 针对钛合金的Al/Ti比例，提升耐磨与抗氧化
      al_content: 27.5,
      ti_content: 22.5,
      n_content: 50.0,
      other_elements: [],
      
      // 工艺参数 - 磁控溅射，中等温度，Ar/N2比例约0.8:1
      process_type: 'magnetron_sputtering',
      deposition_pressure: 0.5,
      deposition_temperature: 450,
      bias_voltage: 100,
      n2_flow: 200,
      other_gases: [{ type: 'Ar', flow: 160 }],
      
      // 结构设计 - 单层涂层，厚度约2.5μm
      structure_type: 'single',
      total_thickness: 2.5,
      layers: [],
      
      // 性能需求 - 钛合金切削工况
      substrate_material: '硬质合金(WC-Co)',
      adhesion_strength: 60.0,
      elastic_modulus: 430,
      working_temperature: 800,
      cutting_speed: 180,
      application_scenario: '钛合金切削工况，要求较高耐磨性与热稳定性'
    }
  },
  highTempWear: {
    name: '高温耐磨应用',
    description: '适用于超高温工况，要求极高热稳定性和耐磨性',
    data: {
      // 涂层成分 - 高Al含量抗氧化，Al/(Al+Ti)≈0.69（最优比例）
      al_content: 38.0,
      ti_content: 17.0,
      n_content: 45.0,
      other_elements: [],
      
      // 工艺参数 - CVD工艺，高温沉积，适中压力
      process_type: 'cvd',
      deposition_pressure: 2.5,
      deposition_temperature: 680,
      bias_voltage: 0,
      n2_flow: 140,
      other_gases: [
        { type: 'H2', flow: 180 },
        { type: 'AlCl3', flow: 70 }
      ],
      
      // 结构设计 - 三层梯度结构，总厚度5.0μm
      structure_type: 'multi',
      total_thickness: 5.0,
      layers: [
        { type: 'TiN(过渡层)', thickness: 0.5 },
        { type: 'AlTiN', thickness: 3.0 },
        { type: 'Al2O3', thickness: 1.5 }
      ],
      
      // 性能需求 - 超高温极端工况
      substrate_material: '硬质合金(WC-Co)',
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
  
  // 性能需求?  substrate_material: '硬质合金(WC-Co)',
  adhesion_strength: 50.0,
  elastic_modulus: 400,
  working_temperature: 800,
  cutting_speed: 200,
  application_scenario: ''
})

// 计算成分总和
const compositionSum = computed(() => {
  let sum = (formData.value.al_content || 0) + (formData.value.ti_content || 0) + (formData.value.n_content || 0)
  formData.value.other_elements.forEach(elem => {
    sum += elem.content || 0
  })
  return sum
})

// 场景切换处理
const handleScenarioSelect = (value) => {
  selectedScenario.value = value
  if (value && exampleScenarios[value]) {
    const scenario = exampleScenarios[value]
    formData.value = { ...scenario.data }
    ElMessage.success(`已切换到「${scenario.name}」场景`)
  }
}

// 重置表单为空值
const resetForm = () => {
  // 清空所有参数，而不是重置到默认值
  formData.value = {
    // 涂层成分 - 清空
    al_content: null,
    ti_content: null,
    n_content: null,
    other_elements: [],
    
    // 工艺参数 - 清空
    process_type: 'magnetron_sputtering',
    deposition_pressure: null,
    deposition_temperature: null,
    bias_voltage: null,
    n2_flow: null,
    other_gases: [],
    
    // 结构设计 - 清空
    structure_type: 'single',
    total_thickness: null,
    layers: [],
    
    // 性能需求 - 清空
    substrate_material: '',
    adhesion_strength: null,
    elastic_modulus: null,
    working_temperature: null,
    cutting_speed: null,
    application_scenario: ''
  }
  selectedScenario.value = ''
  ElMessage.success('已清空表单')
}


// 提交表单
const handleSubmit = () => {
  // 验证必填参数
  const al = formData.value.al_content
  const ti = formData.value.ti_content
  const n = formData.value.n_content
  const temp = formData.value.deposition_temperature
  
  if (!al && !ti && !n) {
    ElMessage.warning('请先输入涂层成分配比')
    return
  }
  
  if (!temp) {
    ElMessage.warning('请先输入沉积温度')
    return
  }
  
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
.left-panel-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  background: var(--bg-primary);
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--bg-tertiary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-primary);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 滚动条样式已在全局 style.css 定义 */
.form-content::-webkit-scrollbar {
  width: 6px;
}

.panel-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--bg-tertiary);
  background: var(--bg-primary);
}

.submit-btn {
  width: 100%;
  background: var(--primary);
  border-color: var(--primary);
  border-radius: 8px;
  font-weight: 600;
  height: 40px;
  transition: all 0.2s;
}

.submit-btn:hover {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
  box-shadow: 0 2px 6px rgba(26, 115, 232, 0.2);
}

.submit-btn:active {
  background: var(--primary-dark);
  border-color: var(--primary-dark);
}

/* 场景选择器 */
.scenario-selector {
  padding: 16px 20px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--bg-tertiary);
}

.selector-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 10px;
}

.scenario-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.scenario-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--bg-tertiary);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-card:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.scenario-card.active {
  background: var(--primary-lighter);
  border-color: var(--primary-lighter);
  color: var(--primary);
  font-weight: 500;
}

/* Element Plus 表单样式覆盖 */
:deep(.el-form-item__label) {
  font-size: 13px;
  color: var(--text-secondary);
  padding-bottom: 6px;
}

:deep(.el-input__inner),
:deep(.el-input-number__inner) {
  border-radius: 8px;
  border-color: var(--border-color);
}

:deep(.el-input__inner:focus),
:deep(.el-input-number__inner:focus) {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
}

/* Element Plus Collapse样式覆盖 */
:deep(.el-collapse) {
  border: none;
}

:deep(.el-collapse-item__header) {
  height: 44px;
  padding: 0 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-weight: 500;
}

:deep(.el-collapse-item__header.is-active) {
  background: var(--bg-secondary);
  border-radius: 8px 8px 0 0;
  border-bottom-color: transparent;
}

:deep(.el-collapse-item__wrap) {
  border: 1px solid var(--border-color);
  border-top: none;
  border-radius: 0 0 8px 8px;
  margin-top: -8px;
  margin-bottom: 8px;
}

:deep(.el-collapse-item__content) {
  padding: 16px;
  background: var(--bg-primary);
}
</style>
