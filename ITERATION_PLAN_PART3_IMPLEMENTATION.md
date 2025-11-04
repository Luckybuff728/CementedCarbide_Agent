# 迭代优化功能 - 实施计划（第3部分）

## 📋 前端UI设计

### 1️⃣ 新增组件

#### 1.1 ExperimentResultInputCard.vue（实验数据输入卡片）

**位置：** `frontend/src/components/ExperimentResultInputCard.vue`

**功能：** 显示在工单生成后，等待实验人员输入实验结果

**UI设计：**
```vue
<template>
  <div class="experiment-input-card">
    <div class="card-header">
      <n-icon class="header-icon" :component="FlaskOutline" />
      <h3>实验结果输入</h3>
      <el-tag type="warning">第 {{ currentIteration }} 轮</el-tag>
    </div>
    
    <div class="card-body">
      <!-- 工单信息回顾 -->
      <div class="workorder-summary">
        <h4>本轮实验参数：</h4>
        <div class="param-grid">
          <div class="param-item">
            <span class="label">Al含量:</span>
            <span class="value">{{ workorder.composition.al_content }}%</span>
          </div>
          <div class="param-item">
            <span class="label">沉积温度:</span>
            <span class="value">{{ workorder.process.temperature }}℃</span>
          </div>
          <!-- 更多参数... -->
        </div>
      </div>
      
      <!-- 实验数据输入表单 -->
      <el-form 
        ref="formRef" 
        :model="experimentData" 
        label-position="left"
        label-width="120px"
      >
        <h4>实测性能数据：</h4>
        
        <el-form-item label="硬度" required>
          <div class="input-with-unit">
            <el-input-number 
              v-model="experimentData.hardness"
              :min="0"
              :max="50"
              :precision="1"
              :step="0.1"
              placeholder="请输入实测硬度"
            />
            <span class="unit">GPa</span>
          </div>
        </el-form-item>
        
        <el-form-item label="结合力" required>
          <div class="input-with-unit">
            <el-input-number 
              v-model="experimentData.adhesion_strength"
              :min="0"
              :max="100"
              :precision="1"
              placeholder="请输入结合力"
            />
            <span class="unit">N</span>
          </div>
        </el-form-item>
        
        <el-form-item label="抗氧化温度" required>
          <div class="input-with-unit">
            <el-input-number 
              v-model="experimentData.oxidation_temperature"
              :min="400"
              :max="1200"
              :step="10"
              placeholder="请输入抗氧化温度"
            />
            <span class="unit">℃</span>
          </div>
        </el-form-item>
        
        <el-form-item label="表面粗糙度">
          <div class="input-with-unit">
            <el-input-number 
              v-model="experimentData.surface_roughness"
              :min="0"
              :max="10"
              :precision="2"
              placeholder="选填"
            />
            <span class="unit">μm</span>
          </div>
        </el-form-item>
        
        <el-form-item label="实验备注">
          <el-input 
            v-model="experimentData.notes"
            type="textarea"
            :rows="3"
            placeholder="记录实验过程中的观察、异常情况等"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <!-- 对比预测值 -->
      <div class="prediction-comparison" v-if="prediction">
        <h4>预测值对比：</h4>
        <div class="comparison-grid">
          <div class="comparison-item">
            <span class="metric">硬度</span>
            <span class="predicted">预测: {{ prediction.hardness }}GPa</span>
            <span class="actual" :class="getComparisonClass('hardness')">
              实测: {{ experimentData.hardness || '-' }}GPa
            </span>
          </div>
          <!-- 更多对比... -->
        </div>
      </div>
    </div>
    
    <div class="card-footer">
      <el-button 
        type="primary" 
        size="large"
        @click="handleSubmit"
        :loading="isSubmitting"
        :disabled="!isDataValid"
        block
      >
        提交实验结果并继续优化
      </el-button>
      <el-button 
        size="large"
        @click="handleStopIteration"
        block
      >
        性能已达标，终止迭代
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { NIcon } from 'naive-ui'
import { FlaskOutline } from '@vicons/ionicons5'

const props = defineProps({
  workorder: {
    type: Object,
    required: true
  },
  prediction: {
    type: Object,
    default: null
  },
  currentIteration: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['submit', 'stop'])

const experimentData = ref({
  hardness: null,
  adhesion_strength: null,
  oxidation_temperature: null,
  surface_roughness: null,
  notes: ''
})

const isSubmitting = ref(false)

// 验证必填字段
const isDataValid = computed(() => {
  return experimentData.value.hardness !== null &&
         experimentData.value.adhesion_strength !== null &&
         experimentData.value.oxidation_temperature !== null
})

// 对比状态类（绿色=超预测，红色=低于预测）
const getComparisonClass = (metric) => {
  if (!props.prediction || !experimentData.value[metric]) return ''
  return experimentData.value[metric] >= props.prediction[metric] ? 'better' : 'worse'
}

// 提交实验结果
const handleSubmit = () => {
  if (!isDataValid.value) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  emit('submit', experimentData.value)
  ElMessage.success('实验结果已提交，正在分析...')
}

// 终止迭代
const handleStopIteration = () => {
  emit('stop', experimentData.value)
}
</script>

<style scoped>
.experiment-input-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.workorder-summary {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.param-item {
  display: flex;
  justify-content: space-between;
}

.prediction-comparison {
  background: #ecf5ff;
  padding: 16px;
  border-radius: 6px;
  margin-top: 20px;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #dcdfe6;
}

.comparison-item:last-child {
  border-bottom: none;
}

.actual.better {
  color: #67c23a;
  font-weight: bold;
}

.actual.worse {
  color: #f56c6c;
}

.card-footer {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unit {
  font-size: 14px;
  color: #909399;
  min-width: 40px;
}
</style>
```

