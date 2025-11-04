<template>
  <div class="left-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <h3>
        <el-icon><Setting /></el-icon>
        涂层参数配置
      </h3>
      <div class="header-actions">
        <el-dropdown @command="handleCommand" size="small">
          <el-button size="small" circle>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="example">加载示例</el-dropdown-item>
              <el-dropdown-item command="clear">清空表单</el-dropdown-item>
              <el-dropdown-item command="save">保存模板</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 连接状态指示 -->
    <div v-if="!connectionStatus" class="connection-warning">
      <el-alert
        title="后端连接断开"
        type="warning"
        size="small"
        show-icon
        :closable="false"
      >
        请检查后端服务是否运行
      </el-alert>
    </div>
    
    <!-- 表单内容区 -->
    <div class="panel-content">
      <CoatingForm
        ref="formRef"
        @submit="handleSubmit"
        @data-change="handleDataChange"
      />
    </div>
    
    <!-- 底部操作区 -->
    <div class="panel-footer">
      <el-button 
        type="primary" 
        size="large"
        :loading="loading"
        :disabled="!hasValidData || !connectionStatus"
        @click="submitForm"
        block
      >
        <el-icon><CaretRight /></el-icon>
        {{ loading ? '分析中...' : '开始分析' }}
      </el-button>
      
      <div class="footer-info">
        <el-text size="small" type="info">
          <el-icon><InfoFilled /></el-icon>
          确保所有参数填写完整后开始分析
        </el-text>
      </div>
    </div>
  </div>
</template>

<script setup>
// Vue 3组合式API核心导入
import { ref, computed } from 'vue'
// Element Plus消息提示组件
import { ElMessage } from 'element-plus'
// Element Plus图标组件导入
import { 
  Setting,      // 设置图标（面板标题）
  MoreFilled,   // 更多操作图标（下拉菜单）
  CaretRight,   // 右箭头图标（开始分析按钮）
  InfoFilled    // 信息图标（提示文本）
} from '@element-plus/icons-vue'
// 涂层参数配置表单组件
import CoatingForm from './CoatingForm.vue'

// ============ 组件属性定义 ============
const props = defineProps({
  loading: {               // 是否正在处理分析请求
    type: Boolean,
    default: false
  },
  connectionStatus: {      // WebSocket连接状态
    type: Boolean,
    default: false
  }
})

// ============ 事件发射器定义 ============
const emit = defineEmits(['submit'])  // 提交表单数据事件

// ============ 响应式状态管理 ============
const formRef = ref(null)       // 表单组件引用
const formData = ref(null)      // 表单数据缓存
const hasData = ref(false)      // 是否已有表单数据标识

// ============ 计算属性 ============
// 检查是否具有有效的表单数据，用于控制提交按钮状态
const hasValidData = computed(() => {
  return formData.value && hasData.value
})

// ============ 数据处理函数 ============
// 处理表单数据变化事件，缓存最新数据并更新状态
const handleDataChange = (data) => {
  formData.value = data  // 缓存表单数据
  hasData.value = !!(data && Object.keys(data).length > 0)  // 检查数据完整性
}

// 处理表单提交事件，将数据传递给父组件
const handleSubmit = (data) => {
  emit('submit', data)  // 发射提交事件到App.vue
}

// 触发表单提交验证和数据收集
const submitForm = () => {
  if (formRef.value) {
    formRef.value.submit()  // 调用子组件的提交方法
  }
}

// ============ 用户操作处理函数 ============
// 处理右上角下拉菜单的命令选择
const handleCommand = (command) => {
  switch (command) {
    case 'example':      // 加载示例数据命令
      loadExample()
      break
    case 'clear':        // 清空表单命令
      clearForm()
      break
    case 'save':         // 保存模板命令
      saveTemplate()
      break
  }
}

// 加载预设示例数据到表单中
const loadExample = () => {
  if (formRef.value) {
    formRef.value.loadExampleData()  // 调用子组件的示例数据加载方法
  }
  ElMessage.success('已加载示例数据')
}

// 清空表单中的所有数据
const clearForm = () => {
  if (formRef.value) {
    formRef.value.reset()  // 调用子组件的重置方法
  }
  formData.value = null      // 清空缓存数据
  hasData.value = false      // 重置数据状态标识
  ElMessage.info('表单已清空')
}

// ============ 模板管理功能 ============
// 将当前表单配置保存为模板到本地存储
const saveTemplate = () => {
  if (!hasValidData.value) {
    ElMessage.warning('请先填写参数')
    return
  }
  
  // 从本地存储获取已有模板列表
  const templates = JSON.parse(localStorage.getItem('coating_templates') || '[]')
  // 生成唯一的模板名称（包含序号和时间戳）
  const templateName = `模板${templates.length + 1}_${new Date().toLocaleString()}`
  
  // 构建新模板对象
  templates.push({
    name: templateName,                      // 模板名称
    data: formData.value,                   // 表单数据
    createdAt: new Date().toISOString()     // 创建时间
  })
  
  // 保存更新后的模板列表到本地存储
  localStorage.setItem('coating_templates', JSON.stringify(templates))
  ElMessage.success(`模板"${templateName}"已保存`)
}
</script>

<style scoped>
.left-panel {
  width: 420px;
  height: calc(100vh - 70px); /* 减去状态栏高度 */
  background: linear-gradient(180deg, #fafbfc 0%, #f5f7fa 100%);
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  z-index: 10;
  flex-shrink: 0; /* 防止header被压缩 */
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.connection-warning {
  padding: 12px 16px;
  background: #fff7e6;
  border-bottom: 1px solid #ffe7ba;
  flex-shrink: 0; /* 防止警告区域被压缩 */
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  scroll-behavior: smooth;
  /* 确保内容区域不会挤压footer */
  min-height: 0;
}

.panel-footer {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: white;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0; /* 防止footer被压缩 */
  min-height: 120px; /* 确保footer有最小高度 */
}

.footer-info {
  margin-top: 12px;
  text-align: center;
}

/* 美化滚动条 */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .left-panel {
    width: 380px;
  }
}

@media (max-width: 1200px) {
  .left-panel {
    width: 320px;
  }
  
  .panel-content {
    padding: 16px;
  }
  
  .panel-header,
  .panel-footer {
    padding: 16px;
  }
}

/* 加载状态动画 */
.panel-footer .el-button.is-loading {
  background: linear-gradient(45deg, #409EFF, #67C23A);
  animation: loading-gradient 2s ease-in-out infinite;
}

@keyframes loading-gradient {
  0%, 100% {
    background: linear-gradient(45deg, #409EFF, #67C23A);
  }
  50% {
    background: linear-gradient(45deg, #67C23A, #409EFF);
  }
}

/* 成功状态提示 */
.panel-content:has(.composition-sum:not(.warning)) {
  border-left: 3px solid #67C23A;
}
</style>
