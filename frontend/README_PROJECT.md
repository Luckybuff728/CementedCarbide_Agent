# TopMat Agent 前端重构项目

## 🎯 项目概述

基于设计方案重新构建的TopMat Agent前端应用，采用Vue 3 + Vite + Element Plus技术栈，实现了现代化的三段式布局。

## 📁 项目结构

```
frontend_new/
├── src/
│   ├── components/          # 组件目录
│   │   ├── StatusBar.vue    # 顶部状态栏（进度指示+节点跳转）
│   │   ├── LeftPanel.vue    # 左侧参数输入面板
│   │   ├── CenterPanel.vue  # 中间分析过程展示
│   │   ├── ProcessCard.vue  # 流程卡片组件（可展开/收起）
│   │   ├── RightPanel.vue   # 右侧任务摘要面板
│   │   └── SummaryCard.vue  # 摘要卡片通用组件
│   ├── composables/         # 组合式函数
│   │   └── useWebSocket.js  # WebSocket通信逻辑
│   ├── stores/              # Pinia状态管理
│   │   └── workflow.js      # 工作流状态Store
│   ├── utils/               # 工具函数
│   │   └── markdown.js      # Markdown渲染和格式化工具
│   ├── App.vue              # 主应用组件
│   ├── main.js              # 应用入口
│   └── style.css            # 全局样式
├── package.json
└── vite.config.js
```

## 🚀 核心功能

### 1. 三段式布局
- **左侧(320px)**: 参数输入表单
- **中间(flex)**: 分析过程流式展示，支持卡片展开/收起
- **右侧(380px)**: 任务摘要和结果展示

### 2. 顶部状态栏
- 实时显示工作流进度
- 点击节点快速跳转到对应分析卡片
- 导出/清空等操作按钮

### 3. 中间流程卡片
- **流式渲染**: 实时显示LLM输出
- **可展开/收起**: 单个卡片或全部控制
- **自动滚动**: 新节点开始时自动滚动到视图
- **Markdown渲染**: 美化显示分析内容

### 4. 右侧摘要面板
- 性能预测摘要卡片
- 历史对比摘要卡片
- 优化方案选择界面
- 实验工单展示

### 5. 状态管理 (Pinia)
- 集中管理工作流状态
- 响应式数据更新
- 支持时间旅行调试

## 🛠️ 技术栈

- **Vue 3**: Composition API
- **Vite**: 极速构建工具
- **Element Plus**: UI组件库
- **Pinia**: 状态管理
- **markdown-it**: Markdown渲染
- **WebSocket**: 实时通信

## 📦 安装和运行

### 安装依赖
```bash
cd frontend_new
npm install
```

### 开发模式
```bash
npm run dev
```

### 生产构建
```bash
npm run build
```

### 预览构建结果
```bash
npm run preview
```

## 🔧 配置

### WebSocket连接
默认连接到 `ws://localhost:8000/ws/coating`

如需修改，编辑 `src/App.vue` 中的连接地址：
```javascript
onMounted(() => {
  connect('ws://localhost:8000/ws/coating', handleWebSocketMessage)
})
```

## 📋 待完善功能

### 高优先级
1. ✅ 核心架构和状态管理
2. ✅ WebSocket通信
3. ✅ 基础组件结构
4. ⏳ 完善LeftPanel表单（参考旧版CoatingForm.vue）
5. ⏳ 优化ProcessCard的数据可视化
6. ⏳ 完善RightPanel的各类摘要卡片

### 中优先级
1. ⏳ 添加动画效果（卡片展开/收起、节点切换）
2. ⏳ 键盘快捷键支持
3. ⏳ 导出功能实现
4. ⏳ 响应式布局优化

### 低优先级
1. ⏳ 主题切换（深色模式）
2. ⏳ 国际化支持
3. ⏳ 性能优化（虚拟滚动）

## 🎨 设计规范

### 色彩系统
- 主色: `#3b82f6` (蓝色)
- 成功: `#10b981` (绿色)
- 警告: `#f59e0b` (橙色)
- 错误: `#ef4444` (红色)
- 背景: `#f9fafb` (浅灰)

### 间距
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px

### 圆角
- sm: 8px
- md: 12px
- lg: 16px

## 📝 开发建议

### 组件开发
1. 保持组件单一职责
2. 使用 Composition API
3. Props和Emits明确定义
4. 适当添加中文注释

### 状态管理
1. 所有共享状态放在Store中
2. 局部状态使用ref/reactive
3. 避免直接修改Store，使用actions

### 样式规范
1. 使用scoped避免污染
2. 遵循BEM命名规范
3. 复用设计系统变量

## 🔗 相关资源

- [Vue 3 文档](https://cn.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/zh-CN/)
- [Pinia 文档](https://pinia.vuejs.org/zh/)
- [Vite 文档](https://cn.vitejs.dev/)

## 📞 联系方式

如有问题，请参考设计方案文档或联系开发团队。