#### 1.2 IterationHistoryPanel.vue（迭代历史面板）

**位置：** `frontend/src/components/IterationHistoryPanel.vue`

**功能：** 在RightPanel底部显示历史迭代记录

```vue
<template>
  <div class="iteration-history">
    <h4>迭代历史</h4>
    
    <el-timeline>
      <el-timeline-item
        v-for="(record, index) in iterationHistory"
        :key="index"
        :timestamp="formatTimestamp(record.timestamp)"
        placement="top"
      >
        <el-card>
          <div class="iteration-record">
            <div class="iteration-header">
              <el-tag :type="getIterationType(index)" size="small">
                第 {{ index + 1 }} 轮
              </el-tag>
              <span class="iteration-gap">
                性能差距: {{ calculateGap(record) }}%
              </span>
            </div>
            
            <div class="iteration-body">
              <div class="performance-row">
                <span class="label">预测硬度:</span>
                <span class="value">{{ record.prediction?.hardness }}GPa</span>
              </div>
              <div class="performance-row">
                <span class="label">实测硬度:</span>
                <span class="value" :class="getAccuracyClass(record)">
                  {{ record.experiment_result?.hardness }}GPa
                </span>
              </div>
            </div>
            
            <div class="iteration-footer">
              <el-button 
                size="small" 
                text 
                @click="viewDetails(record)"
              >
                查看详情
              </el-button>
            </div>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  iterationHistory: {
    type: Array,
    default: () => []
  }
})

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const calculateGap = (record) => {
  const target = 35  // 目标硬度，实际应从props获取
  const actual = record.experiment_result?.hardness || 0
  const gap = ((target - actual) / target * 100).toFixed(1)
  return gap
}

const getIterationType = (index) => {
  if (index === props.iterationHistory.length - 1) return 'primary'
  return 'info'
}

const getAccuracyClass = (record) => {
  const pred = record.prediction?.hardness || 0
  const actual = record.experiment_result?.hardness || 0
  const error = Math.abs(pred - actual) / actual
  return error < 0.1 ? 'accurate' : 'inaccurate'
}

const viewDetails = (record) => {
  // 展示详细对话框
  console.log('查看详情', record)
}
</script>

<style scoped>
.iteration-history {
  padding: 16px;
}

.iteration-record {
  padding: 8px;
}

.iteration-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.performance-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.value.accurate {
  color: #67c23a;
}

.value.inaccurate {
  color: #f56c6c;
}
</style>
```

