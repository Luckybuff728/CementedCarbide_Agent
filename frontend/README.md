# TopMat Agent 前端

基于 Vue 3 + Vite 的现代化材料优化系统前端界面。

## 🚀 快速开始

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本
```bash
npm run build
```

## ⚙️ 配置

### 环境变量（可选）

创建 `.env` 文件配置后端地址：

```bash
# 后端API地址
VITE_API_BASE_URL=http://localhost:8000

# WebSocket地址
VITE_WS_BASE_URL=ws://localhost:8000
```

> 默认配置已经指向 `localhost:8000`，通常无需修改。

### 配置文件

所有配置统一在 `src/config/index.js` 中管理：
- API端点
- WebSocket端点
- 应用配置

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/              # Vue组件
│   │   ├── layout/              # 布局与主界面组件
│   │   │   ├── StatusBar.vue                    # 状态栏
│   │   │   ├── LeftPanel.vue                    # 左侧参数输入面板
│   │   │   ├── CenterPanel.vue                  # 中间流程可视化
│   │   │   ├── RightPanel.vue                   # 右侧结果展示
│   │   │   ├── ProcessCard.vue                  # 流程卡片
│   │   │   └── ErrorBoundary.vue                # 错误边界
│   │   ├── cards/               # 结果卡片组件
│   │   │   ├── result/                          # 结果展示卡片
│   │   │   │   ├── HistoricalComparisonCard.vue    # 历史对比
│   │   │   │   ├── IntegratedAnalysisCard.vue      # 综合分析
│   │   │   │   ├── OptimizationSuggestionsCard.vue # 优化建议
│   │   │   │   └── WorkorderSummaryCard.vue        # 工单摘要
│   │   │   ├── EmptyStateCard.vue                  # 空状态卡片
│   │   │   ├── OptimizationSelector.vue            # 优化方案选择器
│   │   │   ├── PerformancePredictionCard.vue       # 性能预测
│   │   │   ├── TopPhiResultCard.vue                # TopPhi结果
│   │   │   └── ValidationSummaryCard.vue           # 验证摘要
│   │   ├── forms/               # 输入表单组件
│   │   │   ├── CompositionForm.vue                 # 成分配比
│   │   │   ├── PerformanceRequirementsForm.vue     # 性能需求
│   │   │   ├── ProcessParametersForm.vue           # 工艺参数
│   │   │   └── StructureDesignForm.vue             # 结构设计
│   │   ├── experiment/          # 实验与迭代相关组件
│   │   │   ├── ExperimentInputCard.vue             # 实验输入卡片
│   │   │   ├── IterationHistoryPanel.vue           # 迭代历史面板
│   │   │   └── PerformanceComparisonChart.vue      # 性能对比图
│   │   ├── common/              # 通用基础组件
│   │   │   ├── SummaryCard.vue                     # 基础摘要卡片
│   │   │   └── MarkdownRenderer.vue                # Markdown渲染器
│   │   └── viz/                 # VTK 可视化组件
│   │       ├── VtkViewer.vue                       # VTK 3D可视化（单帧）
│   │       └── VtkTimeSeriesViewer.vue             # VTK时间序列播放器
│   ├── composables/             # 组合式函数
│   │   ├── useWebSocket.js      # WebSocket连接管理
│   │   ├── useWorkflowHandler.js # 工作流数据处理
│   │   └── useNotification.js   # 通知管理
│   ├── stores/                  # Pinia状态管理
│   │   └── workflow.js          # 工作流状态
│   ├── config/                  # 配置文件
│   │   └── index.js             # API配置
│   ├── utils/                   # 工具函数
│   │   └── pdfExporter.js       # PDF导出工具
│   ├── assets/                  # 静态资源
│   ├── App.vue                  # 主应用组件
│   ├── main.js                  # 入口文件
│   └── style.css                # 全局样式
├── public/                      # 公共资源
├── .env                         # 环境变量（可选）
├── vite.config.js               # Vite配置
├── package.json                 # 依赖配置
└── README.md                    # 项目说明
```

## 🛠️ 技术栈

- **框架**: Vue 3 (Composition API)
- **构建**: Vite
- **UI库**: Element Plus + Naive UI
- **状态**: Pinia
- **可视化**: VTK.js
- **样式**: CSS

## 📝 开发说明

### 添加新组件
在 `src/components/` 目录下创建 `.vue` 文件。

### 修改API地址
编辑 `src/config/index.js` 或创建 `.env` 文件。

### WebSocket连接
通过 `useWebSocket` composable 管理连接，已自动处理重连。

## 🔧 可用命令

| 命令 | 说明 |
|------|------|
| `npm install` | 安装依赖 |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |

## 🐛 常见问题

**Q: 无法连接后端？**  
A: 检查后端服务是否启动（http://localhost:8000），确认 `src/config/index.js` 中的URL配置正确。

**Q: 端口被占用？**  
A: 修改 `vite.config.js` 中的 `server.port` 配置。

**Q: 热重载不工作？**  
A: 重启开发服务器，清除浏览器缓存。

---

返回[主项目文档](../README.md)
