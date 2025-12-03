<template>
  <div class="experiment-input-card">
    <!-- 输入表单 -->
    <el-form :model="formData" label-position="top" class="experiment-form">
      <!-- 迭代轮次提示 -->
      <div class="iteration-banner">
        <el-tag type="primary" effect="plain" size="small">第 {{ iteration }} 轮</el-tag>
        <span>请填写实验测试结果</span>
      </div>
      
      <!-- 测试数据输入 - 紧凑网格 -->
      <div class="input-grid">
        <div class="input-item">
          <label>硬度 <span class="req">*</span></label>
          <div class="input-wrap">
            <el-input-number v-model="formData.hardness" :min="0" :max="50" :precision="1" :step="0.1" placeholder="0.0" :controls="false" />
            <span class="unit">GPa</span>
          </div>
        </div>
        <div class="input-item">
          <label>结合力 <span class="req">*</span></label>
          <div class="input-wrap">
            <el-input-number v-model="formData.adhesion_strength" :min="0" :max="100" :precision="1" placeholder="0.0" :controls="false" />
            <span class="unit">N</span>
          </div>
        </div>
        <div class="input-item">
          <label>弹性模量 <span class="req">*</span></label>
          <div class="input-wrap">
            <el-input-number v-model="formData.elastic_modulus" :min="0" :max="1000" :precision="1" placeholder="0.0" :controls="false" />
            <span class="unit">GPa</span>
          </div>
        </div>
        <div class="input-item">
          <label>磨损率</label>
          <div class="input-wrap">
            <el-input-number v-model="formData.wear_rate" :min="0" :max="1" :precision="4" :step="0.0001" placeholder="0.0000" :controls="false" />
            <span class="unit">mm³/Nm</span>
          </div>
        </div>
      </div>
      
      <!-- 备注 -->
      <div class="notes-wrap">
        <label>备注</label>
        <el-input v-model="formData.notes" type="textarea" :rows="2" placeholder="特殊情况或备注（可选）" resize="none" />
      </div>
    </el-form>
    
    <!-- 下一步操作 -->
    <div class="action-section">
      <div class="action-title">下一步操作</div>
      
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
  padding: 16px;
}

/* 迭代提示横幅 */
.iteration-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--text-secondary, #6b7280);
}

/* 输入网格 - 2x2 */
.input-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.input-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
}

.input-item .req {
  color: #ef4444;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrap :deep(.el-input-number) {
  width: 100%;
}

.input-wrap :deep(.el-input__inner) {
  text-align: left;
  padding-right: 50px;
  border-radius: 8px;
}

.input-wrap .unit {
  position: absolute;
  right: 10px;
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  pointer-events: none;
}

/* 备注 */
.notes-wrap {
  margin-bottom: 16px;
}

.notes-wrap label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
  margin-bottom: 4px;
}

.notes-wrap :deep(.el-textarea__inner) {
  border-radius: 8px;
}

/* 下一步操作 */
.action-section {
  padding-top: 16px;
  border-top: 1px solid var(--bg-tertiary, #f3f4f6);
}

.action-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  margin-bottom: 12px;
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
  color: #1f2937;
  white-space: nowrap;
}

.section-desc {
  font-size: 12px;
  color: #6b7280;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px 16px;
  margin-bottom: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.input-label {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  white-space: nowrap;
}

.required {
  color: #ef4444;
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
  padding-right: 45px;
  width: 100%;
  border-radius: 8px;
  border-color: #e5e7eb;
}

.input-with-unit :deep(.el-input__inner:focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.unit {
  position: absolute;
  right: 12px;
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  background: transparent;
}

.notes-section :deep(.el-textarea__inner) {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.notes-section :deep(.el-textarea__inner):focus {
  border-color: #3b82f6;
}

/* Reference Section */
.reference-section {
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.comparison-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
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

.stat-value.current { color: #3b82f6; }
.stat-value.historical { color: #10b981; }
.stat-value.target { color: #f59e0b; }

.stat-divider {
  width: 1px;
  height: 32px;
  background: #e5e7eb;
}

/* Decision Section */
.decision-radio-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  width: 100%;
}

.decision-radio {
  margin-right: 0 !important;
  width: 100%;
  height: auto !important;
  padding: 10px 12px !important;
  box-sizing: border-box;
  border-radius: 8px !important;
  border-color: #e5e7eb !important;
}

.decision-radio.is-checked {
  border-color: #3b82f6 !important;
  background-color: #eff6ff !important;
}

.radio-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.radio-icon {
  font-size: 20px;
  color: #9ca3af;
  flex-shrink: 0;
}

.decision-radio.is-checked .radio-icon {
  color: #3b82f6;
}

.radio-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}

.radio-label {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #374151;
}

.decision-radio.is-checked .radio-label {
  color: #1d4ed8;
}

.radio-sub {
  font-size: 12px;
  color: #6b7280;
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
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
}

.submit-btn {
  min-width: 120px;
  border-radius: 8px;
}

/* Responsive */
@media (max-width: 640px) {
  .experiment-input-card {
    padding: 16px;
  }
  
  .comparison-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    min-width: 0;
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
