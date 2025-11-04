<template>
  <div class="coating-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-position="top"
      size="default"
    >
      <!-- 1. 涂层成分 -->
      <div class="form-section">
        <h4 class="section-title">
          <el-icon class="title-icon"><Operation /></el-icon>
          涂层成分
        </h4>
        
        <!-- Al、Ti、N 核心成分 -->
        <div class="composition-grid">
          <el-form-item label="Al含量" prop="al_content">
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.al_content"
                :min="0" 
                :max="100" 
                :precision="1"
                :step="0.5"
                controls-position="right"
                class="composition-input"
              />
              <span class="unit">at.%</span>
            </div>
          </el-form-item>

          <el-form-item label="Ti含量" prop="ti_content">
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.ti_content"
                :min="0" 
                :max="100" 
                :precision="1"
                :step="0.5"
                controls-position="right"
                class="composition-input"
              />
              <span class="unit">at.%</span>
            </div>
          </el-form-item>

          <el-form-item label="N含量" prop="n_content">
            <div class="input-with-unit">
              <el-input-number 
                v-model="formData.n_content"
                :min="0" 
                :max="100" 
                :precision="1"
                :step="0.5"
                controls-position="right"
                class="composition-input"
              />
              <span class="unit">at.%</span>
            </div>
          </el-form-item>
        </div>

        <!-- 其他元素 -->
        <div class="other-elements">
          <label class="sub-label">其他元素</label>
          <div v-for="(element, index) in formData.other_elements" :key="index" class="element-row">
            <el-input 
              v-model="element.name" 
              placeholder="元素名"
              style="width: 100px;"
            />
            <el-input-number 
              v-model="element.content"
              :min="0" 
              :max="50" 
              :precision="1"
              :step="0.1"
              controls-position="right"
              style="width: 100px;"
            />
            <span class="unit">at.%</span>
            <el-button 
              type="danger" 
              size="small" 
              :icon="Delete" 
              circle 
              @click="removeElement(index)"
            />
          </div>
          <el-button 
            type="primary" 
            size="small" 
            :icon="Plus" 
            @click="addElement"
            plain
          >
            添加元素
          </el-button>
        </div>

        <!-- 成份总和显示 -->
        <div class="composition-sum" :class="{ 'warning': compositionSum > 100 }">
          成分总和: {{ compositionSum.toFixed(1) }}%
        </div>
      </div>

      <!-- 2. 工艺参数 -->
      <div class="form-section">
        <h4 class="section-title">
          <el-icon class="title-icon"><Setting /></el-icon>
          工艺参数
        </h4>
        
        <!-- 工艺选择 -->
        <el-form-item label="工艺选择" prop="process_type" class="process-select">
          <el-select v-model="formData.process_type" style="width: 100%">
            <el-option label="磁控溅射" value="magnetron_sputtering" />
            <el-option label="CVD" value="cvd" />
          </el-select>
        </el-form-item>

        <!-- 工艺参数网格 -->
        <div class="process-grid">
          <el-form-item label="沉积气压" prop="deposition_pressure">
            <el-input-number 
              v-model="formData.deposition_pressure"
              :min="0" 
              :max="10" 
              :precision="1"
              :step="0.1"
              controls-position="right"
            />
            <span class="unit">Pa</span>
          </el-form-item>

          <el-form-item label="沉积温度" prop="deposition_temperature">
            <el-input-number 
              v-model="formData.deposition_temperature"
              :min="200" 
              :max="800" 
              :step="10"
              controls-position="right"
            />
            <span class="unit">℃</span>
          </el-form-item>

          <el-form-item label="偏压" prop="bias_voltage">
            <el-input-number 
              v-model="formData.bias_voltage"
              :min="0" 
              :max="500" 
              :step="5"
              controls-position="right"
            />
            <span class="unit">V</span>
          </el-form-item>

          <el-form-item label="N₂流量" prop="n2_flow">
            <el-input-number 
              v-model="formData.n2_flow"
              :min="0" 
              :max="500" 
              :step="5"
              controls-position="right"
            />
            <span class="unit">sccm</span>
          </el-form-item>
        </div>

        <!-- 其他气体 -->
        <div class="gas-section">
          <label class="sub-label">其他气体</label>
          <div v-for="(gas, index) in formData.other_gases" :key="index" class="gas-row">
            <el-input 
              v-model="gas.type" 
              placeholder="气体种类"
              style="width: 100px;"
            />
            <el-input-number 
              v-model="gas.flow"
              :min="0"
              :max="1000"
              :step="5"
              controls-position="right"
              style="width: 100px;"
            />
            <span class="unit">sccm</span>
            <el-button 
              type="danger" 
              size="small" 
              :icon="Delete" 
              circle 
              @click="removeGas(index)"
            />
          </div>
          <el-button 
            type="primary" 
            size="small" 
            :icon="Plus" 
            @click="addGas"
            plain
          >
            添加气体
          </el-button>
        </div>
      </div>

      <!-- 3. 结构设计 -->
      <div class="form-section">
        <h4 class="section-title">
          <el-icon class="title-icon"><Grid /></el-icon>
          结构设计
        </h4>
        
        <el-form-item label="结构类型" prop="structure_type">
          <el-select v-model="formData.structure_type" @change="onStructureChange">
            <el-option label="单层" value="single" />
            <el-option label="多层" value="multi" />
          </el-select>
        </el-form-item>

        <!-- 多层设计 -->
        <div v-if="formData.structure_type === 'multi'" class="multi-layer-design">
          <label class="sub-label">层结构设计</label>
          <div v-for="(layer, index) in formData.layers" :key="index" class="layer-row">
            <el-input 
              v-model="layer.type" 
              placeholder="层种类"
              style="width: 120px;"
            />
            <el-input-number 
              v-model="layer.thickness"
              :min="0"
              :max="10"
              :precision="2"
              :step="0.1"
              controls-position="right"
              style="width: 100px;"
            />
            <span class="unit">μm</span>
            <el-button 
              type="danger" 
              size="small" 
              :icon="Delete" 
              circle 
              @click="removeLayer(index)"
            />
          </div>
          <el-button 
            type="primary" 
            size="small" 
            :icon="Plus" 
            @click="addLayer"
            plain
          >
            添加层
          </el-button>
        </div>

        <!-- 单层厚度 -->
        <el-form-item v-else label="总厚度" prop="total_thickness">
          <el-input-number 
            v-model="formData.total_thickness"
            :min="0.1"
            :max="20"
            :precision="1"
            :step="0.1"
            controls-position="right"
          />
          <span class="unit">μm</span>
        </el-form-item>
      </div>

      <!-- 4. 性能需求 -->
      <div class="form-section">
        <h4 class="section-title">
          <el-icon class="title-icon"><TrendCharts /></el-icon>
          性能需求
        </h4>
        
        <!-- 基体选择（放在最前面） -->
        <el-form-item label="基体选择" prop="substrate_material" class="substrate-select">
          <el-input 
            v-model="formData.substrate_material" 
            placeholder="请输入基体材料，如：硬质合金(WC-Co)、高速钢(HSS)等"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 性能参数 -->
        <div class="performance-grid">
          <el-form-item label="结合力" prop="adhesion_strength">
            <el-input-number 
              v-model="formData.adhesion_strength"
              :min="0"
              :max="100"
              :precision="1"
              :step="1"
              controls-position="right"
            />
            <span class="unit">N</span>
          </el-form-item>

          <el-form-item label="弹性模量" prop="elastic_modulus">
            <el-input-number 
              v-model="formData.elastic_modulus"
              :min="100"
              :max="800"
              :precision="0"
              :step="10"
              controls-position="right"
            />
            <span class="unit">GPa</span>
          </el-form-item>

          <el-form-item label="工作温度" prop="working_temperature">
            <el-input-number 
              v-model="formData.working_temperature"
              :min="200"
              :max="1200"
              :step="50"
              controls-position="right"
            />
            <span class="unit">℃</span>
          </el-form-item>

          <el-form-item label="切削速度" prop="cutting_speed">
            <el-input-number 
              v-model="formData.cutting_speed"
              :min="50"
              :max="1000"
              :step="10"
              controls-position="right"
            />
            <span class="unit">m/min</span>
          </el-form-item>
        </div>

        <!-- 应用场景 -->
        <el-form-item label="应用场景描述" prop="application_scenario">
          <el-input 
            v-model="formData.application_scenario"
            type="textarea"
            :rows="3"
            placeholder="温度，切削的材料，切削速度等"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 提示词标签 -->
        <div class="scenario-hints">
          <span class="hint-label">常用场景：</span>
          <el-tag 
            v-for="hint in scenarioHints" 
            :key="hint"
            size="small"
            class="scenario-hint"
            @click="addHintToScenario(hint)"
          >
            {{ hint }}
          </el-tag>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script setup>
