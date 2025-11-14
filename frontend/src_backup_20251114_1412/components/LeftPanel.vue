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
            <n-icon :component="PlayOutline" />
          </template>
          加载示例
        </n-button>
	        <n-button 
          size="small" 
          @click="resetForm"
          secondary
        >
          <template #icon>
            <n-icon :component="RefreshOutline" />
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
        style="width: 100%"
      >
        开始分析</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { NButton, NIcon } from 'naive-ui'
import { 
  RefreshOutline,
  PlayOutline
} from '@vicons/ionicons5'
import { useWorkflowStore } from '../stores/workflow'

// 导入表单子组件
import CompositionForm from './forms/CompositionForm.vue'
import ProcessParametersForm from './forms/ProcessParametersForm.vue'
import StructureDesignForm from './forms/StructureDesignForm.vue'
import PerformanceRequirementsForm from './forms/PerformanceRequirementsForm.vue'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['submit'])

// 表单引用
const formRef = ref(null)
const selectedTemplate = ref('custom')

// 折叠面板活动项（默认展开第一个，数组格式支持多个同时展开）
const activeCollapse = ref(['composition'])


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

/* 表单子组件的样式已移至各自的组件文件中 */

/* Element Plus 表单项样式调整*/
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

/* Element Plus Collapse样式覆盖 */
:deep(.el-collapse-item__header) {
  height: 52px;
  padding: 0 16px;
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
