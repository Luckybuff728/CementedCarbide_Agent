# ✅ TopMat Agent Docker 部署配置完成

## 📦 已创建的文件

### 核心配置文件
- ✅ `Dockerfile` - Docker镜像定义（前后端整合）
- ✅ `docker-compose.yml` - Docker Compose编排配置
- ✅ `.dockerignore` - Docker构建忽略规则
- ✅ `docker_run.py` - Docker环境专用启动脚本

### Windows便捷脚本
- ✅ `docker-start.bat` - 一键启动
- ✅ `docker-stop.bat` - 一键停止
- ✅ `docker-logs.bat` - 查看日志
- ✅ `docker-check.bat` - 启动前环境检查
- ✅ `docker-rebuild.bat` - 重新构建镜像

### 文档
- ✅ `DOCKER_快速开始.md` - 快速启动指南
- ✅ `DOCKER_README.md` - 详细使用文档
- ✅ `DOCKER_部署完成.md` - 本文档

### 已修改的文件
- ✅ `frontend/vite.config.js` - 修改端口为5173，支持Docker

---

## 🎯 部署架构

```
┌─────────────────────────────────────┐
│   Docker 容器 (topmat-agent-dev)     │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Vue 前端    │  │  FastAPI    │ │
│  │  (5173端口)  │  │  后端       │ │
│  │              │  │  (8000端口) │ │
│  └──────────────┘  └─────────────┘ │
│                                     │
│  热重载: src/ 和 frontend/src/      │
└─────────────────────────────────────┘
         ↓           ↓
    端口映射    端口映射
         ↓           ↓
    localhost:5173  localhost:8000
```

**特点：**
- ✅ 前后端在同一容器中，通信更快
- ✅ 支持代码热重载，修改即生效
- ✅ 统一管理，一条命令启动/停止

---

## 🚀 快速开始（三步走）

### 第1步：环境检查

```bash
# 运行环境检查（Windows）
docker-check.bat
```

**检查内容：**
- Docker是否安装并运行
- 端口5173和8000是否可用
- .env配置文件是否存在

### 第2步：配置环境变量

如果`.env`文件不存在，检查脚本会自动创建。

**编辑 `.env` 文件，填写你的API密钥：**

```bash
# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here  # ⚠️ 必须填写
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 或使用其他LLM提供商
# LLM_PROVIDER=dashscope
# DASHSCOPE_API_KEY=your_api_key_here
```

### 第3步：启动容器

```bash
# Windows用户（推荐）
docker-start.bat

# 或使用命令行
docker-compose up -d
```

**等待约30秒**，服务初始化完成后访问：

- 🌐 前端界面: http://localhost:5173
- 🔌 后端API: http://localhost:8000
- 📚 API文档: http://localhost:8000/docs

---

## 📋 常用操作命令

### 查看运行状态
```bash
docker-compose ps
```

### 查看实时日志
```bash
docker-logs.bat              # Windows
docker-compose logs -f       # Linux/Mac
```

### 停止服务
```bash
docker-stop.bat              # Windows
docker-compose down          # Linux/Mac
```

### 重启服务
```bash
docker-compose restart
```

### 重新构建
```bash
docker-rebuild.bat           # Windows（推荐）
docker-compose build --no-cache && docker-compose up -d  # 手动
```

### 进入容器调试
```bash
docker exec -it topmat-agent-dev bash
```

---

## 🔥 开发工作流

### 场景1：日常开发

```bash
# 1. 启动服务
docker-start.bat

# 2. 修改代码（自动热重载）
#    - 修改 src/ 下的Python代码
#    - 修改 frontend/src/ 下的Vue代码

# 3. 访问 http://localhost:5173 查看效果

# 4. 停止服务
docker-stop.bat
```

### 场景2：添加Python依赖

```bash
# 1. 编辑 requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. 重新构建
docker-rebuild.bat
```

### 场景3：添加npm依赖

```bash
# 1. 编辑 frontend/package.json
#    添加新的依赖

# 2. 重新构建
docker-rebuild.bat
```

### 场景4：清理环境

