# TopMat Agent - 硬质合金涂层智能优化系统

## 📋 项目简介

TopMat Agent 是一个基于 **LangGraph** 的智能材料优化系统，专注于硬质合金涂层的成分设计、结构优化和工艺改进。系统采用先进的 AI 技术和流式交互设计，为材料研发提供实时、智能的决策支持。

### ✨ 核心特点

- 🐳 **一键部署**: Docker整合前后端，30秒启动完整系统
- 🔬 **专业领域**: 专注硬质合金涂层优化，提供精准建议
- 🤖 **AI驱动**: 集成qwen大模型，智能分析预测
- 📊 **实时交互**: WebSocket流式输出，打字机效果展示
- 🔄 **迭代优化**: 支持多轮实验闭环，持续改进性能
- 💡 **多维分析**: 成分/结构/工艺三维度优化建议

## 🚀 快速开始

### 0. 获取代码

```bash
git clone http://192.168.6.104:3000/TangBin/TopMat_Agent.git
cd TopMat_Agent
```

### 方式一：Docker生产环境部署（⭐推荐）

**前后端分离架构，镜像体积优化82%，适合生产环境！**

#### 📦 前置要求
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 20.10+
- Docker Compose 2.0+

#### 🎯 快速启动

**1. 配置API密钥**

编辑 `.env` 文件：
```bash
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL_NAME=qwen-plus
```

**2. 构建并启动**
```bash
docker-compose build
docker-compose up -d
```

**3. 访问系统**

启动完成后，在浏览器打开：
- 🌐 **前端界面**: http://localhost
- 📚 **API文档**: http://localhost/api/docs
- 💚 **健康检查**: http://localhost/health

#### 📖 生产环境文档
- 📘 **详细部署指南**: `PRODUCTION_DEPLOY.md`
- 📊 **镜像优化**: 从2.5GB降至450MB（减少82%）
- 🔒 **安全加固**: 非root用户、健康检查、资源限制

```

### 方式二：本地开发部署

#### 环境要求
- Python 3.11+
- Node.js 18+

#### 安装步骤

**1. 安装Python依赖**
```bash
pip install -r requirements.txt
```

**2. 配置环境变量**
```bash
copy .env.example .env
# 编辑 .env 文件，填入API密钥
```

**3. 安装前端依赖**
```bash
cd frontend
npm install
```

**4. 启动后端（终端1）**
```bash
python run.py
# 选择选项 1: FastAPI后端服务
```

**5. 启动前端（终端2）**
```bash
cd frontend
npm run dev
```

**6. 访问应用**
- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

## 📖 使用指南

### 工作流程

1. **输入参数**: 填写涂层成分、工艺参数、结构设计
2. **性能预测**: 系统实时分析，给出性能预测和根因分析
3. **优化建议**: 获得P1(成分)、P2(结构)、P3(工艺)三类优化方案
4. **实验验证**: 选择方案进行实验，输入结果
5. **迭代优化**: 系统分析实验结果，决定下一步行动

### 界面特性

- 💬 **流式对话**: 实时显示AI分析过程，打字机效果
- 📊 **分步展示**: 各节点结果独立卡片显示，清晰明了
- 🎨 **Markdown渲染**: 支持表格、列表、代码块等丰富格式
- 🔄 **热重载**: Docker环境支持代码修改自动生效
- 💾 **会话管理**: 支持多会话管理和历史记录

### 详细文档
- 📘 **生产部署**: `PRODUCTION_DEPLOY.md`（推荐）
- 📘 **开发环境**: `DOCKER_README.md`

## 🏗️ 系统架构

### 生产环境架构（当前配置）
```
┌──────────────────────────────────────────────┐
│              Docker Network                  │
│                                              │
│  ┌─────────────────┐    ┌────────────────┐  │
│  │  Frontend       │    │  Backend       │  │
│  │  Container      │    │  Container     │  │
│  │                 │    │                │  │
│  │  Nginx:80       │───▶│  FastAPI:8000  │  │
│  │  (50MB镜像)     │    │  (400MB镜像)   │  │
│  │                 │    │                │  │
│  │  - 静态资源     │    │  - LangGraph   │  │
│  │  - Gzip压缩     │    │  - 4 Workers   │  │
│  │  - 反向代理     │    │  - 健康检查    │  │
│  │  - 缓存优化     │    │  - 非root用户  │  │
│  └─────────────────┘    └────────────────┘  │
│          ↓                                   │
└──────────────────────────────────────────────┘
           ↓
     localhost:80
