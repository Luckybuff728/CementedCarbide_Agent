# Docker 生产环境部署指南

## 📋 特点

- ✅ **精简镜像**: 多阶段构建，优化镜像体积
- ✅ **安全加固**: 非root用户运行
- ✅ **健康检查**: 自动监控服务状态
- ✅ **资源限制**: 防止资源过度占用
- ✅ **前后端分离**: 独立扩展和部署

## 🚀 快速部署

### 1. 配置环境变量

编辑 `.env` 文件（或创建）：

```bash
# 必需配置
DASHSCOPE_API_KEY=你的阿里云百炼API密钥

# 可选配置
DASHSCOPE_MODEL_NAME=qwen-plus
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/topmat.db
```

### 2. 构建并启动

```bash
# 构建镜像
docker-compose build

# 启动服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 访问应用

- 🌐 前端界面: http://localhost
- 📚 API文档: http://localhost/api/docs
- 💚 健康检查: http://localhost/health

## 📊 镜像大小

| 镜像 | 大小（预计） |
|------|-------------|
| 后端 | ~400MB |
| 前端 | ~50MB |
| **总计** | **~450MB** |

## 🔧 常用命令

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
docker-compose logs -f [backend|frontend]
```

### 镜像管理

```bash
# 重新构建
docker-compose build --no-cache

# 拉取最新基础镜像
docker-compose pull

# 清理未使用的镜像
docker image prune -a
```

### 数据管理

```bash
# 备份数据卷
docker run --rm -v topmat_backend-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz -C /data .

# 恢复数据卷
docker run --rm -v topmat_backend-data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /data
```

## 🐛 故障排查

### 服务无法启动

```bash
# 检查日志
docker-compose logs backend
docker-compose logs frontend

# 检查容器状态
docker-compose ps

# 进入容器调试
docker-compose exec backend /bin/bash
docker-compose exec frontend /bin/sh
```

### 后端健康检查失败

检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确配置。

### 前端无法访问后端

确保 `docker-compose.yml` 中的网络配置正确，前后端在同一网络中。

### 端口冲突

修改 `docker-compose.yml` 中的端口映射：
```yaml
frontend:
  ports:
    - "8080:80"  # 改为其他端口
```

## 📈 性能优化

### 资源限制调整

编辑 `docker-compose.yml` 中的资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # 增加CPU限制
      memory: 4G     # 增加内存限制
```

### 扩展后端实例

```bash
# 启动多个后端实例
docker-compose up -d --scale backend=3
```

### 日志轮转

使用 Docker 日志驱动配置日志轮转：

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔒 安全建议

1. **不要将 `.env` 提交到版本控制**
2. **使用独立的数据库**（生产环境推荐PostgreSQL）
3. **配置HTTPS**（使用Nginx反向代理或Caddy）
4. **定期更新基础镜像**
5. **限制容器资源使用**

## 📝 生产环境清单

- [ ] 配置正确的API密钥
- [ ] 设置合适的资源限制
- [ ] 配置日志轮转
- [ ] 备份策略
- [ ] 监控和告警
- [ ] HTTPS证书
- [ ] 防火墙规则

---

遇到问题？查看[主文档](README.md)或提交Issue。
