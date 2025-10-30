<template>
  <el-card class="input-form-card">
    <template #header>
      <div class="card-header">
        <span>📝 涂层参数输入</span>
      </div>
    </template>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
      label-position="left"
    >
      <!-- 涂层成分 -->
      <el-divider content-position="left">
        <el-icon><Operation /></el-icon>
        1️⃣ 涂层成分 (wt.%)
      </el-divider>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-form-item label="Al含量" prop="composition.al_content">
            <el-input-number
              v-model="formData.composition.al_content"
              :min="0"
              :max="100"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="Ti含量" prop="composition.ti_content">
            <el-input-number
              v-model="formData.composition.ti_content"
              :min="0"
              :max="100"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="N含量" prop="composition.n_content">
            <el-input-number
              v-model="formData.composition.n_content"
              :min="0"
              :max="100"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="其他元素">
            <el-input-number
              v-model="formData.composition.x_content"
              :min="0"
              :max="20"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-alert
        :title="`成分总和: ${compositionSum.toFixed(1)}%`"
        :type="compositionSum > 100 ? 'error' : 'success'"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- 工艺参数 -->
      <el-divider content-position="left">
        <el-icon><Setting /></el-icon>
        2️⃣ 工艺参数
      </el-divider>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="沉积气压(Pa)" prop="process_params.deposition_pressure">
            <el-input-number
              v-model="formData.process_params.deposition_pressure"
              :min="0.1"
              :max="5"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="偏压(V)" prop="process_params.bias_voltage">
            <el-input-number
              v-model="formData.process_params.bias_voltage"
              :min="0"
              :max="200"
              :step="5"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="沉积温度(℃)" prop="process_params.deposition_temperature">
            <el-input-number
              v-model="formData.process_params.deposition_temperature"
              :min="400"
              :max="800"
              :step="10"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="N₂流量(sccm)" prop="process_params.n2_flow">
            <el-input-number
              v-model="formData.process_params.n2_flow"
              :min="0"
              :max="500"
              :step="10"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Ar流量(sccm)" prop="process_params.ar_flow">
            <el-input-number
              v-model="formData.process_params.ar_flow"
              :min="0"
              :max="500"
              :step="10"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Kr流量(sccm)" prop="process_params.kr_flow">
            <el-input-number
              v-model="formData.process_params.kr_flow"
              :min="0"
              :max="500"
              :step="10"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 结构设计 -->
      <el-divider content-position="left">
        <el-icon><Grid /></el-icon>
        3️⃣ 结构设计
      </el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="总厚度(μm)" prop="structure_design.total_thickness">
            <el-input-number
              v-model="formData.structure_design.total_thickness"
              :min="0.1"
              :max="20"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结构类型" prop="structure_design.layer_type">
            <el-select v-model="formData.structure_design.layer_type" style="width: 100%">
              <el-option label="单层" value="单层" />
              <el-option label="多层" value="多层" />
              <el-option label="梯度" value="梯度" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 性能要求 -->
      <el-divider content-position="left">
        <el-icon><TrendCharts /></el-icon>
        4️⃣ 性能要求
      </el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="硬度要求(GPa)">
            <el-input-number
              v-model="formData.target_hardness"
              :min="20"
              :max="50"
              :step="0.5"
              :precision="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结合力要求">
            <el-select v-model="formData.target_adhesion" style="width: 100%">
              <el-option label="HF1 (优)" value="HF1" />
              <el-option label="HF2 (良)" value="HF2" />
              <el-option label="HF3 (中)" value="HF3" />
              <el-option label="HF4 (一般)" value="HF4" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="应用场景描述">
        <el-input
          v-model="formData.application_scenario"
          type="textarea"
          :rows="3"
          placeholder="请描述涂层的应用场景和具体性能需求..."
        />
      </el-form-item>

      <!-- 提交按钮 -->
      <el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="submitForm"
          style="width: 200px"
        >
          <el-icon><Promotion /></el-icon>
          开始优化分析
        </el-button>
        <el-button size="large" @click="resetForm">重置</el-button>
        <el-button size="large" @click="loadExample">加载示例</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation, Setting, Grid, TrendCharts, Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit'])

// 表单引用
const formRef = ref(null)

// 表单数据
const formData = ref({
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
  target_adhesion: 'HF1',
  application_scenario: '高速切削刀具涂层，需要高硬度和良好的抗氧化性'
})

// 验证规则
const rules = {
  'composition.al_content': [
    { required: true, message: '请输入Al含量', trigger: 'blur' }
  ],
  'composition.ti_content': [
    { required: true, message: '请输入Ti含量', trigger: 'blur' }
  ],
  'composition.n_content': [
    { required: true, message: '请输入N含量', trigger: 'blur' }
  ]
}

// 计算成分总和
const compositionSum = computed(() => {
  const { al_content, ti_content, n_content, x_content } = formData.value.composition
  return al_content + ti_content + n_content + x_content
})

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    // 检查成分总和
    if (compositionSum.value > 100.1) {
      ElMessage.error('成分总和不能超过100%')
      return
    }

    // 构建目标需求字符串
    const targetRequirements = `应用场景: ${formData.value.application_scenario}, 硬度要求: ${formData.value.target_hardness}GPa, 结合力要求: ${formData.value.target_adhesion}`

    // 提交数据
    emit('submit', {
      ...formData.value,
      target_requirements: targetRequirements
    })

    ElMessage.success('已提交，开始分析...')
  } catch (error) {
    console.error('表单验证失败:', error)
    ElMessage.error('请检查输入参数')
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
}

// 加载示例数据
const loadExample = () => {
  formData.value = {
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
    target_adhesion: 'HF1',
    application_scenario: '高速干切削刀具，要求硬度>32GPa，抗氧化温度>900℃'
  }
  ElMessage.info('已加载示例数据')
}
</script>

<style scoped>
.input-form-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-divider__text) {
  font-size: 16px;
  font-weight: 600;
  color: #4CAF50;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>