```

**生产环境特点**：
- ✅ 前后端分离，独立扩展
- ✅ 镜像体积优化82%（450MB vs 2.5GB）
- ✅ 多阶段构建，安全加固
- ✅ 资源限制和健康检查
- ✅ 适合生产部署

### 项目结构
```
TopMat_Agent_1.0/
├── frontend/           # Vue 3 前端
│   ├── src/
│   │   ├── components/ # 表单、结果展示等组件
│   │   ├── composables/# WebSocket、状态管理
│   │   └── App.vue     # 主应用
│   └── package.json    # 前端依赖
├── src/
│   ├── api/            # FastAPI后端服务
│   ├── graph/          # LangGraph工作流定义
│   │   ├── workflow.py # 工作流编排
│   │   ├── nodes.py    # 节点实现
│   │   └── state.py    # 状态定义
│   ├── llm/            # LLM配置和提示词
│   └── models/         # 数据模型
├── Dockerfile          # Docker镜像定义
├── docker-compose.yml  # Docker编排配置
├── docker_run.py       # Docker启动脚本
├── requirements.txt    # Python依赖
└── .env.example        # 环境变量模板
```

### 技术栈

#### 前端
- **框架**: Vue 3 + Composition API
- **UI库**: Element Plus
- **构建**: Vite
- **通信**: WebSocket (原生)
- **渲染**: Markdown (marked)

#### 后端
- **框架**: FastAPI
- **工作流**: LangGraph
- **LLM**: DeepSeek / 阿里云百炼
- **异步**: asyncio

#### 部署
- **容器化**: Docker + Docker Compose
- **开发模式**: 热重载支持
- **端口**: 5173 (前端), 8000 (后端)

## 🔧 工作流节点

系统采用LangGraph构建多节点工作流：

1. **input_validation** - 输入参数验证
2. **topphi_simulation** - TopPhi第一性原理模拟
3. **ml_prediction** - 机器学习模型预测
4. **historical_comparison** - 历史数据比对
5. **integrated_analysis** - 综合分析与根因
6. **p1_composition_optimization** - 成分优化建议
7. **p2_structure_optimization** - 结构优化建议
8. **p3_process_optimization** - 工艺优化建议
9. **optimization_summary** - 优化方案汇总
10. **experiment_workorder_generation** - 实验工单生成
11. **experiment_result_analysis** - 实验结果分析
12. **decide_next_iteration** - 迭代决策

### API接口

访问 `http://localhost:8000/docs` 查看完整的 Swagger API 文档。

主要接口：
- **WebSocket**: `/ws` - 实时双向通信
- **POST**: 提交参数、选择方案、输入实验结果

## 🎯 核心功能

### 1. 智能分析
- ✅ 多源数据融合（TopPhi模拟 + ML预测 + 历史数据）
- ✅ 根因分析，解释性能背后的物理机制
- ✅ 流式输出，实时展示分析过程

### 2. 三维优化
- ✅ **P1 成分优化**: 调整元素配比、添加微量元素
- ✅ **P2 结构优化**: 多层/梯度/纳米复合结构设计
- ✅ **P3 工艺优化**: 温度/气压/偏压等参数调整

### 3. 实验闭环
- ✅ 生成详细实验工单
- ✅ 输入实验结果
- ✅ 智能决策下一步行动（完成/继续/尝试其他）

### 4. 会话管理
- ✅ 多会话支持
- ✅ 会话重命名、删除
- ✅ 历史记录保存（LocalStorage）

## 📝 开发计划

**已完成**
- [x] LangGraph工作流引擎
- [x] Vue 3 现代化前端
- [x] WebSocket实时通信
- [x] 流式输出优化
- [x] Docker一键部署
- [x] 会话管理系统

**规划中**
- [ ] TopPhi/ML模型真实接入（当前为模拟数据）
- [ ] 数据库持久化
- [ ] 用户认证系统
- [ ] 生产环境优化
- [ ] 更多材料体系支持

## 🐛 故障排查

### Docker相关
查看容器日志：
```bash
docker-compose logs -f
```
### 本地开发
后端日志会实时输出到控制台，前端问题请检查浏览器控制台。

详细故障排查见 `DOCKER_README.md`。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

