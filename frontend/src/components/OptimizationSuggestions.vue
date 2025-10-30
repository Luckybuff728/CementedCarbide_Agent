<template>
  <el-card class="optimization-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>💡 优化建议方案</span>
        <el-tag v-if="selectedType" type="success" size="small">
          已选择: {{ selectedType }}
        </el-tag>
      </div>
    </template>

    <div v-if="suggestions && Object.keys(suggestions).length > 0">
      <el-row :gutter="20">
        <!-- P1 成分优化 -->
        <el-col :span="8">
          <div
            class="suggestion-card"
            :class="{ selected: selectedType === 'P1_成分优化' }"
            @click="selectOptimization('P1_成分优化')"
          >
            <div class="card-icon">🧪</div>
            <h3>P1 - 成分优化</h3>
            <el-divider />
            
            <div v-if="getSuggestionsByType('P1') && getSuggestionsByType('P1').length > 0">
              <div
                v-for="(item, index) in getSuggestionsByType('P1')"
                :key="index"
                class="suggestion-item"
              >
                <div class="item-header">
                  <el-tag size="small" type="primary">方案 {{ index + 1 }}</el-tag>
                </div>
                <div class="item-desc-wrapper">
                  <div class="item-desc" v-html="renderMarkdown(item.description || item.type)"></div>
                  <!-- 完整内容展开/折叠 -->
                  <div v-if="item.full_content" class="full-content-toggle">
                    <el-button 
                      link 
                      size="small" 
                      type="primary"
                      @click.stop="toggleContent('P1', index)"
                    >
                      <el-icon><Document /></el-icon>
                      {{ isContentExpanded('P1', index) ? '收起详情' : '查看完整建议' }}
                    </el-button>
                  </div>
                </div>
                <!-- 完整内容区域 -->
                <div v-if="item.full_content" v-show="isContentExpanded('P1', index)" class="full-content" v-html="renderMarkdown(item.full_content)"></div>
              </div>
            </div>
            <el-empty v-else description="暂无方案" :image-size="60" />
          </div>
        </el-col>

        <!-- P2 结构优化 -->
        <el-col :span="8">
          <div
            class="suggestion-card"
            :class="{ selected: selectedType === 'P2_结构优化' }"
            @click="selectOptimization('P2_结构优化')"
          >
            <div class="card-icon">🏗️</div>
            <h3>P2 - 结构优化</h3>
            <el-divider />
            
            <div v-if="getSuggestionsByType('P2') && getSuggestionsByType('P2').length > 0">
              <div
                v-for="(item, index) in getSuggestionsByType('P2')"
                :key="index"
                class="suggestion-item"
              >
                <div class="item-header">
                  <el-tag size="small" type="primary">方案 {{ index + 1 }}</el-tag>
                </div>
                <div class="item-desc-wrapper">
                  <div class="item-desc" v-html="renderMarkdown(item.description || item.type)"></div>
                  <!-- 完整内容展开/折叠 -->
                  <div v-if="item.full_content" class="full-content-toggle">
                    <el-button 
                      link 
                      size="small" 
                      type="primary"
                      @click.stop="toggleContent('P2', index)"
                    >
                      <el-icon><Document /></el-icon>
                      {{ isContentExpanded('P2', index) ? '收起详情' : '查看完整建议' }}
                    </el-button>
                  </div>
                </div>
                <!-- 完整内容区域 -->
                <div v-if="item.full_content" v-show="isContentExpanded('P2', index)" class="full-content" v-html="renderMarkdown(item.full_content)"></div>
              </div>
            </div>
            <el-empty v-else description="暂无方案" :image-size="60" />
          </div>
        </el-col>

        <!-- P3 工艺优化 -->
        <el-col :span="8">
          <div
            class="suggestion-card"
            :class="{ selected: selectedType === 'P3_工艺优化' }"
            @click="selectOptimization('P3_工艺优化')"
          >
            <div class="card-icon">⚙️</div>
            <h3>P3 - 工艺优化</h3>
            <el-divider />
            
            <div v-if="getSuggestionsByType('P3') && getSuggestionsByType('P3').length > 0">
              <div
                v-for="(item, index) in getSuggestionsByType('P3')"
                :key="index"
                class="suggestion-item"
              >
                <div class="item-header">
                  <el-tag size="small" type="primary">方案 {{ index + 1 }}</el-tag>
                </div>
                <div class="item-desc-wrapper">
                  <div class="item-desc" v-html="renderMarkdown(item.description || item.type)"></div>
                  <!-- 完整内容展开/折叠 -->
                  <div v-if="item.full_content" class="full-content-toggle">
                    <el-button 
                      link 
                      size="small" 
                      type="primary"
                      @click.stop="toggleContent('P3', index)"
                    >
                      <el-icon><Document /></el-icon>
                      {{ isContentExpanded('P3', index) ? '收起详情' : '查看完整建议' }}
                    </el-button>
                  </div>
                </div>
                <!-- 完整内容区域 -->
                <div v-if="item.full_content" v-show="isContentExpanded('P3', index)" class="full-content" v-html="renderMarkdown(item.full_content)"></div>
              </div>
            </div>
            <el-empty v-else description="暂无方案" :image-size="60" />
          </div>
        </el-col>
      </el-row>

      <!-- 综合建议 - 显示LLM生成的内容 -->
      <el-card class="comprehensive-recommendation" v-if="comprehensiveRecommendation">
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px; font-weight: 600;">💡 综合建议</span>
          </div>
        </template>
        <div class="recommendation-content" v-html="renderMarkdown(comprehensiveRecommendation)"></div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons" v-if="selectedType">
        <el-button type="primary" size="large" @click="confirmSelection">
          <el-icon><Check /></el-icon>
          确认选择并进入迭代优化
        </el-button>
        <el-button size="large" @click="clearSelection">重新选择</el-button>
      </div>
    </div>

    <el-empty v-else description="等待优化建议..." />
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Check, Document } from '@element-plus/icons-vue'
import { marked } from 'marked'

