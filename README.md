# TopMat Agent - 硬质合金涂层智能优化系统

## 📋 项目简介

TopMat Agent 是一个基于 **LangGraph** 的智能涂层优化系统，专注于硬质合金涂层的成分设计、结构优化和工艺改进。集成阿里云百炼大模型，为材料研发提供实时、智能的决策支持。

### ✨ 核心特点

- 🤖 **AI驱动**: 集成阿里云百炼Qwen大模型，智能分析预测
- 📊 **实时交互**: WebSocket流式输出，即时反馈分析过程
- 🔄 **迭代优化**: 支持多轮实验闭环，持续改进性能
- 💡 **三维优化**: 成分/结构/工艺三个维度的优化建议
- 🎨 **现代化界面**: Vue 3 + Element Plus，直观易用
- 📈 **VTK可视化**: TopPhi模拟结果3D可视化展示

## 🚀 快速开始

### 0. 获取代码

```bash
git clone http://192.168.6.104:3000/TopMaterial_Agent/CementedCarbide_Agent/src/branch/TangBin.git
```

### 方式一：Docker 部署（推荐生产环境）

**一键启动，无需安装依赖！**

```bash
# 1. 配置API密钥
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY

# 2. 构建并启动
docker-compose build
docker-compose up -d

# 3. 访问应用
# 前端: http://localhost
# API文档: http://localhost/api/docs
```

📖 详细说明: 
- [Docker 部署指南](DOCKER_DEPLOY.md)
- [VTK数据部署方案](docs/VTK数据部署方案.md) - 包含VTK可视化数据的部署选项

### 方式二：本地开发部署

#### 环境要求
- Python 3.11+
- Node.js 18+
- 阿里云百炼API密钥

#### 安装步骤

**1. 安装Python依赖**
```bash
pip install -r requirements.txt
```

**2. 配置环境变量**
```bash
# 复制并编辑后端配置
copy .env.example .env
# 编辑 .env 文件，填入你的阿里云百炼API密钥

# 复制前端配置（可选，使用默认配置即可）
cd frontend
copy .env.example .env
cd ..
```

**3. 安装前端依赖**
```bash
cd frontend
npm install
cd ..
```

**4. 启动后端（终端1）**
```bash
# 直接启动（开发模式，支持热重载）
python run.py

# 或生产模式（禁用热重载）
python run.py --no-reload
```

**5. 启动前端（终端2）**
```bash
cd frontend
npm run dev
```

**6. 访问应用**
- 🌐 前端界面: http://localhost:5173
- 📚 API文档: http://localhost:8000/docs
- 💚 健康检查: http://localhost:8000/health

### 配置说明

#### 后端配置 (`.env`)
| 配置项 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| DASHSCOPE_API_KEY | ✓ | - | 阿里云百炼API密钥 |
| DASHSCOPE_MODEL_NAME | ✗ | qwen-plus | LLM模型名称 |
| SERVER_HOST | ✗ | 0.0.0.0 | 服务器监听地址 |
| SERVER_PORT | ✗ | 8000 | 服务器端口 |

#### 前端配置 (可选)
前端会自动使用 `http://localhost:8000` 作为后端地址。如需修改，可在 `frontend/.env` 中配置。

## 📖 使用指南

### 工作流程

1. **输入参数** → 填写涂层成分、工艺参数、结构设计
2. **智能分析** → TopPhi模拟 + ML预测 + 历史数据对比
3. **性能预测** → 硬度、结合力等性能指标预测
4. **优化建议** → 成分/结构/工艺三个维度的优化方案
5. **实验验证** → 选择方案，输入实验结果
6. **迭代优化** → 系统分析结果，智能决策下一步

### 界面特性

- 💬 **流式输出**: 实时显示AI分析过程，打字机效果
- 📊 **分步展示**: 各节点结果独立卡片显示
- 🎨 **Markdown渲染**: 支持表格、列表、代码块等
- 📈 **3D可视化**: TopPhi模拟结果VTK可视化
- 📜 **历史查看**: 查看历史迭代记录

