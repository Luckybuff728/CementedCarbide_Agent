<template>
  <div class="chat-input-container">
    <!-- 快捷参数面板 -->
    <el-collapse-transition>
      <div v-if="showParamsPanel" class="params-panel">
        <el-card>
          <template #header>
            <div class="panel-header">
              <span>⚡ 快捷参数设置</span>
              <el-button text @click="showParamsPanel = false">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </template>
          
          <el-form :model="params" label-width="100px" size="small">
            <el-row :gutter="16">
              <!-- 成分参数 -->
              <el-col :span="12">
                <el-divider content-position="left">成分参数</el-divider>
                <el-form-item label="Al含量(%)">
                  <el-input-number v-model="params.composition.al_content" :min="0" :max="100" :step="0.1" />
                </el-form-item>
                <el-form-item label="Ti含量(%)">
                  <el-input-number v-model="params.composition.ti_content" :min="0" :max="100" :step="0.1" />
                </el-form-item>
                <el-form-item label="N含量(%)">
                  <el-input-number v-model="params.composition.n_content" :min="0" :max="100" :step="0.1" />
                </el-form-item>
              </el-col>
              
              <!-- 工艺参数 -->
              <el-col :span="12">
                <el-divider content-position="left">工艺参数</el-divider>
                <el-form-item label="沉积气压(Pa)">
                  <el-input-number v-model="params.process_params.deposition_pressure" :min="0.1" :max="5" :step="0.1" />
                </el-form-item>
                <el-form-item label="偏压(V)">
                  <el-input-number v-model="params.process_params.bias_voltage" :min="0" :max="200" :step="5" />
                </el-form-item>
                <el-form-item label="沉积温度(℃)">
                  <el-input-number v-model="params.process_params.deposition_temperature" :min="400" :max="800" :step="10" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item>
              <el-button type="primary" size="small" @click="loadExample">加载示例</el-button>
              <el-button size="small" @click="resetParams">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
    </el-collapse-transition>
    
    <!-- 输入框 -->
    <div class="input-wrapper">
      <el-button 
        circle 
        @click="showParamsPanel = !showParamsPanel"
        :type="showParamsPanel ? 'primary' : ''"
        class="params-toggle"
      >
        <el-icon><Setting /></el-icon>
      </el-button>
      
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="描述您的涂层需求，例如：需要硬度32GPa的高速切削刀具涂层..."
        @keydown.enter.exact="handleEnter"
        :disabled="disabled"
        class="chat-input"
      />
      
      <el-button
        type="primary"
        circle
        :disabled="!inputText.trim() || disabled"
        :loading="loading"
        @click="handleSend"
        class="send-button"
      >
        <el-icon><Promotion /></el-icon>
      </el-button>
    </div>
    
    <div class="input-hint">
      按 Enter 发送，Shift + Enter 换行
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Close, Setting, Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

// 输入文本
const inputText = ref('')

// 参数面板显示状态
const showParamsPanel = ref(false)

// 参数数据
const params = ref({
  composition: {
    al_content: 30.0,
    ti_content: 25.0,
    n_content: 45.0,
    x_content: 0.0
  },
  process_params: {
    deposition_pressure: 0.6,
    n2_flow: 210,
    ar_flow: 280,
    kr_flow: 200,
    bias_voltage: 90,
    deposition_temperature: 550
  },
  structure_design: {
    total_thickness: 3.0,
    layer_type: '单层',
    layers: []
  },
  target_hardness: 30.0,
  target_adhesion: 'HF1'
})

// 处理回车发送
const handleEnter = (event) => {
  if (!event.shiftKey && inputText.value.trim()) {
    event.preventDefault()
    handleSend()
  }
}

// 发送消息
const handleSend = () => {
  if (!inputText.value.trim() || props.disabled) return
  
  const message = {
    content: inputText.value.trim(),
    params: { ...params.value },
    timestamp: new Date().toISOString()
  }
  
  emit('send', message)
  inputText.value = ''
}

// 加载示例
const loadExample = () => {
  inputText.value = '需要一款高速干切削刀具涂层，要求硬度>32GPa，抗氧化温度>900℃'
  params.value = {
    composition: {
      al_content: 32.0,
      ti_content: 23.0,
      n_content: 45.0,
      x_content: 0.0
    },
    process_params: {
      deposition_pressure: 0.6,
      n2_flow: 210,
      ar_flow: 280,
      kr_flow: 200,
      bias_voltage: 100,
      deposition_temperature: 520
    },
    structure_design: {
      total_thickness: 3.5,
      layer_type: '多层',
      layers: []
    },
    target_hardness: 32.0,
    target_adhesion: 'HF1'
  }
}

// 重置参数
const resetParams = () => {
  params.value = {
    composition: {
      al_content: 30.0,
      ti_content: 25.0,
      n_content: 45.0,
      x_content: 0.0
    },
    process_params: {
      deposition_pressure: 0.6,
      n2_flow: 210,
      ar_flow: 280,
      kr_flow: 200,
      bias_voltage: 90,
      deposition_temperature: 550
    },
    structure_design: {
      total_thickness: 3.0,
      layer_type: '单层',
      layers: []
    },
    target_hardness: 30.0,
    target_adhesion: 'HF1'
  }
}
</script>

<style scoped>
.chat-input-container {
  border-top: 1px solid #E4E7ED;
  background: white;
  padding: 16px;
}

.params-panel {
  margin-bottom: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #409EFF;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.params-toggle {
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
}

.send-button {
  flex-shrink: 0;
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}

:deep(.el-textarea__inner) {
  box-shadow: none !important;
  border: 1px solid #DCDFE6;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
}

:deep(.el-textarea__inner:focus) {
  border-color: #409EFF;
}
</style>
