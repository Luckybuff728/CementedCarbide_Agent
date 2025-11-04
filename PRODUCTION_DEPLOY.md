# TopMat Agent 生产环境部署指南

## 📦 架构说明

本Docker配置采用**前后端分离架构**，专为生产环境优化：

- **后端**: FastAPI + LangGraph（Python 3.11）
- **前端**: Nginx + 静态资源（Vue 3构建产物）
- **网络**: 独立容器通信，Nginx反向代理
- **优化**: 多阶段构建，最小化镜像体积

## 🎯 镜像大小对比

| 环境 | 架构 | 后端镜像 | 前端镜像 | 总体积 |
|------|------|---------|---------|--------|
| 开发环境 | 单容器 | ~2.5GB | - | ~2.5GB |
| **生产环境** | **分离** | **~400MB** | **~50MB** | **~450MB** |

**优化效果**: 减少约 **82%** 的镜像体积

## ✨ 生产环境特性

### 1. 镜像优化
- ✅ 多阶段构建 - 分离构建和运行环境
- ✅ 最小化基础镜像 - 使用alpine/slim版本
- ✅ 移除开发工具 - 不包含git、gcc等
- ✅ 优化依赖安装 - 虚拟环境隔离

### 2. 安全加固
- ✅ 非root用户运行
- ✅ 最小权限原则
- ✅ 健康检查机制
- ✅ 安全HTTP头设置

### 3. 性能优化
- ✅ Uvicorn多进程模式（4 workers）
- ✅ Nginx静态文件服务
- ✅ Gzip压缩
- ✅ 静态资源缓存（1年）
- ✅ 资源限制（CPU/内存）

### 4. 运维友好
- ✅ 自动重启策略
- ✅ 健康检查
- ✅ 日志轮转
- ✅ 依赖等待机制

## 🚀 快速部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存

### 一键部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 DASHSCOPE_API_KEY

# 2. 构建并启动
docker-compose build
docker-compose up -d

# 3. 查看状态
docker-compose ps
```

### 访问服务

- **前端界面**: http://localhost
- **API文档**: http://localhost/api/docs (通过Nginx代理)
- **健康检查**: http://localhost/health

## 📋 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f           # 全部日志
docker-compose logs -f backend   # 后端日志
docker-compose logs -f frontend  # 前端日志
```

### 镜像管理

```bash
# 重新构建（强制）
docker-compose build --no-cache

# 查看镜像大小
docker-compose images

# 清理未使用的镜像
docker system prune -a
```

### 容器管理

```bash
# 进入后端容器
docker exec -it topmat-backend bash

# 进入前端容器（alpine系统）
docker exec -it topmat-frontend sh

# 查看容器资源使用
docker stats topmat-backend topmat-frontend
```

## 🔧 配置说明

### 环境变量（.env）

```bash
# LLM配置
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL_NAME=qwen-plus

# 日志级别
LOG_LEVEL=info
```

### 资源限制

**后端服务**:
- CPU限制: 2核
- 内存限制: 2GB
- 预留: 0.5核 / 512MB

**前端服务**:
- CPU限制: 0.5核
- 内存限制: 256MB
- 预留: 0.1核 / 64MB

### 日志配置

- 日志驱动: json-file
- 后端: 最大10MB/文件，保留3个文件
- 前端: 最大5MB/文件，保留3个文件

### 健康检查

**后端**:
- 检查间隔: 30秒
- 超时: 10秒
- 启动时间: 40秒
- 重试次数: 3次

**前端**:
- 检查间隔: 30秒
- 超时: 3秒
- 启动时间: 10秒
- 重试次数: 3次

## 🔄 更新部署

### 代码更新

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建
docker-compose build

# 3. 滚动更新（零停机）
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

### 依赖更新

```bash
# Python依赖更新
# 1. 修改 requirements.txt
# 2. 重新构建后端
docker-compose build backend
docker-compose up -d backend

# 前端依赖更新
# 1. 修改 frontend/package.json
# 2. 重新构建前端
docker-compose build frontend
docker-compose up -d frontend
```

## 🐛 故障排查

### 服务无法启动

```bash
# 1. 查看详细日志
docker-compose logs

# 2. 检查容器状态
docker-compose ps

# 3. 检查健康状态
docker inspect topmat-backend | grep -A 5 Health
docker inspect topmat-frontend | grep -A 5 Health
```

### 端口冲突

如果80端口被占用，修改 `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "8080:80"  # 改为8080端口
```

### 内存不足

如果内存不足，调整资源限制:

```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 1G  # 降低到1G
```

### API无法访问

1. 检查后端健康状态
```bash
docker exec topmat-backend curl http://localhost:8000/health
```

2. 检查Nginx配置
```bash
docker exec topmat-frontend cat /etc/nginx/conf.d/default.conf
```

3. 查看Nginx日志
```bash
docker-compose logs frontend
```

## 📊 监控和日志

### 查看实时日志

```bash
# 后端日志（JSON格式）
docker-compose logs -f --tail=100 backend

# 前端访问日志
docker-compose logs -f --tail=100 frontend

# 过滤错误日志
docker-compose logs backend | grep ERROR
```

### 性能监控

```bash
# 实时资源监控
docker stats topmat-backend topmat-frontend

# 查看容器详细信息
docker inspect topmat-backend
docker inspect topmat-frontend
```

## 🔐 安全建议

1. **API密钥管理**
   - 不要将 .env 文件提交到Git
   - 使用环境变量或密钥管理服务

2. **网络安全**
   - 生产环境建议使用HTTPS
   - 配置防火墙规则
   - 限制容器间通信

3. **更新维护**
   - 定期更新基础镜像
   - 及时修复安全漏洞
   - 监控依赖包安全公告

## 📈 性能调优

### 后端优化

调整workers数量（根据CPU核心数）:

```dockerfile
# Dockerfile 中修改
CMD ["uvicorn", "src.api.main:app", \
     "--workers", "8"]  # 改为8个worker
```

### 前端优化

Nginx缓存配置已优化:
- 静态资源缓存1年
- Gzip压缩
- HTTP/2支持（需HTTPS）

### 数据库优化

未来如需添加数据库:
```yaml
database:
  image: postgres:15-alpine
  volumes:
    - postgres_data:/var/lib/postgresql/data
  environment:
    POSTGRES_PASSWORD: ${DB_PASSWORD}
```

## 🎯 生产环境检查清单

部署前检查：
- [ ] `.env` 文件已配置
- [ ] API密钥有效
- [ ] Docker和Docker Compose已安装
- [ ] 端口80未被占用
- [ ] 至少2GB可用内存

部署后验证：
- [ ] 容器状态健康 (`docker-compose ps`)
- [ ] 前端可访问 (http://localhost)
- [ ] API文档可访问 (http://localhost/api/docs)
- [ ] 健康检查通过 (http://localhost/health)
- [ ] WebSocket连接正常
- [ ] 日志无严重错误

## 📞 技术支持

如遇问题：
1. 查看本文档的故障排查章节
2. 检查容器日志: `docker-compose logs`
3. 查看健康状态: `docker-compose ps`
4. 提交Issue并附上错误日志

---

**最后更新**: 2025-11-04  
**版本**: 1.0 生产环境
