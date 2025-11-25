<template>
  <div class="experiment-input-card">
    <div class="card-header">
      <div class="header-left">
        <div class="icon-wrapper">
          <el-icon :size="24" color="#3b82f6">
            <FlaskOutline />
          </el-icon>
        </div>
        <div class="header-text">
          <h3>实验数据录入</h3>
          <span class="subtitle">请输入第 {{ iteration }} 轮迭代的测试结果</span>
        </div>
      </div>
      <el-tag type="primary" effect="plain" round>第 {{ iteration }} 轮</el-tag>
    </div>
    
    <el-form :model="formData" label-position="top" class="experiment-form">
      <!-- 实验数据输入 -->
      <div class="form-section">
        <div class="section-header">
          <h4 class="section-title">
            <el-icon><DocumentTextOutline /></el-icon>
            测试结果
          </h4>
          <span class="section-desc">请准确填写各项测试数据</span>
        </div>
        
        <div class="form-grid">
          <div class="form-item">
            <label class="input-label">
              硬度 <span class="required">*</span>
            </label>
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.hardness"
                :min="0"
                :max="50"
                :precision="1"
                :step="0.1"
                placeholder="0.0"
                :controls="false"
              />
              <span class="unit">GPa</span>
            </div>
          </div>
          
          <div class="form-item">
            <label class="input-label">
              结合力 <span class="required">*</span>
            </label>
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.adhesion_strength"
                :min="0"
                :max="100"
                :precision="1"
                placeholder="0.0"
                :controls="false"
              />
              <span class="unit">N</span>
            </div>
          </div>
          
          <div class="form-item">
            <label class="input-label">
              弹性模量 <span class="required">*</span>
            </label>
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.elastic_modulus"
                :min="0"
                :max="1000"
                :precision="1"
                :step="1"
                placeholder="0.0"
                :controls="false"
              />
              <span class="unit">GPa</span>
            </div>
          </div>
          
          <div class="form-item">
            <label class="input-label">
              磨损率
            </label>
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.wear_rate"
                :min="0"
                :max="1"
                :precision="3"
                :step="0.001"
                placeholder="0.000"
                :controls="false"
              />
              <span class="unit">mm³/Nm</span>
            </div>
          </div>
        </div>
        
        <div class="notes-section">
          <label class="input-label">备注信息</label>
          <el-input 
            v-model="formData.notes"
            type="textarea"
            :rows="2"
            placeholder="请输入实验过程中的特殊情况或备注（可选）"
            resize="none"
          />
        </div>
      </div>
      
      <!-- 对比参考信息 -->
      <div v-if="historicalBest" class="reference-section">
        <div class="section-header">
          <h4 class="section-title">
            <el-icon><BarChartOutline /></el-icon>
            性能参考
          </h4>
        </div>
        <div class="comparison-row">
          <div class="stat-item">
            <span class="stat-label">当前硬度</span>
            <span class="stat-value current">{{ formData.hardness || '-' }} <small>GPa</small></span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">历史最优</span>
            <span class="stat-value historical">{{ historicalBest.hardness }} <small>GPa</small></span>
          </div>
          <template v-if="targetHardness">
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">目标值</span>
              <span class="stat-value target">{{ targetHardness }} <small>GPa</small></span>
            </div>
          </template>
        </div>
      </div>
    </el-form>
    
    <!-- 迭代决策 -->
    <div class="decision-section">
      <div class="section-header">
        <h4 class="section-title">
          <el-icon><GitBranchOutline /></el-icon>
          下一步操作
        </h4>
      </div>
      
      <div class="decision-options">
        <el-radio-group v-model="formData.continue_iteration" class="decision-radio-group">
          <el-radio :value="true" class="decision-radio" border>
            <div class="radio-inner">
              <el-icon class="radio-icon"><RefreshOutline /></el-icon>
              <div class="radio-text">
                <span class="radio-label">继续优化</span>
                <span class="radio-sub">性能未达标</span>
              </div>
            </div>
          </el-radio>
          <el-radio :value="false" class="decision-radio" border>
            <div class="radio-inner">
              <el-icon class="radio-icon"><CheckmarkCircleOutline /></el-icon>
              <div class="radio-text">
                <span class="radio-label">完成实验</span>
                <span class="radio-sub">性能已达标</span>
              </div>
            </div>
          </el-radio>
        </el-radio-group>
      </div>
    </div>
    
    <div class="actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button 
        type="primary" 
        @click="handleSubmit"
        :disabled="!isFormValid"
        class="submit-btn"
      >
        {{ formData.continue_iteration ? '提交并继续' : '提交并完成' }}
        <el-icon class="el-icon--right">
          <component :is="formData.continue_iteration ? RefreshOutline : CheckmarkCircleOutline" />
        </el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElIcon } from 'element-plus'
