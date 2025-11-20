<template>
  <el-collapse-item name="composition">
    <template #title>
      <div class="collapse-title">
        <el-icon class="title-icon"><ConstructOutline /></el-icon>
        <span class="title-text">涂层成分</span>
        <el-tag v-if="compositionSum > 0" size="small" type="info">
          {{ compositionSum.toFixed(1) }}%
        </el-tag>
      </div>
    </template>

    <div class="composition-grid">
      <!-- Al含量 -->
      <el-form-item label="Al含量">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.al_content"
            :min="0" 
            :max="100" 
            :precision="1"
            :step="0.5"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">at.%</span>
        </div>
      </el-form-item>

      <!-- Ti含量 -->
      <el-form-item label="Ti含量">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.ti_content"
            :min="0" 
            :max="100" 
            :precision="1"
            :step="0.5"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">at.%</span>
        </div>
      </el-form-item>

      <!-- N含量 -->
      <el-form-item label="N含量">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.n_content"
            :min="0" 
            :max="100" 
            :precision="1"
            :step="0.5"
            @update:modelValue="emit('update:modelValue', modelValue)"
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
      <div v-for="(element, index) in modelValue.other_elements" :key="index" class="element-row">
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
          circle 
          @click="removeElement(index)"
        >
          <el-icon><TrashOutline /></el-icon>
        </el-button>
      </div>
      <el-button 
        type="primary" 
        size="small" 
        @click="addElement"
        style="border-style: dashed"
      >
        <el-icon class="el-icon--left"><AddOutline /></el-icon>
        添加元素
      </el-button>
    </div>
  </el-collapse-item>
</template>

<script setup>
import { computed } from 'vue'
import { ElButton, ElIcon } from 'element-plus'
import { ConstructOutline, AddOutline, TrashOutline } from '@vicons/ionicons5'

// 定义props和emits
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

// 计算成分总和
const compositionSum = computed(() => {
  let sum = props.modelValue.al_content + props.modelValue.ti_content + props.modelValue.n_content
  props.modelValue.other_elements.forEach(elem => {
    sum += elem.content || 0
  })
  return sum
})

// 添加元素
const addElement = () => {
  props.modelValue.other_elements.push({ name: '', content: 0 })
  emit('update:modelValue', props.modelValue)
}

// 删除元素
const removeElement = (index) => {
  props.modelValue.other_elements.splice(index, 1)
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

.composition-grid {
  display: grid;
  grid-template-columns: 1fr;
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

.other-elements {
  margin-top: 16px;
}

.sub-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 8px;
}

.element-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
