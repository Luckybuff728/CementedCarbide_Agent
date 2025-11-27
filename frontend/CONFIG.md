# 前端配置说明

## 📝 快速配置

所有端口配置统一在 `.env` 文件中管理，修改一处即可全局生效。

### 基础配置（推荐）

编辑 `frontend/.env` 文件：

```env
# 后端服务端口（最重要！）
VITE_BACKEND_PORT=8000

# 前端开发服务器端口
VITE_DEV_PORT=5173

# 后端主机地址（开发环境）
VITE_BACKEND_HOST=localhost
```

### 高级配置（可选）

如果需要完全自定义URL（例如使用域名），可以直接设置完整URL：

```env
# 完整URL配置（会覆盖上述端口配置）
VITE_API_BASE_URL=http://api.example.com
VITE_WS_BASE_URL=ws://api.example.com
```

---

## 🎯 使用场景

### 场景1：修改后端端口

**只需改一处：**

```env
VITE_BACKEND_PORT=9000  # 原 8000 改为 9000
```

自动生效于：
- ✅ WebSocket连接: `ws://localhost:9000`
- ✅ API代理: `http://localhost:9000`
- ✅ 所有API请求

### 场景2：修改前端开发端口

```env
VITE_DEV_PORT=3000  # 原 5173 改为 3000
```

重启开发服务器后，访问 `http://localhost:3000`

### 场景3：局域网访问开发环境

不需要修改配置！前端会自动使用当前访问的主机名：

```
访问: http://192.168.1.100:5173
自动连接: ws://192.168.1.100:8000/ws/coating
```

### 场景4：使用远程后端

```env
VITE_BACKEND_HOST=192.168.1.200
VITE_BACKEND_PORT=8000
```

### 场景5：生产环境（Docker）

生产环境不需要配置端口！会自动通过Nginx代理。

---

## 📂 配置文件层级

```
frontend/
├── .env                    # 开发环境配置（本地修改）
├── .env.example            # 配置模板
├── .env.production         # 生产环境配置（Docker用）
├── vite.config.js          # Vite配置（从.env读取）
└── src/
    └── config/
        └── index.js        # 运行时配置（从.env读取）
```

**配置优先级：**
1. 完整URL配置（`VITE_API_BASE_URL`）
2. 端口配置（`VITE_BACKEND_PORT`）
3. 默认值（`8000`）

---

## 🔍 配置验证

### 检查当前配置

在浏览器控制台执行：

```javascript
import.meta.env  // 查看所有环境变量
```

### 查看实际连接

```javascript
import { API_BASE_URL, WS_BASE_URL } from '@/config'
console.log('API:', API_BASE_URL)
console.log('WebSocket:', WS_BASE_URL)
```

---

## ⚙️ 配置原理

### 开发环境

```
浏览器 → Vite Dev Server (5173) → Proxy → 后端 (8000)
         ↓
      WebSocket 直连 → 后端 (8000)
```

- **API请求**: 通过Vite proxy转发，使用相对路径 `/api/*`
- **WebSocket**: 直接连接后端 `ws://localhost:8000/ws/coating`

### 生产环境（Docker）

```
浏览器 → Nginx (80) → 前端静态文件
         ↓
       Proxy → 后端容器 (8000)
```

- **API请求**: 通过Nginx代理 `/api/*`
- **WebSocket**: 通过Nginx代理 `/ws/*`
- **不需要配置端口**：所有请求都通过Nginx

---

## 🐛 常见问题

### Q: 修改端口后不生效？

A: 需要重启开发服务器：
```bash
# Ctrl+C 停止
npm run dev
```

### Q: WebSocket连接失败？

A: 检查后端服务是否启动：
```bash
# 测试后端健康检查
curl http://localhost:8000/health
```

### Q: 局域网访问前端正常，但无法连接后端？

A: 确保后端服务监听 `0.0.0.0` 而不是 `127.0.0.1`：
```env
# 后端 .env
SERVER_HOST=0.0.0.0
```

### Q: Docker部署需要修改配置吗？

A: **不需要！** 生产环境自动使用相对路径和Nginx代理。

---

## 📚 相关文件

- `frontend/.env` - 开发环境配置
- `frontend/src/config/index.js` - 运行时配置
- `frontend/vite.config.js` - Vite开发服务器配置
- `nginx.conf` - 生产环境Nginx代理配置
- `docker-compose.yml` - Docker端口映射

---

## ✅ 配置清单

修改端口时检查：

- [ ] 修改 `frontend/.env` 中的 `VITE_BACKEND_PORT`
- [ ] 修改后端 `.env` 中的 `SERVER_PORT`（如果修改后端端口）
- [ ] 重启前端开发服务器
- [ ] 重启后端服务器（如果修改后端端口）
- [ ] 测试连接是否正常

---

**💡 提示**：始终优先修改 `.env` 文件，避免修改代码中的端口配置！