### 2️⃣ Store扩展

```javascript
// frontend/src/stores/workflow.js

export const useWorkflowStore = defineStore('workflow', () => {
  // ... 现有状态
  
  // 🆕 迭代相关状态
  const currentIteration = ref(0)
  const maxIterations = ref(5)
  const iterationHistory = ref([])
  const isWaitingExperiment = ref(false)
  const convergenceStatus = ref(null)
  
  // 🆕 计算属性：是否收敛
  const isConverged = computed(() => {
    return convergenceStatus.value?.is_converged === true
  })
  
  // 🆕 方法：添加迭代记录
  const addIterationRecord = (record) => {
    iterationHistory.value.push(record)
  }
  
  // 🆕 方法：清空迭代历史
  const clearIterationHistory = () => {
    iterationHistory.value = []
    currentIteration.value = 0
    convergenceStatus.value = null
  }
  
  // 修改reset方法
  const reset = () => {
    // ... 现有重置逻辑
    clearIterationHistory()
    isWaitingExperiment.value = false
  }
  
  return {
    // ... 现有返回
    
    // 🆕 迭代相关
    currentIteration,
    maxIterations,
    iterationHistory,
    isWaitingExperiment,
    convergenceStatus,
    isConverged,
    addIterationRecord,
    clearIterationHistory
  }
})
```

### 3️⃣ App.vue修改

```javascript
// frontend/src/App.vue

// 🆕 处理新的消息类型
const handleWebSocketMessage = (message) => {
  console.log('[WS消息]', message.type)
  
  switch (message.type) {
    case 'node_output':
      handleNodeOutput(message.data)
      break
    
    case 'llm_stream':
      handleLLMStream(message)
      break
    
    // 🆕 工作流暂停（等待实验）
    case 'workflow_paused':
      handleWorkflowPaused(message)
      break
    
    // 🆕 实验结果已接收
    case 'experiment_received':
      handleExperimentReceived(message)
      break
    
    // 🆕 收敛检查完成
    case 'convergence_checked':
      handleConvergenceChecked(message)
      break
    
    case 'error':
      handleError(message)
      break
    
    default:
      console.warn('未知消息类型:', message.type)
  }
}

// 🆕 处理工作流暂停
const handleWorkflowPaused = (message) => {
  workflowStore.isWaitingExperiment = true
  workflowStore.isProcessing = false
  workflowStore.currentNode = 'await_experiment_results'
  workflowStore.currentNodeTitle = '等待实验结果'
  
  ElMessage.info({
    message: '工单已生成，请输入实验结果后继续',
    duration: 5000
  })
}

// 🆕 处理实验结果提交
const handleExperimentSubmit = (experimentData) => {
  send({
    type: 'submit_experiment_results',
    task_id: workflowStore.taskId,
    data: {
      experiment_results: experimentData
    }
  })
  
  workflowStore.isWaitingExperiment = false
  workflowStore.isProcessing = true
}

// 🆕 处理收敛检查
const handleConvergenceChecked = (message) => {
  const convergence = message.data?.convergence_check
  workflowStore.convergenceStatus = convergence
  
  if (convergence?.is_converged) {
    ElMessage.success({
      message: `迭代完成：${convergence.reason}`,
      duration: 10000
    })
    workflowStore.isProcessing = false
  } else {
    ElMessage.info({
      message: '继续下一轮优化...',
      duration: 3000
    })
  }
}
```

---

## 📋 完整实施计划

### 阶段1：后端基础（1-2周）

**任务清单：**

