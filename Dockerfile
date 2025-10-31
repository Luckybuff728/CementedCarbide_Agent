# TopMat Agent 开发环境 - 前后端整合Docker镜像
FROM python:3.11-slim

# 安装Node.js和必要的系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制前端依赖文件
COPY frontend/package*.json ./frontend/

# 安装前端依赖
WORKDIR /app/frontend
RUN npm install

# 复制整个项目
WORKDIR /app
COPY . .

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "========================================"\n\
echo "  TopMat Agent 开发环境启动中..."\n\
echo "========================================"\n\
echo ""\n\
\n\
# 启动前端开发服务器（后台运行）\n\
echo "[1/2] 启动前端开发服务器..."\n\
cd /app/frontend\n\
npm run dev -- --host 0.0.0.0 > /app/frontend.log 2>&1 &\n\
FRONTEND_PID=$!\n\
echo "      前端服务 PID: $FRONTEND_PID"\n\
echo "      前端地址: http://localhost:5173"\n\
\n\
# 等待前端服务启动\n\
echo "      等待前端服务启动..."\n\
sleep 8\n\
\n\
# 启动后端服务（前台运行）\n\
echo ""\n\
echo "[2/2] 启动后端服务..."\n\
cd /app\n\
python docker_run.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口
# 5173: 前端开发服务器
# 8000: 后端FastAPI服务
EXPOSE 5173 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    NODE_ENV=development \
    VITE_API_BASE_URL=http://localhost:8000

# 启动命令
CMD ["/bin/bash", "/app/start.sh"]
