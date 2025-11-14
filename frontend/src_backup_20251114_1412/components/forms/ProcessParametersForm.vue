<template>
  <el-collapse-item name="process">
    <template #title>
      <div class="collapse-title">
        <n-icon class="title-icon" :component="SettingsOutline" />
        <span class="title-text">工艺参数</span>
      </div>
    </template>

    <!-- 工艺类型选择 -->
    <el-form-item label="工艺选择">
      <el-select 
        v-model="modelValue.process_type" 
        style="width: 100%" 
        placeholder="请选择工艺类型"
        @change="emit('update:modelValue', modelValue)"
      >
        <el-option label="磁控溅射" value="magnetron_sputtering" />
        <el-option label="CVD" value="cvd" />
      </el-select>
    </el-form-item>

    <!-- 主要工艺参数 -->
    <div class="param-grid">
      <el-form-item label="沉积气压">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.deposition_pressure"
            :min="0" 
            :max="10" 
            :precision="1"
            :step="0.1"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">Pa</span>
        </div>
      </el-form-item>

      <el-form-item label="沉积温度">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.deposition_temperature"
            :min="200" 
            :max="800" 
            :step="10"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">℃</span>
        </div>
      </el-form-item>

      <el-form-item label="偏压">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.bias_voltage"
            :min="0" 
            :max="500" 
            :step="5"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">V</span>
        </div>
      </el-form-item>

      <el-form-item label="N₂流量">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.n2_flow"
            :min="0" 
            :max="500" 
            :step="5"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">sccm</span>
        </div>
      </el-form-item>
    </div>

    <!-- 其他气体动态添加 -->
    <div class="gas-section">
      <label class="sub-label">其他气体</label>
      <div v-for="(gas, index) in modelValue.other_gases" :key="index" class="gas-row">
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
          circle 
          @click="removeGas(index)"
        >
          <n-icon :component="TrashOutline" />
        </el-button>
      </div>
      <n-button 
        type="primary" 
        size="small" 
        @click="addGas"
        dashed
      >
        <template #icon>
          <n-icon :component="AddOutline" />
        </template>
        添加气体
      </n-button>
    </div>
  </el-collapse-item>
</template>

<script setup>
import { NButton, NIcon } from 'naive-ui'
import { SettingsOutline, AddOutline, TrashOutline } from '@vicons/ionicons5'

// 定义props和emits
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

// 添加气体
const addGas = () => {
  props.modelValue.other_gases.push({ type: '', flow: 0 })
  emit('update:modelValue', props.modelValue)
}

// 删除气体
const removeGas = (index) => {
  props.modelValue.other_gases.splice(index, 1)
  emit('update:modelValue', props.modelValue)
}
</script>

<style scoped>
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

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

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

.gas-section {
  margin-top: 16px;
}

.sub-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 8px;
}

.gas-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