```bash
# 完全清理并重建
docker-compose down
docker system prune -af
docker-compose build --no-cache
docker-compose up -d
```

---

## 🐛 故障排查

### 问题1：容器启动失败

**症状：** `docker-start.bat` 运行失败

**解决步骤：**
```bash
# 1. 查看错误日志
docker-compose logs

# 2. 检查端口占用
netstat -ano | findstr "5173 8000"

# 3. 确认配置文件
docker-compose config

# 4. 重新构建
docker-rebuild.bat
```

### 问题2：前端无法访问

**症状：** http://localhost:5173 打不开

**解决步骤：**
```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看前端日志
docker exec -it topmat-agent-dev tail -f /app/frontend.log

# 3. 确认端口映射
docker-compose port topmat-agent 5173
```

### 问题3：后端API报错

**症状：** API请求失败或500错误

**解决步骤：**
```bash
# 1. 查看后端日志
docker-compose logs -f topmat-agent

# 2. 检查环境变量
docker exec -it topmat-agent-dev env | grep API

# 3. 确认.env文件已挂载
docker exec -it topmat-agent-dev cat /app/.env
```

### 问题4：代码修改不生效

**症状：** 修改代码后没有热重载

**解决步骤：**
```bash
# 1. 确认数据卷挂载
docker-compose config | findstr volumes

# 2. 重启容器
docker-compose restart

# 3. 如果是依赖修改，需重新构建
docker-rebuild.bat
```

---

## 📊 性能调优

### Docker Desktop设置（Windows）

1. 打开 Docker Desktop
2. Settings → Resources
3. 建议配置：
   - **CPU**: 4核或更多
   - **Memory**: 4GB或更多
   - **Disk**: 20GB或更多

### 加速构建

```bash
# 使用国内镜像源（可选）
# 编辑 Dockerfile，在开头添加：
# RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
# RUN npm config set registry https://registry.npmmirror.com
```

---

## 🎓 学习资源

### Docker基础
- Docker官方文档: https://docs.docker.com/
- Docker Compose文档: https://docs.docker.com/compose/

### 项目相关
- FastAPI文档: https://fastapi.tiangolo.com/
- Vue 3文档: https://vuejs.org/
- LangGraph文档: https://langchain-ai.github.io/langgraph/

---

## ⚠️ 重要提示

1. **环境变量**
   - ⚠️ 必须配置 `.env` 文件中的API密钥
   - ⚠️ 容器启动时会自动加载 `.env`

2. **端口冲突**
   - ⚠️ 确保5173和8000端口未被占用
   - ⚠️ 如需修改端口，编辑 `docker-compose.yml`

3. **数据持久化**
   - ⚠️ 当前配置不持久化会话数据
   - ⚠️ 重启容器后会话历史会丢失
   - ✅ 可通过添加数据卷实现持久化

4. **开发vs生产**
   - ✅ 本配置适用于开发环境
   - ⚠️ 生产环境建议分离前后端部署
   - ⚠️ 生产环境需要额外的安全配置

5. **首次启动**
   - ⏱️ 首次构建需要5-10分钟（下载依赖）
   - ⏱️ 首次启动需要约30秒（服务初始化）
   - ✅ 后续启动会更快（使用缓存）

---

## 📝 版本信息

- **Docker**: 要求 20.10+
- **Docker Compose**: 要求 2.0+
- **Python**: 3.11
- **Node.js**: 18.x
- **部署方式**: 单容器（前后端整合）

---

## 🎉 部署成功标志

看到以下内容说明部署成功：

```
✓ Container topmat-agent-dev  Started

服务地址:
  前端: http://localhost:5173
  后端: http://localhost:8000
  API文档: http://localhost:8000/docs
```

**现在可以在浏览器访问前端界面，开始使用 TopMat Agent！**

---

## 📧 获取支持

如遇到无法解决的问题：

1. 查看详细日志: `docker-compose logs`
2. 检查环境配置: `docker-check.bat`
3. 查阅文档: `DOCKER_README.md`
4. 重置环境: `docker-rebuild.bat`

---

**祝你使用愉快！ 🚀**
