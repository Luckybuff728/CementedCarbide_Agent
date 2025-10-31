# TopMat Agent Docker 开发环境部署指南

## 📦 架构说明

本Docker配置将**前端和后端整合在一个容器中**，适合开发环境使用：

- **前端**: Vue 3 + Vite 开发服务器（端口 5173）
- **后端**: FastAPI + LangGraph（端口 8000）
- **热重载**: 支持代码修改实时生效

## 🚀 快速启动

### 前置要求

- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 确保Docker Desktop已启动

### 一键启动

```bash
# Windows
docker-start.bat

# Linux/Mac
docker-compose up -d
```

### 访问服务

启动完成后，在浏览器访问：

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🛠️ 常用命令

### 启动服务

```bash
docker-compose up -d
```

### 停止服务

```bash
# Windows
docker-stop.bat

# Linux/Mac
docker-compose down
```

### 查看日志

```bash
# Windows
docker-logs.bat

# Linux/Mac
docker-compose logs -f
```

### 重新构建镜像

```bash
docker-compose build --no-cache
docker-compose up -d
```

### 进入容器调试

```bash
docker exec -it topmat-agent-dev bash
```

## 📂 目录结构

```
TopMat_Agent_1.0/
├── Dockerfile              # Docker镜像定义
├── docker-compose.yml      # Docker Compose配置
├── .dockerignore          # Docker忽略文件
├── docker-start.bat       # Windows启动脚本
├── docker-stop.bat        # Windows停止脚本
├── docker-logs.bat        # Windows日志查看脚本
└── DOCKER_README.md       # 本文档
```

## ⚙️ 配置说明

### 端口映射

- `5173:5173` - 前端Vite开发服务器
- `8000:8000` - 后端FastAPI服务

### 数据卷挂载

为了支持热重载，以下目录被挂载到容器：

```yaml
volumes:
  - ./src:/app/src              # 后端源代码
  - ./frontend/src:/app/frontend/src  # 前端源代码
  - ./.env:/app/.env            # 环境配置
```

修改这些目录中的代码会自动重载，无需重启容器。

### 环境变量

在 `.env` 文件中配置：

```bash
# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 其他配置...
```

## 🔧 故障排查

### 容器启动失败

1. **检查Docker是否运行**
   ```bash
   docker info
   ```

2. **查看详细错误日志**
   ```bash
   docker-compose logs
   ```

3. **清理并重新构建**
   ```bash
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   docker-compose up -d
   ```

### 端口占用

如果端口被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "5174:5173"  # 将前端端口改为5174
  - "8001:8000"  # 将后端端口改为8001
```

### 代码修改不生效

1. **确认数据卷挂载**
   ```bash
   docker-compose config
   ```

2. **重启容器**
   ```bash
   docker-compose restart
   ```

### Python依赖缺失

如果添加了新的Python依赖：

```bash
# 1. 在本地更新 requirements.txt
pip freeze > requirements.txt

# 2. 重新构建镜像
docker-compose build
docker-compose up -d
```

### 前端依赖缺失

如果添加了新的npm包：

```bash
# 1. 在本地更新 package.json
cd frontend
npm install <package-name>

# 2. 重新构建镜像
cd ..
docker-compose build
docker-compose up -d
```

## 📊 资源监控

### 查看容器资源使用

```bash
docker stats topmat-agent-dev
```

### 查看容器详细信息

```bash
docker inspect topmat-agent-dev
```

## 🔄 开发工作流

1. **首次启动**
   ```bash
   docker-start.bat
   ```

2. **日常开发**
   - 修改代码（自动热重载）
   - 查看日志：`docker-logs.bat`
   - 访问界面：http://localhost:5173

3. **停止服务**
   ```bash
   docker-stop.bat
   ```

## 💡 提示

- ✅ 支持代码热重载，修改后自动生效
- ✅ 前后端在同一容器中，网络通信更快
- ✅ 适合开发和测试环境
- ⚠️ 不建议用于生产环境（生产环境应分离部署）
- ⚠️ 首次构建可能需要较长时间（下载依赖）
- ⚠️ 确保 `.env` 文件已配置API密钥

## 📝 注意事项

1. **环境配置**: 启动前请确保 `.env` 文件已正确配置
2. **网络访问**: 容器内服务可通过 `localhost` 或 `127.0.0.1` 访问
3. **日志查看**: 建议使用 `docker-logs.bat` 实时查看日志
4. **数据持久化**: 当前配置不持久化数据，重启容器后会话数据会丢失
5. **性能优化**: 如需提升性能，可考虑使用生产模式部署

## 🆘 获取帮助

如遇到问题，请：

1. 查看容器日志：`docker-compose logs`
2. 检查Docker版本：`docker --version` 和 `docker-compose --version`
3. 确认端口未被占用：`netstat -ano | findstr "5173 8000"`
4. 检查 `.env` 配置是否正确