// Vue 3组合式API核心导入
import { ref, computed, watch } from 'vue'
// Element Plus消息提示组件
import { ElMessage } from 'element-plus'
// Element Plus图标组件导入
import { 
  Operation,     // 操作图标（涂层成分）
  Setting,       // 设置图标（工艺参数）
  Grid,          // 网格图标（结构设计）
  TrendCharts,   // 趋势图图标（性能需求）
  Plus,          // 加号图标（添加操作）
  Delete         // 删除图标（删除操作）
} from '@element-plus/icons-vue'

// ============ 事件发射器定义 ============
const emit = defineEmits(['submit', 'data-change'])  // 提交表单和数据变化事件

// ============ 表单引用和数据 ============
const formRef = ref(null)  // 表单DOM引用，用于验证和重置

// 涂层参数表单数据结构
const formData = ref({
  // ============ 涂层成分参数 ============
  al_content: 30.0,        // 铝含量（原子百分比）
  ti_content: 25.0,        // 钛含量（原子百分比）
  n_content: 45.0,         // 氮含量（原子百分比）
  other_elements: [],      // 其他元素成分数组
  
  // ============ 工艺参数 ============
  process_type: 'magnetron_sputtering',  // 工艺类型（磁控溅射/CVD）
  deposition_pressure: 0.6,              // 沉积气压（Pa）
  deposition_temperature: 400,            // 沉积温度（℃）
  bias_voltage: 90,                      // 偏压电压（V）
  n2_flow: 210,                          // 氮气流量（sccm）
  other_gases: [],                       // 其他气体配置数组
  
  // ============ 结构设计参数 ============
  structure_type: 'single',  // 结构类型（单层/多层）
  total_thickness: 3.0,      // 总厚度（微米）
  layers: [],                // 多层结构配置数组
  
  // ============ 性能需求参数 ============
  substrate_material: '硬质合金(WC-Co)',  // 基体材料
  adhesion_strength: 50.0,               // 结合力（N）
  elastic_modulus: 400,                  // 弹性模量（GPa）
  working_temperature: 800,              // 工作温度（℃）
  cutting_speed: 200,                    // 切削速度（m/min）
  application_scenario: ''               // 应用场景描述
})

