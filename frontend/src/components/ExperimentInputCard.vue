<template>
  <div class="experiment-input-card">
    <div class="card-header">
      <div class="header-left">
        <el-icon :size="24" color="#3b82f6">
          <FlaskOutline />
        </el-icon>
        <h3>实验数据录入</h3>
      </div>
      <el-tag type="primary" size="large">第 {{ iteration }} 轮迭代</el-tag>
    </div>
    
    <el-form :model="formData" label-width="140px" class="experiment-form">
      <!-- 实验数据输入 -->
      <div class="form-section">
        <h4 class="section-title">
          <el-icon>
            <DocumentTextOutline />
          </el-icon>
          实验测试结果
        </h4>
        
        <el-form-item label="硬度" required>
          <div class="input-with-unit">
            <el-input-number 
              v-model="formData.hardness"
              :min="0"
              :max="50"
              :precision="1"
              :step="0.1"
              placeholder="请输入实测硬度"
              style="width: 200px"
            />
            <span class="unit">GPa</span>
          </div>
        </el-form-item>
        
        <el-form-item label="结合力" required>
          <div class="input-with-unit">
            <el-input-number 
              v-model="formData.adhesion_strength"
              :min="0"
              :max="100"
              :precision="1"
              placeholder="请输入结合力"
              style="width: 200px"
            />
            <span class="unit">N</span>
          </div>
        </el-form-item>
        
        <el-form-item label="抗氧化温度" required>
          <div class="input-with-unit">
            <el-input-number 
              v-model="formData.oxidation_temperature"
              :min="400"
              :max="1200"
              :step="10"
              placeholder="请输入抗氧化温度"
              style="width: 200px"
            />
            <span class="unit">℃</span>
          </div>
        </el-form-item>
        
        <el-form-item label="磨损率">
          <div class="input-with-unit">
            <el-input-number 
              v-model="formData.wear_rate"
              :min="0"
              :max="1"
              :precision="3"
              :step="0.001"
              placeholder="请输入磨损率"
              style="width: 200px"
            />
            <span class="unit">mm³/Nm</span>
          </div>
        </el-form-item>
        
        <el-form-item label="表面粗糙度">
          <div class="input-with-unit">
            <el-input-number 
              v-model="formData.surface_roughness"
              :min="0"
              :max="10"
              :precision="2"
              :step="0.01"
              placeholder="请输入表面粗糙度"
              style="width: 200px"
            />
            <span class="unit">μm</span>
          </div>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input 
            v-model="formData.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入实验备注（可选）"
            style="width: 400px"
          />
        </el-form-item>
      </div>
      
      <!-- 对比参考信息 -->
      <div v-if="historicalBest" class="reference-section">
        <h4 class="section-title">
          <el-icon>
            <BarChartOutline />
          </el-icon>
          性能对比参考
        </h4>
        <div class="comparison-grid">
          <div class="comparison-item">
            <span class="label">当前实验硬度</span>
            <span class="value current">{{ formData.hardness || '-' }} GPa</span>
          </div>
          <div class="comparison-item">
            <span class="label">历史最优硬度</span>
            <span class="value historical">{{ historicalBest.hardness }} GPa</span>
          </div>
          <div v-if="targetHardness" class="comparison-item">
            <span class="label">目标硬度</span>
            <span class="value target">{{ targetHardness }} GPa</span>
          </div>
        </div>
      </div>
    </el-form>
    
    <!-- 迭代决策 -->
    <div class="decision-section">
      <h4 class="section-title">
        <el-icon>
          <GitBranchOutline />
        </el-icon>
        下一步操作
      </h4>
      
      <div class="decision-hint">
        <el-icon>
          <InformationCircleOutline />
        </el-icon>
        <span>请根据实验结果决定是否继续优化</span>
      </div>
      
      <div class="decision-options">
        <el-radio-group v-model="formData.continue_iteration" class="decision-radio">
          <el-radio :value="true" border size="large">
            <div class="radio-content">
              <div class="radio-header">
                <el-icon class="radio-icon">
                  <RefreshOutline />
                </el-icon>
                <span class="radio-title">继续迭代优化</span>
              </div>
              <div class="radio-desc">性能未达标或希望进一步优化</div>
            </div>
          </el-radio>
          <el-radio :value="false" border size="large">
            <div class="radio-content">
              <div class="radio-header">
                <el-icon class="radio-icon">
                  <CheckmarkCircleOutline />
                </el-icon>
                <span class="radio-title">完成优化</span>
              </div>
              <div class="radio-desc">性能满足要求，结束优化流程</div>
            </div>
          </el-radio>
        </el-radio-group>
      </div>
    </div>
    
    <div class="actions">
      <el-button size="large" @click="handleCancel">取消</el-button>
      <el-button 
        type="primary" 
        size="large"
        @click="handleSubmit"
        :disabled="!isFormValid"
      >
        <el-icon>
          <component :is="formData.continue_iteration ? RefreshOutline : CheckmarkCircleOutline" />
        </el-icon>
        {{ formData.continue_iteration ? '提交数据并继续优化' : '提交数据并完成' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NIcon } from 'naive-ui'
import { 
  FlaskOutline, 
  DocumentTextOutline,
  BarChartOutline,
  GitBranchOutline,
  InformationCircleOutline,
  RefreshOutline,
  CheckmarkCircleOutline
} from '@vicons/ionicons5'

const props = defineProps({
  iteration: {
    type: Number,
    default: 1
  },
  historicalBest: {
    type: Object,
    default: null
  },
  targetHardness: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const formData = ref({
  hardness: null,
  adhesion_strength: null,
  oxidation_temperature: null,
  wear_rate: null,
  surface_roughness: null,
  notes: '',
  continue_iteration: null
})

const isFormValid = computed(() => {
  return formData.value.hardness !== null &&
         formData.value.adhesion_strength !== null &&
         formData.value.oxidation_temperature !== null &&
         formData.value.continue_iteration !== null
})

const handleSubmit = () => {
  emit('submit', {
    experiment_data: {
      hardness: formData.value.hardness,
      adhesion_strength: formData.value.adhesion_strength,
      oxidation_temperature: formData.value.oxidation_temperature,
      wear_rate: formData.value.wear_rate,
      surface_roughness: formData.value.surface_roughness,
      notes: formData.value.notes
    },
    continue_iteration: formData.value.continue_iteration
  })
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.experiment-input-card {
  background: white;
  border-radius: var(--radius-xl);
  padding: 28px;
  box-shadow: var(--shadow-lg);
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 2px solid var(--primary-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.experiment-form {
  margin-top: 0;
}

.form-section,
.reference-section,
.decision-section {
  margin-bottom: 24px;
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.section-title .el-icon {
  font-size: 20px;
  color: var(--primary);
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unit {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 80px;
}

.reference-section {
  background: linear-gradient(135deg, var(--primary-lighter) 0%, var(--primary-light) 100%);
  border: 1px solid var(--primary-light);
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.comparison-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-fast);
}

.comparison-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.comparison-item .label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.comparison-item .value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}

.value.current {
  color: var(--primary);
}

.value.historical {
  color: var(--success);
}

.value.target {
  color: var(--warning);
}

.decision-section {
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, var(--warning-light) 0%, #fef3c7 100%);
  border-radius: var(--radius-lg);
  border: 2px solid var(--warning);
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.decision-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  font-size: 14px;
  color: var(--text-secondary);
  width: 100%;
  box-sizing: border-box;
}

.decision-hint .el-icon {
  font-size: 18px;
  color: var(--primary);
  flex-shrink: 0;
}

.decision-options {
  margin-bottom: 0;
  width: 100%;
}

.decision-radio {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  margin: 0;
}

.decision-radio :deep(.el-radio) {
  margin-right: 0;
  width: 100%;
}

.decision-radio :deep(.el-radio.is-bordered) {
  padding: 20px 24px;
  height: auto;
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-dark);
  background: white;
  transition: all var(--transition-fast);
  display: flex;
  align-items: flex-start;
  width: 100%;
  box-sizing: border-box;
}

.decision-radio :deep(.el-radio.is-bordered:hover) {
  border-color: var(--primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.decision-radio :deep(.el-radio.is-bordered.is-checked) {
  border-color: var(--primary);
  border-width: 3px;
  background: var(--primary-lighter);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.decision-radio :deep(.el-radio__input) {
  display: none;
}

.radio-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.radio-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.radio-icon {
  font-size: 24px;
  color: var(--primary);
  flex-shrink: 0;
}

.radio-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.radio-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-left: 36px;
  margin-top: 4px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  margin-top: 8px;
  border-top: 2px solid var(--border-color);
}

.actions :deep(.el-button) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  font-weight: 600;
}

.form-section :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.form-section :deep(.el-input-number) {
  width: 240px;
}

.form-section :deep(.el-textarea__inner) {
  border-radius: var(--radius-md);
}
</style>
