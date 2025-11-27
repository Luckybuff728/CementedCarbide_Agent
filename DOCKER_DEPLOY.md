# Docker 生产环境部署指南

## 📋 特点

- ✅ **精简镜像**: 多阶段构建，优化镜像体积
- ✅ **安全加固**: 非root用户运行
- ✅ **健康检查**: 自动监控服务状态
- ✅ **资源限制**: 防止资源过度占用
- ✅ **前后端分离**: 独立扩展和部署

## 🚀 快速部署

### 1. 选择部署方案

#### 方案A：VTK数据打包到镜像（推荐）
适用于演示和数据不变的生产环境。
- ✅ 配置简单，即开即用
- ✅ 数据随镜像分发
- ⚠️ 镜像体积增加约60MB
- ⚠️ 更新数据需重新构建镜像

使用默认的 `docker-compose.yml`

#### 方案B：Volume挂载VTK数据
适用于需要频繁更新VTK数据的场景。
- ✅ 数据独立管理，易于更新
- ✅ 镜像体积小
- ⚠️ 部署时需单独上传数据文件
- ⚠️ 需确保数据目录权限正确

使用 `docker-compose.volume.yml`：
```bash
# 在服务器上创建数据目录并上传VTK文件
mkdir -p 涂层-调幅分解
# 上传所有VTK文件到对应目录
```

### 2. 配置环境变量

编辑 `.env` 文件（或创建）：

```bash
# 必需配置
DASHSCOPE_API_KEY=你的阿里云百炼API密钥

# 可选配置
DASHSCOPE_MODEL_NAME=qwen-plus
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/topmat.db
```

### 3. 构建并启动

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

| 镜像 | 方案A（打包VTK） | 方案B（Volume挂载） |
|------|-----------------|-------------------|
| 后端 | ~460MB（含60MB VTK数据） | ~400MB |
| 前端 | ~50MB | ~50MB |
| **总计** | **~510MB** | **~450MB** |

## 🔧 常用命令

### 服务管理

```bash
# 方案A（默认）
docker-compose up -d

# 方案B（Volume挂载）
docker-compose -f docker-compose.volume.yml up -d

# 停止服务
docker-compose down
# 或
docker-compose -f docker-compose.volume.yml down

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

## 🌐 公网部署注意事项

### VTK 文件传输优化

部署到公网后，VTK 文件（60MB）传输可能受带宽影响：

**已优化配置：**
- ✅ Nginx 超时时间延长至 5 分钟
- ✅ 流式传输大文件
- ✅ 浏览器缓存（1天）
- ✅ CORS 跨域支持

**建议进一步优化：**
1. **启用 Gzip 压缩** - 可减少 70% 传输量
2. **前端预加载** - 提升动画流畅度
3. **使用 CDN** - 大规模部署时推荐

📖 详细说明：[公网部署VTK优化指南](docs/公网部署VTK优化指南.md)

### HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
# 1. 安装 Certbot
apt-get install certbot python3-certbot-nginx

# 2. 获取证书
certbot --nginx -d yourdomain.com

# 3. 自动续期
certbot renew --dry-run
```

## 📝 生产环境清单

- [ ] 配置正确的API密钥
- [ ] 设置合适的资源限制
- [ ] 配置日志轮转
- [ ] 备份策略
- [ ] 监控和告警
- [ ] HTTPS证书
- [ ] 防火墙规则
- [ ] VTK传输优化（公网部署必须）
- [ ] 带宽评估（建议 >20Mbps）

---

遇到问题？查看[主文档](README.md)或提交Issue。