// ============ 配置数据和选项 ============
// 应用场景快速选择提示标签
const scenarioHints = [
  '高温切削',     // 高温环境下的切削加工
  '钢材加工',     // 钢铁材料切削加工
  '铝合金加工',   // 铝合金材料切削加工
  '干式切削',     // 无冷却液的干式切削
  '湿式切削',     // 使用冷却液的湿式切削
  '精密加工',     // 高精度要求的精密加工
  '粗加工',       // 大余量去除的粗加工
  '高速加工'      // 高切削速度的加工
]

// ============ 表单验证规则 ============
const rules = {
  al_content: [{ required: true, message: '请输入Al含量', trigger: 'blur' }],               // 铝含量必填验证
  ti_content: [{ required: true, message: '请输入Ti含量', trigger: 'blur' }],               // 钛含量必填验证
  n_content: [{ required: true, message: '请输入N含量', trigger: 'blur' }],                 // 氮含量必填验证
  process_type: [{ required: true, message: '请选择工艺类型', trigger: 'change' }],          // 工艺类型必选验证
  deposition_temperature: [{ required: true, message: '请输入沉积温度', trigger: 'blur' }],  // 沉积温度必填验证
  substrate_material: [{ required: true, message: '请选择基体材料', trigger: 'change' }],     // 基体材料必选验证
  structure_type: [{ required: true, message: '请选择结构类型', trigger: 'change' }]         // 结构类型必选验证
}