| 任务 | 文件 | 工作量 | 优先级 |
|------|------|--------|--------|
| 新增`experiment_workorder_generation_node` | `src/graph/nodes.py` | 0.5天 | P0 |
| 新增`await_experiment_results_node` | `src/graph/nodes.py` | 1天 | P0 |
| 新增`convergence_check_node` | `src/graph/nodes.py` | 0.5天 | P0 |
| ~~创建`WorkorderService`~~ | ~~已存在，无需创建~~ | ~~0天~~ | ~~N/A~~ |
| 创建`ConvergenceService` | `src/services/convergence_service.py` | 1天 | P0 |
| 重构工作流图 | `src/graph/workflow.py` | 2天 | P0 |
| 切换到SQLite持久化 | `src/graph/workflow.py` | 0.5天 | P1 |
| 扩展WebSocket消息处理 | `src/api/routes/websocket_routes.py` | 1天 | P0 |
| 单元测试 | `tests/` | 2天 | P1 |

**验收标准：**
- ✅ 工作流可以在`await_experiment_results`暂停
- ✅ 提交实验数据后可以恢复执行
- ✅ 收敛判断逻辑正确
- ✅ State正确存储迭代历史

### 阶段2：前端UI（1周）

**任务清单：**

| 任务 | 文件 | 工作量 | 优先级 |
|------|------|--------|--------|
| 创建`ExperimentResultInputCard.vue` | `frontend/src/components/` | 1天 | P0 |
| 创建`IterationHistoryPanel.vue` | `frontend/src/components/` | 0.5天 | P1 |
| 扩展`workflow.js` Store | `frontend/src/stores/` | 0.5天 | P0 |
| 修改`App.vue`消息处理 | `frontend/src/App.vue` | 1天 | P0 |
| 修改`CenterPanel.vue`展示逻辑 | `frontend/src/components/` | 0.5天 | P1 |
| 修改`StatusBar.vue`显示迭代轮次 | `frontend/src/components/` | 0.5天 | P2 |
| UI/UX测试 | - | 1天 | P1 |

**验收标准：**
- ✅ 工单生成后显示实验输入卡片
- ✅ 实验数据可正确提交
- ✅ 迭代历史正确展示
- ✅ 收敛后显示明确提示

### 阶段3：联调与优化（0.5-1周）

**任务清单：**

| 任务 | 工作量 | 优先级 |
|------|--------|--------|
| 前后端联调 | 2天 | P0 |
| 性能优化（大量迭代数据） | 1天 | P1 |
| 错误处理和异常流程 | 1天 | P1 |
| 文档编写 | 0.5天 | P2 |

### 阶段4：高级功能（可选，1-2周）

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 智能推荐下一轮参数 | 基于历史趋势AI推荐 | P2 |
| 实验数据可视化对比 | 图表展示历史趋势 | P2 |
| 导出迭代报告 | PDF/Excel导出 | P3 |
| 多任务并行迭代 | 支持同时优化多个涂层 | P3 |

---

## 📊 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LangGraph interrupt机制不稳定 | 工作流暂停失败 | 充分测试，准备降级方案 |
| 长时间等待导致checkpoint丢失 | 用户体验差 | 使用SQLite持久化，添加心跳检测 |
| 前端状态复杂度增加 | 维护困难 | 规范Store结构，添加详细注释 |
| 实验数据验证不足 | 错误数据影响优化 | 添加严格的数据校验逻辑 |
| 无限循环迭代 | 资源浪费 | 设置最大迭代次数（5轮） |

---

## ✅ 总结

**预计总工作量：** 2-3.5周 ⏰ （已优化，因WorkorderService已存在）

**关键里程碑：**
1. Week 1: 后端工作流重构完成（节省1天）
2. Week 2: 前端UI开发完成
3. Week 2.5-3: 联调测试通过
4. Week 3.5: 上线试运行

**技术栈：**
- 后端: LangGraph (Interrupt + Conditional Edges), SQLite Checkpointer
- 前端: Vue 3 + Pinia, Element Plus, WebSocket
- 通信: JSON over WebSocket (新增消息类型)

**下一步行动：**
1. 评审本方案，确认技术可行性
2. 创建开发分支 `feature/iteration-optimization`
3. 按阶段1开始实施