const props = defineProps({
  suggestions: {
    type: Object,
    default: () => ({})
  },
  comprehensiveRecommendation: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select'])

const selectedType = ref('')
const expandedContent = ref({})

// 获取建议数据（兼容P1和P1_成分优化两种格式）
const getSuggestionsByType = (type) => {
  // 尝试多种可能的key格式
  const possibleKeys = [
    type,
    `${type}_成分优化`,
    `${type}_结构优化`,
    `${type}_工艺优化`
  ]
  
  for (const key of possibleKeys) {
    if (props.suggestions[key] && Array.isArray(props.suggestions[key])) {
      return props.suggestions[key]
    }
  }
  
  return []
}

// 选择优化方案
const selectOptimization = (type) => {
  selectedType.value = type
  const displayType = type.replace('_成分优化', '').replace('_结构优化', '').replace('_工艺优化', '')
  ElMessage.success(`已选择 ${displayType} 优化方案`)
}

// 清除选择
const clearSelection = () => {
  selectedType.value = ''
}

// 确认选择
const confirmSelection = () => {
  if (!selectedType.value) {
    ElMessage.warning('请先选择一个优化方案')
    return
  }

  // 获取实际的建议数据
  const selectedSuggestions = props.suggestions[selectedType.value] || []
  
  emit('select', {
    type: selectedType.value,
    suggestions: selectedSuggestions,
    selected_plan: selectedSuggestions[0] || {} // 默认选择第一个方案
  })
  
  ElMessage.success('已确认选择，继续执行工作流...')
}

// 切换内容展开状态
const toggleContent = (type, index) => {
  const key = `${type}_${index}`
  expandedContent.value[key] = !expandedContent.value[key]
}

// 检查内容是否展开
const isContentExpanded = (type, index) => {
  const key = `${type}_${index}`
  return expandedContent.value[key] || false
}

// 渲染Markdown
const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked(content, {
      breaks: true,
      gfm: true
    })
  } catch (error) {
    return content
  }
}
</script>

<style scoped>
.optimization-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.suggestion-card {
  padding: 24px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 350px;
  background: white;
  display: flex;
  flex-direction: column;
}