## 🏗️ 系统架构

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌──────────┐          ┌────────────┐  │
│  │ 浏览器    │ WebSocket│  FastAPI   │  │
│  │          │◄────────►│  Backend   │  │
│  │ Vue 3    │   HTTP   │            │  │
│  │ :5173    │◄────────►│  :8000     │  │
│  └──────────┘          └────────────┘  │
│                              │         │
│                        ┌─────▼──────┐  │
│                        │ LangGraph  │  │
│                        │  Workflow  │  │
│                        └────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

**架构特点**：
- ✅ 前后端分离，独立开发部署
- ✅ WebSocket实时双向通信
- ✅ LangGraph管理复杂工作流
- ✅ 配置文件统一管理

### 项目结构
```
TopMat_Agent/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── components/    # UI组件
│   │   ├── composables/   # 组合式函数
│   │   ├── stores/        # Pinia状态管理
│   │   ├── config/        # 配置文件 (新增)
│   │   └── App.vue        # 主应用
│   ├── .env               # 前端环境变量
│   └── package.json       # 前端依赖
├── src/
│   ├── api/               # FastAPI后端
│   │   ├── routes/        # API路由
│   │   └── websocket/     # WebSocket处理
│   ├── graph/             # LangGraph工作流
│   │   ├── workflow.py    # 工作流编排
│   │   ├── nodes.py       # 节点实现
│   │   └── state.py       # 状态定义
│   ├── llm/               # LLM配置
│   ├── services/          # 业务服务层
│   └── models/            # 数据模型
├── docs/                  # 文档
├── .env                   # 后端环境变量
├── .env.example           # 环境变量示例
├── run.py                 # 启动脚本 (简化版)
└── requirements.txt       # Python依赖
```

### 技术栈

**前端**
- Vue 3 + Composition API
- Element Plus + Naive UI
- Vite
- VTK.js (3D可视化)
- Pinia (状态管理)

**后端**
- FastAPI
- LangGraph
- 阿里云百炼 (Qwen)
- Uvicorn

**开发工具**
- 热重载支持
- 环境变量配置
- 统一配置管理

## 🔧 核心工作流

LangGraph 工作流包含以下关键节点：

**分析阶段**
1. 输入参数验证
2. TopPhi第一性原理模拟
3. ML性能预测
4. 历史数据对比
5. 综合分析与根因诊断

**优化阶段**
6. P1 成分优化建议
7. P2 结构优化建议
8. P3 工艺优化建议
9. 优化方案汇总

**迭代阶段**
10. 实验工单生成
11. 实验结果分析
12. 迭代决策

### API文档

启动后访问 http://localhost:8000/docs 查看完整的 Swagger 文档。

## 🎯 核心功能

**1. 智能分析**
- 多源数据融合（TopPhi + ML + 历史数据）
- 根因分析，解释性能背后的物理机制
- 流式输出，实时展示分析过程

**2. 三维优化**
- **P1 成分优化**: 元素配比、微量元素添加
- **P2 结构优化**: 多层/梯度/纳米复合结构
- **P3 工艺优化**: 温度/气压/偏压等参数

**3. 实验闭环**
- 生成详细实验工单
- 分析实验结果
- 智能决策下一步行动

**4. 可视化**
- TopPhi模拟结果VTK 3D可视化
- 时间序列动画播放
- 历史迭代记录查看

## 🐛 常见问题

**Q: 后端启动失败？**  
A: 检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确配置。

**Q: 前端无法连接后端？**  
A: 确认后端服务已启动（http://localhost:8000），检查防火墙设置。

**Q: 如何修改服务端口？**  
A: 编辑 `.env` 文件中的 `SERVER_PORT` 配置项。

**Q: 如何查看日志？**  
A: 后端日志直接输出到控制台，前端问题检查浏览器开发者工具。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

