# TopMat Agent 前端

对话式多 Agent 智能研发助手 - Vue 3 前端界面

## 🚀 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

访问 http://localhost:5173

## 📁 项目结构

```
src/
├── views/                       # 页面视图
│   └── MultiAgentView.vue       # 主视图（三栏布局）
├── components/                  # 组件（5个目录）
│   ├── panels/                  # 面板组件
│   │   ├── LoginPanel.vue       # 登录面板
│   │   ├── LeftPanel.vue        # 左侧参数输入
│   │   ├── ChatPanel.vue        # 中间对话面板
│   │   └── ResultsPanel.vue     # 右侧结果展示
│   ├── cards/                   # 卡片组件
│   │   ├── PerformancePredictionCard.vue
│   │   ├── TopPhiResultCard.vue
│   │   ├── IntegratedAnalysisCard.vue
│   │   ├── OptimizationPlansCard.vue
│   │   └── WorkorderDownloadCard.vue
│   ├── forms/                   # 表单组件
│   │   ├── CompositionForm.vue
│   │   ├── ProcessParametersForm.vue
│   │   ├── StructureDesignForm.vue
│   │   └── PerformanceRequirementsForm.vue
│   ├── experiment/              # 实验组件
│   │   ├── ExperimentInputCard.vue
│   │   └── PerformanceComparisonChart.vue
│   └── common/                  # 通用组件
│       ├── MarkdownRenderer.vue
│       ├── SummaryCard.vue
│       └── VtkTimeSeriesViewer.vue
├── composables/                 # 组合式函数
│   ├── useMultiAgent.js         # 多Agent对话系统
│   ├── useWebSocket.js          # WebSocket管理
│   ├── useResizeObserver.js     # 尺寸监听
│   └── useVtkTimeSeriesHelpers.js
├── stores/                      # Pinia状态
│   ├── auth.js                  # 认证状态
│   └── workflow.js              # 工作流状态
├── config/
│   └── index.js                 # API配置
├── utils/
│   ├── markdown.js
│   └── pdfExporter.js
├── App.vue
├── main.js
└── style.css
```

## 🛠️ 技术栈

| 类型 | 技术 |
|-----|------|
| 框架 | Vue 3 (Composition API) |
| 构建 | Vite |
| UI | Element Plus |
| 状态 | Pinia |
| 可视化 | VTK.js |

## ⚙️ 配置

编辑 `src/config/index.js` 或创建 `.env` 文件：

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## 🔧 命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 开发服务器 |
| `npm run build` | 生产构建 |
| `npm run preview` | 预览构建 |

---

返回 [主项目文档](../README.md)
