"""
TopMat Agent API

对话式多 Agent 智能研发助手
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from .routes import vtk_router, auth_router, setup_websocket_routes
from ..db.session import engine, Base
from ..models import user as user_model

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="TopMat Agent API",
    description="硬质合金涂层智能研发助手 - 硬质合金涂层研发优化",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
	Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(vtk_router)
app.include_router(auth_router)

# 设置WebSocket路由
setup_websocket_routes(app)


# 基本路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "TopMat Agent API",
        "version": "2.0.0",
        "status": "running",
        "description": "对话式多 Agent 智能研发助手"
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
    """API 信息"""
    return {
        "architecture": "Conversational Multi-Agent",
        "agents": [
            "Router - 智能路由",
            "Assistant - 通用对话 (思考模式)",
            "Validator - 参数验证专家",
            "Analyst - 性能预测专家",
            "Optimizer - 优化建议专家",
            "Experimenter - 实验管理专家"
        ],
        "features": [
            "对话式交互，自然语言理解",
            "思考过程可见，提升可解释性",
            "流式输出，实时响应"
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
    logger.info("对话式多 Agent 系统已就绪")


@app.on_event("shutdown")  
async def shutdown_event():
    """应用关闭事件"""
    logger.info("TopMat Agent API 正在关闭")
