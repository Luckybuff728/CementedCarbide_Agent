# TopMat Agent 前端

基于 Vue 3 + Vite + Element Plus 的现代化前端界面

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Element Plus** - Vue 3 UI 组件库
- **Pinia** - Vue 状态管理
- **WebSocket** - 实时通信

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

前端将运行在 http://localhost:3000

### 生产构建

```bash
npm run build
```

构建输出在 `dist` 目录

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── components/         # Vue 组件
│   │   ├── CoatingInputForm.vue        # 输入表单
│   │   ├── PredictionResults.vue       # 预测结果
│   │   ├── OptimizationSuggestions.vue # 优化建议
│   │   └── IterationProgress.vue       # 迭代进度
│   ├── composables/        # 组合式函数
│   │   └── useWebSocket.js # WebSocket 封装
│   ├── App.vue            # 根组件
│   ├── main.js            # 入口文件
│   └── style.css          # 全局样式
├── index.html             # HTML 模板
├── vite.config.js         # Vite 配置
└── package.json           # 项目配置

## 核心功能

### 1. 实时通信
- WebSocket 连接管理
- 自动重连机制
- 流式数据接收

### 2. 交互式界面
- 模板化表单输入
- 实时状态更新
- 可视化结果展示

### 3. 优化建议
- 三类优化方案对比
- 交互式方案选择
- 详细参数说明

### 4. 迭代追踪
- 时间线展示
- 性能对比
- 收敛判断

## API 配置

后端 API 代理配置在 `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  },
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true
  }
}
```

## 开发说明

### 添加新组件

1. 在 `src/components/` 创建 `.vue` 文件
2. 在 `App.vue` 中导入并使用

### 修改主题

在 `src/style.css` 中修改 CSS 变量:

```css
:root {
  --el-color-primary: #4CAF50;
  /* 其他主题颜色 */
}
```

### WebSocket 事件处理

在 `App.vue` 的 `handleWebSocketMessage` 函数中添加新的事件类型处理。

## 部署

### 开发环境

前端和后端需要同时运行:
- 后端: http://localhost:8000
- 前端: http://localhost:3000

### 生产环境

构建前端并部署到静态文件服务器，或与后端集成:

```bash
npm run build
# 将 dist/ 目录内容部署到 Web 服务器
```

## 浏览器兼容性

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 许可证

MIT
