"""
FastAPI后端服务 - 重构版本
拆分路由，简化主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from .routes import vtk_router, setup_websocket_routes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="TopMat Agent API",
    description="硬质合金涂层优化专家系统API",
    version="1.0.1"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(vtk_router)

# 设置WebSocket路由
setup_websocket_routes(app)


# 基本路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "TopMat Agent API",
        "version": "1.0.1",
        "status": "running",
        "description": "重构版 - 使用Service层架构"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "validation_service": "active",
            "optimization_service": "active",
            "coating_service": "active"
        }
    }


@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "architecture": "Service Layer Pattern",
        "improvements": [
            "修复了成分验证逻辑bug",
            "消除了P1/P2/P3节点代码重复",
            "引入了Service层抽象",
            "拆分了大文件为模块化结构",
            "简化了WebSocket协议"
        ],
        "services": [
            "ValidationService - 输入验证",
            "OptimizationService - 优化建议生成", 
            "CoatingService - 核心业务逻辑"
        ]
    }


# 异常处理
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """处理值错误"""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": "参数错误", "detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "内部服务器错误", "detail": "请稍后重试"}
    )


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("TopMat Agent API 启动完成")
    logger.info("Service层架构已激活")


@app.on_event("shutdown")  
async def shutdown_event():
    """应用关闭事件"""
    logger.info("TopMat Agent API 正在关闭")
