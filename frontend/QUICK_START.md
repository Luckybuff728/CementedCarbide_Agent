# 🚀 快速启动指南

## 📦 已完成的工作

### ✅ 核心架构
- [x] Vue 3 + Vite 项目初始化
- [x] Element Plus UI组件库集成
- [x] Pinia 状态管理配置
- [x] WebSocket 通信封装
- [x] Markdown 渲染工具
- [x] 设计系统（色彩、间距、圆角）

### ✅ 组件结构
```
App.vue (主应用)
├── StatusBar (顶部状态栏 - 节点跳转)
├── LeftPanel (左侧表单 - 参数输入)
├── CenterPanel (中间流程 - 分析展示)
│   └── ProcessCard (流程卡片 - 可展开/收起)
└── RightPanel (右侧摘要 - 结果展示)
    └── SummaryCard (摘要卡片)
```

### ✅ 状态管理 (Pinia Store)
- `workflowStore`: 工作流状态、节点数据、分析结果
- 响应式更新、自动折叠、数据持久化

### ✅ 通信机制
- WebSocket 实时通信
- 支持流式输出（LLM）
- 节点状态同步
- 错误处理

## 🏃 立即运行

### 1. 启动后端服务
```bash
cd d:\Agent\TopMat_Agent_1.0
python run.py
```

### 2. 启动前端（新版）
```bash
cd frontend_new
npm run dev
```

浏览器访问: http://localhost:5173

## 🎯 核心功能演示

### 三段式布局
```
┌────────────────────────────────────┐
│ [●●●○○] 验证 TopPhi ML ... [导出]  │  ← 顶部状态栏
├────────┬──────────────┬─────────────┤
│ 表单   │ 分析过程展示  │ 任务摘要    │
│ [成分] │ ✅ 参数验证   │ 🎯 性能预测 │
│ [工艺] │ 🔬 TopPhi    │ 📊 历史对比 │
│ [结构] │ 🎯 ML预测    │ 💡 优化方案 │
│ [需求] │ (可展开/收起) │ [选择P1/P2] │
│ [提交] │              │             │
└────────┴──────────────┴─────────────┘
```

### 节点跳转
点击顶部状态栏的节点 → 中间面板自动滚动到对应卡片

### 卡片控制
- 单击卡片标题 → 展开/收起
- 全部展开/全部收起按钮
- 自动收起已完成的节点

### 流式显示
实时渲染LLM输出，Markdown格式化展示

## 🔧 下一步工作

### 优先级1：完善表单
从旧版 `frontend/src/components/CoatingForm.vue` 复制完整表单逻辑到 `LeftPanel.vue`

**关键字段：**
- 涂层成分（Al/Ti/N + 其他元素）
- 工艺参数（温度/气压/偏压/气体流量）
- 结构设计（单层/多层/梯度）
- 性能需求（基体/硬度/结合力）

### 优先级2：优化中间面板
**ProcessCard 增强：**
- 数据可视化（图表）
- 更详细的节点内容生成
- 复制/导出单个节点功能

### 优先级3：完善右侧面板
**RightPanel 扩展：**
- 历史对比摘要卡片
- 根因分析摘要卡片
- 实验工单展示和下载
- 点击卡片跳转到对应节点

### 优先级4：动画和交互
- 卡片展开/收起动画
- 节点切换过渡效果
- 加载状态指示器
- 键盘快捷键（如：Space展开/收起）

## 📝 开发建议

### 调试技巧
```javascript
// 在 App.vue 中查看 WebSocket 消息
console.log('[WS消息]', message.type)

// 在 Store 中查看状态变化
console.log('当前节点:', workflowStore.currentNode)
console.log('流程步骤:', workflowStore.processSteps)
```

### 组件开发规范
1. **单一职责**：每个组件只做一件事
2. **Props验证**：使用TypeScript或PropTypes
3. **事件命名**：使用kebab-case（如：`jump-to-node`）
4. **样式隔离**：使用scoped CSS
5. **中文注释**：关键逻辑必须注释

### 常见问题

**Q: WebSocket连接失败？**
A: 确保后端服务已启动（python run.py），检查URL是否为 `ws://localhost:8000/ws/coating`

**Q: 组件不显示？**
A: 检查Store中的数据是否正确更新，使用Vue DevTools调试

**Q: 样式不生效？**
A: 检查是否使用了scoped，CSS变量是否正确引用（如：`var(--primary)`）

**Q: 流式输出卡顿？**
A: 考虑使用防抖（debounce）或限制更新频率

## 🎨 设计资源

### 色彩参考
- 主色: `#3b82f6` - 用于主按钮、链接
- 成功: `#10b981` - 用于完成状态
- 警告: `#f59e0b` - 用于进行中状态
- 危险: `#ef4444` - 用于错误状态

### 图标建议
使用Emoji或Element Plus图标：
- ✅ 验证完成
- 🔬 科学计算
- 🎯 目标/预测
- 📊 数据/图表
- 🧠 分析/智能
- 💡 建议/创意
- 📝 文档/工单

## 📞 需要帮助？

参考文档：
- `README_PROJECT.md` - 项目详细说明
- 旧版前端代码 `frontend/src/` - 参考实现
- 后端API `src/api/routes/` - 接口定义

---

**开始开发前，建议先运行一次确保基础架构正常工作！**