.suggestion-card:hover {
  border-color: #409EFF;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.suggestion-card.selected {
  border-color: #409EFF;
  background: linear-gradient(135deg, #ecf5ff 0%, #e6f3ff 100%);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.25);
}

.card-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 10px;
}

.suggestion-card h3 {
  text-align: center;
  margin: 0;
  font-size: 18px;
  color: #333;
}

.suggestion-item {
  margin-bottom: 20px;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #409EFF;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.item-desc-wrapper {
  margin: 10px 0;
}

.item-desc {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

/* description中的Markdown元素行内显示 */
.item-desc :deep(p) {
  display: inline;
  margin: 0;
}

.item-desc :deep(strong) {
  color: #303133;
  font-weight: 600;
}

.full-content-toggle {
  margin-top: 8px;
}

.full-content-toggle .el-button {
  font-size: 13px;
  padding: 4px 8px;
}

.item-metrics {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #4CAF50;
  margin: 8px 0;
}

.item-metrics strong {
  color: #2e7d32;
}

.item-difficulty {
  font-size: 12px;
  color: #999;
}

.comprehensive-recommendation {
  margin-top: 24px;
  background: linear-gradient(135deg, #f5f9ff 0%, #ecf5ff 100%);
  border: 1px solid #d4e4ff;
}

.comprehensive-recommendation :deep(.el-card__header) {
  background: linear-gradient(135deg, #e8f4ff 0%, #d9ecff 100%);
  border-bottom: 2px solid #409EFF;
}

.recommendation-content {
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

.recommendation-content :deep(h1),
.recommendation-content :deep(h2),
.recommendation-content :deep(h3) {
  color: #303133;
  margin: 16px 0 12px;
  font-weight: 600;
}

.recommendation-content :deep(h1) {
  font-size: 18px;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 8px;
}

.recommendation-content :deep(h2) {
  font-size: 16px;
  color: #409EFF;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
}

.recommendation-content :deep(h3) {
  font-size: 15px;
}

.recommendation-content :deep(strong) {
  color: #409EFF;
  font-weight: 600;
}

.recommendation-content :deep(ol),
.recommendation-content :deep(ul) {
  margin: 12px 0;
  padding-left: 24px;
}

.recommendation-content :deep(li) {
  margin: 8px 0;
  line-height: 1.8;
}

.recommendation-content :deep(p) {
  margin: 12px 0;
  line-height: 1.8;
}

.recommendation-content :deep(code) {
  background: #F5F7FA;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #E6A23C;
}

.recommendation-content :deep(pre) {
  background: #F5F7FA;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.recommendation-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #303133;
}

.recommendation-content :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 16px;
  border-left: 4px solid #409EFF;
  background: #F5F9FF;
  color: #606266;
}

.recommendation-content :deep(a) {
  color: #409EFF;
  text-decoration: none;
}

.recommendation-content :deep(a:hover) {
  text-decoration: underline;
}

.action-buttons {
  margin-top: 24px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}

.full-content {
  margin-top: 12px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  max-height: 600px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.full-content :deep(h1),
.full-content :deep(h2),
.full-content :deep(h3) {
  color: #303133;
  margin: 16px 0 8px;
  font-weight: 600;
}

.full-content :deep(h1) {
  font-size: 18px;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 8px;
}

.full-content :deep(h2) {
  font-size: 16px;
  color: #409EFF;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
}

.full-content :deep(h3) {
  font-size: 15px;
}

.full-content :deep(p) {
  margin: 12px 0;
  color: #606266;
  line-height: 1.8;
}

.full-content :deep(ul),
.full-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.full-content :deep(li) {
  margin: 6px 0;
  color: #606266;
  line-height: 1.8;
}

.full-content :deep(strong) {
  color: #409EFF;
  font-weight: 600;
}

.full-content :deep(code) {
  background: #F5F7FA;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #E6A23C;
}

.full-content :deep(pre) {
  background: #F5F7FA;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.full-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #303133;
}

.full-content :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 16px;
  border-left: 4px solid #409EFF;
  background: #F5F9FF;
  color: #606266;
}

.full-content :deep(a) {
  color: #409EFF;
  text-decoration: none;
}

.full-content :deep(a:hover) {
  text-decoration: underline;
}
</style>