// ============ 计算属性 ============
// 计算涂层成分总和，用于验证成分配比合理性
const compositionSum = computed(() => {
  // 计算主要成分（Al + Ti + N）
  let sum = formData.value.al_content + formData.value.ti_content + formData.value.n_content
  // 累加其他元素成分
  formData.value.other_elements.forEach(elem => {
    sum += elem.content || 0
  })
  return sum  // 返回总成分百分比
})

// ============ 成分管理操作函数 ============
// 添加新的其他元素到成分配置中
const addElement = () => {
  formData.value.other_elements.push({ name: '', content: 0 })  // 添加空白元素项
}

// 从成分配置中移除指定元素
const removeElement = (index) => {
  formData.value.other_elements.splice(index, 1)  // 按索引删除元素
}

// ============ 气体管理操作函数 ============
// 添加新的其他气体到工艺配置中
const addGas = () => {
  formData.value.other_gases.push({ type: '', flow: 0 })  // 添加空白气体项
}

// 从气体配置中移除指定气体
const removeGas = (index) => {
  formData.value.other_gases.splice(index, 1)  // 按索引删除气体
}

// ============ 结构设计管理函数 ============
// 处理结构类型变化，自动初始化多层结构
const onStructureChange = (value) => {
  if (value === 'multi' && formData.value.layers.length === 0) {
    addLayer()  // 切换到多层时自动添加第一层
  }
}

// 添加新的涂层结构层
const addLayer = () => {
  formData.value.layers.push({ type: '', thickness: 1.0 })  // 添加默认厚度为1.0μm的层
}

// 从结构配置中移除指定层
const removeLayer = (index) => {
  formData.value.layers.splice(index, 1)  // 按索引删除层
}

// ============ UI交互辅助函数 ============
// 将场景提示标签内容添加到应用场景描述中
const addHintToScenario = (hint) => {
  if (!formData.value.application_scenario.includes(hint)) {
    // 如果场景描述中不包含该提示，则添加（用逗号分隔）
    formData.value.application_scenario += (formData.value.application_scenario ? '，' : '') + hint
  }
}

// ============ 核心业务函数 ============
// 提交表单数据进行涂层分析
const submitForm = async () => {
  if (!formRef.value) return  // 检查表单引用是否存在

  try {
    // 执行表单验证，确保必填项已填写
    await formRef.value.validate()
    
    // 验证成分配比的合理性（总和不超过100%，允许0.1%的误差）
    if (compositionSum.value > 100.1) {
      ElMessage.error('成分总和不能超过100%')
      return
    }
    
    // 验证通过，发射提交事件到父组件
    emit('submit', formData.value)
  } catch (error) {
    // 验证失败，提示用户检查输入参数
    ElMessage.error('请检查输入参数')
  }
}

// 重置表单到初始状态
const resetForm = () => {
  formRef.value?.resetFields()           // 重置表单字段到默认值
  formData.value.other_elements = []     // 清空其他元素配置
  formData.value.other_gases = []        // 清空其他气体配置
  formData.value.layers = []             // 清空多层结构配置
}

