# TopMat Agent - 硬质合金涂层优化专家系统

## 📋 项目概述

TopMat Agent 是一个基于 LangGraph 的智能材料优化系统，专注于硬质合金涂层的成分开发、结构设计和工艺优化。系统采用先进的 AI 技术，为材料研发提供智能化的决策支持。

### 核心特点

- 🔬 **专业性**: 专注于硬质合金涂层领域，提供专业的优化建议
- 🤖 **智能化**: 集成阿里云百炼大模型，提供智能分析和预测
- 🔄 **迭代优化**: 支持多轮迭代优化，持续改进涂层性能
- 📊 **实时反馈**: 流式输出和WebSocket通信，提供实时状态更新
- 📈 **数据驱动**: 基于历史数据和机器学习模型进行性能预测
- 💬 **对话式交互**: ChatGPT 风格的对话界面，自然流畅的交互体验

## 🚀 快速开始

### 环境要求

**后端：**
- Python 3.9+
- pip 或 conda 包管理器

**前端（推荐）：**
- Node.js 16+
- npm 或 yarn

### 安装步骤

#### 方案一：Vue 3 前端（推荐 ⭐ - ChatGPT 风格界面）

**快速启动（推荐）**
```bash
# 1. 一键安装前端依赖
setup_chat_ui.bat

# 2. 启动后端（终端1）
python run.py
# 选择选项 3 (仅FastAPI后端)

# 3. 启动前端（终端2）
start_vue.bat
```

**手动安装**

**1. 安装后端依赖**
```bash
cd d:\Agent\TopMat_Agent_1.0
pip install -r requirements.txt
```

**2. 配置环境变量**
```bash
# 复制环境变量模板
copy .env.example .env
# 编辑 .env 文件，填入阿里云百炼API密钥
```

**3. 安装前端依赖**
```bash
cd frontend
npm install
```

**4. 启动服务**
```bash
# 终端 1: 启动后端
python run.py
# 选择选项 3 (仅FastAPI后端)

# 终端 2: 启动前端
cd frontend
npm run dev
```

**5. 访问应用**
- 前端界面: http://localhost:5173 （ChatGPT 风格对话界面）
- API 文档: http://localhost:8000/docs

> 💡 **新界面特性**: 
> - ChatGPT 风格的对话式交互
> - 实时流式输出，打字机效果
> - Markdown 渲染，内容展示更清晰
> - 快捷参数设置，简化操作流程
> - 详细使用说明见 `CHATGPT_UI_GUIDE.md`

#### 方案二：Streamlit 前端（快速原型）

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env

# 运行
python run.py
# 选择选项 2 (仅Streamlit)
```

### 演示模式

快速体验系统功能：

```bash
python run.py demo
```

## 📖 使用指南

### Vue 3 对话式界面（推荐）

**快速开始**
1. 在欢迎界面点击示例提示卡片快速开始
2. 或在底部输入框描述您的涂层需求
3. 点击⚙️按钮设置详细参数（可选）
4. 按 Enter 发送，Shift+Enter 换行

**对话流程**
- **需求分析**: AI 理解并提取您的需求
- **性能预测**: 实时流式显示预测结果和根因分析
- **优化建议**: 展示 P1/P2/P3 三类优化方案
- **迭代优化**: 持续改进直到达到目标

**界面特性**
- 💬 类似 ChatGPT 的对话体验
- ⚡ 实时流式输出，打字机效果
- 📝 Markdown 格式渲染
- 📊 性能数据卡片化展示
- 🎯 快捷参数面板
- 🔄 节点独立显示，内容不覆盖

> 📘 详细使用说明：`CHATGPT_UI_GUIDE.md`  
> 🔧 流式优化方案：`STREAMING_OPTIMIZATION.md`

### Streamlit 界面（备选）

**1. 需求提取**

在 Streamlit 界面的"需求提取"标签页中输入：

- **涂层成分**: Al、Ti、N 及可选 X 元素的含量
- **工艺参数**: 沉积气压、气体流量、偏压、温度等
- **结构设计**: 涂层厚度、层数结构
- **目标需求**: 应用场景和性能要求描述

**2. 性能预测**

系统自动预测涂层性能：

- 硬度预测 (GPa)
- 结合力等级
- 耐磨性评估
- 抗氧化温度
- 微观结构特征

**3. 优化建议**

系统提供三类优化方案：

- **P1 - 成分优化**: 调整元素配比
- **P2 - 结构优化**: 多层或梯度结构设计
- **P3 - 工艺优化**: 参数调整建议

**4. 迭代优化**

- 选择优化方案
- 输入实验验证结果
- 系统自动分析并推荐下一步优化方向
- 达到收敛条件后生成最终报告

## 🏗️ 系统架构

### 项目结构
```
TopMat_Agent_1.0/
├── frontend/           # Vue 3 前端
│   ├── src/
│   │   ├── components/ # Vue 组件
│   │   ├── composables/# 组合式函数
│   │   ├── App.vue     # 根组件
│   │   └── main.js     # 入口文件
│   ├── vite.config.js  # Vite 配置
│   └── package.json    # 前端依赖
├── src/
│   ├── models/         # 数据模型定义
│   ├── graph/          # LangGraph工作流
│   ├── llm/            # LLM配置和集成
│   └── api/            # FastAPI后端服务
├── tests/              # 测试用例
├── docs/               # 文档资料
├── streamlit_app.py    # Streamlit前端（备选）
├── run.py              # 主运行脚本
├── requirements.txt    # Python依赖
└── .env.example        # 环境变量模板
```

### 技术架构图
```
┌─────────────────────────────────────┐
│  Vue 3 前端 (Port 5173)              │
│  ┌──────────────────────────────┐   │
│  │  ChatGPT 风格对话界面         │   │
│  │  - 流式消息展示               │   │
│  │  - Markdown 渲染              │   │
│  │  - 快捷参数设置               │   │
│  │  - WebSocket 实时通信         │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
            ↕ WebSocket/HTTP
