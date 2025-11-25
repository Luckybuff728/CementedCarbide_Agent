<template>
  <div class="empty-state">
    <!-- <div class="empty-icon"> -->
      <!-- <n-icon :component="RocketOutline" /> -->
    <!-- </div> -->
    <h3 class="empty-title">准备开始分析</h3>
    <p class="empty-description">
      在左侧面板输入涂层参数，点击「开始分析」按钮<br />
      系统将为您提供全面的性能预测和优化建议
    </p>
    <div class="empty-features">
      <div class="feature-item">
        <el-icon color="#2d2d2d"><CheckmarkCircleOutline /></el-icon>
        <span>参数验证与可行性分析</span>
      </div>
      <div class="feature-item">
        <el-icon color="#2d2d2d"><CheckmarkCircleOutline /></el-icon>
        <span>TopPhi相场模拟</span>
      </div>
      <div class="feature-item">
        <el-icon color="#2d2d2d"><CheckmarkCircleOutline /></el-icon>
        <span>ML性能预测与历史对比</span>
      </div>
      <div class="feature-item">
        <el-icon color="#2d2d2d"><CheckmarkCircleOutline /></el-icon>
        <span>智能优化建议与实验工单</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElIcon } from 'element-plus'
import { RocketOutline, CheckmarkCircleOutline } from '@vicons/ionicons5'
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: linear-gradient(135deg, #f8fafb 0%, #ffffff 100%);
  border-radius: 12px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.empty-icon {
  font-size: 80px;
  color: #10a37f;
  margin-bottom: 24px;
  opacity: 0.9;
}

.empty-title {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 600;
  color: #0d0d0d;
}

.empty-description {
  margin: 0 0 32px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.empty-features {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 340px;
  margin: 0 auto;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  font-size: 13px;
  color: #0d0d0d;
  transition: all 0.2s;
}

.feature-item:hover {
  border-color: #2d2d2d;
  background: rgba(0, 0, 0, 0.02);
  transform: translateX(4px);
}

.feature-item .el-icon {
  font-size: 18px;
  flex-shrink: 0;
}
</style>