// 加载预设的示例数据，便于快速测试和演示
const loadExampleData = () => {
  formData.value = {
    // ============ 示例涂层成分配置 ============
    al_content: 32.0,        // 铝含量32%（典型AlTiN涂层配比）
    ti_content: 23.0,        // 钛含量23%
    n_content: 45.0,         // 氮含量45%
    other_elements: [],      // 不包含其他元素
    
    // ============ 示例工艺参数配置 ============
    process_type: 'magnetron_sputtering',      // 采用磁控溅射工艺
    deposition_pressure: 0.6,                 // 沉积气压0.6Pa（典型值）
    deposition_temperature: 450,               // 沉积温度450℃（典型值）
    bias_voltage: 100,                        // 偏压电压100V（中等偏压）
    n2_flow: 210,                             // 氮气流量210sccm
    other_gases: [{ type: 'Ar', flow: 280 }], // 氩气作为载气280sccm
    
    // ============ 示例结构设计配置 ============
    structure_type: 'multi',   // 多层结构设计
    total_thickness: 3.5,      // 总厚度3.5μm
    layers: [
      { type: 'AlTiN', thickness: 2.0 },  // 主功能层：AlTiN 2.0μm
      { type: 'TiN', thickness: 1.5 }     // 粘合层：TiN 1.5μm
    ],
    
    // ============ 示例性能需求配置 ============
    substrate_material: '硬质合金(WC-Co)',               // 硬质合金基体
    adhesion_strength: 50.0,                           // 结合力50N
    elastic_modulus: 400,                              // 弹性模量400GPa
    working_temperature: 900,                          // 工作温度900℃
    cutting_speed: 250,                               // 切削速度250m/min
    application_scenario: '高速切削钢材，干式加工环境，要求高硬度和优异抗氧化性能'  // 具体应用场景
  }
  ElMessage.success('已加载示例数据')
}

// ============ 组件接口暴露 ============
// 向父组件暴露可调用的方法
defineExpose({
  submit: submitForm,           // 提交表单方法
  reset: resetForm,            // 重置表单方法
  loadExampleData: loadExampleData  // 加载示例数据方法
})

// ============ 响应式监听器 ============
// 监听表单数据变化，实时通知父组件
watch(formData, (newData) => {
  emit('data-change', newData)  // 发射数据变化事件，传递最新表单数据
}, { deep: true })  // 深度监听，确保嵌套对象变化也能被检测到
</script>

<style scoped>
/* ============ 涂层表单主容器 ============ */
.coating-form {
  padding: 0;                       /* 清除内边距，由父容器控制 */
}

/* ============ 表单分节布局 ============ */
.form-section {
  margin-bottom: 24px;              /* 分节间距：24px */
  padding-bottom: 20px;             /* 底部内边距：20px */
  border-bottom: 1px solid #e4e7ed; /* 分节分隔线 */
}

/* 最后一个分节样式 */
.form-section:last-child {
  border-bottom: none;              /* 移除最后分节的分隔线 */
  margin-bottom: 0;                 /* 移除底部外边距 */
}

/* ============ 分节标题样式 ============ */
.section-title {
  margin: 0 0 16px 0;               /* 外边距：底部16px */
  font-size: 15px;                  /* 标题字体大小 */
  font-weight: 600;                 /* 字体粗细：半粗体 */
  color: #303133;                   /* 深色文字 */
  display: flex;                    /* 弹性布局用于图标文字对齐 */
  align-items: center;              /* 垂直居中对齐 */
  gap: 8px;                        /* 图标和文字间距：8px */
}

/* 标题图标颜色 */
.title-icon {
  color: #409EFF;                   /* 主题蓝色 */
}

/* ============ 成分输入网格布局 ============ */
.composition-grid {
  display: grid;                    /* 网格布局 */
  grid-template-columns: 1fr;       /* 默认单列布局 */
  gap: 12px;                       /* 网格项间距：12px */
  margin-bottom: 16px;              /* 底部外边距：16px */
}

/* 响应式布局：小屏幕(350px+) - 两列 */
@media (min-width: 350px) {
  .composition-grid {
    grid-template-columns: 1fr 1fr;  /* 两列等宽布局 */
  }
}

/* 响应式布局：中等屏幕(450px+) - 三列 */
@media (min-width: 450px) {
  .composition-grid {
    grid-template-columns: 1fr 1fr 1fr; /* 三列等宽布局(Al、Ti、N) */
  }
}

/* ============ 带单位的输入框布局 ============ */
.input-with-unit {
  display: flex;                    /* 弹性布局 */
  align-items: center;              /* 垂直居中对齐 */
  gap: 6px;                        /* 输入框和单位间距：6px */
}

