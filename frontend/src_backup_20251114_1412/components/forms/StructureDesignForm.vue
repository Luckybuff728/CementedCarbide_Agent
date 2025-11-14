<template>
  <el-collapse-item name="structure">
    <template #title>
      <div class="collapse-title">
        <n-icon class="title-icon" :component="BuildOutline" />
        <span class="title-text">结构设计</span>
        <el-tag v-if="modelValue.structure_type" size="small" type="info">
          {{ modelValue.structure_type === 'multi' ? '多层' : '单层' }}
        </el-tag>
      </div>
    </template>

    <!-- 结构类型选择 -->
    <el-form-item label="结构类型">
      <el-select 
        v-model="modelValue.structure_type" 
        @change="onStructureChange" 
        style="width: 100%" 
        placeholder="请选择结构类型"
      >
        <el-option label="单层" value="single" />
        <el-option label="多层" value="multi" />
      </el-select>
    </el-form-item>

    <!-- 多层结构设计 -->
    <div v-if="modelValue.structure_type === 'multi'" class="multi-layer-design">
      <label class="sub-label">层结构设计</label>
      <div v-for="(layer, index) in modelValue.layers" :key="index" class="layer-row">
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
          circle 
          @click="removeLayer(index)"
        >
          <n-icon :component="TrashOutline" />
        </el-button>
      </div>
      <n-button 
        type="primary" 
        size="small" 
        @click="addLayer"
        dashed
      >
        <template #icon>
          <n-icon :component="AddOutline" />
        </template>
        添加层
      </n-button>
    </div>

    <!-- 单层厚度 -->
    <el-form-item v-else label="总厚度">
      <div class="input-with-unit">
        <el-input-number 
          v-model="modelValue.total_thickness"
          :min="0.1"
          :max="20"
          :precision="1"
          :step="0.1"
          @update:modelValue="emit('update:modelValue', modelValue)"
        />
        <span class="unit">μm</span>
      </div>
    </el-form-item>
  </el-collapse-item>
</template>

<script setup>
import { NButton, NIcon } from 'naive-ui'
import { BuildOutline, AddOutline, TrashOutline } from '@vicons/ionicons5'

// 定义props和emits
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

// 添加层
const addLayer = () => {
  props.modelValue.layers.push({ type: '', thickness: 1.0 })
  emit('update:modelValue', props.modelValue)
}

// 删除层
const removeLayer = (index) => {
  props.modelValue.layers.splice(index, 1)
  emit('update:modelValue', props.modelValue)
}

// 结构类型变化处理
const onStructureChange = (value) => {
  if (value === 'multi' && props.modelValue.layers.length === 0) {
    addLayer()
  }
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

.layer-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