┌─────────────────────────────────────┐
│  FastAPI 后端 (Port 8000)            │
│  ┌──────────────────────────────┐   │
│  │  LangGraph 工作流引擎         │   │
│  │  ├─ 需求提取                 │   │
│  │  ├─ 性能预测                 │   │
│  │  ├─ 优化建议                 │   │
│  │  └─ 迭代优化                 │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
            ↕ API
┌─────────────────────────────────────┐
│  阿里云百炼 LLM                      │
│  - 材料专家分析                      │
│  - 优化建议生成                      │
│  - 根因分析                         │
└─────────────────────────────────────┘
```

## 🔧 API 接口

### REST API

- `POST /api/coating/submit` - 提交涂层优化任务
- `GET /api/coating/task/{task_id}` - 获取任务状态
- `POST /api/coating/optimize` - 请求优化建议
- `POST /api/coating/iterate` - 执行迭代优化

### WebSocket

- `/ws/coating/{task_id}` - 实时任务状态更新

访问 `http://localhost:8000/docs` 查看完整的 API 文档。

## 🧪 测试

运行测试套件：

```bash
pytest tests/ -v
```

或通过主脚本运行：

```bash
python run.py
# 选择选项 4
```

## 🎯 技术特性

### 前端技术 (Vue 3)

- **现代化框架**: Vue 3 + Composition API
- **UI 组件库**: Element Plus 完整组件
- **实时通信**: WebSocket 原生支持，自动重连
- **状态管理**: 响应式状态管理
- **流式展示**: 平滑的实时数据更新，打字机效果
- **Markdown 渲染**: marked 库支持完整 Markdown 语法
- **对话式交互**: ChatGPT 风格的对话界面设计

**为什么选择 Vue 3？**
- ✅ 与 LangGraph 异步流式输出完美配合
- ✅ 无需页面刷新，用户体验流畅
- ✅ 组件化开发，易于维护和扩展
- ✅ 性能优异，虚拟 DOM 高效渲染
- ✅ ChatGPT 风格界面，专注内容展示

### LangGraph 工作流

- **状态管理**: 使用 TypedDict 定义工作流状态
- **节点设计**: 模块化的处理节点（验证、预测、优化等）
- **条件路由**: 基于状态的智能路由决策
- **内存存储**: 支持历史数据和知识积累

### 流式处理

- 支持多种流模式（updates、messages、custom）
- WebSocket 实时通信
- 异步任务处理
- 前端平滑展示

### 性能优化

- 结果缓存机制
- 并行任务处理
- 批量预测优化
- 前端按需渲染

## 📝 开发计划

- [x] 基础框架搭建
- [x] LangGraph 工作流实现
- [x] 阿里云百炼集成
- [x] Streamlit UI 界面（原型）
- [x] Vue 3 现代化前端
- [x] WebSocket 实时通信
- [x] 流式输出展示
- [x] ChatGPT 风格对话界面（推荐）
- [x] Markdown 内容渲染
- [x] 流式输出优化（节点独立、内容累积）
- [ ] 对话历史保存
- [ ] 性能预测模型集成（预留接口）
- [ ] 数据库持久化
- [ ] 用户认证系统
- [ ] 生产部署优化
- [ ] 更多材料体系支持

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m '添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至：topmat-support@example.com

## 🙏 致谢

- LangChain 和 LangGraph 团队
- 阿里云百炼平台
- 所有贡献者和用户

---

**TopMat Agent** - 打通产品研发-生产链条，在核心场景提供独有价值！
