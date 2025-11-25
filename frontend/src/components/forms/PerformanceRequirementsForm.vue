<template>
  <el-collapse-item name="performance">
    <template #title>
      <div class="collapse-title">
        <el-icon class="title-icon"><SpeedometerOutline /></el-icon>
        <span class="title-text">性能需求</span>
      </div>
    </template>

    <!-- 基体材料 -->
    <el-form-item label="基体材料">
      <el-input 
        v-model="modelValue.substrate_material" 
        placeholder="如：硬质合金(WC-Co)"
        @input="emit('update:modelValue', modelValue)"
      />
    </el-form-item>

    <!-- 性能参数网格 -->
    <div class="param-grid">
      <el-form-item label="结合力">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.adhesion_strength"
            :min="0"
            :max="100"
            :precision="1"
            :controls="false"
            placeholder="0.0"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">N</span>
        </div>
      </el-form-item>

      <el-form-item label="弹性模量">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.elastic_modulus"
            :min="100"
            :max="800"
            :step="10"
            :controls="false"
            placeholder="0"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">GPa</span>
        </div>
      </el-form-item>

      <el-form-item label="工作温度">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.working_temperature"
            :min="200"
            :max="1200"
            :step="50"
            :controls="false"
            placeholder="0"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">℃</span>
        </div>
      </el-form-item>

      <el-form-item label="切削速度">
        <div class="input-with-unit">
          <el-input-number 
            v-model="modelValue.cutting_speed"
            :min="50"
            :max="1000"
            :step="10"
            :controls="false"
            placeholder="0"
            @update:modelValue="emit('update:modelValue', modelValue)"
          />
          <span class="unit">m/min</span>
        </div>
      </el-form-item>
    </div>

    <!-- 应用场景 -->
    <el-form-item label="应用场景">
      <el-input 
        v-model="modelValue.application_scenario"
        type="textarea"
        :rows="3"
        placeholder="描述具体应用场景，如：高温切削、钢材加工等"
        maxlength="200"
        show-word-limit
        @input="emit('update:modelValue', modelValue)"
      />
      <!-- 场景提示词标签 -->
      <div class="scenario-hints">
        <span class="hint-label">快速选择：</span>
        <el-tag
          v-for="hint in scenarioHints"
          :key="hint"
          size="small"
          effect="plain"
          round
          type="info"
          class="scenario-hint"
          @click="addHintToScenario(hint)"
        >
          {{ hint }}
        </el-tag>
      </div>
    </el-form-item>
  </el-collapse-item>
</template>

<script setup>
import { ElIcon } from 'element-plus'
import { SpeedometerOutline } from '@vicons/ionicons5'

// 定义props和emits
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

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

// 添加提示词到应用场景
const addHintToScenario = (hint) => {
  if (!props.modelValue.application_scenario.includes(hint)) {
    props.modelValue.application_scenario += (props.modelValue.application_scenario ? '，' : '') + hint
    emit('update:modelValue', props.modelValue)
  }
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

.input-with-unit .unit {
  position: absolute;
  right: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  pointer-events: none;
  background: transparent;
  min-width: auto;
}

/* 保留原来用于其他地方的unit样式 */
.unit {
  font-size: 13px;
  color: var(--text-secondary);
  flex-shrink: 0;
  /* min-width: 40px; */
}

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
  border-color: #e5e7eb;
  color: #6b7280;
  background-color: #ffffff;
}

.scenario-hint:hover {
  transform: translateY(-1px);
  color: #2d2d2d;
  border-color: #2d2d2d;
  background-color: #f9fafb;
}
</style>
