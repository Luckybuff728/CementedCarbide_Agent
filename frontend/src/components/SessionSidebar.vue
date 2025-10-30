<template>
  <div class="session-sidebar" :class="{ collapsed: isCollapsed }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <el-button 
        v-if="!isCollapsed"
        type="primary" 
        class="new-session-btn"
        @click="createNewSession"
      >
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>
      <el-button 
        v-else
        type="primary" 
        circle
        @click="createNewSession"
      >
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>

    <!-- 会话列表 -->
    <div class="sessions-list" v-if="!isCollapsed">
      <el-scrollbar>
        <div
          v-for="session in sortedSessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === currentSessionId }"
          @click="selectSession(session.id)"
        >
          <div class="session-content">
            <div class="session-title">
              {{ session.title || '新对话' }}
            </div>
            <div class="session-meta">
              <span class="session-time">{{ formatTime(session.updatedAt) }}</span>
              <span class="session-count">{{ session.messageCount || 0 }} 条消息</span>
            </div>
          </div>
          <div class="session-actions">
            <el-dropdown trigger="click" @click.stop>
              <el-button text circle size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="renameSession(session.id)">
                    <el-icon><Edit /></el-icon>
                    重命名
                  </el-dropdown-item>
                  <el-dropdown-item @click="deleteSession(session.id)" divided>
                    <el-icon><Delete /></el-icon>
                    删除对话
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <el-empty v-if="sessions.length === 0" description="暂无对话历史" :image-size="80" />
      </el-scrollbar>
    </div>

    <!-- 折叠/展开按钮 -->
    <div class="sidebar-footer">
      <el-button 
        text 
        class="toggle-btn"
        @click="toggleCollapse"
      >
        <el-icon>
          <DArrowLeft v-if="!isCollapsed" />
          <DArrowRight v-else />
        </el-icon>
        <span v-if="!isCollapsed">收起</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Edit, Delete, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => []
  },
  currentSessionId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['create', 'select', 'rename', 'delete'])

// 是否折叠
const isCollapsed = ref(false)

// 排序后的会话列表（按更新时间倒序）
const sortedSessions = computed(() => {
  return [...props.sessions].sort((a, b) => {
    return new Date(b.updatedAt) - new Date(a.updatedAt)
  })
})

// 创建新会话
const createNewSession = () => {
  emit('create')
}

// 选择会话
const selectSession = (sessionId) => {
  if (sessionId !== props.currentSessionId) {
    emit('select', sessionId)
  }
}

// 重命名会话
const renameSession = async (sessionId) => {
  const session = props.sessions.find(s => s.id === sessionId)
  if (!session) return

  try {
    const { value } = await ElMessageBox.prompt('请输入新的对话名称', '重命名对话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: session.title || '新对话',
      inputPattern: /\S+/,
      inputErrorMessage: '对话名称不能为空'
    })

    if (value && value.trim()) {
      emit('rename', { sessionId, newTitle: value.trim() })
      ElMessage.success('重命名成功')
    }
  } catch {
    // 用户取消
  }
}

// 删除会话
const deleteSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm(
      '删除后无法恢复，确定要删除这个对话吗？',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    emit('delete', sessionId)
    ElMessage.success('对话已删除')
  } catch {
    // 用户取消
  }
}

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  // 超过7天显示具体日期
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}
</script>

<style scoped>
.session-sidebar {
  width: 260px;
  background: #F7F8FA;
  border-right: 1px solid #E4E7ED;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.session-sidebar.collapsed {
  width: 60px;
}

/* 头部 */
.sidebar-header {
  padding: 16px 12px;
  border-bottom: 1px solid #E4E7ED;
  flex-shrink: 0;
}

.new-session-btn {
  width: 100%;
  font-size: 14px;
}

/* 会话列表 */
.sessions-list {
  flex: 1;
  overflow: hidden;
}

.sessions-list :deep(.el-scrollbar__view) {
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  border: 1px solid transparent;
}

.session-item:hover {
  background: #F0F9FF;
  border-color: #409EFF;
}

.session-item.active {
  background: linear-gradient(135deg, #E7F5FF 0%, #D9ECFF 100%);
  border-color: #409EFF;
}

.session-content {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.session-time,
.session-count {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

/* 底部 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #E4E7ED;
  flex-shrink: 0;
}

.toggle-btn {
  width: 100%;
  color: #606266;
  font-size: 13px;
}

.toggle-btn:hover {
  color: #409EFF;
  background: #F0F9FF;
}

/* 折叠状态 */
.session-sidebar.collapsed .session-item {
  justify-content: center;
}

.session-sidebar.collapsed .session-content,
.session-sidebar.collapsed .session-actions {
  display: none;
}
</style>