/* 成分输入框样式 */
.composition-input {
  flex: 1;                         /* 占用剩余空间 */
  min-width: 0;                    /* 允许收缩，防止溢出 */
}

/* 单位标签样式 */
.unit {
  font-size: 14px;                 /* 调整字体大小到14px */
  color: #909399;                  /* 中性灰色 */
  flex-shrink: 0;                  /* 不允许收缩，保持可读性 */
}

/* ============ 动态配置区域布局 ============ */
.other-elements,
.gas-section,
.multi-layer-design {
  margin-top: 16px;                /* 顶部外边距：16px */
}

/* 子标题标签样式 */
.sub-label {
  display: block;                  /* 块级元素 */
  font-size: 14px;                 /* 字体大小：增大到14px */
  color: #606266;                  /* 中性灰色 */
  font-weight: 500;                /* 中等字重 */
  margin-bottom: 8px;              /* 底部外边距：8px */
}

/* ============ 动态行项目布局 ============ */
.element-row,
.gas-row,
.layer-row {
  display: flex;                   /* 弹性布局 */
  align-items: center;             /* 垂直居中对齐 */
  gap: 8px;                       /* 元素间距：8px */
  margin-bottom: 8px;              /* 底部外边距：8px */
}

/* ============ 参数网格布局 ============ */
.process-grid,
.performance-grid {
  display: grid;                   /* 网格布局 */
  grid-template-columns: 1fr;      /* 默认单列布局 */
  gap: 12px;                      /* 网格项间距：12px */
}

/* 响应式布局：小屏幕(400px+) - 两列 */
@media (min-width: 400px) {
  .process-grid,
  .performance-grid {
    grid-template-columns: 1fr 1fr; /* 两列等宽布局 */
  }
}

/* 响应式布局：大屏幕(768px+) - 工艺参数四列，性能参数两列 */
@media (min-width: 768px) {
  .process-grid {
    grid-template-columns: 1fr 1fr 1fr 1fr; /* 四列布局适应4个工艺参数 */
  }
  
  .performance-grid {
    grid-template-columns: 1fr 1fr; /* 性能参数保持两列 */
  }
}

.process-select,
.substrate-select {
  margin-bottom: 16px;
}

.composition-sum {
  text-align: center;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  background: #f0f9ff;
  color: #67C23A;
  border: 1px solid #e1f3d8;
}

.composition-sum.warning {
  background: #fef0f0;
  color: #F56C6C;
  border-color: #fbc4c4;
}

.scenario-hints {
  margin-top: 8px;
}

.hint-label {
  font-size: 14px;                /* 增大到14px */
  color: #909399;
  margin-right: 8px;
}

.scenario-hint {
  margin-right: 6px;
  margin-bottom: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-hint:hover {
  transform: translateY(-1px);
}

:deep(.el-form-item) {
  margin-bottom: 14px;
}

:deep(.el-form-item__label) {
  font-size: 14px;                /* 增大表单标签字体到14px */
  color: #606266;
  font-weight: 500;
  padding-bottom: 4px;
}

:deep(.el-input__wrapper),
:deep(.el-select .el-input .el-input__wrapper),
:deep(.el-textarea__inner) {
  border-radius: 6px;
}

:deep(.el-input-number) {
  width: 100%;
  min-width: 80px;
}

:deep(.el-input-number .el-input__wrapper) {
  padding-right: 40px;
  padding-left: 10px;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
  padding-right: 8px;
}

/* 增大按钮字体 */
:deep(.el-button) {
  font-size: 14px;                /* 增大按钮字体到14px */
}

:deep(.el-button--small) {
  font-size: 13px;                /* 小号按钮字体13px */
}

/* Element Plus下拉菜单字体调整 */
:deep(.el-dropdown-menu__item) {
  font-size: 14px;                /* 下拉菜单项字体14px */
}

:deep(.el-select-dropdown__item) {
  font-size: 14px;                /* 选择器下拉项字体14px */
}
</style>