import { 
  FlaskOutline, 
  DocumentTextOutline,
  BarChartOutline,
  GitBranchOutline,
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
  elastic_modulus: null,
  adhesion_strength: null,
  wear_rate: null,
  notes: '',
  continue_iteration: null
})

const isFormValid = computed(() => {
  return formData.value.hardness !== null &&
         formData.value.elastic_modulus !== null &&
         formData.value.adhesion_strength !== null &&
         formData.value.continue_iteration !== null
})

const handleSubmit = () => {
  emit('submit', {
    experiment_data: {
      hardness: formData.value.hardness,
      elastic_modulus: formData.value.elastic_modulus,
      adhesion_strength: formData.value.adhesion_strength,
      wear_rate: formData.value.wear_rate,
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
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
  max-width: 100%;
  overflow-x: hidden; /* Prevent overflow */
  box-sizing: border-box;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
  flex-wrap: wrap; /* Allow wrapping */
  gap: 12px;
}

.header-left {
  display: flex;
  gap: 12px;
  min-width: 0; /* Allow text truncation */
  flex: 1;
}

.icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--primary-lighter);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-text {
  min-width: 0; /* Allow text truncation */
}

.header-text h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.form-section, .reference-section, .decision-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.section-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); /* Flexible grid */
  gap: 16px;
  margin-bottom: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0; /* Prevent flex item overflow */
}

.input-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

.required {
  color: var(--danger);
}

.input-with-unit {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.input-with-unit :deep(.el-input-number) {
  width: 100%;
}

.input-with-unit :deep(.el-input__inner) {
  text-align: left;
  padding-right: 45px; /* Space for unit */
  width: 100%;
}

.unit {
  position: absolute;
  right: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  pointer-events: none;
  background: transparent;
}

.notes-section :deep(.el-textarea__inner) {
  background: var(--bg-secondary);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.notes-section :deep(.el-textarea__inner):focus {
  background: white;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-lighter);
}

/* Reference Section */
.reference-section {
  background: linear-gradient(to right, var(--primary-lighter), white);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--primary-light);
  overflow-x: auto; /* Allow scroll if needed */
}

.comparison-row {
  display: flex;
  align-items: center;
  gap: 24px;
  min-width: max-content; /* Ensure content fits */
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.stat-value small {
  font-size: 12px;
  font-weight: 500;
  margin-left: 2px;
}

.stat-value.current { color: var(--primary); }
.stat-value.historical { color: var(--success); }
.stat-value.target { color: var(--warning); }

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--border-color);
}

/* Decision Section */
.decision-radio-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); /* Flexible grid */
  gap: 16px;
  width: 100%;
}

.decision-radio {
  margin-right: 0 !important;
  width: 100%;
  height: auto !important;
  padding: 12px !important;
  box-sizing: border-box;
}

.radio-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.radio-icon {
  font-size: 20px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.decision-radio.is-checked .radio-icon {
  color: var(--primary);
}

.radio-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0; /* Allow text truncation */
}

.radio-label {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.radio-sub {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Actions */
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
  flex-wrap: wrap;
}

.submit-btn {
  min-width: 140px;
}

/* Responsive */
@media (max-width: 640px) {
  .experiment-input-card {
    padding: 16px;
  }
  
  /* Auto-fit handles grid columns now, so we don't need explicit media queries for that */
  
  .comparison-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    min-width: 0; /* Reset min-width */
  }
  
  .stat-divider {
    display: none;
  }
  
  .actions {
    flex-direction: column-reverse;
  }
  
  .actions .el-button {
    width: 100%;
    margin-left: 0 !important;
  }
}
</style>
